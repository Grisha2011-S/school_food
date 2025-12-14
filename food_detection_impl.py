"""Food detection helpers.

This module provides analyze_image_with_gemini(image_path) which attempts to
call the Google Gemini (Generative) Vision API via the python SDK. The
implementation is defensive:

- If the GEMINI API key is not configured, the function will return None and
  log a warning (so the app can show a friendly message instead of crashing).
- Any exceptions during the call are caught and logged; the function returns
  None on failure.

If you prefer the previous behaviour (always return "food not found" with 0
values), we can change the fallback to return that stub instead of None.
"""

from typing import Dict, Union, Optional
import os
import json
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def _safe_float(v: Union[str, float, int, None]) -> float:
    try:
        if v is None:
            return 0.0
        return float(str(v).replace(',', '.'))
    except Exception:
        return 0.0


def analyze_image_with_gemini(image_path: str) -> Optional[Dict[str, Union[str, float]]]:
    """Analyze image using Google Gemini (Generative) Vision API.

    Returns a dict with keys: name, serving_size, calories, protein, fat, carbs
    or None if analysis is not available (API key missing or error).
    """
    # Загружаем переменные окружения из .env файла
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment variables from .env file")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file")
    try:
        # Lazy import of SDK to avoid hard dependency at module import time
        try:
            import google.generativeai as genai
            logger.info('Successfully imported google.generativeai')
        except Exception as e:
            logger.error(f'Failed to import google.generativeai: {str(e)}')
            return None

        # Read API key from environment or .env (prefer env)
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('API_KEY')
        if not api_key:
            logger.warning('GEMINI_API_KEY or API_KEY not set; image analysis disabled.')
            return None
        logger.info('Using GEMINI API key from environment (value not logged).')

        try:
            genai.configure(api_key=api_key)
            logger.info('Successfully configured google.generativeai SDK')
        except Exception as e:
            logger.error(f'Failed to configure google.generativeai SDK: {e}. Check SDK installation/version.')
            return None

        # open image to ensure file exists and is readable; make a copy to pass to SDK
        try:
            with Image.open(image_path) as img:
                img_copy = img.copy()
                logger.info(f'Opened image {image_path}, size={img.size}')
        except Exception as e:
            logger.error(f'Failed to open image {image_path}: {e}')
            return None

        # Define response schema (mirror the JS example). We will request JSON.
        nutrition_schema = {
            "type": "OBJECT",
            "properties": {
                "foodName": {"type": "STRING", "description": "Detected food name"},
                "servingSize": {"type": "STRING", "description": "Estimated serving size"},
                "calories": {"type": "NUMBER", "description": "Estimated calories"},
                "protein": {"type": "NUMBER", "description": "Protein grams"},
                "fat": {"type": "NUMBER", "description": "Fat grams"},
                "carbohydrates": {"type": "NUMBER", "description": "Carbs grams"},
            },
            "required": ["foodName", "servingSize", "calories", "protein", "fat", "carbohydrates"],
        }

        prompt = [
            "Определи еду на этом изображении. Оцени размер порции и предоставь примерную оценку пищевой ценности для порции, показанной на фото. Если на изображении нет еды, укажи это в 'foodName' и установи все значения питательных веществ на 0. Ответ должен быть только в формате JSON.",
            img_copy,
        ]

        # Call the SDK to generate content. Wrap in try/except because SDK public
        # API may differ between versions; surface clear logs if it's incompatible.
        try:
            logger.info('Calling genai.GenerativeModel.generate_content...')
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type='application/json',
                    response_schema=nutrition_schema,
                ),
            )
            logger.info('Gemini API call succeeded')
        except Exception as e:
            logger.exception(f'Error while calling google.generativeai SDK: {e}')
            return None

        # Extract textual response
        text = getattr(response, 'text', None) or str(response)
        logger.debug(f'Raw Gemini response: {text}')

        # Be defensive: try to find the first JSON object in the response
        parsed = None
        try:
            start = text.find('{')
            end = text.rfind('}')
            to_parse = text
            if start != -1 and end != -1 and end > start:
                to_parse = text[start:end+1]
            parsed = json.loads(to_parse)
            logger.info(f'Parsed JSON: {parsed}')
        except Exception as e:
            logger.error(f'Failed to parse JSON from Gemini response: {e} -- raw: {text}')
            return None

        # Map to stable keys expected by templates
        food_name = parsed.get('foodName') or parsed.get('food_name') or parsed.get('name') or 'Проанализированное блюдо'
        serving = parsed.get('servingSize') or parsed.get('serving_size') or parsed.get('serving') or ''
        calories = _safe_float(parsed.get('calories'))
        protein = _safe_float(parsed.get('protein'))
        fat = _safe_float(parsed.get('fat'))
        carbs = _safe_float(parsed.get('carbohydrates') or parsed.get('carbs'))

        result = {
            'name': food_name,
            'serving_size': serving,
            'calories': calories,
            'protein': protein,
            'fat': fat,
            'carbs': carbs,
            # keep original keys for compatibility
            'foodName': parsed.get('foodName'),
            'servingSize': parsed.get('servingSize'),
            'carbohydrates': parsed.get('carbohydrates'),
        }
        logger.info(f'Returning result: {result}')
        return result

    except Exception as e:
        logger.exception(f'Error in analyze_image_with_gemini: {e}')
        return None
