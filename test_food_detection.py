from food_detection import analyze_image_with_gemini
import os
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

def test_food_detection():
    # Проверяем наличие API ключа
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("ОШИБКА: GEMINI_API_KEY не установлен")
        return

    print(f"API ключ найден (длина: {len(api_key)})")

    # Путь к тестовому изображению
    test_image = os.path.join('static', 'uploads', 'test.jpg')
    
    if not os.path.exists(test_image):
        print(f"ОШИБКА: Тестовое изображение не найдено: {test_image}")
        return

    print(f"Анализируем изображение: {test_image}")
    result = analyze_image_with_gemini(test_image)
    
    if result is None:
        print("ОШИБКА: Не удалось проанализировать изображение")
        return

    print("\nРезультат анализа:")
    print(f"Название: {result.get('name', 'не определено')}")
    print(f"Размер порции: {result.get('serving_size', 'не определен')}")
    print(f"Калории: {result.get('calories', 0)}")
    print(f"Белки: {result.get('protein', 0)}г")
    print(f"Жиры: {result.get('fat', 0)}г")
    print(f"Углеводы: {result.get('carbs', 0)}г")

if __name__ == "__main__":
    test_food_detection()