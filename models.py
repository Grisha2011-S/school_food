from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Parents(db.Model):
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    babe = db.Column(db.String(120), nullable=True)
    login = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    school = db.Column(db.String(200), nullable=True)
    children = db.relationship('Student', backref='parent', lazy=True)

    def __init__(self, login, password, school=None, babe=None):
        self.login = login
        self.password = password
        self.school = school
        self.babe = babe


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(120), nullable=True)
    calories = db.Column(db.Float, default=2000.0)
    protein = db.Column(db.Float, default=0.0)
    fat = db.Column(db.Float, default=0.0)
    carbs = db.Column(db.Float, default=0.0)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=True)
    role = db.Column(db.String(20), default="student")
    is_teacher = db.Column(db.Boolean, default=False)
    city = db.Column(db.String(100), nullable=True)
    school = db.Column(db.String(200), nullable=True)
    grade = db.Column(db.String(20), nullable=True)

    def __init__(self, login: str, password: str, parent_id: int | None = None, 
                 calories: float = 2000.0, protein: float = 0.0, fat: float = 0.0, carbs: float = 0.0,
                 role: str = "student", is_teacher: bool = False, city: str | None = None, 
                 school: str | None = None, grade: str | None = None, name: str | None = None):
        self.login = login
        self.password = password
        self.parent_id = parent_id
        self.calories = float(calories)
        self.protein = float(protein)
        self.fat = float(fat)
        self.carbs = float(carbs)
        self.role = role
        self.is_teacher = is_teacher
        self.city = city
        self.school = school
        self.grade = grade
        self.name = name

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True


class Cook(db.Model):
    __tablename__ = 'cooks'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    city = db.Column(db.String(100), nullable=True)
    school = db.Column(db.String(200), nullable=True)

    def __init__(self, login, password, city=None, school=None):
        self.login = login
        self.password = password
        self.city = city
        self.school = school


class Eat(db.Model):
    __tablename__ = 'eat'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False, default="school")
    image = db.Column(db.String(250), nullable=True)
    week = db.Column(db.Integer, nullable=True)  # 1 или 2 для школьной еды
    day = db.Column(db.Integer, nullable=True)   # 1-7 для школьной еды

    def __init__(self, name, calories, protein, fat, carbs, type="school", 
                 image=None, week=None, day=None):
        self.name = name
        self.calories = calories
        self.protein = protein
        self.fat = fat
        self.carbs = carbs
        self.type = type
        self.image = image
        self.week = week
        self.day = day


class EatLog(db.Model):
    __tablename__ = 'eatlog'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('eat.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Float, nullable=False, default=0.0)
    protein = db.Column(db.Float, nullable=False, default=0.0)
    fat = db.Column(db.Float, nullable=False, default=0.0)
    carbs = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='eat_logs')
    food = db.relationship('Eat', backref='eat_logs')

    def __init__(self, student_id: int, food_id: int | None, name: str, 
                 calories: float, protein: float, fat: float, carbs: float):
        self.student_id = student_id
        self.food_id = food_id
        self.name = name
        self.calories = float(calories)
        self.protein = float(protein)
        self.fat = float(fat)
        self.carbs = float(carbs)


class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name


class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    city = db.relationship('City', backref='schools')

    def __init__(self, name, city_id):
        self.name = name
        self.city_id = city_id


class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    school = db.relationship('School', backref='grades')

    def __init__(self, name, school_id):
        self.name = name
        self.school_id = school_id


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_master = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)

    def __init__(self, login, password, is_master=False, created_by=None):
        self.login = login
        self.password = password
        self.is_master = is_master
        self.created_by = created_by

    @property
    def is_active(self):
        return True


# --- Packs (наборы еды по дням) ---
class Pack(db.Model):
    __tablename__ = 'packs'
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, nullable=False)  # Номер недели (1 или 2)
    day = db.Column(db.Integer, nullable=False)   # День недели (1-7)
    created_by = db.Column(db.Integer, db.ForeignKey('cooks.id'), nullable=True)

    def __init__(self, week, day, created_by=None):
        self.week = week
        self.day = day
        self.created_by = created_by

    @property
    def name(self):
        """Автоматическое формирование названия пака"""
        days = {
            1: 'Понедельник',
            2: 'Вторник',
            3: 'Среда',
            4: 'Четверг',
            5: 'Пятница',
            6: 'Суббота',
            7: 'Воскресенье'
        }
        return f"Неделя {self.week}, {days.get(self.day, str(self.day))}"


class PackItem(db.Model):
    __tablename__ = 'pack_items'
    id = db.Column(db.Integer, primary_key=True)
    pack_id = db.Column(db.Integer, db.ForeignKey('packs.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('eat.id'), nullable=False)
    ord = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    pack = db.relationship('Pack', backref='items')
    food = db.relationship('Eat')

    def __init__(self, pack_id, food_id, ord=None, is_active=True):
        self.pack_id = pack_id
        self.food_id = food_id
        self.ord = ord
        self.is_active = is_active