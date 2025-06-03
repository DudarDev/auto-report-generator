# /workspaces/auto-report-generator/app/gsheet.py
import os
import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials 
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import pandas as pd
import traceback

load_dotenv()
print(f"INFO: [gsheet.py] Module loaded. Attempted to load .env file.")

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file" 
]

# Цей список має бути ЄДИНИМ ДЖЕРЕЛОМ ІСТИНИ для внутрішніх ключів.
# Найкраще його визначити в app/run_app.py як APP_INTERNAL_KEYS 
# і імпортувати сюди та в context_builder.py.
# Поки що, для простоти, дублюємо його тут, АЛЕ ПЕРЕКОНАЙТЕСЯ, ЩО ВІН ІДЕНТИЧНИЙ!
EXPECTED_INTERNAL_KEYS = ["client_name", "task", "status", "date", "comments", "amount"] 

def init_gsheet():
    print("INFO: [gsheet.py] Initializing gspread client...")
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path or not os.path.exists(creds_path):
        error_msg = "ERROR: [gsheet.py] GOOGLE_APPLICATION_CREDENTIALS env var not set or key file path invalid."
        print(error_msg)
        raise ValueError(error_msg)
    try:
        gc = gspread.service_account(filename=creds_path)
        print("SUCCESS: [gsheet.py] gspread client initialized successfully.")
        return gc
    except Exception as e:
        print(f"ERROR: [gsheet.py] Failed to initialize gspread client: {e}")
        traceback.print_exc()
        raise

def _normalize_data(data_list: List[Dict], 
                    expected_keys: List[str], # Передаємо сюди APP_INTERNAL_KEYS
                    column_mapping: Optional[Dict[str, str]] = None) -> List[Dict]:
    normalized_list = []
    if not data_list:
        return []

    print(f"DEBUG: [_normalize_data] Normalizing {len(data_list)} records. Expected keys: {expected_keys}. Provided CSV mapping: {column_mapping}")

    for record_index, original_record in enumerate(data_list):
        if not isinstance(original_record, dict):
            print(f"WARNING: [_normalize_data] Record at index {record_index} is not a dict, skipping: {original_record}")
            continue
        
        new_record = {}
        # Спочатку обробляємо випадок з CSV та явним мапуванням від користувача
        if column_mapping: 
            print(f"DEBUG: [_normalize_data] Applying CSV column_mapping for record {record_index}. Original keys: {list(original_record.keys())}")
            for internal_key in expected_keys: # internal_key це, наприклад, "client_name"
                user_header = column_mapping.get(internal_key) # Назва стовпця в CSV, яку вказав користувач
                if user_header and user_header in original_record:
                    new_record[internal_key] = original_record[user_header]
                else:
                    new_record[internal_key] = None 
                    if user_header: # Якщо користувач вказав мапування, але такого стовпця немає в CSV
                         print(f"WARNING: [_normalize_data] For internal key '{internal_key}', mapped CSV header '{user_header}' not found in record {record_index}. Setting to None.")
        # Обробка для Google Sheets (де column_mapping is None) або CSV без явного мапування
        else:
            print(f"DEBUG: [_normalize_data] Normalizing keys for Google Sheet (or CSV w/o mapping) for record {record_index}. Original keys: {list(original_record.keys())}")
            # Створюємо словник з нормалізованими ключами з original_record для пошуку
            # Ключ - нормалізований (маленькі літери, підкреслення), значення - оригінальний ключ з запису
            normalized_original_keys_map = {
                str(k).lower().replace(' ', '_').replace('-', '_'): k 
                for k in original_record.keys()
            }
            print(f"DEBUG: [_normalize_data] Normalized original keys map for record {record_index}: {normalized_original_keys_map}")

            for internal_key in expected_keys: # internal_key це, наприклад, "client_name"
                # 1. Спробуємо знайти точне співпадіння internal_key в оригінальних ключах
                if internal_key in original_record:
                    new_record[internal_key] = original_record[internal_key]
                    print(f"DEBUG: [_normalize_data] Direct match found for '{internal_key}' in record {record_index}.")
                # 2. Якщо немає, спробуємо знайти internal_key серед нормалізованих ключів з original_record
                elif internal_key in normalized_original_keys_map:
                    original_key_from_source = normalized_original_keys_map[internal_key]
                    new_record[internal_key] = original_record[original_key_from_source]
                    print(f"DEBUG: [_normalize_data] Mapped source key '{original_key_from_source}' (as '{internal_key}') to internal key '{internal_key}' for record {record_index} (normalized match).")
                # 3. Специфічне виправлення для кириличної 'с' в 'сlient_name' (якщо ще актуально)
                elif internal_key == "client_name" and "сlient_name" in original_record: # Кирилична 'с'
                    new_record["client_name"] = original_record["сlient_name"]
                    print(f"DEBUG: [_normalize_data] Applied specific fix for Cyrillic 'сlient_name' to 'client_name' for record {record_index}")
                else:
                    new_record[internal_key] = None 
                    print(f"WARNING: [_normalize_data] Could not find a match for internal key '{internal_key}' in record {record_index}. Available original keys: {list(original_record.keys())}. Setting to None.")
        
        normalized_list.append(new_record)
    
    if normalized_list:
        print(f"DEBUG: [_normalize_data] First fully normalized record example after all processing: {normalized_list[0]}")
    else:
        print("WARNING: [_normalize_data] Normalization resulted in an empty list.")
    return normalized_list


def get_sheet_data(sheet_id: Optional[str] = None, 
                   csv_file: Optional[Any] = None, 
                   column_mapping: Optional[Dict[str, str]] = None) -> Optional[List[Dict]]:
    if sheet_id:
        try:
            print(f"INFO: [gsheet.py] Attempting to fetch data for sheet_id: {sheet_id}")
            client = init_gsheet()
            gsheet_id_to_open = os.getenv("GOOGLE_SHEET_ID") or sheet_id
            if not gsheet_id_to_open:
                print("ERROR: [gsheet.py] No Google Sheet ID provided.")
                return None
            
            spreadsheet = client.open_by_key(gsheet_id_to_open)
            sheet1 = spreadsheet.sheet1
            data_from_sheet = sheet1.get_all_records() # Список словників з оригінальними заголовками
            
            if not data_from_sheet:
                print(f"WARNING: [gsheet.py] No data found in Google Sheet ID: {gsheet_id_to_open}")
                return []

            print(f"INFO: [gsheet.py] Successfully fetched {len(data_from_sheet)} records from Google Sheet: {spreadsheet.title}")
            # Для Google Sheets, column_mapping тут буде None.
            # _normalize_data спробує зіставити стовпці з APP_INTERNAL_KEYS.
            return _normalize_data(data_from_sheet, EXPECTED_INTERNAL_KEYS, None) 
        except Exception as e:
            print(f"ERROR: [gsheet.py] Failed to fetch data from Google Sheet ID {sheet_id}: {e}")
            traceback.print_exc()
            return None

    elif csv_file:
        try:
            print(f"INFO: [gsheet.py] Reading data from uploaded CSV file. Provided mapping: {column_mapping}")
            df = pd.read_csv(csv_file, encoding='utf-8')
            csv_file.seek(0) 
            data_from_csv = df.to_dict('records')

            if not data_from_csv:
                print(f"WARNING: [gsheet.py] No data found in CSV file.")
                return []
            
            return _normalize_data(data_from_csv, EXPECTED_INTERNAL_KEYS, column_mapping)
        except Exception as e:
            print(f"ERROR: [gsheet.py] Failed to read or map data from CSV file: {e}")
            traceback.print_exc()
            return None
    else:
        print("ERROR: [gsheet.py] No sheet_id or csv_file provided to get_sheet_data.")
        return None
