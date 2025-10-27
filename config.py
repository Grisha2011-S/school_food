import os
from datetime import timedelta

class Config:
    # Базовая конфигурация
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///school.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки API ключей
    GEMINI_API_KEY = "AIzaSyDwtKfxvwm7b6y0IskUenjez-QgGvBC2Ug" # Замените на ваш API ключ
    
    # Настройки сессии
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # Настройки загрузки файлов
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Настройки кэширования
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Настройки логирования
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    
    # В продакшене используем более безопасные настройки
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Более короткая сессия
    
    # Настройки SSL
    SSL_REDIRECT = True