import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const CalorieCalculator: React.FC = () => {
  const [age, setAge] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [activity, setActivity] = useState('low');
  const [gender, setGender] = useState('male');
  const [result, setResult] = useState<number | null>(null);

  const calculateCalories = () => {
    const a = parseInt(age);
    const h = parseInt(height);
    const w = parseInt(weight);
    if (!a || !h || !w) return;

    // Простая формула Mifflin-St Jeor
    let bmr = gender === 'male'
      ? 10 * w + 6.25 * h - 5 * a + 5
      : 10 * w + 6.25 * h - 5 * a - 161;

    const activityMultipliers = {
      low: 1.2,
      medium: 1.55,
      high: 1.725
    };

    const tdee = bmr * activityMultipliers[activity as keyof typeof activityMultipliers];
    setResult(Math.round(tdee));
  };

  return (
    <>
      <header data-bs-theme="dark">
        <div className="navbar navbar-dark bg-dark shadow-sm">
          <div className="container d-flex justify-content-between align-items-center">
            <Link to="/" className="navbar-brand">School Cafe</Link>
            <Link to="/dashboard" className="btn btn-outline-light">Назад</Link>
          </div>
        </div>
      </header>

      <main className="container py-5">
        <div className="row justify-content-center">
          <div className="col-md-6">
            <h2 className="text-center mb-4">Калькулятор калорий</h2>
            <div className="card">
              <div className="card-body">
                <form onSubmit={(e) => { e.preventDefault(); calculateCalories(); }}>
                  <div className="mb-3">
                    <label className="form-label">Возраст (лет)</label>
                    <input type="number" className="form-control" value={age} onChange={(e) => setAge(e.target.value)} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Рост (см)</label>
                    <input type="number" className="form-control" value={height} onChange={(e) => setHeight(e.target.value)} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Вес (кг)</label>
                    <input type="number" className="form-control" value={weight} onChange={(e) => setWeight(e.target.value)} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Пол</label>
                    <select className="form-control" value={gender} onChange={(e) => setGender(e.target.value)}>
                      <option value="male">Мужской</option>
                      <option value="female">Женский</option>
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Уровень активности</label>
                    <select className="form-control" value={activity} onChange={(e) => setActivity(e.target.value)}>
                      <option value="low">Низкий</option>
                      <option value="medium">Средний</option>
                      <option value="high">Высокий</option>
                    </select>
                  </div>
                  <button type="submit" className="btn btn-primary w-100">Рассчитать</button>
                </form>
                {result && (
                  <div className="mt-3 alert alert-success">
                    <strong>Рекомендуемая суточная норма калорий: {result} ккал</strong>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default CalorieCalculator;