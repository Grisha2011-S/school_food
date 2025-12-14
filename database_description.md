# Описание структуры базы данных

## Общая информация
База данных — это SQLite (файл `school.db`), используемая в Flask-приложении с SQLAlchemy для системы школьного питания.

## Таблицы и их структура

### Основные таблицы пользователей и ролей

#### parents (Родители)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `babe` (VARCHAR(120), NULL) — возможно, имя ребенка
- `login` (VARCHAR(120), UNIQUE, NOT NULL) — логин
- `password` (VARCHAR(128), NOT NULL) — пароль
- `school` (VARCHAR(200), NULL) — школа
- Связь: один ко многим с таблицей `student` (дети)

#### student (Ученики)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `login` (VARCHAR(50), UNIQUE, NOT NULL) — логин
- `password` (VARCHAR(200), NOT NULL) — пароль
- `name` (VARCHAR(120), NULL) — имя
- `gender` (VARCHAR(10), NULL) — пол
- `calories` (REAL, DEFAULT 2000.0) — калории
- `protein` (REAL, DEFAULT 0.0) — белки
- `fat` (REAL, DEFAULT 0.0) — жиры
- `carbs` (REAL, DEFAULT 0.0) — углеводы
- `age` (REAL, NULL) — возраст
- `height` (REAL, NULL) — рост
- `weight` (REAL, NULL) — вес
- `activity` (REAL, NULL) — активность
- `parent_id` (INTEGER, FOREIGN KEY -> parents.id, NULL) — родитель
- `role` (VARCHAR(20), DEFAULT "student") — роль
- `city` (VARCHAR(100), NULL) — город
- `school` (VARCHAR(200), NULL) — школа
- `grade` (VARCHAR(20), NULL) — класс

#### cooks (Повара)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `login` (VARCHAR(120), UNIQUE, NOT NULL) — логин
- `password` (VARCHAR(128), NOT NULL) — пароль
- `city` (VARCHAR(100), NULL) — город
- `school` (VARCHAR(200), NULL) — школа

#### admins (Администраторы)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `login` (VARCHAR(120), UNIQUE, NOT NULL) — логин
- `password` (VARCHAR(200), NOT NULL) — пароль
- `is_master` (BOOLEAN, DEFAULT FALSE) — является ли мастер-админом
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP) — дата создания
- `created_by` (INTEGER, FOREIGN KEY -> admins.id, NULL) — кто создал

### Таблицы для образовательной структуры

#### cities (Города)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `name` (VARCHAR(200), UNIQUE, NOT NULL) — название города

#### schools (Школы)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `name` (VARCHAR(250), NOT NULL) — название школы
- `city_id` (INTEGER, FOREIGN KEY -> cities.id, NOT NULL) — город
- Связь: многие к одному с таблицей `cities`

#### grades (Классы)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `name` (VARCHAR(50), UNIQUE, NOT NULL) — название класса
- `school_id` (INTEGER, FOREIGN KEY -> schools.id, NOT NULL) — школа
- Связь: многие к одному с таблицей `schools`

### Таблицы для питания

#### eat (Еда)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `name` (VARCHAR(120), NOT NULL) — название
- `calories` (REAL, NOT NULL) — калории
- `protein` (REAL, NOT NULL) — белки
- `fat` (REAL, NOT NULL) — жиры
- `carbs` (REAL, NOT NULL) — углеводы
- `type` (VARCHAR(20), DEFAULT "school") — тип
- `image` (VARCHAR(250), NULL) — путь к изображению
- `week` (INTEGER, NULL) — неделя (1 или 2)
- `day` (INTEGER, NULL) — день (1-7)

#### eatlog (Логи питания)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `student_id` (INTEGER, FOREIGN KEY -> student.id, NOT NULL) — ученик
- `food_id` (INTEGER, FOREIGN KEY -> eat.id, NULL) — еда
- `name` (VARCHAR(200), NOT NULL) — название
- `calories` (REAL, NOT NULL, DEFAULT 0.0) — калории
- `protein` (REAL, NOT NULL, DEFAULT 0.0) — белки
- `fat` (REAL, NOT NULL, DEFAULT 0.0) — жиры
- `carbs` (REAL, NOT NULL, DEFAULT 0.0) — углеводы
- `created_at` (DATETIME, NOT NULL, DEFAULT CURRENT_TIMESTAMP) — дата создания
- Связи: многие к одному с `student` и `eat`

#### packs (Наборы еды по дням)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `week` (INTEGER, NOT NULL) — номер недели (1 или 2)
- `day` (INTEGER, NOT NULL) — день недели (1-7)
- `created_by` (INTEGER, FOREIGN KEY -> cooks.id, NULL) — кто создал

#### pack_items (Элементы наборов)
- `id` (INTEGER, PRIMARY KEY) — уникальный идентификатор
- `pack_id` (INTEGER, FOREIGN KEY -> packs.id, NOT NULL) — набор
- `food_id` (INTEGER, FOREIGN KEY -> eat.id, NOT NULL) — еда
- `ord` (INTEGER, NULL) — порядок
- `is_active` (BOOLEAN, NOT NULL, DEFAULT TRUE) — активен ли
- Связи: многие к одному с `packs` и `eat`

## Связи между таблицами
- Родители могут иметь несколько детей (учеников).
- Ученики связаны с родителями, городами, школами и классами.
- Школы принадлежат городам.
- Классы принадлежат школам.
- Логи питания связаны с учениками и едой.
- Наборы еды создаются поварами и состоят из элементов (еды).
- Администраторы могут создавать других администраторов.

Это приложение предназначено для управления школьным питанием, отслеживания потребления еды учениками и административного управления.