# Миграция на Google Apps Script

## Обзор
Это руководство по миграции Flask-приложения на Google Apps Script для работы в Google Таблицах.

## Шаги миграции

### 1. Создание Google Apps Script проекта
1. Откройте Google Таблицы (sheets.google.com)
2. Создайте новую таблицу
3. Перейдите в "Расширения" > "Apps Script"
4. Скопируйте содержимое `apps_script.gs` в редактор Apps Script
5. Создайте HTML-файлы в Apps Script:
   - "Файл" > "Новый" > "HTML-файл", назовите `index` и вставьте содержимое `templates/index.html`
   - Аналогично для `login`, `register`, `dashboard`, `calorie_calculator`, `photo_analyze`, `about` (используйте соответствующие файлы из templates/)

### 2. Включение API
1. В Apps Script редакторе, "Ресурсы" > "Дополнительные сервисы"
2. Найдите и включите "Google Cloud Vision API"
3. Сохраните проект

### 3. Настройка веб-приложения
1. В Apps Script редакторе, "Опубликовать" > "Развернуть как веб-приложение"
2. Выберите версию, установите права доступа (для всех, включая анонимных)
3. Получите URL веб-приложения

### 4. Инициализация таблиц
1. В Apps Script редакторе, запустите функцию `initializeSheets`
2. Это создаст все необходимые листы в таблице

### 5. Структура данных
- **Parents**: Родители
- **Students**: Ученики
- **Cooks**: Повара
- **Eat**: Еда
- **EatLog**: Логи питания
- **Cities**: Города
- **Schools**: Школы
- **Grades**: Классы
- **Admins**: Администраторы
- **Packs**: Наборы еды
- **PackItems**: Элементы наборов

## Функции Apps Script

### Основные функции
- `initializeSheets()`: Инициализация заголовков таблиц
- `createParent()`, `getParent()`: Работа с родителями
- `createStudent()`, `getStudent()`: Работа с учениками
- `createEat()`, `getEatById()`: Работа с едой
- `createEatLog()`: Создание логов питания
- `analyzeFoodImage()`: Анализ фото через Vision API
- `createNutritionReport()`: Создание отчета в Word

### Веб-функции
- `doGet()`: Возвращает HTML интерфейс
- `doPost()`: Обрабатывает POST-запросы
- `handleLogin()`: Обработка входа
- `handleRegister()`: Обработка регистрации
- `getTodaysMenu()`: Получение меню на сегодня
- `getCities()`, `getSchools()`: Получение списков городов и школ

### HTML-файлы
- `index.html`: Главная страница с меню
- `login.html`: Форма входа
- `register.html`: Форма регистрации
- `dashboard.html`: Панель управления
- `calorie_calculator.html`: Калькулятор калорий
- `photo_analyze.html`: Анализ фото еды
- `about.html`: О проекте

## Функциональность
- Регистрация и вход пользователей (ученики, родители, повара, админы)
- Отслеживание питания
- Анализ фото еды через Google Vision API
- Управление школами, городами, классами
- Создание наборов еды
- Генерация отчетов в формате Word

## Технологии
- Google Apps Script (JavaScript)
- Google Sheets (база данных)
- Google Vision API (анализ изображений)
- Google Docs API (создание документов)
- HTML/CSS/JavaScript (фронтенд)

## Безопасность
- Хэширование паролей
- Проверка ролей
- CSP для защиты от XSS

## Миграция с Flask
Проект был перенесен из Flask-приложения. Все Python-файлы больше не используются. Данные из SQLite нужно будет импортировать в Google Sheets вручную или написать скрипт миграции.