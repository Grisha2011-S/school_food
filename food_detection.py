"""
Безопасная обёртка для analyze_image_with_gemini.
Импортирует рабочую реализацию из food_detection_impl.
"""
from food_detection_impl import analyze_image_with_gemini

__all__ = ["analyze_image_with_gemini"]