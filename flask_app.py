from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g, send_from_directory
from datetime import timedelta, datetime, date
from flask_caching import Cache
from models import db, Parents, Student, Cook, Eat, EatLog
from models import City, School, Grade, Admin
from admin_utils import verify_admin, create_admin, activate_admin
from forms import ChildForm, FoodForm
from nutrition_calc import calculate_nutrition, validate_measurements
from food_detection_impl import analyze_image_with_gemini
import time
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import math
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
try:
    # dotenv_values allows reading .env files without touching os.environ
    from dotenv import dotenv_values
except Exception:
    dotenv_values = None
import io
import csv
from flask import make_response

# Настройка логирования
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Инициализация Flask приложения
app = Flask(__name__)
logger.info("Starting Flask application...")

# Базовая конфигурация
try:
    # Try to read config from .env (without using os.environ directly)
    env = dotenv_values('.env') if dotenv_values is not None else {}
    app.config['SECRET_KEY'] = (env.get('SECRET_KEY') if env else None) or 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = (env.get('DATABASE_URL') if env else None) or 'sqlite:///school.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    logger.info("Basic configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading configuration: {str(e)}")
    raise
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
# Use pathlib.Path instead of os.path for path manipulation
BASE_DIR = Path(__file__).resolve().parent
APP_UPLOAD_PATH = BASE_DIR / 'static' / 'uploads'
app.config['UPLOAD_FOLDER'] = str(APP_UPLOAD_PATH)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# Создаем папку для загрузок, если её нет
APP_UPLOAD_PATH.mkdir(parents=True, exist_ok=True)

# Инициализация кэша
cache = Cache(app)

# --- Удобная настройка GEMINI API KEY ---
# Если вы не хотите работать с переменными окружения, можно просто
# записать ключ сюда (временное решение для локальной отладки).
# ВАЖНО: не оставляйте секретные ключи в коде в продакшене и не коммитьте их в репозиторий.
# Пример: GEMINI_API_KEY = "ваш_секретный_ключ"
GEMINI_API_KEY = "AIzaSyALiST2y0go1Aen3_GnJjzjbr6UsBevn3I"
# Если вы явно укажете ключ в переменной ниже, он будет экспортирован в окружение
# и подхвачен функцией analyze_image_with_gemini из food_detection_impl.py
# if GEMINI_API_KEY:
#     try:
#         os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
#         app.logger.info('GEMINI_API_KEY configured from flask_app variable')
#     except Exception:
#         app.logger.exception('Failed to set GEMINI_API_KEY in environment')

# Языковые настройки
import json
from functools import wraps

def load_translations(lang):
    """Загружает переводы для указанного языка"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Абсолютный путь к папке с переводами (используем pathlib)
    translations_dir = BASE_DIR / 'translations'
    
    try:
        # Сначала пробуем загрузить запрошенный язык
        path = translations_dir / f'{lang}.json'
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                logger.info(f"Loaded translations for '{lang}' from {path}")
                return translations
                
        # Если не нашли, пробуем fallback на русский
        fallback = translations_dir / 'ru.json'
        if fallback.exists():
            with open(fallback, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                logger.warning(f"Translation file for '{lang}' not found, using fallback ru.json")
                return translations
                
        # Если и русский не нашли
        logger.error(f"No translations found for '{lang}' and no fallback ru.json in {translations_dir}")
        return {}
        
    except Exception as e:
        logger.exception(f"Error loading translations for {lang}: {str(e)}")
        return {}

# Декоратор для добавления переводов в контекст шаблона
def with_translations(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.lang = session.get('language', 'ru')  # По умолчанию русский
        if not hasattr(g, 'translations') or not g.translations:
            g.translations = load_translations(g.lang)
        return f(*args, **kwargs)
    return decorated_function

# Регистрируем декоратор для всех роутов
@app.before_request
def before_request():
    # Приоритет: session -> cookie -> по умолчанию 'ru'
    lang = session.get('language')
    if not lang:
        # fallback: если сессия не сохранилась (например, Secure cookie при http),
        # попробуем прочитать значение из обычного cookie и записать в сессию
        cookie_lang = request.cookies.get('language')
        if cookie_lang in ('ru', 'kk'):
            session['language'] = cookie_lang
            session.permanent = True
            lang = cookie_lang
        
    current_lang = lang or 'ru'
    g.lang = current_lang
    
    # Загружаем переводы только если их нет или язык изменился
    if not hasattr(g, 'translations') or not g.translations or getattr(g, 'current_lang', None) != current_lang:
        g.translations = load_translations(current_lang)
        g.current_lang = current_lang
        app.logger.debug(f"Loaded translations for language: {current_lang}")

# Добавляем функцию перевода в контекст шаблона
@app.context_processor
def utility_processor():
    def translate(key):
        """
        Получает перевод по ключу.
        Поддерживает вложенные ключи через точку.
        Например: 
        {{ t('auth.login') }} - получит translations['auth']['login']
        {{ t('welcome') }} - получит translations['welcome']
        """
        if not hasattr(g, 'translations'):
            g.translations = {}

        translations = g.translations
        parts = key.split('.')
        current = translations
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Если перевод не найден, пробуем загрузить файл переводов и повторить попытку
                g.translations = load_translations(g.lang if hasattr(g, 'lang') else 'ru')
                translations = g.translations
                current = translations

                # Повторная попытка получить перевод по всем частям
                found = True
                for p in parts:
                    if isinstance(current, dict) and p in current:
                        current = current[p]
                    else:
                        found = False
                        break

                if not found:
                    # логируем отсутствующий ключ и возвращаем пустую строку
                    app.logger.debug(f"Missing translation for key: {key} (lang={g.lang})")
                    return ''

        return current if current is not None else ''

    return dict(t=translate)

# Роут для изменения языка
@app.route('/lang/<lang>')
def change_lang(lang):
    if lang in ['ru', 'kk']:
        session['language'] = lang
        session.permanent = True
        flash(f"Language set: {lang}")
    # Формируем redirect-ответ и устанавливаем простой cookie 'language' как backup
    resp = redirect(request.referrer or url_for('index'))
    try:
        secure = bool(app.config.get('SESSION_COOKIE_SECURE', False))
        samesite = app.config.get('SESSION_COOKIE_SAMESITE', None)
        max_age = int(app.permanent_session_lifetime.total_seconds())
        if samesite:
            resp.set_cookie('language', lang, max_age=max_age, secure=secure, httponly=False, samesite=samesite)
        else:
            resp.set_cookie('language', lang, max_age=max_age, secure=secure, httponly=False)
    except Exception:
        # если что-то пошло не так при установке cookie — всё равно делаем redirect
        pass
    return resp

# Инициализация расширений
db.init_app(app)
cache = Cache(app)

# Настройка логирования
if not Path('logs').exists():
    Path('logs').mkdir(parents=True, exist_ok=True)
if not app.debug:
    file_handler = RotatingFileHandler(str(Path('logs') / 'app.log'), maxBytes=10000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask App startup')

# Настройка логирования
if not Path('logs').exists():
    Path('logs').mkdir(parents=True, exist_ok=True)
handler = RotatingFileHandler(str(Path('logs') / 'app.log'), maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Длительность "постоянной" сессии (например 30 дней)
app.permanent_session_lifetime = timedelta(days=30)

# Функция для безопасного сохранения в базу данных
def safe_commit():
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f'Database error: {str(e)}')
        flash('Произошла ошибка базы данных')
        return False

# Legacy manual implementation removed — using the SDK-based implementation defined later in this file.
# The older manual POST-based function produced inconsistent 404 responses because the
# endpoint/format used didn't match the current Generative Language / Vision API.
# See `analyze_image_with_gemini` (SDK) defined further down.

# Декоратор для проверки авторизации
from functools import wraps

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != role:
                flash('Доступ запрещён!')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- file upload settings (restore) ---
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Создаем папку для загрузок, если её нет
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

from PIL import Image

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, max_size=(800, 800)):
    """
    Сохраняет и оптимизирует изображение
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"

        # Создаем директорию если не существует
        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

        # Сохраняем оригинал
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))

        try:
            # Оптимизируем размер
            with Image.open(str(filepath)) as img:
                img.thumbnail(max_size)
                img.save(str(filepath), optimize=True, quality=85)
            app.logger.info(f'Image saved and optimized: {filename}')
        except Exception as e:
            app.logger.error(f'Image optimization failed: {str(e)}')

        return filename
    return None





# Контекст-процессор: предоставляет флаги авторизации в шаблоны и очищает невалидную сессию
@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id:
        return dict(logged_in=False, current_role=None)
    try:
        if role == 'student':
            user = Student.query.get(user_id)
        elif role == 'parent':
            user = Parents.query.get(user_id)
        elif role == 'cook':
            user = Cook.query.get(user_id)
        elif role == 'admin':
            user = Admin.query.get(user_id)
        else:
            user = None
    except Exception:
        user = None

    if user is None:
        # Очистим сессию, если данные невалидны
        session.pop('user_id', None)
        session.pop('role', None)
        session.pop('calories', None)
        session.pop('protein', None)
        session.pop('fat', None)
        session.pop('carbs', None)
        session.pop('eaten', None)
        return dict(logged_in=False, current_role=None)

    return dict(logged_in=True, current_role=role)

from typing import Union, Optional, Dict, List, Tuple

def safe_float(value: Union[str, int, float, None]) -> float:
    """Преобразует строки с запятой в float"""
    try:
        if value is None:
            return 0.0
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0

def get_session_user_id() -> int:
    """Безопасно получает user_id из сессии"""
    try:
        user_id = session.get('user_id')
        if user_id is not None:
            return int(user_id)
        raise ValueError("No user_id in session")
    except (ValueError, TypeError):
        app.logger.error("Invalid user_id in session")
        raise ValueError("Invalid user_id in session")

def get_session_role() -> str:
    """Безопасно получает role из сессии"""
    role = session.get('role')
    if role not in ('student', 'parent', 'cook'):
        app.logger.error(f"Invalid role in session: {role}")
        raise ValueError("Invalid role in session")
    return role

def get_nutrition_summary(logs: List[EatLog]) -> Dict[str, float]:
    """Считает суммарные показатели питания из логов"""
    sum_cal = sum(safe_float(log.calories) for log in logs)
    sum_prot = sum(safe_float(log.protein) for log in logs)
    sum_fat = sum(safe_float(log.fat) for log in logs)
    sum_carbs = sum(safe_float(log.carbs) for log in logs)
    
    return {
        'calories': round(sum_cal, 1),
        'protein': round(sum_prot, 1),
        'fat': round(sum_fat, 1),
        'carbs': round(sum_carbs, 1)
    }

def calculate_remaining_nutrients(total: Dict[str, float], consumed: Dict[str, float]) -> Dict[str, float]:
    """Считает оставшиеся показатели питания"""
    return {
        'calories': round(total['calories'] - consumed['calories'], 1),
        'protein': round(total['protein'] - consumed['protein'], 1),
        'fat': round(total['fat'] - consumed['fat'], 1),
        'carbs': round(total['carbs'] - consumed['carbs'], 1)
    }


def _extract_text_from_chunk(chunk):
    """Try to extract text from a chunk which can be str, dict, bytes, or have nested structures."""
    try:
        if chunk is None:
            return ''
        if isinstance(chunk, bytes):
            return chunk.decode('utf-8', errors='ignore')
        if isinstance(chunk, str):
            return chunk
        if isinstance(chunk, dict):
            # OpenAI-like: {'choices':[{'message':{'content': '...'}}]}
            if 'choices' in chunk and isinstance(chunk['choices'], (list, tuple)):
                parts = []
                for ch in chunk['choices']:
                    if isinstance(ch, dict):
                        if 'message' in ch and isinstance(ch['message'], dict) and ch['message'].get('content'):
                            parts.append(str(ch['message'].get('content')))
                        elif ch.get('text'):
                            parts.append(str(ch.get('text')))
                        elif ch.get('delta') and isinstance(ch.get('delta'), dict) and ch['delta'].get('content'):
                            parts.append(str(ch['delta'].get('content')))
                return ''.join(parts)
            # direct content
            if chunk.get('content'):
                return str(chunk.get('content'))
            if chunk.get('text'):
                return str(chunk.get('text'))
            # fallback: join values
            try:
                return ' '.join([str(v) for v in chunk.values()])
            except Exception:
                return str(chunk)
        # iterable (generator/list) -> join recursive
        if hasattr(chunk, '__iter__'):
            try:
                parts = []
                for c in chunk:
                    parts.append(_extract_text_from_chunk(c))
                return ''.join(parts)
            except Exception:
                return str(chunk)
    except Exception:
        return str(chunk)


def normalize_response(obj):
    """Normalize various g4f responses into a single text string."""
    return _extract_text_from_chunk(obj) or ''


def extract_clean_answer(text: str) -> str:
    """Try to strip metadata/dict dumps and return the final assistant message.

    Strategy:
    - If there's a trailing '}' (JSON-like), take substring after the last '}' and strip.
    - Otherwise, try to find the last block of Cyrillic or printable chars and return that.
    - Fallback to original text.
    """
    if not text:
        return ''
    try:
        import re
        import json

        # 1) If the output contains a JSON block(s), try to parse the last JSON object
        #    and extract common fields like choices[].message.content, content, text.
        last_json = None
        # try to find last opening brace and parse from there moving left
        for start in range(len(text) - 1, -1, -1):
            if text[start] == '{':
                candidate = text[start:]
                try:
                    parsed = json.loads(candidate)
                    last_json = parsed
                    break
                except Exception:
                    # not valid JSON from this position, continue
                    continue

        if last_json is not None:
            # try to extract assistant text from known shapes
            def extract_from_obj(obj):
                if obj is None:
                    return ''
                if isinstance(obj, str):
                    return obj
                if isinstance(obj, dict):
                    # OpenAI-like
                    if 'choices' in obj and isinstance(obj['choices'], (list, tuple)):
                        parts = []
                        for ch in obj['choices']:
                            if isinstance(ch, dict):
                                # g4f/OpenAI streaming shape
                                if ch.get('message') and isinstance(ch.get('message'), dict) and ch['message'].get('content'):
                                    parts.append(str(ch['message']['content']))
                                elif ch.get('text'):
                                    parts.append(str(ch['text']))
                                elif ch.get('delta') and isinstance(ch['delta'], dict) and ch['delta'].get('content'):
                                    parts.append(str(ch['delta'].get('content')))
                        if parts:
                            return ' '.join(parts)
                    # common keys
                    for key in ('assistant', 'response', 'content', 'text'):
                        val = obj.get(key)
                        if val:
                            return extract_from_obj(val)
                    # fallback: try to join string values
                    try:
                        return ' '.join([str(v) for v in obj.values() if isinstance(v, (str, int, float))])
                    except Exception:
                        return ''
                if isinstance(obj, (list, tuple)):
                    return ' '.join([extract_from_obj(x) for x in obj])
                return str(obj)

            extracted = extract_from_obj(last_json)
            if extracted and any(ch.isalpha() for ch in extracted):
                return extracted.strip()

        # 2) If JSON parsing didn't help: look for common assistant prefixes and return everything after them
        #    e.g. 'assistant:', 'Assistant:', 'Ответ:', 'Response:'
        prefixes = [r'assistant[:\-\s]+', r'Assistant[:\-\s]+', r'Ответ[:\-\s]+', r'Response[:\-\s]+', r'Ответ бота[:\-\s]+']
        for p in prefixes:
            m = re.search(p + r'(.+)$', text, re.IGNORECASE | re.DOTALL)
            if m:
                cand = m.group(1).strip()
                # drop any leading JSON-like garbage
                cand = re.sub(r'^\s*\{.*?\}\s*', '', cand, flags=re.DOTALL).strip()
                if cand:
                    return cand

        # 3) Heuristic: scan lines from bottom up and pick the first contiguous block that looks like natural language
        lines = text.splitlines()
        natural = []
        for line in reversed(lines):
            s = line.strip()
            if not s:
                if natural:
                    break
                else:
                    continue
            # skip obvious metadata lines
            if s.startswith('{') or s.startswith('[') or s.startswith('Traceback') or 'status_code' in s or s.lower().startswith('error'):
                if natural:
                    break
                else:
                    continue
            # skip short lines that look like JSON keys or file paths
            if len(s) < 20 and (':' in s and not re.search(r'[А-Яа-яA-Za-z]', s)):
                if natural:
                    break
                else:
                    continue
            natural.append(s)
            # collect a reasonable amount
            if sum(len(x) for x in natural) > 2000:
                break

        if natural:
            natural.reverse()
            return '\n'.join(natural).strip()

        # 4) final fallback: take last chunk of text and strip leading non-letter characters
        tail = text[-1200:]
        m = re.search(r'[\w\p{L}].*', tail)
        if m:
            return m.group(0).strip()
        return tail.strip()
    except Exception:
        return text.strip()


# ---------------- Регистрация ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role")
        login = request.form.get("login")  # Изменено с logine на login
        password = request.form.get("password")
        if not login or not password:  # Изменено с logine на login
            flash("Пожалуйста, заполните все поля")
            return redirect("/register")
            
        hash_pass = generate_password_hash(password)

        if role == "parent":
            # Родитель больше не указывает имя/метку ребёнка при регистрации.
            user = Parents(login=login, password=hash_pass)  # Изменено с logine на login
        
        elif role == "cook":
            city = request.form.get("city")
            school = request.form.get("school")
            user = Cook(login=login, password=hash_pass, city=city, school=school)  # Изменено с logine на login
        
        elif role == "teacher":
            # Создаем учителя как студента с особыми правами
            city = request.form.get("city")
            school = request.form.get("school")
            has_class = request.form.get("has_class") == "on"
            grade = request.form.get("grade") if has_class else None
            
            user = Student(
                login=login,  # Изменено с logine на login
                password=hash_pass, 
                role="student", 
                is_teacher=True,
                city=city,
                school=school,
                grade=grade
            )

        else:
            flash("Регистрация учеников через форму запрещена. Родитель должен добавить ребёнка в своём аккаунте.")
            return redirect("/register")

        # end of role handling

        try:
            db.session.add(user)
            db.session.commit()
            flash("Регистрация прошла успешно!")
            return redirect("/login")
        except Exception:
            db.session.rollback()
            flash("Ошибка: логин уже существует.")

    return render_template("register.html")


# ---------------- Вход ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        # Проверяем администратора
        success, message = verify_admin(login, password)
        if success:
            admin = Admin.query.filter_by(login=login).first()
            session['user_id'] = admin.id
            session['role'] = 'admin'
            session.permanent = True  # Сессия будет жить до выхода
            flash('Добро пожаловать, администратор!')
            return redirect(url_for('dashboard'))
        elif "не активирован" in message:
            flash('Аккаунт администратора не активирован.')
            return redirect(url_for('admin_activation'))

        # Проверяем сначала студента/учителя
        user = Student.query.filter_by(login=login).first()  # Изменено с logine на login
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'student'
            session["calories"] = user.calories
            session["protein"] = user.protein
            session["fat"] = user.fat
            session["carbs"] = user.carbs
            session["eaten"] = []
            session["is_teacher"] = user.is_teacher  # Сохраняем флаг учителя
            session.permanent = True
            
            if user.is_teacher:
                flash('Добро пожаловать, учитель!')
            else:
                flash('Добро пожаловать, ученик!')
            return redirect(url_for('dashboard'))

        # Проверяем родителя
        user = Parents.query.filter_by(login=login).first()  # Изменено с logine на login
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'parent'
            session.permanent = True
            flash('Добро пожаловать, родитель!')
            return redirect(url_for('dashboard'))

        # Проверяем повара
        user = Cook.query.filter_by(login=login).first()  # Изменено с logine на login
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'cook'
            session.permanent = True
            flash('Добро пожаловать, повар!')
            return redirect(url_for('dashboard'))

        flash('Неверный логин или пароль.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


# ---------------- Dashboard ----------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Сначала войдите в систему.')
        return redirect(url_for('login'))

    role = session.get('role')
    user_id = session.get('user_id')
    template_data = {}

    if role == 'student':
        user = Student.query.get(user_id)
        if not user:
            session.clear()
            flash('Ошибка: пользователь не найден.')
            return redirect(url_for('login'))
            
        template_data = {
            'role': 'student',
            'login': user.login,
            'name': user.name,
            'calories': session.get("calories", user.calories),
            'protein': session.get("protein", user.protein),
            'fat': session.get("fat", user.fat),
            'carbs': session.get("carbs", user.carbs),
            'eaten': session.get("eaten", []),
            'is_teacher': user.is_teacher
        }

    elif role == 'parent':
        user = Parents.query.get(user_id)
        if not user:
            session.clear()
            flash('Ошибка: пользователь не найден.')
            return redirect(url_for('login'))
        
        children = Student.query.filter_by(parent_id=user.id).all()
        start_of_day = datetime.combine(date.today(), datetime.min.time())
        child_summaries = {}
        child_logs = {}
        for c in children:
            logs = EatLog.query.filter(EatLog.student_id == c.id, EatLog.created_at >= start_of_day).all()
            child_logs[c.id] = logs
            sum_cal = sum([safe_float(l.calories) for l in logs])
            sum_prot = sum([safe_float(l.protein) for l in logs])
            sum_fat = sum([safe_float(l.fat) for l in logs])
            sum_carbs = sum([safe_float(l.carbs) for l in logs])
            remaining_cal = round(safe_float(c.calories) - sum_cal, 1)
            remaining_prot = round(safe_float(c.protein) - sum_prot, 1)
            remaining_fat = round(safe_float(c.fat) - sum_fat, 1)
            remaining_carbs = round(safe_float(c.carbs) - sum_carbs, 1)
            child_summaries[c.id] = {
                'sum_cal': round(sum_cal, 1), 'sum_prot': round(sum_prot, 1), 
                'sum_fat': round(sum_fat, 1), 'sum_carbs': round(sum_carbs, 1),
                'remaining_cal': remaining_cal, 'remaining_prot': remaining_prot, 
                'remaining_fat': remaining_fat, 'remaining_carbs': remaining_carbs
            }
        
        template_data = {
            'role': 'parent',
            'login': user.login,
            'babe': user.babe,
            'children': children,
            'child_logs': child_logs,
            'child_summaries': child_summaries
        }

    elif role == 'cook':
        if not user:
            session.clear()
            flash('Ошибка: пользователь не найден.')
            return redirect(url_for('login'))
        template_data = {
            'role': 'cook',
            'login': user.login
        }

    else:
        flash('Неизвестная роль.')
        return redirect(url_for('login'))

    return render_template('dashboard.html', **template_data)


# ---------------- Выход ----------------

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.')
    return redirect(url_for('login'))  # login для всех ролей


# ---------------- Обновление КБЖУ вручную ----------------

@app.route('/update_calories', methods=['POST'])
def update_calories():
    if "user_id" not in session:
        return redirect(url_for('login'))

    user = Student.query.get(session["user_id"])
    if user:
        calories = request.form.get("calories")
        protein = request.form.get("protein")
        fat = request.form.get("fat")
        carbs = request.form.get("carbs")

        if calories and calories.isdigit():
            session["calories"] = int(calories)
        if protein:
            session["protein"] = float(protein)
        if fat:
            session["fat"] = float(fat)
        if carbs:
            session["carbs"] = float(carbs)

        session.modified = True
        flash("Данные успешно обновлены!", "success")

    return redirect(url_for('dashboard'))


# ---------------- Страница выбора еды ----------------

@app.route('/eat', methods=['GET', 'POST'])
@login_required(role='student')
def eat():

    # Обработка поискового запроса (GET-параметр q)
    q = request.args.get('q', '').strip()
    barcode_q = request.args.get('barcode', '').strip()

    # Если задан штрихкод — ищем точное совпадение по barcode
    if barcode_q:
        foods = Eat.query.filter_by(barcode=barcode_q).all()
    elif q:
        # Используем case-insensitive поиск через LIKE для SQLite
        search_pattern = f"%{q}%"
        foods = Eat.query.filter(
            db.or_(
                Eat.name.ilike(search_pattern),
                Eat.type.ilike(search_pattern)
            )
        ).all()
    else:
        foods = Eat.query.all()  # показываем и школьную, и обычную

    if request.method == 'POST':
        try:
            food_id = int(request.form.get('food_id') or 0)
        except ValueError:
            flash('Некорректный ID блюда')
            return redirect(url_for('eat'))

        grams = request.form.get('grams')
        food = Eat.query.get(food_id)

        if food:
            if "eaten" not in session:
                session["eaten"] = []


            if food.type == 'school':
                session["calories"] = round(session.get("calories", 0) - safe_float(food.calories), 1)
                session["protein"] = round(session.get("protein", 0) - safe_float(food.protein), 1)
                session["fat"] = round(session.get("fat", 0) - safe_float(food.fat), 1)
                session["carbs"] = round(session.get("carbs", 0) - safe_float(food.carbs), 1)
                session["eaten"].append(f"{food.name} (фикс)")

                # логируем в базу
                try:
                    try:
                        student_id = get_session_user_id()
                        log = EatLog(
                            student_id=student_id,
                            food_id=food.id,
                            name=food.name,
                            calories=round(safe_float(food.calories), 1),
                            protein=round(safe_float(food.protein), 1),
                            fat=round(safe_float(food.fat), 1),
                            carbs=round(safe_float(food.carbs), 1)
                        )
                        db.session.add(log)
                        if not safe_commit():
                            flash('Ошибка при сохранении', 'error')
                    except ValueError:
                        flash('Ошибка: некорректный ID пользователя', 'error')
                        return redirect(url_for('login'))
                except Exception:
                    db.session.rollback()

            else:  # обычная еда
                try:
                    grams = float(grams or 0)  # масса блюда в граммах
                except ValueError:
                    grams = 0
                session["calories"] = round(session.get("calories", 0) - safe_float(food.calories) * grams / 100, 1)
                session["protein"] = round(session.get("protein", 0) - safe_float(food.protein) * grams / 100, 1)
                session["fat"] = round(session.get("fat", 0) - safe_float(food.fat) * grams / 100, 1)
                session["carbs"] = round(session.get("carbs", 0) - safe_float(food.carbs) * grams / 100, 1)
                session["eaten"].append(f"{food.name} ({grams} г)")

                # логируем в базу для обычной еды
                try:
                    factor = grams / 100.0
                    log = EatLog(student_id=session.get('user_id'), food_id=food.id, name=food.name,
                                 calories=round(safe_float(food.calories) * factor, 1),
                                 protein=round(safe_float(food.protein) * factor, 1),
                                 fat=round(safe_float(food.fat) * factor, 1),
                                 carbs=round(safe_float(food.carbs) * factor, 1))
                    db.session.add(log)
                    db.session.commit()
                except Exception:
                    db.session.rollback()

            session.modified = True
            flash(f"Вы добавили {food.name}!")

        return redirect(url_for('eat'))

    return render_template('eat.html', foods=foods)


# ---------------- Главная ----------------

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/img', 'favicon.ico')

@app.route('/')
def index():
    """Показать школьное меню и кнопку анализа фото"""
    # Отладочный вывод для проверки языка и переводов
    app.logger.debug(f"Current language: {g.lang if hasattr(g, 'lang') else 'not set'}")
    app.logger.debug(f"Translations loaded: {bool(g.translations) if hasattr(g, 'translations') else False}")
    if hasattr(g, 'translations'):
        app.logger.debug(f"Sample translations: todays_menu='{g.translations.get('todays_menu', 'missing')}'")
    
    # Показать школьное меню для сегодняшнего рабочего дня по двухнедельному циклу
    today = date.today()
    weekday = today.weekday()  # 0=Mon .. 6=Sun
    foods_today = []
    if weekday <= 6:  # include Sunday for testing (0=Mon .. 6=Sun)
        # определяем двунедельный цикл: рассчитываем количество недель от опорной даты
        # Принято: цикл начинается от 2025-01-01. Если нужно другое начало — поменяйте reference_date.
        reference_date = date(2025, 1, 1)
        weeks_since = (today - reference_date).days // 7
        week = (weeks_since % 2) + 1
        day = weekday + 1
        foods_today = Eat.query.filter_by(type='school', week=week, day=day).all()

    return render_template('index.html', foods_today=foods_today)

# ---------------- Управление школьной едой для повара ----------------
@app.route('/cook_menu', methods=['GET', 'POST'])
def cook_menu():
    if 'user_id' not in session or session.get('role') != 'cook':
        flash("Доступ запрещён!")
        return redirect(url_for('login'))

    foods = Eat.query.filter_by(type='school').all()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name')
            calories = safe_float(request.form.get('calories'))
            protein = safe_float(request.form.get('protein'))
            fat = safe_float(request.form.get('fat'))
            carbs = safe_float(request.form.get('carbs'))
            # Для школьной еды можно указать неделю и день (1..2 и 1..5)
            try:
                try:
                    week = int(request.form.get('week') or 0) or None
                except ValueError:
                    week = None
            except Exception:
                week = None

            try:
                try:
                    day = int(request.form.get('day') or 0) or None
                except ValueError:
                    day = None
            except Exception:
                day = None
            # Обработка файла изображения (при загрузке с телефона)
            image = request.form.get('image')  # по умолчанию текстовое поле
            file = request.files.get('image_file')
            filename = None
            if file and file.filename and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                # добавить префикс времени для уникальности
                import time
                fname = f"{int(time.time())}_{fname}"
                UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
                file.save(str(UPLOAD_FOLDER / fname))
                filename = fname

            img_field = filename if filename else (image or None)
            new_food = Eat(name=name, calories=calories, protein=protein,
                           fat=fat, carbs=carbs, type='school', image=img_field, week=week, day=day)
            barcode = request.form.get('barcode')
            if barcode:
                new_food.barcode = barcode.strip()
            db.session.add(new_food)
            db.session.commit()
            flash(f"Продукт {name} добавлен!")

        elif action == 'edit':
            try:
                food_id = int(request.form.get('food_id') or 0)
            except ValueError:
                flash('Некорректный ID блюда')
                return redirect(url_for('cook_menu'))
            food = Eat.query.get(food_id)
            if food:
                food.name = request.form.get('name')
                food.calories = safe_float(request.form.get('calories'))
                food.protein = safe_float(request.form.get('protein'))
                food.fat = safe_float(request.form.get('fat'))
                food.carbs = safe_float(request.form.get('carbs'))
                # barcode
                food.barcode = request.form.get('barcode') or None
                # week/day при редактировании
                try:
                    try:
                        food.week = int(request.form.get('week') or 0) or None
                    except ValueError:
                        food.week = None
                except Exception:
                    food.week = None

                try:
                    try:
                        food.day = int(request.form.get('day') or 0) or None
                    except ValueError:
                        food.day = None
                except Exception:
                    food.day = None
                # если загружен файл — сохраняем и подменяем
                file = request.files.get('image_file')
                if file and file.filename and allowed_file(file.filename):
                    fname = secure_filename(file.filename)
                    import time
                    fname = f"{int(time.time())}_{fname}"
                    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
                    file.save(str(UPLOAD_FOLDER / fname))
                    food.image = fname
                else:
                    food.image = request.form.get('image')
                db.session.commit()
                flash(f"Продукт {food.name} обновлён!")

        elif action == 'delete':
            try:
                food_id = int(request.form.get('food_id') or 0)
            except ValueError:
                flash('Некорректный ID блюда')
                return redirect(url_for('cook_menu'))
            food = Eat.query.get(food_id)
            if food:
                db.session.delete(food)
                db.session.commit()
                flash(f"Продукт {food.name} удалён!")

        return redirect(url_for('cook_menu'))

    return render_template('cook_menu.html', foods=foods)


@app.route('/scan')
@login_required(role='student')
def scan():
    """
    Обработка сканирования QR-кода продукта.
    URL format: /scan?food_id=ID[&grams=NN] или /scan?barcode=CODE[&grams=NN]
    """
    # Получение и валидация параметров
    try:
        student_id = get_session_user_id()
        
        try:
            food_id = request.args.get('food_id', type=int)
        except ValueError:
            food_id = None
            
        barcode = request.args.get('barcode')
        if barcode:
            barcode = barcode.strip()
            
        try:
            grams = request.args.get('grams', type=float)
            if grams and (grams <= 0 or grams > 5000):  # разумное ограничение
                raise ValueError("Invalid grams value")
        except ValueError:
            grams = None

        # Проверка наличия идентификатора продукта
        if not food_id and not barcode:
            flash('Некорректный QR-код (нет id или штрихкода).', 'error')
            return redirect(url_for('dashboard'))
            
        # Поиск продукта
        if food_id:
            food = Eat.query.get(food_id)
        elif barcode:
            food = Eat.query.filter_by(barcode=barcode).first()
            
        if not food:
            flash('Продукт не найден', 'error')
            return redirect(url_for('dashboard'))
            
    except ValueError as e:
        app.logger.error(f'Error in scan: {str(e)}')
        flash('Ошибка при обработке запроса', 'error')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        app.logger.error(f'Unexpected error in scan: {str(e)}')
        flash('Произошла неожиданная ошибка', 'error')
        return redirect(url_for('dashboard'))

    food = None
    if food_id:
        try:
            food = Eat.query.get(int(food_id))
        except Exception:
            food = None
    elif barcode:
        try:
            food = Eat.query.filter_by(barcode=str(barcode).strip()).first()
        except Exception:
            food = None

    if not food:
        flash('Блюдо не найдено.')
        return redirect(url_for('dashboard'))

    if 'eaten' not in session:
        session['eaten'] = []

    # для школьной еды фиксированное снятие
    if food.type == 'school':
        session["calories"] = round(session.get("calories", 0) - safe_float(food.calories), 1)
        session["protein"] = round(session.get("protein", 0) - safe_float(food.protein), 1)
        session["fat"] = round(session.get("fat", 0) - safe_float(food.fat), 1)
        session["carbs"] = round(session.get("carbs", 0) - safe_float(food.carbs), 1)
        session['eaten'].append(f"{food.name} (фикс)")
        try:
            log = EatLog(student_id=session.get('user_id'), food_id=food.id, name=food.name,
                         calories=round(safe_float(food.calories), 1), protein=round(safe_float(food.protein), 1),
                         fat=round(safe_float(food.fat), 1), carbs=round(safe_float(food.carbs), 1))
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()
    else:
        # если указан вес в QR, учитываем его
        if grams:
            g = safe_float(grams)
            session["calories"] = round(session.get("calories", 0) - safe_float(food.calories) * g / 100, 1)
            session["protein"] = round(session.get("protein", 0) - safe_float(food.protein) * g / 100, 1)
            session["fat"] = round(session.get("fat", 0) - safe_float(food.fat) * g / 100, 1)
            session["carbs"] = round(session.get("carbs", 0) - safe_float(food.carbs) * g / 100, 1)
            session['eaten'].append(f"{food.name} ({g} г)")
            try:
                factor = g / 100.0
                log = EatLog(student_id=session.get('user_id'), food_id=food.id, name=food.name,
                             calories=round(safe_float(food.calories) * factor, 1),
                             protein=round(safe_float(food.protein) * factor, 1),
                             fat=round(safe_float(food.fat) * factor, 1),
                             carbs=round(safe_float(food.carbs) * factor, 1))
                db.session.add(log)
                db.session.commit()
            except Exception:
                db.session.rollback()
        else:
            session["calories"] = round(session.get("calories", 0) - safe_float(food.calories), 1)
            session["protein"] = round(session.get("protein", 0) - safe_float(food.protein), 1)
            session["fat"] = round(session.get("fat", 0) - safe_float(food.fat), 1)
            session["carbs"] = round(session.get("carbs", 0) - safe_float(food.carbs), 1)
            session['eaten'].append(f"{food.name}")

    session.modified = True
    flash('Блюдо добавлено после сканирования QR-кода.')
    return redirect(url_for('dashboard'))


# Родитель может добавить ребёнка
@app.route('/parent/add_child', methods=['GET', 'POST'])
@login_required(role='parent')
def parent_add_child():
    from forms import ChildForm
    form = ChildForm()

    # Получаем списки для селекторов
    cities = City.query.order_by(City.name).all()
    schools = School.query.order_by(School.name).all()
    grades = Grade.query.order_by(Grade.name).all()

    # Динамически заполняем choices для WTForms
    form.city.choices = [('', '— выберите город —')] + [(c.name, c.name) for c in cities]
    form.school.choices = [('', '— выберите школу —')] + [(s.name, s.name) for s in schools]
    form.grade.choices = [('', '— выберите класс —')] + [(g.name, g.name) for g in grades]

    if form.validate_on_submit():
        try:
            parent_id = get_session_user_id()

            if not form.login.data or not form.password.data:
                flash('Логин и пароль обязательны')
                return redirect(url_for('parent_add_child'))

            # Подготовка измерений
            try:
                measurements = {
                    'age': float(form.age.data) if form.age.data is not None else None,
                    'height': float(form.height.data) if form.height.data is not None else None,
                    'weight': float(form.weight.data) if form.weight.data is not None else None,
                    'activity': float(form.activity.data) if form.activity.data is not None else None,
                }
            except (ValueError, TypeError):
                measurements = {'age': None, 'height': None, 'weight': None, 'activity': None}

            # Значения по умолчанию
            calories = 2000.0
            protein = round((calories * 0.2) / 4, 1)
            fat = round((calories * 0.3) / 9, 1)
            carbs = round((calories * 0.5) / 4, 1)

            # Если все данные предоставлены, валидируем и считаем
            if all(v is not None for v in measurements.values()):
                # приведение к Dict[str, float] для валидаторов
                measurements_float: dict[str, float] = {k: float(v) for k, v in measurements.items()}  # type: ignore
                is_valid, err = validate_measurements(measurements_float)
                if is_valid:
                    try:
                        calories, protein, fat, carbs = calculate_nutrition(gender=str(form.gender.data or 'male'), measurements=measurements_float)
                        # BMI
                        bmi = measurements_float['weight'] / ((measurements_float['height']/100.0)**2)
                        if bmi < 18.5 or calories < 1800:
                            flash('Рекомендуется увеличить суточную калорийность для ребёнка.', 'info')
                        elif bmi > 25 or calories > 2200:
                            flash('Рекомендуется уменьшить суточную калорийность для ребёнка.', 'info')
                    except Exception as e:
                        app.logger.warning(f'Nutrition calc failed: {e}')
                else:
                    app.logger.warning(f'Invalid measurements: {err}')

            # Создаем ученика
            try:
                hash_pass = generate_password_hash(str(form.password.data))
                # Определяем город/школу/класс — берём из select-полей формы
                city_val = None
                school_val = None
                grade_val = None
                try:
                    city_val = (form.city.data or None) if hasattr(form, 'city') else (request.form.get('city') or None)
                    school_val = (form.school.data or None) if hasattr(form, 'school') else (request.form.get('school') or None)
                    grade_val = (str(form.grade.data) if form.grade.data else None) if hasattr(form, 'grade') else (request.form.get('grade') or None)
                except Exception:
                    city_val = request.form.get('city') or None
                    school_val = request.form.get('school') or None
                    grade_val = request.form.get('grade') or None

                child = Student(
                    login=form.login.data,
                    password=hash_pass,
                    parent_id=parent_id,
                    calories=calories,
                    protein=protein,
                    fat=fat,
                    carbs=carbs,
                    city=city_val,
                    school=school_val,
                    grade=grade_val
                )
                db.session.add(child)
                if safe_commit():
                    app.logger.info(f'Child added: {child.login}')
                    flash('Ребёнок успешно добавлен!')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Ошибка при сохранении', 'error')
            except Exception as e:
                app.logger.error(f'Error adding child: {str(e)}')
                flash('Ошибка: логин ребёнка уже существует.', 'error')

        except ValueError:
            flash('Ошибка сессии. Пожалуйста, войдите снова.', 'error')
            return redirect(url_for('login'))  # login для родителя
        except Exception as e:
            app.logger.error(f'Unexpected error in parent_add_child: {e}')
            flash('Произошла неожиданная ошибка', 'error')

    return render_template('parent_add_child.html', form=form, cities=cities, schools=schools, grades=grades)


# Родитель видит список своих детей и их логи
@app.route('/parent/children')
@login_required(role='parent')
@cache.cached(timeout=60)  # кэшируем на 1 минуту
def parent_children():
    """Показывает список детей родителя и их логи питания за сегодня"""
    try:
        # Получаем и проверяем id родителя
        parent_id = get_session_user_id()
        parent = Parents.query.get_or_404(parent_id)
        
        # Используем join для оптимизации запроса
        children = (Student.query
                   .filter_by(parent_id=parent_id)
                   .order_by(Student.login)
                   .all())
                   
        if not children:
            flash('У вас пока нет добавленных детей')
            return redirect(url_for('parent_add_child'))
            
        # Инициализируем структуры для логов
        child_logs: Dict[int, List[EatLog]] = {}
        child_summaries: Dict[int, Dict[str, Dict[str, float]]] = {}
        start_of_day = datetime.combine(date.today(), datetime.min.time())
        
        # Получаем логи и считаем суммы для каждого ребенка
        for child in children:
            # Получаем логи за сегодня
            logs = EatLog.query.filter(
                db.and_(
                    EatLog.student_id == child.id,
                    EatLog.created_at >= start_of_day
                )
            ).all()
            child_logs[child.id] = logs
            
            # Считаем потребленные питательные вещества
            consumed = get_nutrition_summary(logs)
            
            # Формируем целевые показатели
            target = {
                'calories': safe_float(child.calories),
                'protein': safe_float(child.protein),
                'fat': safe_float(child.fat),
                'carbs': safe_float(child.carbs)
            }
            
            # Считаем остатки
            remaining = calculate_remaining_nutrients(target, consumed)
            
            # Сохраняем результаты
            child_summaries[child.id] = {
                'consumed': consumed,
                'remaining': remaining,
                'target': target
            }
            
            # Логируем для мониторинга
            app.logger.info(f'Calculated nutrition for child {child.id}: consumed={consumed}, remaining={remaining}')
            
    except ValueError as e:
        app.logger.error(f'Session error in parent_children: {str(e)}')
        flash('Ошибка сессии', 'error')
        return redirect(url_for('login'))
        
    except Exception as e:
        app.logger.error(f'Error in parent_children: {str(e)}')
        flash('Произошла ошибка', 'error')
        return redirect(url_for('dashboard'))
        
    return render_template('parent_children.html',
                         children=children,
                         child_logs=child_logs,
                         child_summaries=child_summaries)


@app.route('/parent/child/<int:student_id>/export')
@login_required(role='parent')
def export_child_year(student_id: int):
    """Экспортирует логи питания ребёнка за последний год в CSV (Excel) или Word (HTML в .doc).

    Параметры query: fmt=excel|word (по умолчанию excel)
    Доступен только родителю, у которого этот ребёнок привязан.
    """
    fmt = request.args.get('fmt', 'excel').lower()
    # Проверка прав: родитель должен владеть ребёнком
    try:
        parent_id = get_session_user_id()
    except ValueError:
        flash('Ошибка сессии. Пожалуйста, войдите снова.', 'error')
        return redirect(url_for('login'))

    child = Student.query.get_or_404(student_id)
    if child.parent_id != parent_id:
        flash('Доступ запрещён', 'error')
        return redirect(url_for('parent_children'))

    # Сбор логов за последний год
    now = datetime.utcnow()
    start = now - timedelta(days=365)
    logs = EatLog.query.filter(
        EatLog.student_id == child.id,
        EatLog.created_at >= start,
        EatLog.created_at <= now
    ).order_by(EatLog.created_at.asc()).all()

    # Подготавливаем сводные данные
    total_cal = sum(safe_float(l.calories) for l in logs)
    total_prot = sum(safe_float(l.protein) for l in logs)
    total_fat = sum(safe_float(l.fat) for l in logs)
    total_carbs = sum(safe_float(l.carbs) for l in logs)

    # Формируем имя файла
    start_label = start.date().isoformat()
    end_label = now.date().isoformat()
    base_name = f"{child.login}_nutrition_{start_label}_to_{end_label}"

    if fmt == 'word' or fmt == 'doc':
        # Генерируем HTML-таблицу и отдаем как .doc (Word откроет HTML)
        rows_html = []
        rows_html.append(f"<h2>Отчёт питания за год — {child.login}</h2>")
        rows_html.append(f"<p>Период: {start_label} — {end_label}</p>")
        rows_html.append('<table border="1" cellpadding="4" cellspacing="0">')
        rows_html.append('<tr><th>Дата</th><th>Время</th><th>Блюдо</th><th>Ккал</th><th>Белки</th><th>Жиры</th><th>Углеводы</th></tr>')
        for l in logs:
            rows_html.append(f"<tr><td>{l.created_at.date().isoformat()}</td><td>{l.created_at.time().strftime('%H:%M:%S')}</td><td>{l.name}</td><td>{l.calories}</td><td>{l.protein}</td><td>{l.fat}</td><td>{l.carbs}</td></tr>")
        rows_html.append(f"<tr><td colspan=3><strong>Итого</strong></td><td><strong>{round(total_cal,1)}</strong></td><td><strong>{round(total_prot,1)}</strong></td><td><strong>{round(total_fat,1)}</strong></td><td><strong>{round(total_carbs,1)}</strong></td></tr>")
        rows_html.append('</table>')
        html = '<html><head><meta charset="utf-8"></head><body>' + ''.join(rows_html) + '</body></html>'
        resp = make_response(html)
        resp.headers['Content-Type'] = 'application/msword; charset=utf-8'
        resp.headers['Content-Disposition'] = f'attachment; filename="{base_name}.doc"'
        return resp

    # По умолчанию — CSV для Excel
    si = io.StringIO()
    writer = csv.writer(si)
    # BOM для Excel (UTF-8) — поможет корректно показать кириллицу в Excel на Windows
    bom = '\ufeff'
    writer.writerow(['Дата', 'Время', 'Блюдо', 'Ккал', 'Белки', 'Жиры', 'Углеводы'])
    for l in logs:
        writer.writerow([l.created_at.date().isoformat(), l.created_at.time().strftime('%H:%M:%S'), l.name, l.calories, l.protein, l.fat, l.carbs])
    writer.writerow(['Итого', '', '', round(total_cal,1), round(total_prot,1), round(total_fat,1), round(total_carbs,1)])
    data = bom + si.getvalue()
    resp = make_response(data)
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = f'attachment; filename="{base_name}.csv"'
    return resp


@app.route('/parent/child/<int:student_id>/photo_analyze', methods=['GET', 'POST'])
@login_required(role='parent')
def photo_analyze_child(student_id: int):
    """Позволяет родителю загрузить фото и проанализировать его для конкретного ребёнка."""
    try:
        parent_id = get_session_user_id()
    except ValueError:
        flash('Ошибка сессии. Пожалуйста, войдите снова.', 'error')
        return redirect(url_for('login'))

    child = Student.query.get_or_404(student_id)
    if child.parent_id != parent_id:
        flash('Доступ запрещён', 'error')
        return redirect(url_for('parent_children'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не был отправлен. Пожалуйста, выберите файл.')
            return redirect(request.url)
        file = request.files['file']
        if not file or not file.filename:
            flash('Файл не был выбран.')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename or '')
            import time
            fname = f"{int(time.time())}_{fname}"
            filepath = str(UPLOAD_FOLDER / fname)
            try:
                file.save(filepath)
            except Exception as e:
                flash(f"Ошибка при сохранении файла: {e}")
                return redirect(request.url)

            app.logger.info(f'Calling analyze_image_with_gemini for file: {filepath}')
            try:
                nutrition_data = analyze_image_with_gemini(filepath)
            except Exception as e:
                app.logger.exception(f'Unexpected exception from analyze_image_with_gemini: {e}')
                nutrition_data = None

            if nutrition_data:
                app.logger.info(f'Image analysis succeeded for file: {filepath} -> {nutrition_data.get("name") if isinstance(nutrition_data, dict) else "<non-dict>"}')
                return render_template('photo_analyze.html', filename=fname, data=nutrition_data, target_student_id=student_id)
            else:
                try:
                    size = Path(filepath).stat().st_size
                except Exception:
                    size = 'unknown'
                app.logger.warning(f'Image analysis failed for file: {filepath} (size={size})')
                flash('Не удалось проанализировать изображение. Возможно, файл поврежден или API временно недоступен.')
                return render_template('photo_analyze.html', filename=fname, data=None, target_student_id=student_id)
        else:
            flash('Недопустимый тип файла. Разрешены: png, jpg, jpeg, gif, webp.')
            return redirect(request.url)

    return render_template('photo_analyze.html', filename=None, data=None, target_student_id=student_id)

from forms import FoodForm

@app.route('/add_food', methods=['GET', 'POST'])
@login_required(role='student')
def add_food():
    form = FoodForm()
    
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            name = request.form.get('name')
            calories = safe_float(request.form.get('calories'))
            protein = safe_float(request.form.get('protein'))
            fat = safe_float(request.form.get('fat'))
            carbs = safe_float(request.form.get('carbs'))
            
            if not name or calories < 0 or protein < 0 or fat < 0 or carbs < 0:
                flash('Пожалуйста, заполните все поля корректными значениями', 'error')
                return render_template('add_food.html', form=form)
            
            # Обработка изображения
            file = request.files.get('image_file')
            image = request.form.get('image')  # URL изображения
            
            image_filename = None
            if file and file.filename:
                image_filename = save_image(file)
            elif image:
                image_filename = image
            
            # Создание новой записи о еде
            new_food = Eat(
                name=name,
                calories=calories,
                protein=protein,
                fat=fat,
                carbs=carbs,
                type='normal',
                image=image_filename
            )
            
            # Добавление штрихкода если есть
            barcode = request.form.get('barcode')
            if barcode:
                new_food.barcode = barcode.strip()
                
            # Сохранение в базу
            db.session.add(new_food)
            if safe_commit():
                app.logger.info(f'Food added: {new_food.name}')
                flash(f"Продукт {new_food.name} добавлен!", 'success')
                return redirect(url_for('eat'))
                
        except Exception as e:
            app.logger.error(f'Error adding food: {str(e)}')
            flash('Ошибка при добавлении продукта', 'error')
            db.session.rollback()

    return render_template('add_food.html', form=form)

@app.route('/calorie_calculator')
def calorie_calculator():
    return render_template('calorie_calculator.html')


# ---------------- Анализ фото еды ----------------
@app.route('/photo_analyze', methods=['GET', 'POST'])
@login_required(role='student')
def photo_analyze():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не был отправлен. Пожалуйста, выберите файл.')
            return redirect(request.url)
            
        file = request.files['file']
        if not file or not file.filename:
            flash('Файл не был выбран.')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename or '')
            filepath = str(UPLOAD_FOLDER / filename)
            
            try:
                file.save(filepath)
            except Exception as e:
                flash(f"Ошибка при сохранении файла: {e}")
                return redirect(request.url)

            # Используем функцию анализа изображения из анализатора-питания-по-фото
            app.logger.info(f'Calling analyze_image_with_gemini for file: {filepath}')
            try:
                nutrition_data = analyze_image_with_gemini(filepath)
            except Exception as e:
                app.logger.exception(f'Unexpected exception from analyze_image_with_gemini: {e}')
                nutrition_data = None

            if nutrition_data:
                app.logger.info(f'Image analysis succeeded for file: {filepath} -> {nutrition_data.get("name") if isinstance(nutrition_data, dict) else "<non-dict>"}')
                return render_template('photo_analyze.html', filename=filename, data=nutrition_data)
            else:
                try:
                    size = Path(filepath).stat().st_size
                except Exception:
                    size = 'unknown'
                app.logger.warning(f'Image analysis failed for file: {filepath} (size={size})')
                flash('Не удалось проанализировать изображение. Возможно, файл поврежден или API временно недоступен.')
                return render_template('photo_analyze.html', filename=filename, data=None)
        else:
            flash('Недопустимый тип файла. Разрешены: png, jpg, jpeg, gif, webp.')
            return redirect(request.url)

    return render_template('photo_analyze.html', filename=None, data=None)

@app.route('/add_analyzed_food', methods=['POST'])
def add_analyzed_food():
    """Добавляет проанализированную еду в дневник питания"""
    try:
        # Проверяем базовые права: должен быть либо ученик, либо родитель
        role = session.get('role')
        if role not in ('student', 'parent'):
            flash('Доступ запрещён', 'error')
            return redirect(url_for('login'))
        calories = float(request.form.get('calories', 0))
        protein = float(request.form.get('protein', 0))
        fat = float(request.form.get('fat', 0))
        carbs = float(request.form.get('carbs', 0))
        name = request.form.get('name', 'Неизвестное блюдо')
        serving_size = request.form.get('serving_size', '100г')

        # Опционально: student_id — если родитель добавляет еду для ребёнка
        student_id = request.form.get('student_id')
        target_student_id = None
        if student_id:
            try:
                target_student_id = int(student_id)
            except Exception:
                target_student_id = None

        # Если передан target_student_id — проверяем права родителя
        if target_student_id:
            # must be parent and owner of child
            if session.get('role') != 'parent':
                flash('Недостаточно прав для добавления еды другому пользователю', 'error')
                return redirect(url_for('parent_children'))
            parent_id = get_session_user_id()
            child = Student.query.get(target_student_id)
            if not child or child.parent_id != parent_id:
                flash('Ребёнок не найден или доступ запрещён', 'error')
                return redirect(url_for('parent_children'))

            # Логируем только в базу для ребёнка — не меняем сессию родителя
            try:
                log = EatLog(
                    student_id=target_student_id,
                    food_id=None,
                    name=name,
                    calories=round(calories, 1),
                    protein=round(protein, 1),
                    fat=round(fat, 1),
                    carbs=round(carbs, 1)
                )
                db.session.add(log)
                if safe_commit():
                    flash(f"Блюдо {name} добавлено в дневник ребёнка {child.login}!")
                else:
                    flash('Ошибка при сохранении в дневник', 'error')
            except Exception:
                db.session.rollback()

            return redirect(url_for('parent_children'))

        # Иначе — стандартный путь для ученика: обновляем сессию текущего пользователя
        session["calories"] = round(session.get("calories", 0) - calories, 1)
        session["protein"] = round(session.get("protein", 0) - protein, 1)
        session["fat"] = round(session.get("fat", 0) - fat, 1)
        session["carbs"] = round(session.get("carbs", 0) - carbs, 1)
        if "eaten" not in session:
            session["eaten"] = []
        session["eaten"].append(f"{name} ({serving_size})")
        session.modified = True

        # Логируем в базу данных для текущего ученика
        try:
            log = EatLog(
                student_id=session.get('user_id'),
                food_id=None,  # это проанализированная еда, у нее нет id в базе
                name=name,
                calories=round(calories, 1),
                protein=round(protein, 1),
                fat=round(fat, 1),
                carbs=round(carbs, 1)
            )
            db.session.add(log)
            if safe_commit():
                flash(f"Блюдо {name} добавлено в дневник питания!")
            else:
                flash('Ошибка при сохранении в дневник', 'error')
        except Exception:
            db.session.rollback()
            flash('Ошибка при сохранении в базу данных', 'error')

    except ValueError:
        flash('Ошибка при обработке данных о питательности', 'error')
    except Exception as e:
        flash(f'Неожиданная ошибка: {str(e)}', 'error')

    return redirect(url_for('photo_analyze'))

# ---------------- API endpoints ----------------
# Удалено дублирующееся определение photo_analyze

@app.route('/api/v1/food/<int:food_id>')
@login_required()
def get_food(food_id):
    food = Eat.query.get_or_404(food_id)
    return jsonify({
        'id': food.id,
        'name': food.name,
        'calories': food.calories,
        'protein': food.protein,
        'fat': food.fat,
        'carbs': food.carbs,
        'type': food.type,
        'image': food.image
    })

# ---------------- API: cities / schools ----------------
@app.route('/api/cities')
def api_cities():
    cities = City.query.order_by(City.name).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in cities])


@app.route('/api/schools')
def api_schools():
    # query param: city (name)
    city = request.args.get('city')
    if not city:
        return jsonify([])
    c = City.query.filter_by(name=city).first()
    if not c:
        return jsonify([])
    schools = School.query.filter_by(city_id=c.id).order_by(School.name).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in schools])

@app.route('/api/grades')
def api_grades():
    school = request.args.get('school')
    if not school:
        return jsonify([])
    s = School.query.filter_by(name=school).first()
    if not s:
        return jsonify([])
    grades = Grade.query.filter_by(school_id=s.id).order_by(Grade.name).all()
    return jsonify([{'id': g.id, 'name': g.name} for g in grades])


# ---------------- Admin management ----------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Вход для администратора"""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if not login or not password:
            flash('Необходимо указать логин и пароль', 'error')
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.filter_by(login=login).first()
        if admin and check_password_hash(admin.password, password):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            session['is_master_admin'] = admin.is_master
            session.permanent = True  # Сессия будет жить до выхода
            flash('Добро пожаловать, администратор!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверный логин или пароль', 'error')
            
    return render_template('admin_login.html')

@app.route('/admin')
@login_required(role='admin')
def admin_dashboard():
    """Главная панель администратора"""
    cities = City.query.order_by(City.name).all()
    schools = School.query.join(City).order_by(City.name, School.name).all()
    grades = Grade.query.order_by(Grade.name).all()
    
    return render_template(
        'admin_panel.html',
        cities=cities,
        schools=schools,
        grades=grades
    )

@app.route('/admin/create', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_create():
    """Создание нового администратора (только для master admin)"""
    if not session.get('is_master_admin'):
        flash('Только главный администратор может создавать новых администраторов', 'error')
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if not login or not password:
            flash('Необходимо указать логин и пароль', 'error')
            return redirect(url_for('admin_create'))
            
        try:
            admin = Admin(
                login=login,
                password=generate_password_hash(password),
                is_master=False,
                created_by=session.get('user_id')
            )
            db.session.add(admin)
            db.session.commit()
            flash('Администратор успешно создан', 'success')
            return redirect(url_for('admin_panel'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании администратора: {str(e)}', 'error')
            
    return render_template('admin_create.html')

# ---------------- Admin: manage cities/schools/grades ----------------
@app.route('/admin/cities', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_cities():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            try:
                db.session.add(City(name=name.strip()))
                db.session.commit()
                flash('Город добавлен', 'success')
            except Exception:
                db.session.rollback()
                flash('Ошибка при добавлении города', 'error')
        # Остаёмся на вкладке "Города"
        return redirect(url_for('admin_dashboard', tab='cities'))
    cities = City.query.order_by(City.name).all()
    return render_template('admin_panel.html', cities=cities, schools=School.query.join(City).order_by(City.name, School.name).all(), grades=Grade.query.order_by(Grade.name).all())


@app.route('/admin/cities/delete/<int:city_id>', methods=['POST'])
@login_required(role='admin')
def admin_delete_city(city_id):
    c = City.query.get_or_404(city_id)
    try:
        # cascade manual: delete schools in this city first
        School.query.filter_by(city_id=c.id).delete()
        db.session.delete(c)
        db.session.commit()
        flash('Город удалён', 'success')
    except Exception:
        db.session.rollback()
        flash('Ошибка при удалении города', 'error')
    return redirect(url_for('admin_cities'))


@app.route('/admin/cities/edit/<int:city_id>', methods=['POST'])
@login_required(role='admin')
def admin_edit_city(city_id):
    c = City.query.get_or_404(city_id)
    new_name = request.form.get('name')
    if new_name:
        try:
            c.name = new_name.strip()
            db.session.commit()
            flash('Город обновлён', 'success')
        except Exception:
            db.session.rollback()
            flash('Ошибка при обновлении города', 'error')
    return redirect(url_for('admin_cities'))


@app.route('/admin/schools', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_schools():
    if request.method == 'POST':
        name = request.form.get('name')
        city_id = request.form.get('city_id')
        if name and city_id:
            try:
                db.session.add(School(name=name.strip(), city_id=int(city_id)))
                db.session.commit()
                flash('Школа добавлена', 'success')
            except Exception:
                db.session.rollback()
                flash('Ошибка при добавлении школы', 'error')
        # Остаёмся на вкладке "Школы"
        return redirect(url_for('admin_dashboard', tab='schools'))
    cities = City.query.order_by(City.name).all()
    schools = School.query.join(City).order_by(City.name, School.name).all()
    return render_template('admin_panel.html', cities=cities, schools=schools, grades=Grade.query.order_by(Grade.name).all())


@app.route('/admin/schools/delete/<int:school_id>', methods=['POST'])
@login_required(role='admin')
def admin_delete_school(school_id):
    s = School.query.get_or_404(school_id)
    try:
        db.session.delete(s)
        db.session.commit()
        flash('Школа удалена', 'success')
    except Exception:
        db.session.rollback()
        flash('Ошибка при удалении школы', 'error')
    return redirect(url_for('admin_schools'))


@app.route('/admin/schools/edit/<int:school_id>', methods=['POST'])
@login_required(role='admin')
def admin_edit_school(school_id):
    s = School.query.get_or_404(school_id)
    new_name = request.form.get('name')
    new_city_id = request.form.get('city_id')
    if new_name and new_city_id:
        try:
            s.name = new_name.strip()
            s.city_id = int(new_city_id)
            db.session.commit()
            flash('Школа обновлена', 'success')
        except Exception:
            db.session.rollback()
            flash('Ошибка при обновлении школы', 'error')
    return redirect(url_for('admin_schools'))


@app.route('/admin/grades', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_grades():
    if request.method == 'POST':
        name = request.form.get('name')
        school_id = request.form.get('school_id')
        if name and school_id:
            try:
                db.session.add(Grade(name=name.strip(), school_id=int(school_id)))
                db.session.commit()
                flash('Класс добавлен', 'success')
            except Exception:
                db.session.rollback()
                flash('Ошибка при добавлении класса', 'error')
        return redirect(url_for('admin_dashboard', tab='grades'))
    grades = Grade.query.order_by(Grade.name).all()
    schools = School.query.order_by(School.name).all()
    return render_template('admin_panel.html', cities=City.query.order_by(City.name).all(), schools=schools, grades=grades)


@app.route('/admin/grades/delete/<int:grade_id>', methods=['POST'])
@login_required(role='admin')
def admin_delete_grade(grade_id):
    g = Grade.query.get_or_404(grade_id)
    try:
        db.session.delete(g)
        db.session.commit()
        flash('Класс удалён', 'success')
    except Exception:
        db.session.rollback()
        flash('Ошибка при удалении класса', 'error')
    return redirect(url_for('admin_grades'))


@app.route('/admin/grades/edit/<int:grade_id>', methods=['POST'])
@login_required(role='admin')
def admin_edit_grade(grade_id):
    g = Grade.query.get_or_404(grade_id)
    new_name = request.form.get('name')
    if new_name:
        try:
            g.name = new_name.strip()
            db.session.commit()
            flash('Класс обновлён', 'success')
        except Exception:
            db.session.rollback()
            flash('Ошибка при обновлении класса', 'error')
    return redirect(url_for('admin_grades'))


# Роуты для анализа по фото удалены — функциональность определения по фото отключена.
# Если нужно полностью удалить связанные шаблоны и ссылки в UI, выполните дополнительные правки.

@app.route('/about')
def about():
    return render_template('about.html')


# ---- Debug helper: показать текущую сессию (полезно при локальной разработке) ----
@app.route('/_debug/session')
def _debug_session():
    # Возвращаем только полезные ключи
    return jsonify({
        'language': session.get('language'),
        'user_id': session.get('user_id'),
        'role': session.get('role')
    })

# API endpoints

@app.route('/api/v1/student/<int:student_id>/logs')
@login_required()
@cache.cached(timeout=60)
def get_student_logs(student_id):
    # Проверяем права доступа
    if session.get('role') == 'student' and session.get('user_id') != student_id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    if session.get('role') == 'parent':
        parent = Parents.query.get(session.get('user_id'))
        if not parent or not Student.query.filter_by(id=student_id, parent_id=parent.id).first():
            return jsonify({'error': 'Доступ запрещен'}), 403
            
    start_of_day = datetime.combine(date.today(), datetime.min.time())
    logs = EatLog.query.filter(
        EatLog.student_id == student_id,
        EatLog.created_at >= start_of_day
    ).all()
    
    return jsonify([{
        'id': log.id,
        'name': log.name,
        'calories': log.calories,
        'protein': log.protein,
        'fat': log.fat,
        'carbs': log.carbs,
        'created_at': log.created_at.isoformat()
    } for log in logs])

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500





# ---------------- Запуск ----------------

# Инициализация базы данных и создание таблиц при запуске
with app.app_context():
    # Создаём таблицы, если их ещё нет
    db.create_all()

    # Для существующих SQLite-баз: если добавлена колонка barcode в модель, но в таблице её нет,
    # автоматически добавим столбец (простая ALTER TABLE) чтобы не падало приложение.
    try:
        # Получаем список колонок через PRAGMA
        res = db.session.execute(text("PRAGMA table_info('eat')")).all()
        cols = [r[1] for r in res]
        if 'barcode' not in cols:
            try:
                db.session.execute(text("ALTER TABLE eat ADD COLUMN barcode VARCHAR(64)"))
                db.session.commit()
                print('Added missing column eat.barcode')
            except Exception as e:
                # не критично — просто логируем
                print('Failed to add barcode column:', e)
    except Exception:
        # если что-то пошло не так с PRAGMA — не мешаем запуску
        pass

# Запускаем приложение только при локальной разработке
if __name__ == "__main__":
    # Run locally when executed directly. In hosted environments (uwsgi/gunicorn)
    # the application should be served by the WSGI server instead.
    import os
    import socket

    def find_free_port(host: str, start_port: int = 5000, max_tries: int = 50) -> int:
        """Return first free port starting from start_port (tries max_tries)."""
        for p in range(start_port, start_port + max_tries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((host, p))
                return p
            except OSError:
                continue
        raise RuntimeError(f'No free port found in range {start_port}..{start_port+max_tries-1}')

    host = os.environ.get('HOST', '0.0.0.0')
    try:
        requested_port = int(os.environ.get('PORT', '5000'))
    except Exception:
        requested_port = 5000

    try:
        port_to_use = find_free_port(host, requested_port, max_tries=100)
        if port_to_use != requested_port:
            app.logger.warning(f'Port {requested_port} in use, starting on {port_to_use} instead')
        app.run(host=host, port=port_to_use, debug=True)
    except Exception as e:
        app.logger.exception(f'Failed to start Flask dev server: {e}')
        raise
