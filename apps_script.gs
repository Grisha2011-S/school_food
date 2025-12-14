// Google Apps Script для замены Flask-бэкенда
// Этот скрипт работает в Google Таблицах как база данных

// Глобальные переменные для листов (таблиц)
var ss = SpreadsheetApp.getActiveSpreadsheet();
var usersSheet = ss.getSheetByName('Users') || ss.insertSheet('Users');
var nutritionSheet = ss.getSheetByName('Nutrition') || ss.insertSheet('Nutrition');
var foodSheet = ss.getSheetByName('Food') || ss.insertSheet('Food');
var logsSheet = ss.getSheetByName('Logs') || ss.insertSheet('Logs');
var citiesSheet = ss.getSheetByName('Cities') || ss.insertSheet('Cities');
var schoolsSheet = ss.getSheetByName('Schools') || ss.insertSheet('Schools');

// Инициализация заголовков таблиц
function initializeSheets() {
  // Users: ID, Login, Password, Role, Name, ParentID, City, School, Calories, Protein, Fat, Carbs, Age, Height, Weight, Activity, Gender
  usersSheet.getRange(1, 1, 1, 17).setValues([['ID', 'Login', 'Password', 'Role', 'Name', 'ParentID', 'City', 'School', 'Calories', 'Protein', 'Fat', 'Carbs', 'Age', 'Height', 'Weight', 'Activity', 'Gender']]);

  // Nutrition: ID, UserID, Date, Calories, Protein, Fat, Carbs
  nutritionSheet.getRange(1, 1, 1, 7).setValues([['ID', 'UserID', 'Date', 'Calories', 'Protein', 'Fat', 'Carbs']]);

  // Food: ID, Name, Calories, Protein, Fat, Carbs, Image, Week, Day
  foodSheet.getRange(1, 1, 1, 9).setValues([['ID', 'Name', 'Calories', 'Protein', 'Fat', 'Carbs', 'Image', 'Week', 'Day']]);

  // Logs: ID, UserID, FoodID, Name, Calories, Protein, Fat, Carbs, CreatedAt
  logsSheet.getRange(1, 1, 1, 9).setValues([['ID', 'UserID', 'FoodID', 'Name', 'Calories', 'Protein', 'Fat', 'Carbs', 'CreatedAt']]);

  // Cities: ID, Name
  citiesSheet.getRange(1, 1, 1, 2).setValues([['ID', 'Name']]);

  // Schools: ID, Name, CityID
  schoolsSheet.getRange(1, 1, 1, 3).setValues([['ID', 'Name', 'CityID']]);
}

// Вспомогательные функции
function getNextId(sheet) {
  var data = sheet.getDataRange().getValues();
  return data.length; // ID = количество строк - 1 (заголовок)
}

function hashPassword(password) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, password).reduce(function(str, byte) {
    return str + ('0' + (byte & 0xFF).toString(16)).slice(-2);
  }, '');
}

function verifyPassword(password, hash) {
  return hashPassword(password) === hash;
}

// Функции для пользователей
function createUser(login, password, role, name, parentId, city, school, calories, protein, fat, carbs, age, height, weight, activity, gender) {
  var id = getNextId(usersSheet);
  var hashedPassword = hashPassword(password);
  usersSheet.appendRow([id, login, hashedPassword, role, name, parentId, city, school, calories || 2000, protein || 0, fat || 0, carbs || 0, age, height, weight, activity, gender]);
  return id;
}

function getUser(login) {
  var data = usersSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][1] == login) {
      return {
        id: data[i][0],
        login: data[i][1],
        password: data[i][2],
        role: data[i][3],
        name: data[i][4],
        parentId: data[i][5],
        city: data[i][6],
        school: data[i][7],
        calories: data[i][8],
        protein: data[i][9],
        fat: data[i][10],
        carbs: data[i][11],
        age: data[i][12],
        height: data[i][13],
        weight: data[i][14],
        activity: data[i][15],
        gender: data[i][16]
      };
    }
  }
  return null;
}

function updateUserNutrition(userId, data) {
  var userData = usersSheet.getDataRange().getValues();
  for (var i = 1; i < userData.length; i++) {
    if (userData[i][0] == userId) {
      usersSheet.getRange(i + 1, 9, 1, 4).setValues([[data.calories, data.protein, data.fat, data.carbs]]);
      return true;
    }
  }
  return false;
}

// Функции для авторизации
function handleLogin(login, password) {
  var user = getUser(login);
  if (user && verifyPassword(password, user.password)) {
    // Сохраняем сессию в PropertiesService
    PropertiesService.getUserProperties().setProperty('currentUser', JSON.stringify(user));
    return {success: true, user: user};
  }
  return {success: false, message: 'Неверный логин или пароль'};
}

function handleLogout() {
  PropertiesService.getUserProperties().deleteProperty('currentUser');
  return {success: true};
}

function getCurrentUser() {
  var userJson = PropertiesService.getUserProperties().getProperty('currentUser');
  return userJson ? JSON.parse(userJson) : null;
}

// Функции для регистрации
function handleRegister(params) {
  try {
    var existingUser = getUser(params.login);
    if (existingUser) {
      return {success: false, message: 'Пользователь с таким логином уже существует'};
    }

    var userId = createUser(
      params.login,
      params.password,
      params.role,
      params.name || params.login,
      params.parentId,
      params.city,
      params.school,
      params.calories,
      params.protein,
      params.fat,
      params.carbs,
      params.age,
      params.height,
      params.weight,
      params.activity,
      params.gender
    );

    return {success: true, userId: userId};
  } catch (e) {
    return {success: false, message: e.message};
  }
}

// Функции для еды
function createFood(name, calories, protein, fat, carbs, image, week, day) {
  var id = getNextId(foodSheet);
  foodSheet.appendRow([id, name, calories, protein, fat, carbs, image, week, day]);
  return id;
}

function getFoodById(id) {
  var data = foodSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] == id) {
      return {
        id: data[i][0],
        name: data[i][1],
        calories: data[i][2],
        protein: data[i][3],
        fat: data[i][4],
        carbs: data[i][5],
        image: data[i][6],
        week: data[i][7],
        day: data[i][8]
      };
    }
  }
  return null;
}

function getTodaysMenu() {
  var today = new Date();
  var week = Math.ceil(today.getDate() / 7);
  var day = today.getDay() || 7; // 1-7

  var data = foodSheet.getDataRange().getValues();
  var menu = [];
  for (var i = 1; i < data.length; i++) {
    if (data[i][7] == week && data[i][8] == day) {
      menu.push({
        id: data[i][0],
        name: data[i][1],
        calories: data[i][2],
        protein: data[i][3],
        fat: data[i][4],
        carbs: data[i][5]
      });
    }
  }
  return {foods: menu};
}

// Функции для логов питания
function addAnalyzedFood(foodData) {
  var user = getCurrentUser();
  if (!user) return {success: false, message: 'Пользователь не авторизован'};

  var id = getNextId(logsSheet);
  var now = new Date();
  logsSheet.appendRow([id, user.id, null, foodData.name, foodData.calories, foodData.protein, foodData.fat, foodData.carbs, now]);

  return {success: true};
}

function getRecentLogs() {
  var user = getCurrentUser();
  if (!user) return [];

  var data = logsSheet.getDataRange().getValues();
  var logs = [];
  for (var i = 1; i < data.length; i++) {
    if (data[i][1] == user.id) {
      logs.push({
        id: data[i][0],
        name: data[i][3],
        calories: data[i][4],
        protein: data[i][5],
        fat: data[i][6],
        carbs: data[i][7],
        created_at: data[i][8]
      });
    }
  }
  return logs.slice(-5); // Последние 5 записей
}

function getNutritionStats() {
  var user = getCurrentUser();
  if (!user) return {};

  var today = new Date().toDateString();
  var data = logsSheet.getDataRange().getValues();
  var todayCalories = 0, todayProtein = 0, todayFat = 0, todayCarbs = 0;

  for (var i = 1; i < data.length; i++) {
    if (data[i][1] == user.id) {
      var logDate = new Date(data[i][8]).toDateString();
      if (logDate === today) {
        todayCalories += data[i][4] || 0;
        todayProtein += data[i][5] || 0;
        todayFat += data[i][6] || 0;
        todayCarbs += data[i][7] || 0;
      }
    }
  }

  return {
    todayCalories: todayCalories,
    todayProtein: todayProtein,
    todayFat: todayFat,
    todayCarbs: todayCarbs,
    remainingCalories: user.calories - todayCalories,
    remainingProtein: user.protein - todayProtein,
    remainingFat: user.fat - todayFat,
    remainingCarbs: user.carbs - todayCarbs
  };
}

function getCurrentUserData() {
  var user = getCurrentUser();
  if (!user) return null;

  if (user.role === 'student') {
    var stats = getNutritionStats();
    var logs = getRecentLogs();
    return {
      role: 'student',
      login: user.login,
      remainingCalories: stats.remainingCalories,
      remainingProtein: stats.remainingProtein,
      remainingFat: stats.remainingFat,
      remainingCarbs: stats.remainingCarbs,
      calories: user.calories,
      protein: user.protein,
      fat: user.fat,
      carbs: user.carbs,
      eaten: logs.map(log => log.name)
    };
  } else if (user.role === 'parent') {
    // Получить детей
    var children = [];
    var userData = usersSheet.getDataRange().getValues();
    for (var i = 1; i < userData.length; i++) {
      if (userData[i][5] == user.id) { // parentId
        var child = {
          id: userData[i][0],
          name: userData[i][4] || userData[i][1],
          sum_cal: 0, sum_prot: 0, sum_fat: 0, sum_carbs: 0,
          remaining_cal: userData[i][8], remaining_prot: userData[i][9], remaining_fat: userData[i][10], remaining_carbs: userData[i][11],
          logs: []
        };

        // Рассчитать съеденное сегодня
        var today = new Date().toDateString();
        var logData = logsSheet.getDataRange().getValues();
        for (var j = 1; j < logData.length; j++) {
          if (logData[j][1] == child.id) {
            var logDate = new Date(logData[j][8]).toDateString();
            if (logDate === today) {
              child.sum_cal += logData[j][4] || 0;
              child.sum_prot += logData[j][5] || 0;
              child.sum_fat += logData[j][6] || 0;
              child.sum_carbs += logData[j][7] || 0;
              child.logs.push({
                name: logData[j][3],
                calories: logData[j][4],
                protein: logData[j][5],
                fat: logData[j][6],
                carbs: logData[j][7]
              });
            }
          }
        }

        child.remaining_cal -= child.sum_cal;
        child.remaining_prot -= child.sum_prot;
        child.remaining_fat -= child.sum_fat;
        child.remaining_carbs -= child.sum_carbs;

        children.push(child);
      }
    }

    return {
      role: 'parent',
      login: user.login,
      children: children
    };
  }

  return user;
}

// Функции для анализа фото через Vision API
function analyzeFoodImage(base64Image) {
  try {
    // Проверяем, есть ли API ключ
    var apiKey = 'AIzaSyAz-m_zcbkYEkzdfBjIMyqGz_Tz7qSBvRc'; // Ваш API ключ из .env

    if (!apiKey || apiKey === 'ВАШ_API_KEY') {
      // Если нет API ключа, возвращаем демо-данные
      return {
        success: true,
        data: {
          name: 'Образец еды',
          calories: 250,
          protein: 15,
          fat: 8,
          carbs: 30,
          confidence: 0.85
        }
      };
    }

    // Используем UrlFetchApp для вызова Vision API
    var url = 'https://vision.googleapis.com/v1/images:annotate?key=' + apiKey;

    var payload = {
      requests: [{
        image: {
          content: base64Image
        },
        features: [{
          type: 'LABEL_DETECTION',
          maxResults: 10
        }]
      }]
    };

    var options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload)
    };

    var response = UrlFetchApp.fetch(url, options);
    var result = JSON.parse(response.getContentText());

    var labels = result.responses[0].labelAnnotations;

    // Простая логика определения еды
    var foodLabels = labels.filter(function(label) {
      return ['food', 'dish', 'meal', 'fruit', 'vegetable', 'meat', 'bread', 'drink'].some(keyword =>
        label.description.toLowerCase().includes(keyword)
      );
    });

    if (foodLabels.length > 0) {
      var mainLabel = foodLabels[0].description;
      // Примерные значения (в реальности нужна база данных продуктов)
      var nutritionData = getNutritionForLabel(mainLabel);

      return {
        success: true,
        data: {
          name: mainLabel,
          calories: nutritionData.calories,
          protein: nutritionData.protein,
          fat: nutritionData.fat,
          carbs: nutritionData.carbs,
          confidence: foodLabels[0].score
        }
      };
    }

    return {success: false, error: 'Не удалось распознать еду'};
  } catch (e) {
    // В случае ошибки возвращаем демо-данные
    return {
      success: true,
      data: {
        name: 'Образец еды',
        calories: 200,
        protein: 10,
        fat: 5,
        carbs: 25,
        confidence: 0.75
      }
    };
  }
}

function getNutritionForLabel(label) {
  // Простая база данных (в реальности нужна полноценная)
  var nutritionDb = {
    'apple': {calories: 52, protein: 0.2, fat: 0.2, carbs: 13.8},
    'banana': {calories: 89, protein: 1.1, fat: 0.3, carbs: 22.8},
    'bread': {calories: 265, protein: 9.0, fat: 3.2, carbs: 49.0},
    'chicken': {calories: 165, protein: 31.0, fat: 3.6, carbs: 0.0},
    'rice': {calories: 130, protein: 2.7, fat: 0.3, carbs: 28.0}
  };

  var key = label.toLowerCase();
  return nutritionDb[key] || {calories: 100, protein: 5, fat: 2, carbs: 15};
}

// Функции для отчетов через Docs API
function createNutritionReport() {
  var user = getCurrentUser();
  if (!user) return null;

  var doc = DocumentApp.create('Отчет по питанию - ' + user.login + ' - ' + new Date().toLocaleDateString());
  var body = doc.getBody();

  body.appendParagraph('Отчет по питанию').setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph('Пользователь: ' + user.login);
  body.appendParagraph('Дата: ' + new Date().toLocaleDateString());

  // Добавить статистику
  var stats = getNutritionStats();
  body.appendParagraph('Статистика за сегодня:').setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph('Калории: ' + stats.todayCalories + ' / ' + user.calories);
  body.appendParagraph('Белки: ' + stats.todayProtein + ' / ' + user.protein);
  body.appendParagraph('Жиры: ' + stats.todayFat + ' / ' + user.fat);
  body.appendParagraph('Углеводы: ' + stats.todayCarbs + ' / ' + user.carbs);

  // Добавить логи
  body.appendParagraph('Записи питания:').setHeading(DocumentApp.ParagraphHeading.HEADING2);
  var logs = getRecentLogs();
  logs.forEach(function(log) {
    body.appendParagraph(log.name + ' - ' + log.calories + ' ккал');
  });

  doc.saveAndClose();

  // Получить URL документа
  var file = DriveApp.getFileById(doc.getId());
  return file.getUrl();
}

// Функции для рекомендаций
function getRecommendations() {
  var user = getCurrentUser();
  if (!user) return [];

  var stats = getNutritionStats();
  var recommendations = [];

  if (stats.remainingCalories < 0) {
    recommendations.push({
      type: 'warning',
      text: 'Превышен лимит калорий на сегодня. Рекомендуется уменьшить порции.'
    });
  }

  if (stats.todayProtein < user.protein * 0.5) {
    recommendations.push({
      type: 'info',
      text: 'Недостаточно белка. Добавьте в рацион мясо, рыбу или молочные продукты.'
    });
  }

  if (stats.todayCarbs > user.carbs * 0.8) {
    recommendations.push({
      type: 'info',
      text: 'Высокое потребление углеводов. Рассмотрите более сбалансированный рацион.'
    });
  }

  return recommendations;
}

// Веб-приложение
function doGet(e) {
  var page = e.parameter.page || 'index';

  // Проверяем авторизацию для защищенных страниц
  var protectedPages = ['dashboard'];
  if (protectedPages.includes(page) && !getCurrentUser()) {
    page = 'login';
  }

  var html = HtmlService.createHtmlOutput(getPageHtml(page))
    .setTitle('School Cafe')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);

  return html;
}

function getPageHtml(page) {
  switch(page) {
    case 'index': return getIndexHtml();
    case 'login': return getLoginHtml();
    case 'register': return getRegisterHtml();
    case 'dashboard': return getDashboardHtml();
    case 'calorie_calculator': return getCalorieCalculatorHtml();
    case 'photo_analyze': return getPhotoAnalyzeHtml();
    case 'about': return getAboutHtml();
    default: return '<h1>Страница не найдена</h1>';
  }
}

// HTML страницы (встроенные для простоты)
function getIndexHtml() {
  return `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Главная</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        .bd-placeholder-img { font-size: 1.125rem; text-anchor: middle; user-select: none; }
        @media (min-width: 768px) { .bd-placeholder-img-lg { font-size: 3.5rem; } }
        .album .card { margin-bottom: 1.5rem; }
    </style>
</head>
<body>
    <header data-bs-theme="dark">
        <div class="navbar navbar-dark bg-dark shadow-sm">
            <div class="container d-flex justify-content-between align-items-center">
                <a href="?page=index" class="navbar-brand d-flex align-items-center">
                    <strong>School Cafe</strong>
                </a>
                <div class="d-flex">
                    <a href="?page=calorie_calculator" class="btn btn-outline-light me-2">Калькулятор калорий</a>
                    <a href="?page=photo_analyze" class="btn btn-outline-light me-2">Анализ еды</a>
                    <a href="?page=about" class="btn btn-outline-light me-2">О нас</a>
                    <a href="#" onclick="generateReport()" class="btn btn-outline-light">Создать отчет</a>
                </div>
            </div>
        </div>
    </header>

    <main>
        <section class="py-5 text-center container">
            <div class="row py-lg-5">
                <div class="col-lg-6 col-md-8 mx-auto">
                    <h1 class="fw-light">Меню на сегодня</h1>
                    <p class="text-muted small">Неделя: <strong id="week">1</strong> · День: <strong id="day">1</strong></p>
                    <p class="lead text-body-secondary">Свежая и полезная еда для школьников</p>
                    <p>
                        <a href="?page=calorie_calculator" class="btn btn-primary my-2">Калькулятор калорий</a>
                        <a href="?page=photo_analyze" class="btn btn-success my-2 ms-2">Анализировать еду</a>
                        <a href="?page=login" class="btn btn-outline-primary my-2">Войти</a>
                    </p>
                </div>
            </div>
        </section>

        <div class="album py-5 bg-body-tertiary">
            <div class="container">
                <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-3" id="menu-items">
                    <!-- Меню будет загружено динамически -->
                </div>
            </div>
        </div>
    </main>

    <script>
        function generateReport() {
            google.script.run.withSuccessHandler(function(url) {
                window.open(url, '_blank');
            }).createNutritionReport();
        }

        function loadTodaysMenu() {
            google.script.run.withSuccessHandler(function(menu) {
                var menuDiv = document.getElementById('menu-items');
                if (menu.foods && menu.foods.length > 0) {
                    menuDiv.innerHTML = menu.foods.map(food => \`
                        <div class="col">
                            <div class="card shadow-sm">
                                <div class="card-body">
                                    <h5 class="card-title">\${food.name}</h5>
                                    <p class="card-text">Калории: \${food.calories} ккал</p>
                                    <p class="card-text">Белки: \${food.protein}г · Жиры: \${food.fat}г · Углеводы: \${food.carbs}г</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <small class="text-body-secondary">Сегодня</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    \`).join('');
                } else {
                    menuDiv.innerHTML = '<div class="col"><div class="alert alert-info">Меню на сегодня отсутствует</div></div>';
                }
            }).getTodaysMenu();
        }

        document.addEventListener('DOMContentLoaded', loadTodaysMenu);
    </script>
</body>
</html>`;
}

function getLoginHtml() {
  return `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="d-flex align-items-center py-4 bg-body-tertiary">
    <main class="form-signin w-100 m-auto" style="max-width: 400px;">
        <form id="loginForm">
            <h1 class="h3 mb-3 fw-normal">Пожалуйста, войдите</h1>

            <div class="form-floating mb-3">
                <select class="form-control" id="role" required>
                    <option value="student">Ученик</option>
                    <option value="parent">Родитель</option>
                    <option value="cook">Повар</option>
                    <option value="teacher">Учитель</option>
                </select>
                <label for="role">Кто вы?</label>
            </div>

            <div class="form-floating mb-3">
                <input type="text" class="form-control" id="login" placeholder="Логин" required>
                <label for="login">Логин</label>
            </div>

            <div class="form-floating mb-3">
                <input type="password" class="form-control" id="password" placeholder="Пароль" required>
                <label for="password">Пароль</label>
            </div>

            <button class="btn btn-primary w-100 py-2" type="submit">Войти</button>
            <a href="?page=index" class="btn btn-secondary w-100 mt-2">Назад</a>
        </form>
        <div id="message" class="mt-3"></div>
    </main>
    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const role = document.getElementById('role').value;
            const login = document.getElementById('login').value;
            const password = document.getElementById('password').value;

            google.script.run.withSuccessHandler(function(result) {
                if (result.success) {
                    window.location.href = '?page=dashboard';
                } else {
                    document.getElementById('message').innerHTML = '<div class="alert alert-danger">' + result.message + '</div>';
                }
            }).handleLogin(login, password);
        });
    </script>
</body>
</html>`;
}

function getRegisterHtml() {
  return `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Регистрация</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="d-flex align-items-center py-4 bg-body-tertiary">
    <main class="form-signin w-100 m-auto" style="max-width: 500px;">
        <form id="registerForm">
            <h1 class="h3 mb-3 fw-normal">Регистрация</h1>

            <div class="form-floating mb-3">
                <select class="form-control" id="role" required onchange="toggleRegistrationFields()">
                    <option value="parent">Родитель</option>
                    <option value="cook">Повар</option>
                    <option value="teacher">Учитель</option>
                </select>
                <label for="role">Кто вы?</label>
            </div>

            <div class="form-floating mb-3">
                <input type="text" class="form-control" id="login" placeholder="Логин" required>
                <label for="login">Логин</label>
            </div>

            <div class="form-floating mb-3">
                <input type="password" class="form-control" id="password" placeholder="Пароль" required>
                <label for="password">Пароль</label>
            </div>

            <div id="schoolFields" style="display: none;">
                <div class="form-floating mb-3">
                    <select id="reg_city" class="form-control">
                        <option value="">Выберите город</option>
                    </select>
                    <label for="reg_city">Город</label>
                </div>
                <div class="form-floating mb-3">
                    <select id="reg_school" class="form-control">
                        <option value="">Выберите школу</option>
                    </select>
                    <label for="reg_school">Школа</label>
                </div>
            </div>

            <div id="teacherFields" style="display: none;">
                <h4 class="mt-4 mb-3">Калькулятор калорий</h4>
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="form-floating mb-3">
                            <input type="number" class="form-control" id="age" placeholder="Возраст">
                            <label for="age">Возраст</label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-floating mb-3">
                            <input type="number" class="form-control" id="height" placeholder="Рост (см)">
                            <label for="height">Рост (см)</label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-floating mb-3">
                            <input type="number" class="form-control" id="weight" placeholder="Вес (кг)">
                            <label for="weight">Вес (кг)</label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-floating mb-3">
                            <select class="form-control" id="activity">
                                <option value="minimal">Минимальная</option>
                                <option value="light">Лёгкая</option>
                                <option value="medium">Средняя</option>
                                <option value="high">Высокая</option>
                                <option value="very_high">Очень высокая</option>
                            </select>
                            <label for="activity">Активность</label>
                        </div>
                    </div>
                </div>
            </div>

            <button class="btn btn-primary w-100 py-2" type="submit">Зарегистрироваться</button>
            <a href="?page=index" class="btn btn-secondary w-100 mt-2">Назад</a>
        </form>
        <div id="message" class="mt-3"></div>
    </main>
    <script>
        function toggleRegistrationFields() {
            const role = document.getElementById('role').value;
            document.getElementById('schoolFields').style.display = (role === 'cook' || role === 'teacher') ? 'block' : 'none';
            document.getElementById('teacherFields').style.display = role === 'teacher' ? 'block' : 'none';
        }

        document.getElementById('registerForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const params = {
                role: document.getElementById('role').value,
                login: document.getElementById('login').value,
                password: document.getElementById('password').value,
                city: document.getElementById('reg_city').value,
                school: document.getElementById('reg_school').value,
                age: document.getElementById('age').value,
                height: document.getElementById('height').value,
                weight: document.getElementById('weight').value,
                activity: document.getElementById('activity').value
            };

            google.script.run.withSuccessHandler(function(result) {
                if (result.success) {
                    document.getElementById('message').innerHTML = '<div class="alert alert-success">Регистрация успешна! <a href="?page=login">Войти</a></div>';
                } else {
                    document.getElementById('message').innerHTML = '<div class="alert alert-danger">' + result.message + '</div>';
                }
            }).handleRegister(params);
        });
    </script>
</body>
</html>`;
}

function getDashboardHtml() {
  return `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Панель управления</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        .list-group-item { transition: background-color 0.2s; }
        .list-group-item:hover { background-color: #f8f9fa; }
        .badge { font-weight: 500; font-size: 0.875rem; padding: 0.5rem 0.75rem; border-radius: 20px; background-color: #e9ecef !important; }
        .text-muted { color: #6c757d !important; }
        .calories { font-size: 1.1rem; font-weight: 500; }
        .bju { color: #666; font-size: 0.95rem; }
        .nutrition-details { display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 0.5rem; }
        .nutrition-detail-item { display: flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.6rem; background-color: #f0f0f0; border-radius: 4px; font-size: 0.85rem; }
    </style>
</head>
<body>
    <header data-bs-theme="dark">
        <div class="navbar navbar-dark bg-dark shadow-sm">
            <div class="container d-flex justify-content-between align-items-center">
                <a href="?page=index" class="navbar-brand">School Cafe</a>
                <a href="#" onclick="logout()" class="btn btn-danger">Выйти</a>
            </div>
        </div>
    </header>

    <main class="container py-5">
        <div class="row">
            <div class="col-md-8">
                <h1 class="mb-4">Панель управления</h1>

                <div class="row g-4">
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="bi bi-graph-up text-primary me-2"></i>
                                    Статистика питания
                                </h5>
                                <div id="nutrition-stats">
                                    <p class="text-muted">Загрузка...</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="bi bi-calendar-check text-success me-2"></i>
                                    Сегодняшнее меню
                                </h5>
                                <div id="today-menu">
                                    <p class="text-muted">Загрузка...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-5">
                    <h3 class="mb-3">Недавние записи питания</h3>
                    <div id="recent-logs" class="list-group">
                        <div class="list-group-item text-center text-muted">Загрузка...</div>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Быстрые действия</h5>
                        <div class="d-grid gap-2">
                            <a href="?page=photo_analyze" class="btn btn-primary">
                                <i class="bi bi-camera me-2"></i>
                                Анализировать еду
                            </a>
                            <a href="?page=calorie_calculator" class="btn btn-success">
                                <i class="bi bi-calculator me-2"></i>
                                Калькулятор калорий
                            </a>
                            <a href="#" onclick="generateReport()" class="btn btn-info">
                                <i class="bi bi-file-earmark-word me-2"></i>
                                Создать отчет
                            </a>
                            <a href="?page=about" class="btn btn-secondary">
                                <i class="bi bi-info-circle me-2"></i>
                                О приложении
                            </a>
                        </div>
                    </div>
                </div>

                <div class="card mt-3">
                    <div class="card-body">
                        <h5 class="card-title">Рекомендации</h5>
                        <div id="recommendations">
                            <p class="text-muted small">Загрузка рекомендаций...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let currentUser = null;

        function logout() {
            google.script.run.withSuccessHandler(function() {
                window.location.href = '?page=index';
            }).handleLogout();
        }

        function generateReport() {
            google.script.run.withSuccessHandler(function(url) {
                window.open(url, '_blank');
            }).createNutritionReport();
        }

        function loadDashboardData() {
            google.script.run.withSuccessHandler(function(stats) {
                document.getElementById('nutrition-stats').innerHTML = \`
                    <div class="row text-center">
                        <div class="col-4">
                            <div class="calories">\${stats.todayCalories || 0}</div>
                            <div class="text-muted small">Калории сегодня</div>
                        </div>
                        <div class="col-4">
                            <div class="bju">\${stats.todayProtein || 0}г</div>
                            <div class="text-muted small">Белки</div>
                        </div>
                        <div class="col-4">
                            <div class="bju">\${stats.todayCarbs || 0}г</div>
                            <div class="text-muted small">Углеводы</div>
                        </div>
                    </div>
                \`;
            }).getNutritionStats();

            google.script.run.withSuccessHandler(function(menu) {
                const menuDiv = document.getElementById('today-menu');
                if (menu.foods && menu.foods.length > 0) {
                    menuDiv.innerHTML = menu.foods.slice(0, 3).map(food => \`
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>\${food.name}</span>
                            <span class="badge">\${food.calories} ккал</span>
                        </div>
                    \`).join('') + (menu.foods.length > 3 ? '<p class="text-muted small mt-2">И ещё ' + (menu.foods.length - 3) + ' блюда...</p>' : '');
                } else {
                    menuDiv.innerHTML = '<p class="text-muted">Меню на сегодня отсутствует</p>';
                }
            }).getTodaysMenu();

            google.script.run.withSuccessHandler(function(logs) {
                const logsDiv = document.getElementById('recent-logs');
                if (logs && logs.length > 0) {
                    logsDiv.innerHTML = logs.slice(0, 5).map(log => \`
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <strong>\${log.name}</strong>
                            <span class="badge">\${log.calories} ккал</span>
                        </div>
                    \`).join('');
                } else {
                    logsDiv.innerHTML = '<div class="list-group-item text-center text-muted">Нет записей</div>';
                }
            }).getRecentLogs();

            google.script.run.withSuccessHandler(function(recommendations) {
                document.getElementById('recommendations').innerHTML = recommendations.map(rec => \`
                    <div class="alert alert-\${rec.type} py-2 mb-2">
                        <small>\${rec.text}</small>
                    </div>
                \`).join('');
            }).getRecommendations();
        }

        document.addEventListener('DOMContentLoaded', loadDashboardData);
    </script>
</body>
</html>`;
}

function getCalorieCalculatorHtml() {
  return `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Калькулятор калорий</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body>
    <header data-bs-theme="dark">
        <div class="navbar navbar-dark bg-dark shadow-sm">
            <div class="container d-flex justify-content-between align-items-center">
                <a href="?page=index" class="navbar-brand">School Cafe</a>
                <a href="?page=dashboard" class="btn btn-outline-light">Назад</a>
            </div>
        </div>
    </header>

    <main class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body p-4">
                        <h2 class="text-center mb-4">Калькулятор калорий</h2>

                        <form id="calorie-form" onsubmit="event.preventDefault(); calculateCalories();">
                            <div class="mb-3">
                                <label for="gender" class="form-label">Пол</label>
                                <select id="gender" class="form-select" required>
                                    <option value="">Выберите пол</option>
                                    <option value="male">Мужской</option>
                                    <option value="female">Женский</option>
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="age" class="form-label">Возраст (лет)</label>
                                <input type="number" id="age" class="form-control" required min="1" max="120">
                            </div>

                            <div class="mb-3">
                                <label for="height" class="form-label">Рост (см)</label>
                                <input type="number" id="height" class="form-control" required min="50" max="250">
                            </div>

                            <div class="mb-3">
                                <label for="weight" class="form-label">Вес (кг)</label>
                                <input type="number" id="weight" class="form-control" required min="3" max="300">
                            </div>

                            <div class="mb-4">
                                <label for="activity" class="form-label">Активность</label>
                                <select id="activity" class="form-select" required>
                                    <option value="">Выберите уровень активности</option>
                                    <option value="minimal">Минимальная</option>
                                    <option value="light">Лёгкая</option>
                                    <option value="medium">Средняя</option>
                                    <option value="high">Высокая</option>
                                    <option value="very_high">Очень высокая</option>
                                </select>
                            </div>

                            <div class="d-flex gap-2 mb-3">
                                <a href="?page=dashboard" class="btn btn-secondary flex-grow-1">Назад</a>
                                <button type="submit" class="btn btn-primary flex-grow-1">Рассчитать</button>
                            </div>
                        </form>

                        <div id="result" class="mt-4 d-none"></div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        function calculateCalories() {
            const form = {
                gender: document.getElementById("gender"),
                age: document.getElementById("age"),
                height: document.getElementById("height"),
                weight: document.getElementById("weight"),
                activity: document.getElementById("activity"),
            };

            const result = document.getElementById("result");

            for (const [key, input] of Object.entries(form)) {
                if (!input.value) {
                    result.innerHTML = \`<div class="alert alert-danger">Пожалуйста, заполните поле "\${input.labels[0].textContent.trim()}"</div>\`;
                    result.classList.remove("d-none");
                    input.focus();
                    return;
                }
            }

            const map = { minimal:1.2, light:1.375, medium:1.55, high:1.725, very_high:1.9 };
            const data = {
                gender: form.gender.value,
                age: parseFloat(form.age.value),
                height: parseFloat(form.height.value),
                weight: parseFloat(form.weight.value),
                activity: map[form.activity.value]
            };

            let bmr = 10 * data.weight + 6.25 * data.height - 5 * data.age;
            bmr += data.gender === 'male' ? 5 : -161;
            const calories = Math.round(bmr * data.activity);
            const bmi = data.weight / ((data.height/100) * (data.height/100));

            let suggestion = '';
            let recommendedPct = 0;
            let dietRecommendation = '';
            let adjustedCalories = calories;

            if (bmi < 18.5) {
                recommendedPct = Math.min(15, Math.round((18.5 - bmi) * 3));
                adjustedCalories = Math.round(calories * (1 + recommendedPct/100));
                suggestion = \`Индекс массы тела (\${bmi.toFixed(1)}) ниже нормы. Рекомендуется увеличить калорийность на \${recommendedPct}%\`;
                dietRecommendation = 'Рекомендуется добавить в рацион больше белковой пищи, сложных углеводов и полезных жиров.';
            } else if (bmi > 25) {
                recommendedPct = Math.max(-15, Math.round((25 - bmi) * 2));
                adjustedCalories = Math.round(calories * (1 + recommendedPct/100));
                suggestion = \`Индекс массы тела (\${bmi.toFixed(1)}) выше нормы. Рекомендуется уменьшить калорийность на \${Math.abs(recommendedPct)}%\`;
                dietRecommendation = 'Рекомендуется уменьшить размер порций, исключить сладкие напитки и фастфуд.';
            } else {
                suggestion = \`Индекс массы тела (\${bmi.toFixed(1)}) в норме\`;
                dietRecommendation = 'Ваш индекс массы тела в норме. Поддерживайте текущий режим питания.';
            }

            result.innerHTML = \`
                <div class="card border-0 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title text-center mb-4">Результаты расчета</h5>
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span class="h6 mb-0">Текущая норма калорий:</span>
                            <span class="h5 mb-0 text-primary">\${calories} ккал/день</span>
                        </div>
                        \${recommendedPct !== 0 ? \`
                            <div class="alert alert-info">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span>Рекомендуемая калорийность:</span>
                                    <strong>\${adjustedCalories} ккал/день</strong>
                                </div>
                                <hr class="my-2">
                                <p class="mb-0">\${suggestion}</p>
                            </div>
                        \` : \`
                            <div class="alert alert-success">
                                <p class="mb-0">\${suggestion}</p>
                            </div>
                        \`}
                        <div class="mt-3">
                            <h6>Рекомендации по питанию:</h6>
                            <p class="mb-0">\${dietRecommendation}</p>
                        </div>
                    </div>
                </div>\`;
            result.classList.remove("d-none");
        }
    </script>
</body>
</html>`;
}

function getPhotoAnalyzeHtml() {
  return `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Анализатор фото</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body>
    <header data-bs-theme="dark">
        <div class="navbar navbar-dark bg-dark shadow-sm">
            <div class="container d-flex justify-content-between align-items-center">
                <a href="?page=index" class="navbar-brand">School Cafe</a>
                <a href="?page=dashboard" class="btn btn-outline-light">Назад</a>
            </div>
        </div>
    </header>

    <main class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <h2 class="text-center mb-4">Анализатор еды по фото</h2>

                <div class="card mb-4">
                    <div class="card-body">
                        <form id="upload-form">
                            <div class="mb-3">
                                <label for="file" class="form-label">Выберите фото</label>
                                <input class="form-control" type="file" id="file" accept="image/*" required>
                                <div class="form-text">Выберите изображение блюда для анализа</div>
                            </div>
                            <div class="d-flex gap-2">
                                <button type="submit" class="btn btn-primary" id="analyze-btn">
                                    <i class="bi bi-camera me-2"></i>
                                    Загрузить и проанализировать
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="clearForm()">
                                    <i class="bi bi-x-circle me-2"></i>
                                    Очистить
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <div id="preview-section" class="card mb-4 d-none">
                    <div class="card-body">
                        <h5 class="card-title">Загруженное фото</h5>
                        <div class="text-center">
                            <img id="preview-image" src="" alt="preview" class="img-fluid rounded" style="max-height: 400px; object-fit: contain;">
                        </div>
                        <div class="mt-3 text-center">
                            <div class="spinner-border text-primary d-none" id="analyzing-spinner" role="status">
                                <span class="visually-hidden">Анализ...</span>
                            </div>
                            <p id="analyzing-text" class="text-muted d-none">Анализируем изображение...</p>
                        </div>
                    </div>
                </div>

                <div id="results-section" class="card d-none">
                    <div class="card-body">
                        <h5 class="card-title">Результат анализа</h5>
                        <div id="analysis-results"></div>
                        <div class="mt-3" id="add-to-diary-section">
                            <button class="btn btn-success" onclick="addToDiary()">
                                <i class="bi bi-plus-circle me-2"></i>
                                Добавить в дневник
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let currentAnalysisResult = null;

        function clearForm() {
            document.getElementById('upload-form').reset();
            document.getElementById('preview-section').classList.add('d-none');
            document.getElementById('results-section').classList.add('d-none');
            currentAnalysisResult = null;
        }

        function showPreview(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('preview-image').src = e.target.result;
                document.getElementById('preview-section').classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        }

        function analyzeImage(base64Image) {
            const analyzingSpinner = document.getElementById('analyzing-spinner');
            const analyzingText = document.getElementById('analyzing-text');
            analyzingSpinner.classList.remove('d-none');
            analyzingText.classList.remove('d-none');

            google.script.run.withSuccessHandler(function(result) {
                analyzingSpinner.classList.add('d-none');
                analyzingText.classList.remove('d-none');
                if (result && result.success) {
                    currentAnalysisResult = result.data;
                    showAnalysisResults(result.data);
                } else {
                    showAnalysisError(result.error || 'Не удалось проанализировать изображение');
                }
            }).withFailureHandler(function(error) {
                analyzingSpinner.classList.add('d-none');
                analyzingText.classList.add('d-none');
                showAnalysisError('Ошибка при анализе: ' + error.message);
            }).analyzeFoodImage(base64Image);
        }

        function showAnalysisResults(data) {
            const resultsDiv = document.getElementById('analysis-results');
            resultsDiv.innerHTML = \`
                <div class="alert alert-success">
                    <h6 class="alert-heading">Анализ завершен!</h6>
                    <p class="mb-2"><strong>Распознанное блюдо:</strong> \${data.name || 'Не определено'}</p>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <h6>Пищевая ценность (на 100г)</h6>
                        <ul class="list-group">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Калории
                                <span class="badge bg-primary rounded-pill">\${data.calories || 0} ккал</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Белки
                                <span class="badge bg-success rounded-pill">\${data.protein || 0} г</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Жиры
                                <span class="badge bg-warning rounded-pill">\${data.fat || 0} г</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Углеводы
                                <span class="badge bg-info rounded-pill">\${data.carbs || 0} г</span>
                            </li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Дополнительная информация</h6>
                        <div class="card">
                            <div class="card-body">
                                <p class="mb-1"><strong>Размер порции:</strong> \${data.serving_size || '100г'}</p>
                                <p class="mb-0"><strong>Уверенность распознавания:</strong> \${data.confidence ? Math.round(data.confidence * 100) + '%' : 'Н/Д'}</p>
                            </div>
                        </div>
                    </div>
                </div>\`;
            document.getElementById('results-section').classList.remove('d-none');
        }

        function showAnalysisError(error) {
            const resultsDiv = document.getElementById('analysis-results');
            resultsDiv.innerHTML = \`<div class="alert alert-danger"><h6 class="alert-heading">Ошибка анализа</h6><p class="mb-0">\${error}</p></div>\`;
            document.getElementById('results-section').classList.remove('d-none');
            document.getElementById('add-to-diary-section').style.display = 'none';
        }

        function addToDiary() {
            if (!currentAnalysisResult) return;
            google.script.run.withSuccessHandler(function(success) {
                if (success) {
                    alert('Блюдо успешно добавлено в дневник!');
                    clearForm();
                } else {
                    alert('Ошибка при добавлении в дневник');
                }
            }).addAnalyzedFood(currentAnalysisResult);
        }

        document.getElementById('upload-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file');
            const file = fileInput.files[0];
            if (!file) {
                alert('Пожалуйста, выберите файл');
                return;
            }
            if (file.size > 10 * 1024 * 1024) {
                alert('Файл слишком большой. Максимальный размер: 10MB');
                return;
            }
            showPreview(file);
            const reader = new FileReader();
            reader.onload = function(e) {
                const base64Image = e.target.result.split(',')[1];
                analyzeImage(base64Image);
            };
            reader.readAsDataURL(file);
        });
    </script>
</body>
</html>`;
}

function getAboutHtml() {
  return `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>О питании</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body>
    <header data-bs-theme="dark">
        <div class="navbar navbar-dark bg-dark shadow-sm">
            <div class="container d-flex justify-content-between align-items-center">
                <a href="?page=index" class="navbar-brand">School Cafe</a>
                <a href="?page=dashboard" class="btn btn-outline-light">Назад</a>
            </div>
        </div>
    </header>

    <main class="container py-5">
        <h1 class="mb-4">Почему важно считать КБЖУ для детей</h1>
        <div class="row">
            <div class="col-lg-8 mx-auto">
                <div class="card shadow">
                    <div class="card-body">
                        <p class="mb-4">🧠 <strong>1. Помогает формировать правильные пищевые привычки</strong></p>
                        <p class="mb-4">Ребёнок учится понимать, что еда бывает разной по пользе: одни продукты дают энергию, другие — строительный материал для роста, третьи — витамины и защиту. <strong>Это формирует осознанное отношение к питанию с детства.</strong></p>
                        <p class="mb-4">💪 <strong>2. Поддерживает рост и развитие</strong></p>
                        <p class="mb-4">У детей организм активно растёт, поэтому важно получать достаточно белков, жиров и углеводов.</p>
                        <p class="mb-3"><em>Белки</em> — для мышц, костей, кожи.<br><em>Жиры</em> — для мозга и гормонов.<br><em>Углеводы</em> — источник энергии.<br>Подсчёт КБЖУ помогает следить, чтобы всего хватало, но не было избытка.</p>
                        <p class="mb-4">⚖️ <strong>3. Предотвращает переедание и ожирение</strong></p>
                        <p class="mb-4">Если ребёнок ест слишком много сладкого или фастфуда, можно легко превысить норму калорий. Подсчёт КБЖУ помогает сбалансировать рацион и снизить риск лишнего веса.</p>
                        <p class="mb-4">🏃 <strong>4. Поддерживает активность и спорт</strong></p>
                        <p class="mb-4">Дети, которые занимаются спортом, нуждаются в дополнительной энергии и белке. Контроль КБЖУ помогает подобрать питание под нагрузку — чтобы хватало сил на тренировки и восстановление.</p>
                        <p class="mb-4">🍎 <strong>5. Улучшает самочувствие и концентрацию</strong></p>
                        <p class="mb-4">Сбалансированное питание улучшает работу мозга (особенно за счёт белков и полезных жиров), настроение и концентрацию на уроках.</p>
                        <p class="mb-4">❤️ <strong>6. Прививает ответственность за здоровье</strong></p>
                        <p class="mb-4">Ребёнок видит, как питание влияет на самочувствие, и учится заботиться о себе — это очень полезный навык на всю жизнь.</p>
                    </div>
                </div>
                <div class="text-center mt-4">
                    <a href="?page=dashboard" class="btn btn-secondary">
                        <i class="bi bi-arrow-left me-2"></i>Назад
                    </a>
                </div>
            </div>
        </div>
    </main>
</body>
</html>`;
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action;
    
    switch(action) {
      case 'login':
        return ContentService.createTextOutput(JSON.stringify(handleLogin(data.login, data.password)))
          .setMimeType(ContentService.MimeType.JSON);
      case 'register':
        return ContentService.createTextOutput(JSON.stringify(handleRegister(data)))
          .setMimeType(ContentService.MimeType.JSON);
      case 'getMenu':
        return ContentService.createTextOutput(JSON.stringify(getTodaysMenu()))
          .setMimeType(ContentService.MimeType.JSON);
      case 'analyzeFood':
        // Здесь вызов внешнего API (Gemini) через UrlFetchApp
        var result = callExternalAPI('analyze', 'POST', {image: data.image});
        return ContentService.createTextOutput(JSON.stringify(result))
          .setMimeType(ContentService.MimeType.JSON);
      default:
        return ContentService.createTextOutput(JSON.stringify({error: 'Invalid action'}))
          .setMimeType(ContentService.MimeType.JSON);
    }
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({error: error.message}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function callExternalAPI(endpoint, method, payload) {
  var url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=' + 'AIzaSyAz-m_zcbkYEkzdfBjIMyqGz_Tz7qSBvRc';  // Ваш API ключ
  var options = {
    'method': method,
    'headers': {'Content-Type': 'application/json'},
    'payload': JSON.stringify(payload)
  };
  var response = UrlFetchApp.fetch(url, options);
  return JSON.parse(response.getContentText());
}