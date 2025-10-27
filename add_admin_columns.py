from flask_app import app
from models import db
from sqlalchemy import text

def add_columns():
    with app.app_context():
        try:
            # Проверяем существующие столбцы
            columns = db.session.execute(text("PRAGMA table_info(admins)")).fetchall()
            column_names = [col[1] for col in columns]
            
            # Добавляем недостающие столбцы
            if 'is_master' not in column_names:
                db.session.execute(text("ALTER TABLE admins ADD COLUMN is_master BOOLEAN DEFAULT 0"))
                print("Added column: is_master")
                
            if 'created_by' not in column_names:
                db.session.execute(text("ALTER TABLE admins ADD COLUMN created_by INTEGER REFERENCES admins(id)"))
                print("Added column: created_by")
                
            if 'created_at' not in column_names:
                db.session.execute(text("ALTER TABLE admins ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                print("Added column: created_at")
                
            db.session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    add_columns()