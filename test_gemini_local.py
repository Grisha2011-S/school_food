#!/usr/bin/env python
"""Локальный тест анализа изображения с Gemini API."""

import os
import sys
import urllib.request
from pathlib import Path

# Установить ключ
os.environ['GEMINI_API_KEY'] = 'AIzaSyAz-m_zcbkYEkzdfBjIMyqGz_Tz7qSBvRc'

# Импортировать функцию
from food_detection_impl import analyze_image_with_gemini

# Создать папку для тестовых изображений
test_img_dir = Path(__file__).parent / 'test_images'
test_img_dir.mkdir(exist_ok=True)

# Загрузить тестовое изображение с интернета (простой продукт)
test_img_path = test_img_dir / 'test_product.jpg'

if not test_img_path.exists():
    print(f"Создаю тестовое изображение...")
    # Если PIL доступен, создать простое изображение с текстом
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Apple", fill='black')
        draw.rectangle([50, 50, 350, 250], outline='red', width=3)
        img.save(test_img_path)
        print(f"Создано тестовое изображение: {test_img_path}")
    except ImportError:
        # Fallback: загрузить с альтернативного источника
        print(f"Загружаю тестовое изображение...")
        urls = [
            'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png',
            'https://via.placeholder.com/400x300?text=Apple'
        ]
        for url in urls:
            try:
                urllib.request.urlretrieve(url, test_img_path, timeout=5)
                print(f"Скачано: {test_img_path}")
                break
            except Exception as e:
                print(f"Ошибка загрузки {url}: {e}")
        else:
            print("Не удалось загрузить тестовое изображение")
            sys.exit(1)

print(f"\nТестирую анализ изображения: {test_img_path}")
print(f"Размер файла: {test_img_path.stat().st_size} bytes")

try:
    result = analyze_image_with_gemini(str(test_img_path))
    print(f"\n✓ Результат анализа:")
    if result:
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print("  Result is None — см. логи выше")
except Exception as e:
    print(f"\n✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()
