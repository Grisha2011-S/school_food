import React from 'react';
import { Link } from 'react-router-dom';

const About: React.FC = () => {
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
        <h1 className="mb-4">Почему важно считать КБЖУ для детей</h1>
        <div className="row">
          <div className="col-lg-8 mx-auto">
            <div className="card shadow">
              <div className="card-body">
                <p className="mb-4">🧠 <strong>1. Помогает формировать правильные пищевые привычки</strong></p>
                <p className="mb-4">Ребёнок учится понимать, что еда бывает разной по пользе...</p>
                {/* Остальной контент из about.html */}
                <p className="mb-4">❤️ <strong>6. Прививает ответственность за здоровье</strong></p>
                <p className="mb-4">Ребёнок видит, как питание влияет на самочувствие...</p>
              </div>
            </div>
            <div className="text-center mt-4">
              <Link to="/dashboard" className="btn btn-secondary">
                <i className="bi bi-arrow-left me-2"></i>Назад
              </Link>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default About;