from werkzeug.security import generate_password_hash
from flask_app import app
from models import db, Admin

LOGIN = "-"           # <- замените на желаемый логин
PASSWORD = "-" # <- замените на желаемый пароль

with app.app_context():
    if Admin.query.count() > 0:
        print("Admin already exists; aborting.")
    else:
        admin = Admin(login=LOGIN, password=generate_password_hash(PASSWORD))
        db.session.add(admin)
        db.session.commit()
        print("Created admin:", LOGIN)
