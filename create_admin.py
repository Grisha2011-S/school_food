from werkzeug.security import generate_password_hash
from flask_app import app
from models import db, Admin

LOGIN = "-"           # <- замените на желаемый логин
PASSWORD = "-" # <- замените на желаемый пароль

with app.app_context():
    existing_admin = Admin.query.filter_by(login=LOGIN).first()
    
    if existing_admin:
        existing_admin.password = generate_password_hash(PASSWORD)
        db.session.commit()
        print(f"Updated password for admin: {LOGIN}")
    else:
        admin = Admin(login=LOGIN, password=generate_password_hash(PASSWORD))
        db.session.add(admin)
        db.session.commit()
        print(f"Created new admin: {LOGIN}")
