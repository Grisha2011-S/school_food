from flask_app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

MASTER_ADMIN_LOGIN = "admin"
MASTER_ADMIN_PASSWORD = "admin123"  # Измените на более безопасный пароль!

def create_master_admin():
    with app.app_context():
        # Создаем все таблицы (если их нет)
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")

        # Проверяем, существует ли уже главный админ
        try:
            if Admin.query.filter_by(is_master=True).first():
                print("Master admin already exists")
                return
        except Exception as e:
            print(f"Error checking admin existence: {str(e)}")
            return

        try:
            # Создаем главного админа
            admin = Admin(
                login=MASTER_ADMIN_LOGIN,
                password=generate_password_hash(MASTER_ADMIN_PASSWORD),
                is_master=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Master admin created successfully!")
            print(f"Login: {MASTER_ADMIN_LOGIN}")
            print(f"Password: {MASTER_ADMIN_PASSWORD}")
            
        except Exception as e:
            print(f"Error creating master admin: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_master_admin()