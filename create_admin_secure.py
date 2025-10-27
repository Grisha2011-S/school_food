from werkzeug.security import generate_password_hash
from flask_app import app
from models import db, Admin
import os
import getpass
import sys

def create_admin(login=None, password=None, is_master=False):
    """
    Создает администратора с запросом учетных данных.
    
    Args:
        login: Опционально, логин администратора
        password: Опционально, пароль администратора
        is_master: Будет ли это мастер-админ
    """
    # Если логин не передан - запрашиваем
    if not login:
        login = input("Введите логин администратора: ").strip()
        if not login:
            print("Ошибка: логин не может быть пустым")
            return False
            
    # Проверяем существование админа с таким логином
    with app.app_context():
        if Admin.query.filter_by(login=login).first():
            print(f"Ошибка: администратор с логином '{login}' уже существует")
            return False
    
    # Если пароль не передан - запрашиваем дважды для подтверждения
    if not password:
        while True:
            password = getpass.getpass("Введите пароль: ")
            if not password:
                print("Ошибка: пароль не может быть пустым")
                continue
                
            password2 = getpass.getpass("Подтвердите пароль: ")
            if password != password2:
                print("Ошибка: пароли не совпадают")
                continue
            break
    
    # Проверяем минимальные требования к паролю
    if len(password) < 8:
        print("Ошибка: пароль должен содержать минимум 8 символов")
        return False
    
    # Создаем администратора
    try:
        with app.app_context():
            admin = Admin(
                login=login,
                password=generate_password_hash(password),
                is_master=is_master
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Администратор '{login}' успешно создан!")
            return True
    except Exception as e:
        print(f"Ошибка при создании администратора: {str(e)}")
        return False

if __name__ == "__main__":
    # Проверяем аргументы командной строки
    is_master = "--master" in sys.argv
    
    # Можно передать логин и пароль через переменные среды
    env_login = os.getenv("ADMIN_LOGIN")
    env_password = os.getenv("ADMIN_PASSWORD")
    
    if env_login and env_password:
        create_admin(env_login, env_password, is_master)
    else:
        create_admin(is_master=is_master)