from PIL import Image
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(BASE_DIR, 'static', 'img', 'favicon.ico')
OUT_DIR = os.path.join(BASE_DIR, 'static', 'img')
SIZES = [180, 152, 120]

if not os.path.exists(SRC):
    print('Source favicon not found:', SRC)
    raise SystemExit(1)

img = Image.open(SRC)
for s in SIZES:
    out_path = os.path.join(OUT_DIR, f'apple-touch-icon-{s}x{s}.png')
    # convert and resize
    icon = img.convert('RGBA')
    icon = icon.resize((s, s), Image.LANCZOS)
    icon.save(out_path, format='PNG')
    print('Wrote', out_path)

print('Done')
