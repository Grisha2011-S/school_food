from flask_app import app
from models import db, Admin
from sqlalchemy import text

def recreate_admins_table():
    with app.app_context():
        try:
            # Сначала получаем текущих админов
            try:
                current_admins = Admin.query.all()
                admin_data = [(a.login, a.password) for a in current_admins]
            except Exception:
                admin_data = []
                print("Could not retrieve current admins")

            # Удаляем старую таблицу
            db.session.execute(text("DROP TABLE IF EXISTS admins"))
            db.session.commit()
            
            # Создаем таблицу заново
            db.create_all()
            
            # Восстанавливаем данные
            for login, password in admin_data:
                admin = Admin(login=login, password=password)
                db.session.add(admin)
            
            db.session.commit()
            print("Admins table recreated successfully!")
            
        except Exception as e:
            print(f"Recreation failed: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    recreate_admins_table()