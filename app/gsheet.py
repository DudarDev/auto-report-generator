# /workspaces/auto-report-generator/app/gsheet.py
import gspread
import pandas as pd
import logging
from typing import Optional, List, Dict, Any

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)

# Глобальний клієнт, щоб не ініціалізувати його щоразу
_gspread_client = None

def _get_gspread_client() -> Optional[gspread.Client]:
    """
    Ініціалізує та повертає клієнт gspread.
    Використовує автоматичну автентифікацію Application Default Credentials.
    """
    global _gspread_client
    if _gspread_client is None:
        try:
            logging.info("Ініціалізація gspread клієнта...")
            # Ця команда автоматично знайде доступи в середовищі Cloud Run
            _gspread_client = gspread.service_account()
            logging.info("Клієнт gspread успішно ініціалізовано.")
        except Exception as e:
            logging.error(f"Не вдалося ініціалізувати gspread клієнт: {e}")
            return None
    return _gspread_client

def get_sheet_data(sheet_id: str,
                   csv_file: Optional[Any] = None,
                   column_mapping: Optional[Dict[str, str]] = None) -> Optional[List[Dict]]:
    """
    Отримує дані з Google Sheet або CSV-файлу.
    """
    try:
        # Логіка для CSV
        if csv_file is not None:
            logging.info(f"Обробка завантаженого CSV-файлу: {csv_file.name}")
            df = pd.read_csv(csv_file)
            # Перейменовуємо колонки, якщо є мапінг
            if column_mapping:
                df = df.rename(columns=column_mapping)
            return df.to_dict('records')

        # Логіка для Google Sheets
        elif sheet_id:
            gc = _get_gspread_client()
            if not gc:
                return None  # Помилка ініціалізації клієнта

            spreadsheet = gc.open_by_key(sheet_id)
            worksheet = spreadsheet.sheet1
            data = worksheet.get_all_records()
            
            # Якщо є мапінг, перейменовуємо ключі в словниках
            if column_mapping:
                renamed_data = []
                for row in data:
                    new_row = {column_mapping.get(k, k): v for k, v in row.items()}
                    renamed_data.append(new_row)
                data = renamed_data
                
            return data
        else:
            logging.error("Не надано ані sheet_id, ані csv_file.")
            return None

    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"Таблицю з ID '{sheet_id}' не знайдено.")
        return None
    except Exception as e:
        logging.error(f"Сталася помилка при отриманні даних: {e}", exc_info=True)
        return None