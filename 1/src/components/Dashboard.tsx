import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem('user');
    navigate('/');
  };

  return (
    <>
      <header data-bs-theme="dark">
        <div className="navbar navbar-dark bg-dark shadow-sm">
          <div className="container d-flex justify-content-between align-items-center">
            <Link to="/" className="navbar-brand">School Cafe</Link>
            <button onClick={logout} className="btn btn-danger">Выйти</button>
          </div>
        </div>
      </header>

      <main className="container py-5">
        <div className="row">
          <div className="col-md-8">
            <h1 className="mb-4">Панель управления</h1>

            <div className="row g-4">
              <div className="col-md-6">
                <div className="card h-100">
                  <div className="card-body">
                    <h5 className="card-title">
                      <i className="bi bi-graph-up text-primary me-2"></i>
                      Статистика питания
                    </h5>
                    <div>
                      <p className="text-muted">Здесь будет статистика</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="col-md-6">
                <div className="card h-100">
                  <div className="card-body">
                    <h5 className="card-title">
                      <i className="bi bi-calendar-check text-success me-2"></i>
                      Сегодняшнее меню
                    </h5>
                    <div>
                      <p className="text-muted">Меню загружается...</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-5">
              <h3>Быстрые действия</h3>
              <div className="list-group">
                <Link to="/photo-analyze" className="list-group-item list-group-item-action">
                  <i className="bi bi-camera me-2"></i>
                  Анализировать еду по фото
                </Link>
                <Link to="/calorie-calculator" className="list-group-item list-group-item-action">
                  <i className="bi bi-calculator me-2"></i>
                  Калькулятор калорий
                </Link>
                <Link to="/about" className="list-group-item list-group-item-action">
                  <i className="bi bi-info-circle me-2"></i>
                  О программе
                </Link>
              </div>
            </div>
          </div>

          <div className="col-md-4">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">Рекомендации</h5>
                <ul className="list-unstyled">
                  <li className="mb-2">
                    <i className="bi bi-check-circle text-success me-2"></i>
                    Следите за балансом БЖУ
                  </li>
                  <li className="mb-2">
                    <i className="bi bi-check-circle text-success me-2"></i>
                    Пейте достаточно воды
                  </li>
                  <li className="mb-2">
                    <i className="bi bi-check-circle text-success me-2"></i>
                    Ешьте разнообразную пищу
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default Dashboard;