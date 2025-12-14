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
    # Используем StringField для гибкости и чтобы избежать "Not a valid choice."
    city = StringField('Город', validators=[Optional()])
    school = StringField('Школа', validators=[Optional()])
    grade = StringField('Класс', validators=[Optional()])
    # Убрана верхняя граница возраста: теперь можно ввести любое неотрицательное значение
    age = FloatField('Возраст', validators=[Optional(), NumberRange(min=0)])
    height = FloatField('Рост (см)', validators=[Optional(), NumberRange(min=0, max=250)])
    weight = FloatField('Вес (кг)', validators=[Optional(), NumberRange(min=0, max=150)])
    # Поле активности оставляем свободным (коэффициент или ключ).
    activity = StringField('Активность', validators=[Optional()])