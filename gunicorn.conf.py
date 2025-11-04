# Gunicorn configuration file
import multiprocessing
import os
from pathlib import Path

# Базовые настройки
bind = "127.0.0.1:8000"  # или "unix:/path/to/school.sock" для Unix сокета
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
threads = 2
timeout = 120

# Логирование
accesslog = str(Path(__file__).parent / "logs" / "gunicorn_access.log")
errorlog = str(Path(__file__).parent / "logs" / "gunicorn_error.log")
loglevel = "info"

# Рабочие директории и пользователь
chdir = str(Path(__file__).parent)
user = "SchoolFOD"  # имя пользователя на сервере
group = "SchoolFOD"  # группа на сервере

# Настройки перезапуска
reload = True  # автоматический перезапуск при изменении кода
max_requests = 1000
max_requests_jitter = 50

# Настройки процесса
daemon = False  # запуск в фоновом режиме
pidfile = str(Path(__file__).parent / "school.pid")

# Настройки безопасности
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190