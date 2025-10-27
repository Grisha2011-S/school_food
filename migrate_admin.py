from flask_app import app
from models import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Добавляем новые столбцы в таблицу admins
            for column_sql in [
                "ALTER TABLE admins ADD COLUMN activation_code VARCHAR(32)",
                "ALTER TABLE admins ADD COLUMN is_activated BOOLEAN DEFAULT 0",
                "ALTER TABLE admins ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ]:
                try:
                    db.session.execute(text(column_sql))
                    print(f"Successfully executed: {column_sql}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"Column already exists: {column_sql}")
                    else:
                        raise
            
            db.session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    migrate()