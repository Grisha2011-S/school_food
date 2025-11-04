"""
Ленивая обёртка для analyze_image_with_gemini.
Импорт реализации выполняется при первом вызове, чтобы не ломать
загрузку приложения, если модуль или зависимости отсутствуют на старом/целевом хосте.
"""
from typing import Optional, Dict, Union
import logging

logger = logging.getLogger(__name__)


def analyze_image_with_gemini(image_path: str) -> Optional[Dict[str, Union[str, float]]]:
	"""Вызвать реальную реализацию из food_detection_impl, если она доступна.

	Возвращает результат или None при ошибке / отсутствии SDK / ключа.
	"""
	try:
		# Импортируем реализацию при вызове (лениво)
		from food_detection_impl import analyze_image_with_gemini as _impl
	except Exception as e:
		logger.exception(f'Failed to import food_detection_impl.analyze_image_with_gemini: {e}')
		return None

	try:
		return _impl(image_path)
	except Exception:
		logger.exception('Error while running analyze_image_with_gemini implementation')
		return None


__all__ = ["analyze_image_with_gemini"]