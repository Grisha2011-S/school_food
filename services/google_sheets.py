import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_credentials():
    """Получает учетные данные для доступа к Google Sheets API"""
    try:
        # Используем service account
        creds_file = os.path.join(os.path.dirname(__file__), 'google_credentials.json')
        if os.path.exists(creds_file):
            return service_account.Credentials.from_service_account_file(
                creds_file, scopes=SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {e}")
    return None

def create_nutrition_report(student_name: str, logs: List[Dict], 
                          targets: Dict[str, float]) -> Optional[str]:
    """
    Создает отчет о питании в Google Sheets
    
    Args:
        student_name: Имя ученика
        logs: Список логов питания [{created_at, name, calories, protein, fat, carbs}]
        targets: Целевые показатели {'calories': float, 'protein': float, 'fat': float, 'carbs': float}
    
    Returns:
        URL созданной таблицы или None в случае ошибки
    """
    try:
        creds = get_credentials()
        if not creds:
            print("Failed to get credentials")
            return None

        service = build('sheets', 'v4', credentials=creds)
        
        # Создаем новую таблицу
        title = f"Отчет питания - {student_name} ({datetime.now().strftime('%Y-%m-%d')})"
        spreadsheet = {
            'properties': {
                'title': title
            },
            'sheets': [
                {
                    'properties': {
                        'title': 'Ежедневный отчет',
                        'gridProperties': {
                            'frozenRowCount': 2
                        }
                    }
                },
                {
                    'properties': {
                        'title': 'Итоговый анализ'
                    }
                }
            ]
        }
        
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        # Группируем логи по дням
        daily_logs = {}
        for log in logs:
            date = log['created_at'].date()
            if date not in daily_logs:
                daily_logs[date] = []
            daily_logs[date].append(log)
        
        # Формируем данные для ежедневного отчета
        daily_rows = [
            ['Отчет питания для ' + student_name],
            ['Дата', 'Блюдо', 'Время', 'Калории', 'Белки', 'Жиры', 'Углеводы']
        ]
        
        daily_colors = []  # [(row, col, color), ...]
        current_row = 2  # начинаем после заголовков
        
        for date in sorted(daily_logs.keys()):
            day_logs = daily_logs[date]
            
            # Считаем дневные суммы
            day_total = {
                'calories': sum(log['calories'] for log in day_logs),
                'protein': sum(log['protein'] for log in day_logs),
                'fat': sum(log['fat'] for log in day_logs),
                'carbs': sum(log['carbs'] for log in day_logs)
            }
            
            # Добавляем записи за день
            for log in sorted(day_logs, key=lambda x: x['created_at']):
                daily_rows.append([
                    date.strftime('%Y-%m-%d'),
                    log['name'],
                    log['created_at'].strftime('%H:%M'),
                    log['calories'],
                    log['protein'],
                    log['fat'],
                    log['carbs']
                ])
                
                # Отмечаем цветом отклонения от нормы
                for col, (field, target) in enumerate(['calories', 'protein', 'fat', 'carbs'], start=3):
                    value = log[field]
                    if value > target * 1.1:  # превышение на 10%
                        daily_colors.append((current_row, col, {'red': 0.9, 'green': 0.8, 'blue': 0.8}))
                    elif value < target * 0.9:  # недобор на 10%
                        daily_colors.append((current_row, col, {'red': 0.8, 'green': 0.8, 'blue': 0.9}))
                
                current_row += 1
            
            # Добавляем итоги за день
            daily_rows.append([
                'ИТОГО за ' + date.strftime('%Y-%m-%d'),
                '',
                '',
                f"=SUM(D{current_row-len(day_logs)}:D{current_row-1})",
                f"=SUM(E{current_row-len(day_logs)}:E{current_row-1})",
                f"=SUM(F{current_row-len(day_logs)}:F{current_row-1})",
                f"=SUM(G{current_row-len(day_logs)}:G{current_row-1})"
            ])
            current_row += 2  # пустая строка после итогов
            
        # Обновляем данные в таблице
        range_name = 'Ежедневный отчет!A1'
        body = {
            'values': daily_rows
        }
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='USER_ENTERED', body=body).execute()
        
        # Применяем форматирование
        requests = []
        
        # Форматирование заголовков
        requests.append({
            'repeatCell': {
                'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 2},
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                        'textFormat': {'bold': True}
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })
        
        # Применяем цветовые выделения
        for row, col, color in daily_colors:
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': row,
                        'endRowIndex': row + 1,
                        'startColumnIndex': col,
                        'endColumnIndex': col + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': color
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })

        # Автоматическая ширина колонок
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 7
                }
            }
        })
        
        # Применяем форматирование
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}).execute()
        
        # Возвращаем URL таблицы
        return f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'
        
    except HttpError as e:
        print(f'Google Sheets API error: {e}')
        return None
    except Exception as e:
        print(f'Unexpected error: {e}')
        return None