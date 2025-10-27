import os
import json

# Указываем путь к проекту
proj_root = os.path.dirname(os.path.dirname(__file__))
import sys
sys.path.insert(0, proj_root)

from flask_app import analyze_image_with_gemini

# Выберите существующий файл в static/uploads
test_file = os.path.join(proj_root, 'static', 'uploads', 'shokoladnyy_batonchik_snickers_50_5g_3_full.jpg')
print('Test file:', test_file)
if not os.path.exists(test_file):
    print('Test image not found, listing uploads dir:')
    for f in os.listdir(os.path.join(proj_root, 'static', 'uploads')):
        print(' -', f)
    raise SystemExit(1)

result = analyze_image_with_gemini(test_file)
print('Result:')
print(json.dumps(result, ensure_ascii=False, indent=2))
