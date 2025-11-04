import os
import sys
from pathlib import Path

# Настройка пути проекта
project_home = Path(__file__).resolve().parent
if str(project_home) not in sys.path:
    sys.path.insert(0, str(project_home))

# Настройка virtualenv (если используется)
venv_path = Path('/home/SchoolFOD/.virtualenvs/myenv/bin/activate_this.py')
if venv_path.exists():
    with venv_path.open() as f:
        exec(f.read(), {'__file__': str(venv_path)})

# Настройка окружения перед импортом Flask приложения
os.environ.setdefault('GEMINI_API_KEY', 'AIzaSyALiST2y0go1Aen3_GnJjzjbr6UsBevn3I')

# Импорт и настройка логирования
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(str(project_home / 'logs' / 'wsgi.log'))
    ]
)
logger = logging.getLogger('wsgi')

try:
    # Импорт Flask приложения
    from flask_app import app as application
    logger.info('WSGI app loaded successfully')
except Exception as e:
    logger.error(f'Failed to load WSGI app: {e}')
    raise

if __name__ == '__main__':
    application.run()