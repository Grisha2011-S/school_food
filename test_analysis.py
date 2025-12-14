import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyAz-m_zcbkYEkzdfBjIMyqGz_Tz7qSBvRc'
from food_detection_impl import analyze_image_with_gemini

# Используйте реальное изображение (замените путь)
result = analyze_image_with_gemini('C:/path/to/image.jpg')
print('Result:', result)
