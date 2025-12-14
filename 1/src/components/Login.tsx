import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const [role, setRole] = useState('student');
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'login', login, password }),
      });
      const result = await response.json();
      if (result.success) {
        // Сохранить пользователя в localStorage или state
        localStorage.setItem('user', JSON.stringify(result.user));
        navigate('/dashboard');
      } else {
        setMessage(result.message);
      }
    } catch (error) {
      setMessage('Ошибка входа');
    }
  };

  return (
    <main className="form-signin w-100 m-auto" style={{ maxWidth: '400px', padding: '4rem 1rem' }}>
      <form onSubmit={handleSubmit}>
        <h1 className="h3 mb-3 fw-normal">Пожалуйста, войдите</h1>

        <div className="form-floating mb-3">
          <select
            className="form-control"
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            required
          >
            <option value="student">Ученик</option>
            <option value="parent">Родитель</option>
            <option value="cook">Повар</option>
            <option value="teacher">Учитель</option>
          </select>
          <label htmlFor="role">Кто вы?</label>
        </div>

        <div className="form-floating mb-3">
          <input
            type="text"
            className="form-control"
            id="login"
            placeholder="Логин"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            required
          />
          <label htmlFor="login">Логин</label>
        </div>

        <div className="form-floating mb-3">
          <input
            type="password"
            className="form-control"
            id="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <label htmlFor="password">Пароль</label>
        </div>

        <button className="btn btn-primary w-100 py-2" type="submit">Войти</button>
        <Link to="/" className="btn btn-secondary w-100 mt-2">Назад</Link>
      </form>
      {message && (
        <div className="mt-3 alert alert-danger">{message}</div>
      )}
    </main>
  );
};

export default Login;