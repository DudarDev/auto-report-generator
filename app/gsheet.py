# /app/gsheet.py

import gspread
import pandas as pd
import logging
from typing import List, Dict, Optional, Any

# --- ІМПОРТУЄМО ГОТОВІ НАЛАШТУВАННЯ З НАШОГО "МОЗКУ" ---
from app import config

def init_gsheet() -> gspread.Client:
    """Ініціалізує клієнт gspread, використовуючи ГОТОВІ налаштування з config."""
    logging.info("Ініціалізація gspread клієнта...")

    # ВИКОРИСТОВУЄМО ЗМІННУ НАПРЯМУ З КОНФІГУРАЦІЇ
    creds_path = config.GOOGLE_APPLICATION_CREDENTIALS
    
    if not creds_path:
        error_msg = "Шлях до GOOGLE_APPLICATION_CREDENTIALS не встановлено у config.py."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    gc = gspread.service_account(filename=creds_path)
    logging.info("Клієнт gspread успішно ініціалізовано.")
    return gc

def get_sheet_headers(sheet_id: str) -> List[str]:
    """Ефективно завантажує лише заголовок з Google-таблиці."""
    client = init_gsheet()
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet.row_values(1)

def get_sheet_data(
    sheet_id: Optional[str] = None, 
    csv_file: Optional[Any] = None, 
    column_mapping: Optional[Dict[str, str]] = None
) -> Optional[List[Dict]]:
    """Отримує та нормалізує дані з Google Sheets або CSV файлу."""
    if sheet_id:
        client = init_gsheet()
        sheet = client.open_by_key(sheet_id).sheet1
        data_from_sheet = sheet.get_all_records()
        return _normalize_data(data_from_sheet, config.APP_INTERNAL_KEYS, column_mapping)
    elif csv_file:
        df = pd.read_csv(csv_file)
        data_from_csv = df.to_dict('records')
        return _normalize_data(data_from_csv, config.APP_INTERNAL_KEYS, column_mapping)
    return None

def _normalize_data(
    data_list: List[Dict], 
    expected_keys: List[str], 
    column_mapping: Optional[Dict[str, str]] = None
) -> List[Dict]:
    """Приводить дані до єдиного формату."""
    if not column_mapping:
        return []
    normalized_list = []
    for record in data_list:
        new_record = {key: record.get(column_mapping.get(key)) for key in expected_keys}
        normalized_list.append(new_record)
    return normalized_list