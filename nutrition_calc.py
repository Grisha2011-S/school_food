from typing import Tuple, Dict
import math

def validate_measurements(measurements: Dict[str, float]) -> Tuple[bool, str]:
    """
    Проверяет корректность антропометрических данных.
    
    Args:
        measurements: словарь с ключами 'age', 'height', 'weight', 'activity'
        
    Returns:
        (bool, str): (валидно ли, сообщение об ошибке)
    """
    if not measurements or any(k not in measurements for k in ['age', 'height', 'weight', 'activity']):
        return False, "Отсутствуют необходимые измерения"

    try:
        age = float(measurements['age'])
        height = float(measurements['height'])
        weight = float(measurements['weight'])
        activity = float(measurements['activity'])

        if not (0 <= age <= 18):
            return False, "Возраст должен быть от 0 до 18 лет"
            
        if not (50 <= height <= 250):
            return False, "Рост должен быть от 50 до 250 см"
            
        if not (3 <= weight <= 150):
            return False, "Вес должен быть от 3 до 150 кг"
            
        if not (1.2 <= activity <= 2.0):
            return False, "Коэффициент активности должен быть от 1.2 до 2.0"
            
        return True, ""
        
    except (ValueError, TypeError) as e:
        return False, f"Ошибка в данных: {str(e)}"

def calculate_nutrition(gender: str, measurements: Dict[str, float]) -> Tuple[float, float, float, float]:
    """
    Рассчитывает КБЖУ на основе антропометрических данных.
    
    Args:
        gender: 'male' или 'female'
        measurements: словарь с ключами 'age', 'height', 'weight', 'activity'
        
    Returns:
        (калории, белки, жиры, углеводы)
    """
    if gender not in ('male', 'female'):
        raise ValueError("Некорректный пол")
        
    age = float(measurements['age'])
    height = float(measurements['height'])
    weight = float(measurements['weight'])
    activity = float(measurements['activity'])
    
    # Формула Миффлина-Сан Жеора
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
    total_calories = round(math.ceil(bmr * activity), 1)
    total_protein = round((total_calories * 0.2) / 4, 1)
    total_fat = round((total_calories * 0.3) / 9, 1)
    total_carbs = round((total_calories * 0.5) / 4, 1)
    
    return total_calories, total_protein, total_fat, total_carbs