// Google Apps Script для замены Flask-бэкенда
// Этот скрипт работает в Google Таблицах как база данных

// Глобальные переменные для листов (таблиц)
var ss = SpreadsheetApp.getActiveSpreadsheet();
var parentsSheet = ss.getSheetByName('Parents') || ss.insertSheet('Parents');
var studentsSheet = ss.getSheetByName('Students') || ss.insertSheet('Students');
var cooksSheet = ss.getSheetByName('Cooks') || ss.insertSheet('Cooks');
var eatSheet = ss.getSheetByName('Eat') || ss.insertSheet('Eat');
var eatLogSheet = ss.getSheetByName('EatLog') || ss.insertSheet('EatLog');
var citiesSheet = ss.getSheetByName('Cities') || ss.insertSheet('Cities');
var schoolsSheet = ss.getSheetByName('Schools') || ss.insertSheet('Schools');
var gradesSheet = ss.getSheetByName('Grades') || ss.insertSheet('Grades');
var adminsSheet = ss.getSheetByName('Admins') || ss.insertSheet('Admins');
var packsSheet = ss.getSheetByName('Packs') || ss.insertSheet('Packs');
var packItemsSheet = ss.getSheetByName('PackItems') || ss.insertSheet('PackItems');

// Инициализация заголовков таблиц
function initializeSheets() {
  // Parents
  parentsSheet.getRange(1, 1, 1, 5).setValues([['ID', 'Babe', 'Login', 'Password', 'School']]);

  // Students
  studentsSheet.getRange(1, 1, 1, 18).setValues([['ID', 'Login', 'Password', 'Name', 'Gender', 'Calories', 'Protein', 'Fat', 'Carbs', 'Age', 'Height', 'Weight', 'Activity', 'ParentID', 'Role', 'City', 'School', 'Grade']]);

  // Cooks
  cooksSheet.getRange(1, 1, 1, 5).setValues([['ID', 'Login', 'Password', 'City', 'School']]);

  // Eat
  eatSheet.getRange(1, 1, 1, 10).setValues([['ID', 'Name', 'Calories', 'Protein', 'Fat', 'Carbs', 'Type', 'Image', 'Week', 'Day']]);

  // EatLog
  eatLogSheet.getRange(1, 1, 1, 9).setValues([['ID', 'StudentID', 'FoodID', 'Name', 'Calories', 'Protein', 'Fat', 'Carbs', 'CreatedAt']]);

  // Cities
  citiesSheet.getRange(1, 1, 1, 2).setValues([['ID', 'Name']]);

  // Schools
  schoolsSheet.getRange(1, 1, 1, 3).setValues([['ID', 'Name', 'CityID']]);

  // Grades
  gradesSheet.getRange(1, 1, 1, 3).setValues([['ID', 'Name', 'SchoolID']]);

  // Admins
  adminsSheet.getRange(1, 1, 1, 6).setValues([['ID', 'Login', 'Password', 'IsMaster', 'CreatedAt', 'CreatedBy']]);

  // Packs
  packsSheet.getRange(1, 1, 1, 4).setValues([['ID', 'Week', 'Day', 'CreatedBy']]);

  // PackItems
  packItemsSheet.getRange(1, 1, 1, 6).setValues([['ID', 'PackID', 'FoodID', 'Ord', 'IsActive']]);
}

// Вспомогательные функции
function getNextId(sheet) {
  var data = sheet.getDataRange().getValues();
  return data.length; // ID = количество строк - 1 (заголовок)
}

function hashPassword(password) {
  // Простой хэш для примера (в реальности используйте bcrypt или подобное)
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, password).reduce(function(str, byte) {
    return str + ('0' + (byte & 0xFF).toString(16)).slice(-2);
  }, '');
}

// Функции для работы с пользователями
function createParent(login, password, school, babe) {
  var id = getNextId(parentsSheet);
  var hashedPassword = hashPassword(password);
  parentsSheet.appendRow([id, babe, login, hashedPassword, school]);
  return id;
}

function getParent(login) {
  var data = parentsSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][2] == login) { // login в столбце 3
      return {
        id: data[i][0],
        babe: data[i][1],
        login: data[i][2],
        password: data[i][3],
        school: data[i][4]
      };
    }
  }
  return null;
}

function createStudent(login, password, parentId, calories, protein, fat, carbs, role, city, school, grade, name, age, height, weight, activity, gender) {
  var id = getNextId(studentsSheet);
  var hashedPassword = hashPassword(password);
  studentsSheet.appendRow([id, login, hashedPassword, name, gender, calories, protein, fat, carbs, age, height, weight, activity, parentId, role, city, school, grade]);
  return id;
}

function getStudent(login) {
  var data = studentsSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][1] == login) { // login в столбце 2
      return {
        id: data[i][0],
        login: data[i][1],
        password: data[i][2],
        name: data[i][3],
        gender: data[i][4],
        calories: data[i][5],
        protein: data[i][6],
        fat: data[i][7],
        carbs: data[i][8],
        age: data[i][9],
        height: data[i][10],
        weight: data[i][11],
        activity: data[i][12],
        parentId: data[i][13],
        role: data[i][14],
        city: data[i][15],
        school: data[i][16],
        grade: data[i][17]
      };
    }
  }
  return null;
}

// Аналогично для других сущностей...

// Функции для еды
function createEat(name, calories, protein, fat, carbs, type, image, week, day) {
  var id = getNextId(eatSheet);
  eatSheet.appendRow([id, name, calories, protein, fat, carbs, type, image, week, day]);
  return id;
}

function getEatById(id) {
  var data = eatSheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] == id) {
      return {
        id: data[i][0],
        name: data[i][1],
        calories: data[i][2],
        protein: data[i][3],
        fat: data[i][4],
        carbs: data[i][5],
        type: data[i][6],
        image: data[i][7],
        week: data[i][8],
        day: data[i][9]
      };
    }
  }
  return null;
}

// Функции для логов питания
function createEatLog(studentId, foodId, name, calories, protein, fat, carbs) {
  var id = getNextId(eatLogSheet);
  var now = new Date();
  eatLogSheet.appendRow([id, studentId, foodId, name, calories, protein, fat, carbs, now]);
  return id;
}

// Функции для городов, школ и т.д.
function createCity(name) {
  var id = getNextId(citiesSheet);
  citiesSheet.appendRow([id, name]);
  return id;
}

function createSchool(name, cityId) {
  var id = getNextId(schoolsSheet);
  schoolsSheet.appendRow([id, name, cityId]);
  return id;
}

function createGrade(name, schoolId) {
  var id = getNextId(gradesSheet);
  gradesSheet.appendRow([id, name, schoolId]);
  return id;
}

// Функции для админов
function createAdmin(login, password, isMaster, createdBy) {
  var id = getNextId(adminsSheet);
  var hashedPassword = hashPassword(password);
  var now = new Date();
  adminsSheet.appendRow([id, login, hashedPassword, isMaster, now, createdBy]);
  return id;
}

// Функции для пакетов
function createPack(week, day, createdBy) {
  var id = getNextId(packsSheet);
  packsSheet.appendRow([id, week, day, createdBy]);
  return id;
}

function createPackItem(packId, foodId, ord, isActive) {
  var id = getNextId(packItemsSheet);
  packItemsSheet.appendRow([id, packId, foodId, ord, isActive]);
  return id;
}

// Функция для анализа фото (использует Google Vision API)
function analyzeFoodImage(imageBlob) {
  try {
    var vision = Vision.newVisionService().newAnnotator();
    var features = vision.newFeature().setType('LABEL_DETECTION').setMaxResults(10);
    var requests = vision.newBatchAnnotateImagesRequest();
    var image = vision.newImage().setContent(Utilities.base64Encode(imageBlob.getBytes()));
    requests.setRequests([vision.newAnnotateImageRequest().setImage(image).setFeatures([features])]);

    var response = vision.batchAnnotateImages(requests);
    var labels = response.getResponses()[0].getLabelAnnotations();

    // Возвращаем метки для анализа еды
    return labels.map(function(label) {
      return {
        description: label.getDescription(),
        score: label.getScore()
      };
    });
  } catch (e) {
    return [{description: 'Ошибка анализа: ' + e.message, score: 0}];
  }
}

// Веб-приложение функции (для публикации как веб-app)
function doGet(e) {
  var html = HtmlService.createHtmlOutputFromFile('base_new').setTitle('School Food App');
  return html;
}

function doPost(e) {
  // Обработка POST-запросов
  var action = e.parameter.action;
  switch(action) {
    case 'login':
      return handleLogin(e.parameter.login, e.parameter.password);
    case 'register':
      return handleRegister(e.parameter);
    // Другие действия...
    default:
      return ContentService.createTextOutput('Invalid action');
  }
}

function handleLogin(login, password) {
  // Логика входа
  var user = getStudent(login) || getParent(login) || getCook(login) || getAdmin(login);
  if (user && user.password === hashPassword(password)) {
    return ContentService.createTextOutput(JSON.stringify({success: true, user: user}));
  }
  return ContentService.createTextOutput(JSON.stringify({success: false, message: 'Invalid credentials'}));
}

function handleRegister(params) {
  // Логика регистрации
  try {
    var role = params.role;
    if (role === 'student') {
      createStudent(params.login, params.password, null, 2000, 0, 0, 0, 'student', null, null, null, null, null, null, null, null, null, null);
    } else if (role === 'parent') {
      createParent(params.login, params.password, null, null);
    } else if (role === 'cook') {
      createCook(params.login, params.password, null, null);
    }
    return ContentService.createTextOutput(JSON.stringify({success: true}));
  } catch (e) {
    return ContentService.createTextOutput(JSON.stringify({success: false, message: e.message}));
  }
}