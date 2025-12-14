# School Cafe Apps Script Deployment

## Быстрое развертывание

### Автоматический способ (рекомендуется)

1. **Установите clasp** (если не установлен):
   ```bash
   npm install -g @google/clasp
   ```

2. **Авторизуйтесь в Google**:
   ```bash
   clasp login
   ```
   Откройте ссылку в браузере и разрешите доступ.

3. **Включите Apps Script API**:
   Перейдите на https://script.google.com/home/usersettings и включите Apps Script API.

4. **Запустите скрипт развертывания**:
   ```bash
   deploy_apps_script.bat
   ```

### Ручной способ

1. Перейдите на [script.google.com](https://script.google.com)
2. Создайте новый проект
3. Скопируйте код из `apps_script.gs`
4. Создайте Google Таблицу для базы данных
5. Обновите ID таблицы в коде

## Настройка после развертывания

### 1. Включите API в Apps Script
- Откройте проект Apps Script
- Перейдите: Services → Add service
- Добавьте:
  - Google Vision API
  - Google Docs API

### 2. Создайте Google Таблицу
- Создайте новую таблицу в Google Sheets
- Скопируйте ID из URL (между `/d/` и `/edit`)
- Обновите код в Apps Script:
  ```javascript
  var ss = SpreadsheetApp.openById('ВАШ_ID_ТАБЛИЦЫ');
  ```

### 3. Опубликуйте веб-приложение
- В Apps Script: Deploy → New deployment
- Тип: Web app
- Execute as: Me
- Who has access: Anyone
- Deploy
- **СКОПИРУЙТЕ URL**

### 4. Тестирование
- Откройте URL веб-приложения в браузере
- Попробуйте регистрацию и анализ фото

## Структура проекта

- `apps_script.gs` - основной код Apps Script
- `deploy_apps_script.bat` - скрипт автоматического развертывания
- `.clasp.json` - конфигурация clasp
- `.claspignore` - файлы, исключаемые из загрузки

## Команды clasp

```bash
# Загрузить код в Apps Script
clasp push

# Скачать код из Apps Script
clasp pull

# Открыть редактор Apps Script
clasp open

# Просмотреть логи
clasp logs

# Создать новую версию
clasp deploy
```