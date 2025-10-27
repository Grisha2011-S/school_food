from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, PasswordField
from wtforms.validators import DataRequired, NumberRange, Optional

class FoodForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    calories = FloatField('Калории', validators=[DataRequired(), NumberRange(min=0)])
    protein = FloatField('Белки', validators=[DataRequired(), NumberRange(min=0)])
    fat = FloatField('Жиры', validators=[DataRequired(), NumberRange(min=0)])
    carbs = FloatField('Углеводы', validators=[DataRequired(), NumberRange(min=0)])
    type = SelectField('Тип', choices=[('school', 'Школьная'), ('normal', 'Обычная')])

class ChildForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    gender = SelectField('Пол', choices=[('male', 'Мужской'), ('female', 'Женский')])
    # Выбор города/школы/класса в виде селекторов
    city = SelectField('Город', choices=[('', '— выберите город —'), ('Москва', 'Москва'), ('Санкт-Петербург','Санкт-Петербург'), ('Новосибирск','Новосибирск')], validators=[Optional()])
    school = SelectField('Школа', choices=[('', '— выберите школу —')], validators=[Optional()])
    grade = SelectField('Класс', choices=[('', '— выберите класс —')] + [(str(i), str(i)) for i in range(1, 12)], validators=[Optional()])
    age = FloatField('Возраст', validators=[Optional(), NumberRange(min=0, max=18)])
    height = FloatField('Рост (см)', validators=[Optional(), NumberRange(min=0, max=250)])
    weight = FloatField('Вес (кг)', validators=[Optional(), NumberRange(min=0, max=150)])
    activity = SelectField('Активность', choices=[
        ('1.2', 'Минимальная'),
        ('1.375', 'Легкая'),
        ('1.55', 'Средняя'),
        ('1.725', 'Высокая'),
        ('1.9', 'Очень высокая')
    ])