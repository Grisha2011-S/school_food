import os
import json
from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import google.generativeai as genai

# --- Конфигурация ---
# Создаем папку для загрузок внутри папки static, чтобы к ней был веб-доступ
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Настраиваем логирование
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, 'app.log'))
    ]
)

# --- Настройка Flask ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Нужен для flash-сообщений
app.secret_key = os.urandom(24) 

# Убедимся, что папка для загрузок существует
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Настройка Gemini API ---
try:
    # API ключ должен быть установлен как переменная окружения
    API_KEY = "AIzaSyA9Q8fn8SGDbPmVsfNp0qCYe0IRPxHeKlI"
    genai.configure(api_key=API_KEY)
except KeyError:
    # В среде разработки AI Studio это должно быть настроено автоматически.
    # Это сообщение поможет при локальном запуске.
    raise RuntimeError("API_KEY не найдена в переменных окружения. Убедитесь, что она установлена.")


def allowed_file(filename):
    """Проверяет, что расширение файла разрешено."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_image_with_gemini(image_path):
    """
    Анализирует изображение с помощью Gemini API и возвращает данные о питательности.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Проверяем существование файла
        if not os.path.exists(image_path):
            logger.error(f"Файл не найден: {image_path}")
            return None
            
        # Проверяем права доступа
        try:
            with open(image_path, 'rb') as f:
                pass
        except PermissionError:
            logger.error(f"Нет прав доступа к файлу: {image_path}")
            return None
            
        logger.info(f"Начинаем анализ изображения: {image_path}")
        
        # Используем модель gemini-2.5-flash, как в JS-версии
        from dotenv import load_dotenv
        load_dotenv()  # загружаем переменные окружения из .env
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY не найден в переменных окружения")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        img = Image.open(image_path)
        
        # Схема для получения структурированного JSON ответа
        # Python SDK использует словари для схемы
        nutrition_schema = {
            "type": "OBJECT",
            "properties": {
                "foodName": {
                    "type": "STRING",
                    "description": "Название блюда, определенного на изображении. Если еда не найдена, укажите 'Еда не найдена'.",
                },
                "servingSize": {
                    "type": "STRING",
                    "description": "Примерный вес порции, показанной на изображении, например 'около 250г'.",
                },
                "calories": {
                    "type": "NUMBER",
                    "description": "Примерное количество калорий для порции на фото.",
                },
                "protein": {
                    "type": "NUMBER",
                    "description": "Примерное количество белка в граммах для порции на фото.",
                },
                "fat": {
                    "type": "NUMBER",
                    "description": "Примерное количество жиров в граммах для порции на фото.",
                },
                "carbohydrates": {
                    "type": "NUMBER",
                    "description": "Примерное количество углеводов в граммах для порции на фото.",
                },
            },
            "required": ["foodName", "servingSize", "calories", "protein", "fat", "carbohydrates"],
        }
        
        prompt_parts = [
            "Определи еду на этом изображении. Оцени размер порции и предоставь примерную оценку пищевой ценности для порции, показанной на фото. Если на изображении нет еды, укажи это в 'foodName' и установи все значения питательных веществ на 0. Ответ должен быть только в формате JSON.",
            img,
        ]

        # Выполняем запрос к API с указанием формата ответа
        response = model.generate_content(
            prompt_parts,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=nutrition_schema
            )
        )
        
        # Парсим JSON из текстового ответа
        return json.loads(response.text)

    except Exception as e:
        # Логируем ошибку для отладки
        print(f"Error during Gemini API call or image processing: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Проверяем наличие файла
        if 'file' not in request.files:
            flash('Файл не был отправлен. Пожалуйста, выберите файл.')
            return redirect(request.url)
            
        file = request.files['file']

        # 2. Проверяем, что файл выбран
        if file.filename == '':
            flash('Файл не был выбран.')
            return redirect(request.url)
            
        # 3. Проверяем расширение и сохраняем файл
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                # Проверяем права на запись в директорию
                if not os.access(os.path.dirname(filepath), os.W_OK):
                    logger.error(f"Нет прав на запись в директорию: {os.path.dirname(filepath)}")
                    flash("Ошибка: нет прав на запись в директорию загрузки")
                    return redirect(request.url)
                
                # Проверяем наличие места на диске
                try:
                    total, used, free = os.statvfs(os.path.dirname(filepath))
                    if file.content_length and free * total < file.content_length:
                        logger.error("Недостаточно места на диске")
                        flash("Ошибка: недостаточно места на диске")
                        return redirect(request.url)
                except AttributeError:
                    # statvfs не доступен на Windows
                    pass
                    
                file.save(filepath)
                logger.info(f"Файл успешно сохранен: {filepath}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении файла {filepath}: {str(e)}")
                flash(f"Ошибка при сохранении файла: {e}")
                return redirect(request.url)

            # 4. Анализируем изображение
            nutrition_data = analyze_image_with_gemini(filepath)

            # 5. Отображаем результат
            if nutrition_data:
                return render_template('index.html', filename=filename, data=nutrition_data)
            else:
                flash('Не удалось проанализировать изображение. Возможно, файл поврежден или API временно недоступен. Попробуйте другое фото.')
                # Отображаем загруженное изображение даже при ошибке анализа
                return render_template('index.html', filename=filename, data=None)
        else:
            flash('Недопустимый тип файла. Разрешены: png, jpg, jpeg, gif, webp.')
            return redirect(request.url)

    # Для GET-запроса просто отображаем главную страницу
    return render_template('index.html', filename=None, data=None)


@app.route('/debug')
def debug_info():
    """Отладочная информация о настройках приложения"""
    if not app.debug:
        return "Debug mode is disabled"
    
    info = {
        'UPLOAD_FOLDER': app.config['UPLOAD_FOLDER'],
        'UPLOAD_FOLDER_EXISTS': os.path.exists(app.config['UPLOAD_FOLDER']),
        'UPLOAD_FOLDER_WRITABLE': os.access(app.config['UPLOAD_FOLDER'], os.W_OK),
        'API_KEY_SET': bool(os.environ.get('GEMINI_API_KEY')),
        'PYTHON_VERSION': sys.version,
        'WORKING_DIR': os.getcwd(),
        'APP_ROOT': os.path.abspath(os.path.dirname(__file__)),
    }
    return json.dumps(info, indent=2)

# Определяем, работаем ли мы на PythonAnywhere
import sys
IS_PYTHONANYWHERE = 'PYTHONANYWHERE_SITE' in os.environ

# Настройка для запуска на разных окружениях
if __name__ == '__main__':
    if IS_PYTHONANYWHERE:
        # На PythonAnywhere используется WSGI
        application = app
    else:
        # Локальный запуск для разработки
        try:
            # Пробуем порт 8080
            app.run(host='0.0.0.0', port=8080)
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print("Порт 8080 занят, пробуем 8081...")
                try:
                    app.run(host='0.0.0.0', port=8081)
                except OSError:
                    print("Порт 8081 тоже занят, пробуем случайный порт...")
                    app.run(host='0.0.0.0', port=0)  # Случайный свободный порт
            else:
                raise
