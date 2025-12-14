
import { GoogleGenAI, Type } from "@google/genai";
import { NutritionData } from '../types';

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
    throw new Error("API_KEY environment variable not set");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });

const nutritionSchema = {
    type: Type.OBJECT,
    properties: {
        foodName: {
            type: Type.STRING,
            description: "Название блюда, определенного на изображении. Если еда не найдена, укажите 'Еда не найдена'.",
        },
        servingSize: {
            type: Type.STRING,
            description: "Примерный вес порции, показанной на изображении, например 'около 250г'.",
        },
        calories: {
            type: Type.NUMBER,
            description: "Примерное количество калорий для порции на фото.",
        },
        protein: {
            type: Type.NUMBER,
            description: "Примерное количество белка в граммах для порции на фото.",
        },
        fat: {
            type: Type.NUMBER,
            description: "Примерное количество жиров в граммах для порции на фото.",
        },
        carbohydrates: {
            type: Type.NUMBER,
            description: "Примерное количество углеводов в граммах для порции на фото.",
        },
    },
    required: ["foodName", "servingSize", "calories", "protein", "fat", "carbohydrates"],
};

export async function analyzeFoodImage(base64Image: string, mimeType: string): Promise<NutritionData> {
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: {
                parts: [
                    {
                        inlineData: {
                            data: base64Image,
                            mimeType: mimeType,
                        },
                    },
                    {
                        text: "Определи еду на этом изображении. Оцени размер порции и предоставь примерную оценку пищевой ценности для порции, показанной на фото. Если на изображении нет еды, укажи это в 'foodName' и установи все значения питательных веществ на 0. Ответ должен быть только в формате JSON.",
                    },
                ],
            },
            config: {
                responseMimeType: "application/json",
                responseSchema: nutritionSchema,
            },
        });

        const jsonText = response.text.trim();
        const data = JSON.parse(jsonText);
        
        return data as NutritionData;

    } catch (error) {
        console.error("Error analyzing food image:", error);
        throw new Error("Не удалось получить данные о питательности от Gemini API.");
    }
}
