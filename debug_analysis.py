#!/usr/bin/env python
"""Тест анализа изображения — проверить все этапы цепочки."""

import os
import sys
from pathlib import Path

# Установить ключ
os.environ['GEMINI_API_KEY'] = 'AIzaSyAz-m_zcbkYEkzdfBjIMyqGz_Tz7qSBvRc'

print("=" * 60)
print("Этап 1: Импорт food_detection_impl напрямую")
print("=" * 60)

try:
    from food_detection_impl import analyze_image_with_gemini as direct_analyze
    print("✓ food_detection_impl импортирован")
except Exception as e:
    print(f"✗ Ошибка импорта food_detection_impl: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Этап 2: Импорт через food_detection (обёртка)")
print("=" * 60)

try:
    from food_detection import analyze_image_with_gemini as wrapped_analyze
    print("✓ food_detection импортирован")
except Exception as e:
    print(f"✗ Ошибка импорта food_detection: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Этап 3: Создание тестового изображения")
print("=" * 60)

test_img_dir = Path(__file__).parent / 'test_images'
test_img_dir.mkdir(exist_ok=True)
test_img_path = test_img_dir / 'test_product.jpg'

try:
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Apple", fill='black')
    draw.rectangle([50, 50, 350, 250], outline='red', width=3)
    img.save(test_img_path)
    print(f"✓ Создано изображение: {test_img_path}")
except Exception as e:
    print(f"✗ Ошибка создания изображения: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Этап 4: Прямой вызов food_detection_impl")
print("=" * 60)

try:
    result = direct_analyze(str(test_img_path))
    print(f"✓ Результат: {result}")
    if result is None:
        print("  ⚠ Результат = None (но это может быть нормально, если на фото нет еды)")
except Exception as e:
    print(f"✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Этап 5: Вызов через обёртку food_detection")
print("=" * 60)

try:
    result = wrapped_analyze(str(test_img_path))
    print(f"✓ Результат: {result}")
    if result is None:
        print("  ⚠ Результат = None (но это может быть нормально, если на фото нет еды)")
except Exception as e:
    print(f"✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Этап 6: Тест через Flask app контекст")
print("=" * 60)

try:
    from flask_app import app, _ensure_analyze_image_loaded
    
    with app.app_context():
        print("Flask app контекст активирован")
        
        # Проверить загрузку анализатора
        is_loaded = _ensure_analyze_image_loaded()
        print(f"_ensure_analyze_image_loaded() = {is_loaded}")
        
        if is_loaded and hasattr(app, '_analyze_image') and app._analyze_image:
            print("✓ app._analyze_image установлен")
            result = app._analyze_image(str(test_img_path))
            print(f"✓ Результат: {result}")
        else:
            print("✗ app._analyze_image не установлен или None")
            
except Exception as e:
    print(f"✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("ИТОГ")
print("=" * 60)
print("Если все этапы прошли — анализ работает и проблема только в веб-интерфейсе.")
