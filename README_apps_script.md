# School Food System - Apps Script Version

## Описание
Это система школьного питания, перенесенная с Flask/Python на Google Apps Script для работы в Google Таблицах.

## Структура проекта
- `apps_script_project/`: Файлы для Google Apps Script
  - `apps_script.gs`: Основной код Apps Script
  - `base_new.html`: HTML-интерфейс
  - `apps_script_migration_guide.md`: Руководство по миграции

## Быстрый старт
1. Откройте Google Таблицы
2. Создайте новый Apps Script проект
3. Скопируйте содержимое файлов из `apps_script_project/`
4. Включите Google Cloud Vision API
5. Опубликуйте как веб-приложение
6. Запустите `initializeSheets()` для создания таблиц

## Функциональность
- Регистрация и вход пользователей (ученики, родители, повара, админы)
- Отслеживание питания
- Анализ фото еды через Google Vision API
- Управление школами, городами, классами
- Создание наборов еды

## Технологии
- Google Apps Script (JavaScript)
- Google Sheets (база данных)
- Google Vision API (анализ изображений)
- HTML/CSS/JavaScript (фронтенд)

## Безопасность
- Хэширование паролей
- Проверка ролей
- CSP для защиты от XSS

## Миграция с Flask
Проект был перенесен из Flask-приложения. Все Python-файлы больше не используются. Данные из SQLite нужно будет импортировать в Google Sheets вручную или написать скрипт миграции.