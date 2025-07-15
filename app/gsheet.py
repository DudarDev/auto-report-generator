# /workspaces/auto-report-generator/app/gsheet.py
import gspread
import pandas as pd
import logging
from typing import Optional, List, Dict, Any

_gspread_client = None

def _get_gspread_client() -> Optional[gspread.Client]:
    """Ініціалізує gspread, використовуючи автентифікацію, що надається середовищем."""
    global _gspread_client
    if _gspread_client is None:
        try:
            logging.info("Ініціалізація gspread клієнта (автоматичний режим)...")
            _gspread_client = gspread.service_account()
            logging.info("Клієнт gspread успішно ініціалізовано.")
        except Exception as e:
            logging.error(f"Не вдалося ініціалізувати gspread клієнт: {e}", exc_info=True)
            return None
    return _gspread_client

def get_sheet_headers(sheet_id: str) -> List[str]:
    """Отримує тільки заголовки (перший рядок) з Google Sheet."""
    gc = _get_gspread_client()
    if not gc: raise Exception("Клієнт gspread не ініціалізовано")
    return gc.open_by_key(sheet_id).sheet1.row_values(1)

def get_sheet_data(sheet_id: str, csv_file: Optional[Any] = None, column_mapping: Optional[Dict[str, str]] = None) -> Optional[List[Dict]]:
    try:
        if csv_file is not None:
            df = pd.read_csv(csv_file)
            if column_mapping: df = df.rename(columns=column_mapping)
            return df.to_dict('records')
        elif sheet_id:
            gc = _get_gspread_client()
            if not gc: return None
            data = gc.open_by_key(sheet_id).sheet1.get_all_records()
            if column_mapping:
                return [{column_mapping.get(k, k): v for k, v in row.items()} for row in data]
            return data
        return None
    except Exception as e:
        logging.error(f"Сталася помилка при отриманні даних: {e}", exc_info=True)
        return None