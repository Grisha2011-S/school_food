import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Food {
  id: number;
  name: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  image?: string;
}

const Index: React.FC = () => {
  const [week, setWeek] = useState(1);
  const [day, setDay] = useState(1);
  const [foods, setFoods] = useState<Food[]>([]);

  useEffect(() => {
    loadTodaysMenu();
  }, []);

  const loadTodaysMenu = async () => {
    try {
      const response = await fetch('https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'getMenu' }),
      });
      const data = await response.json();
      if (data.foods) {
        setFoods(data.foods);
        // Вычислить неделю и день
        const today = new Date();
        setWeek(Math.ceil(today.getDate() / 7));
        setDay(today.getDay() || 7);
      }
    } catch (error) {
      console.error('Error loading menu:', error);
    }
  };

  const generateReport = () => {
    // Для GitHub Pages это может быть заглушка или ссылка на скачивание
    alert('Отчет будет создан (интеграция с Apps Script)');
  };

  return (
    <>
      <style>
        {`
          .bd-placeholder-img { font-size: 1.125rem; text-anchor: middle; user-select: none; }
          @media (min-width: 768px) { .bd-placeholder-img-lg { font-size: 3.5rem; } }
          .album .card { margin-bottom: 1.5rem; }
        `}
      </style>
      <header data-bs-theme="dark">
        <div className="navbar navbar-dark bg-dark shadow-sm">
          <div className="container d-flex justify-content-between align-items-center">
            <Link to="/" className="navbar-brand d-flex align-items-center">
              <strong>School Cafe</strong>
            </Link>
            <div className="d-flex">
              <Link to="/calorie-calculator" className="btn btn-outline-light me-2">Калькулятор калорий</Link>
              <Link to="/photo-analyze" className="btn btn-outline-light me-2">Анализ еды</Link>
              <Link to="/about" className="btn btn-outline-light me-2">О нас</Link>
              <button onClick={generateReport} className="btn btn-outline-light">Создать отчет</button>
            </div>
          </div>
        </div>
      </header>

      <main>
        <section className="py-5 text-center container">
          <div className="row py-lg-5">
            <div className="col-lg-6 col-md-8 mx-auto">
              <h1 className="fw-light">Меню на сегодня</h1>
              <p className="text-muted small">Неделя: <strong>{week}</strong> · День: <strong>{day}</strong></p>
              <p className="lead text-body-secondary">Свежая и полезная еда для школьников</p>
              <p>
                <Link to="/calorie-calculator" className="btn btn-primary my-2">Калькулятор калорий</Link>
                <Link to="/photo-analyze" className="btn btn-success my-2 ms-2">Анализировать еду</Link>
                <Link to="/about" className="btn btn-secondary my-2">Узнать больше</Link>
              </p>
            </div>
          </div>
        </section>

        <div className="album py-5 bg-body-tertiary">
          <div className="container">
            <div className="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-3">
              {foods.length > 0 ? foods.map(food => (
                <div key={food.id} className="col">
                  <div className="card shadow-sm">
                    {food.image ? (
                      <img src={food.image} className="card-img-top" style={{ height: '225px', objectFit: 'cover' }} alt={food.name} />
                    ) : (
                      <svg className="bd-placeholder-img card-img-top" width="100%" height="225" xmlns="http://www.w3.org/2000/svg" role="img" preserveAspectRatio="xMidYMid slice">
                        <title>Thumbnail</title>
                        <rect width="100%" height="100%" fill="#55595c"></rect>
                        <text x="50%" y="50%" fill="#eceeef" dy=".3em">{food.name}</text>
                      </svg>
                    )}
                    <div className="card-body">
                      <h5>{food.name}</h5>
                      <p className="card-text small">
                        Калории: {food.calories} · Белки: {food.protein}г · Жиры: {food.fat}г · Углеводы: {food.carbs}г
                      </p>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="col-12">
                  <div className="alert alert-info">Меню на сегодня отсутствует</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default Index;