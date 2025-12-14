import os
import sys

# Настройка пути проекта
project_home = '/home/SchoolFOD/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Настройка virtualenv
venv_paths = [
    '/home/SchoolFOD/.virtualenvs/school_food_env/bin/activate_this.py',
    '/home/SchoolFOD/.virtualenvs/myenv/bin/activate_this.py'
]
for venv_path in venv_paths:
    if os.path.exists(venv_path):
        with open(venv_path) as f:
            exec(f.read(), {'__file__': venv_path})
        break

# Настройка окружения
os.environ['GEMINI_API_KEY'] = 'AIzaSyAz-m_zcbkYEkzdfBjIMyqGz_Tz7qSBvRc'

# Импорт приложения
from flask_app import app as application

if __name__ == '__main__':
    application.run()