import os
import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin

# Секретный ключ активации (храните в безопасном месте, например в env)
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "your-very-long-secret-key-here")

def generate_activation_code(login: str) -> str:
    """Генерирует уникальный код активации на основе логина и времени"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data = f"{login}{timestamp}{ADMIN_SECRET}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()[:32]

def create_admin(login: str, password: str) -> tuple[bool, str, str | None]:
    """
    Создаёт неактивированного администратора.
    Возвращает (успех, сообщение, код_активации).
    """
    try:
        # Проверяем, нет ли уже активного админа
        if Admin.query.filter_by(is_activated=True).count() > 0:
            return False, "Активный администратор уже существует", None

        # Генерируем код активации
        activation_code = generate_activation_code(login)

        # Создаём админа
        admin = Admin(
            login=login,
            password=generate_password_hash(password),
            activation_code=activation_code
        )
        db.session.add(admin)
        db.session.commit()
        
        return True, f"Администратор {login} создан. Требуется активация.", activation_code
        
    except Exception as e:
        db.session.rollback()
        return False, f"Ошибка при создании администратора: {str(e)}", None

def verify_admin(login: str, password: str) -> tuple[bool, str]:
    """
    Проверяет существование и аутентификацию админа.
    Возвращает (успех, сообщение).
    """
    admin = Admin.query.filter_by(login=login).first()
    
    if not admin:
        return False, "Администратор не найден"
        
    if not check_password_hash(admin.password, password):
        return False, "Неверный пароль"
        
    if not admin.is_activated:
        return False, "Аккаунт не активирован"
        
    return True, "Успешная аутентификация"

def activate_admin(login: str, activation_code: str) -> tuple[bool, str]:
    """
    Активирует аккаунт администратора.
    Возвращает (успех, сообщение).
    """
    admin = Admin.query.filter_by(login=login).first()
    
    if not admin:
        return False, "Администратор не найден"
        
    if admin.is_activated:
        return False, "Аккаунт уже активирован"
        
    if admin.activate(activation_code):
        try:
            db.session.commit()
            return True, "Аккаунт успешно активирован"
        except Exception as e:
            db.session.rollback()
            return False, f"Ошибка при активации: {str(e)}"
    
    return False, "Неверный код активации"