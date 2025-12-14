import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Index from './components/Index';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import PhotoAnalyze from './components/PhotoAnalyze';
import About from './components/About';
import CalorieCalculator from './components/CalorieCalculator';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/photo-analyze" element={<PhotoAnalyze />} />
        <Route path="/about" element={<About />} />
        <Route path="/calorie-calculator" element={<CalorieCalculator />} />
      </Routes>
    </Router>
  );
}

export default App;