from flask import flash, redirect, url_for
from werkzeug.security import generate_password_hash
from models import Student, db
import logging

def process_child_form(form, parent_id):
    """
    Обрабатывает форму добавления ребенка.
    
    Args:
        form: форма ChildForm
        parent_id: ID родителя
        
    Returns:
        bool: успешно ли обработана форма
    """
    try:
        # Проверка обязательных полей
        if not form.login.data or not form.password.data:
            flash('Логин и пароль обязательны')
            return False
            
        # Базовые значения КБЖУ
        calories = 2000.0
        protein = round((calories * 0.2) / 4, 1)  # 20% калорий из белка
        fat = round((calories * 0.3) / 9, 1)      # 30% калорий из жира
        carbs = round((calories * 0.5) / 4, 1)    # 50% калорий из углеводов
        
        # Получение и валидация антропометрических данных
        try:
            gender = str(form.gender.data) if form.gender.data else 'male'
            age = float(form.age.data) if form.age.data is not None else None
            height = float(form.height.data) if form.height.data is not None else None
            weight = float(form.weight.data) if form.weight.data is not None else None
            activity = float(form.activity.data) if form.activity.data is not None else None
            
            # Если все данные есть, рассчитываем КБЖУ
            if all(x is not None for x in [age, height, weight, activity]):
                try:
                    from nutrition_calc import calculate_nutrition
                    calories, protein, fat, carbs = calculate_nutrition(
                        gender, age, height, weight, activity
                    )
                    
                    # Проверка BMI и рекомендации
                    bmi = weight / ((height/100.0)**2)
                    if bmi < 18.5 or calories < 1800:
                        flash('Рекомендуется увеличить суточную калорийность для ребёнка.', 'info')
                    elif bmi > 25 or calories > 2200:
                        flash('Рекомендуется уменьшить суточную калорийность для ребёнка.', 'info')
                        
                except Exception as e:
                    logging.warning(f'Error calculating nutrition: {str(e)}')
                    flash('Ошибка при расчете питания, используются значения по умолчанию', 'warning')
                    
        except (ValueError, TypeError) as e:
            logging.warning(f'Error processing measurements: {str(e)}')
            flash('Ошибка в антропометрических данных, используются значения по умолчанию', 'warning')
        
        # Создание нового ученика
        hash_pass = generate_password_hash(str(form.password.data))
        child = Student(
            login=form.login.data,
            password=hash_pass,
            parent_id=parent_id,
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs
        )
        
        db.session.add(child)
        db.session.commit()
        flash('Ребёнок успешно добавлен!')
        logging.info(f'Child added: {child.login}, nutrition: {calories}kcal')
        return True
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error adding child: {str(e)}')
        flash('Ошибка: возможно, логин ребёнка уже существует.', 'error')
        return False