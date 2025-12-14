
import React, { useState, useCallback, useRef } from 'react';
import { NutritionData } from './types';
import { analyzeFoodImage } from './services/geminiService';

// --- Helper Functions ---
const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            const result = reader.result as string;
            // Remove the "data:image/jpeg;base64," part
            resolve(result.split(',')[1]);
        };
        reader.onerror = (error) => reject(error);
    });
};

// --- Icon Components (defined outside main component) ---
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
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
);


// --- UI Components ---

interface ImageUploaderProps {
    onImageSelect: (file: File) => void;
    imageUrl: string | null;
}

const ImageUploader: React.FC<ImageUploaderProps> = ({ onImageSelect, imageUrl }) => {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            onImageSelect(file);
        }
    };

    const handleDrop = (event: React.DragEvent<HTMLLabelElement>) => {
        event.preventDefault();
        event.stopPropagation();
        const file = event.dataTransfer.files?.[0];
        if (file && file.type.startsWith('image/')) {
            onImageSelect(file);
        }
    };

    const handleDragOver = (event: React.DragEvent<HTMLLabelElement>) => {
        event.preventDefault();
        event.stopPropagation();
    };

    return (
        <div className="w-full max-w-lg mx-auto">
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="hidden"
                id="file-upload"
            />
            <label
                htmlFor="file-upload"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                className="cursor-pointer bg-white rounded-xl border-2 border-dashed border-slate-300 hover:border-sky-500 transition-colors p-4 w-full flex flex-col items-center justify-center text-center aspect-video"
            >
                {imageUrl ? (
                    <img src={imageUrl} alt="Предпросмотр" className="max-h-full max-w-full object-contain rounded-lg" />
                ) : (
                    <div className="text-slate-500 flex flex-col items-center gap-2">
                        <UploadIcon className="w-12 h-12 text-slate-400" />
                        <span className="font-semibold text-slate-600">Нажмите, чтобы загрузить</span>
                        <span className="text-sm">или перетащите фото сюда</span>
                    </div>
                )}
            </label>
        </div>
    );
};

interface NutritionCardProps {
    data: NutritionData;
}
const NutritionCard: React.FC<NutritionCardProps> = ({ data }) => {
    if (data.foodName === 'Еда не найдена' || data.calories === 0) {
        return (
            <div className="w-full max-w-lg mx-auto mt-8 bg-white p-6 rounded-xl shadow-md text-center">
                 <h2 className="text-2xl font-bold text-slate-700">{data.foodName}</h2>
                 <p className="text-slate-500 mt-2">Не удалось определить еду на изображении. Пожалуйста, попробуйте другое фото.</p>
            </div>
        )
    }

    return (
        <div className="w-full max-w-lg mx-auto mt-8 bg-white p-6 rounded-xl shadow-md">
            <h2 className="text-3xl font-bold text-center text-slate-800 mb-1">{data.foodName}</h2>
            <p className="text-center text-slate-500 mb-6">Пищевая ценность на порцию ({data.servingSize})</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div className="flex flex-col items-center p-3 bg-orange-50 rounded-lg">
                    <CalorieIcon className="w-8 h-8 text-orange-500 mb-2" />
                    <span className="text-xl font-bold text-orange-600">{Math.round(data.calories)}</span>
                    <span className="text-sm text-slate-600">Калории</span>
                </div>
                <div className="flex flex-col items-center p-3 bg-sky-50 rounded-lg">
                    <ProteinIcon className="w-8 h-8 text-sky-500 mb-2" />
                    <span className="text-xl font-bold text-sky-600">{data.protein.toFixed(1)} г</span>
                    <span className="text-sm text-slate-600">Белки</span>
                </div>
                <div className="flex flex-col items-center p-3 bg-amber-50 rounded-lg">
                    <FatIcon className="w-8 h-8 text-amber-500 mb-2" />
                    <span className="text-xl font-bold text-amber-600">{data.fat.toFixed(1)} г</span>
                    <span className="text-sm text-slate-600">Жиры</span>
                </div>
                <div className="flex flex-col items-center p-3 bg-lime-50 rounded-lg">
                    <CarbIcon className="w-8 h-8 text-lime-500 mb-2" />
                    <span className="text-xl font-bold text-lime-600">{data.carbohydrates.toFixed(1)} г</span>
                    <span className="text-sm text-slate-600">Углеводы</span>
                </div>
            </div>
        </div>
    );
};

// FIX: Corrected the corrupted SVG path data and made the component render the 'message' prop.
const Loader: React.FC<{ message: string }> = ({ message }) => (
    <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex flex-col items-center justify-center rounded-xl z-10">
        <svg className="animate-spin h-10 w-10 text-sky-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <p className="mt-4 text-slate-600 font-semibold">{message}</p>
    </div>
);

// FIX: Added the main App component to serve as the entry point and orchestrate the UI.
const App: React.FC = () => {
    const [nutritionData, setNutritionData] = useState<NutritionData | null>(null);
    const [imageUrl, setImageUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const currentObjectUrl = useRef<string | null>(null);

    const handleImageSelect = useCallback(async (file: File) => {
        if (isLoading) return;

        setIsLoading(true);
        setError(null);
        setNutritionData(null);

        if (currentObjectUrl.current) {
            URL.revokeObjectURL(currentObjectUrl.current);
        }

        const newImageUrl = URL.createObjectURL(file);
        setImageUrl(newImageUrl);
        currentObjectUrl.current = newImageUrl;

        try {
            const base64Image = await fileToBase64(file);
            const data = await analyzeFoodImage(base64Image, file.type);
            setNutritionData(data);
        } catch (err: any) {
            setError(err.message || 'Произошла неизвестная ошибка.');
        } finally {
            setIsLoading(false);
        }
    }, [isLoading]);

    return (
        <main className="bg-slate-50 min-h-screen font-sans p-4 sm:p-8 flex flex-col items-center">
            <div className="w-full max-w-lg mx-auto text-center mb-8">
                <h1 className="text-4xl sm:text-5xl font-bold text-slate-800">Калькулятор калорий по фото</h1>
                <p className="text-slate-600 mt-2">Загрузите фотографию еды, и ИИ определит её пищевую ценность.</p>
            </div>

            <div className="relative w-full max-w-lg">
                <ImageUploader onImageSelect={handleImageSelect} imageUrl={imageUrl} />
                {isLoading && <Loader message="Анализирую изображение..." />}
            </div>

            {error && (
                 <div className="w-full max-w-lg mx-auto mt-8 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl relative" role="alert">
                    <strong className="font-bold">Ошибка! </strong>
                    <span className="block sm:inline">{error}</span>
                </div>
            )}

            {nutritionData && !isLoading && <NutritionCard data={nutritionData} />}
        </main>
    );
};

export default App;
