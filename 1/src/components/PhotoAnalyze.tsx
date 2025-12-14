import React, { useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { NutritionData } from '../types';
import { analyzeFoodImage } from '../services/geminiService';

// Helper Functions
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1]);
    };
    reader.onerror = (error) => reject(error);
  });
};

// Icon Components
const CalorieIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
    <path d="M15.5 8.5c-.75-2-2.5-3-4.5-3s-3.75 1-4.5 3" />
    <path d="M8.5 15.5c2 1.5 4 1.5 6 0" />
  </svg>
);

const ProteinIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

const FatIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0L12 2.69z" />
  </svg>
);

const CarbIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.4 2.4a2 2 0 0 1 3.2 0l5.6 8.2a2 2 0 0 1-1.6 3.4H6.4a2 2 0 0 1-1.6-3.4Z" />
    <path d="m12 14 1 7" />
    <path d="m7 21 1.5-7" />
    <path d="m17 21-1.5-7" />
  </svg>
);

const UploadIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const PhotoAnalyze: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [nutritionData, setNutritionData] = useState<NutritionData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
      setError(null);
      setNutritionData(null);
    }
  }, []);

  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const base64 = await fileToBase64(selectedFile);
      const mimeType = selectedFile.type;
      const data = await analyzeFoodImage(base64, mimeType);
      setNutritionData(data);
    } catch (err) {
      setError('Ошибка анализа изображения. Попробуйте другое фото.');
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  }, [selectedFile]);

  const clearForm = useCallback(() => {
    setSelectedFile(null);
    setPreview(null);
    setNutritionData(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

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
          <div className="col-md-8">
            <h2 className="text-center mb-4">Анализатор еды по фото</h2>

            <div className="card mb-4">
              <div className="card-body">
                <form onSubmit={handleSubmit}>
                  <div className="mb-3">
                    <label htmlFor="file" className="form-label">Выберите фото</label>
                    <input
                      className="form-control"
                      type="file"
                      id="file"
                      accept="image/*"
                      onChange={handleFileSelect}
                      ref={fileInputRef}
                      required
                    />
                    <div className="form-text">Выберите изображение блюда для анализа</div>
                  </div>
                  <div className="d-flex gap-2">
                    <button type="submit" className="btn btn-primary" disabled={isAnalyzing || !selectedFile}>
                      <UploadIcon className="me-2" style={{ width: '1em', height: '1em' }} />
                      {isAnalyzing ? 'Анализируем...' : 'Загрузить и проанализировать'}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={clearForm}>
                      <i className="bi bi-x-circle me-2"></i>
                      Очистить
                    </button>
                  </div>
                </form>
              </div>
            </div>

            {preview && (
              <div className="card mb-4">
                <div className="card-body">
                  <h5>Предварительный просмотр</h5>
                  <img src={preview} alt="Preview" className="img-fluid rounded" />
                </div>
              </div>
            )}

            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}

            {nutritionData && (
              <div className="card">
                <div className="card-body">
                  <h5 className="card-title">Результаты анализа</h5>
                  <div className="row">
                    <div className="col-md-6">
                      <p><strong>Блюдо:</strong> {nutritionData.foodName}</p>
                      <p><strong>Размер порции:</strong> {nutritionData.servingSize}</p>
                    </div>
                    <div className="col-md-6">
                      <div className="d-flex align-items-center mb-2">
                        <CalorieIcon className="me-2 text-warning" style={{ width: '1.5em', height: '1.5em' }} />
                        <span><strong>Калории:</strong> {nutritionData.calories} ккал</span>
                      </div>
                      <div className="d-flex align-items-center mb-2">
                        <ProteinIcon className="me-2 text-primary" style={{ width: '1.5em', height: '1.5em' }} />
                        <span><strong>Белки:</strong> {nutritionData.protein} г</span>
                      </div>
                      <div className="d-flex align-items-center mb-2">
                        <FatIcon className="me-2 text-secondary" style={{ width: '1.5em', height: '1.5em' }} />
                        <span><strong>Жиры:</strong> {nutritionData.fat} г</span>
                      </div>
                      <div className="d-flex align-items-center mb-2">
                        <CarbIcon className="me-2 text-info" style={{ width: '1.5em', height: '1.5em' }} />
                        <span><strong>Углеводы:</strong> {nutritionData.carbohydrates} г</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
};

export default PhotoAnalyze;