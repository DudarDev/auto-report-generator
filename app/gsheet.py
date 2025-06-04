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

# Імпортуємо APP_INTERNAL_KEYS з run_app.py
# Це передбачає, що run_app.py знаходиться в тій же папці 'app'
# Якщо структура інша, шлях імпорту потрібно буде змінити.
try:
    from .run_app import APP_INTERNAL_KEYS
except ImportError:
    print("WARNING: [gsheet.py] Could not import APP_INTERNAL_KEYS from .run_app. Using a fallback list. Ensure consistent key definitions.")
    APP_INTERNAL_KEYS = ["client_name", "task", "status", "date", "comments", "amount"] 

def init_gsheet():
    # ... (код init_gsheet() залишається таким, як я надавав раніше) ...
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
                    expected_keys: List[str], # Сюди передається APP_INTERNAL_KEYS
                    column_mapping: Optional[Dict[str, str]] = None) -> List[Dict]:
    normalized_list = []
    if not data_list:
        return []

    print(f"DEBUG: [_normalize_data] Normalizing {len(data_list)} records. Expected internal keys: {expected_keys}. Provided CSV mapping: {column_mapping}")

    for record_index, original_record in enumerate(data_list):
        if not isinstance(original_record, dict):
            print(f"WARNING: [_normalize_data] Record at index {record_index} is not a dict, skipping: {original_record}")
            continue
        
        new_record = {}
        # Обробка CSV з явним мапуванням від користувача
        if column_mapping: 
            print(f"DEBUG: [_normalize_data] Applying CSV column_mapping for record {record_index}. Original keys: {list(original_record.keys())}")
            for internal_key in expected_keys: 
                user_header = column_mapping.get(internal_key) 
                if user_header and user_header in original_record:
                    new_record[internal_key] = original_record[user_header]
                else:
                    new_record[internal_key] = None 
                    if user_header: 
                         print(f"WARNING: [_normalize_data] For internal key '{internal_key}', mapped CSV header '{user_header}' not found in record {record_index}. Setting to None.")
        # Обробка для Google Sheets (де column_mapping is None) або CSV без явного мапування
        else:
            print(f"DEBUG: [_normalize_data] Normalizing keys for Google Sheet (or CSV w/o mapping) for record {record_index}. Original keys: {list(original_record.keys())}")
            normalized_original_keys_map = {
                str(k).lower().replace(' ', '_').replace('-', '_'): k 
                for k in original_record.keys()
            }
            
            for internal_key in expected_keys: 
                found_value = False
                # 1. Спробуємо знайти точне співпадіння internal_key в оригінальних ключах
                if internal_key in original_record:
                    new_record[internal_key] = original_record[internal_key]
                    found_value = True
                # 2. Якщо немає, спробуємо знайти internal_key серед нормалізованих ключів з original_record
                elif internal_key in normalized_original_keys_map:
                    original_key_from_source = normalized_original_keys_map[internal_key]
                    new_record[internal_key] = original_record[original_key_from_source]
                    found_value = True
                
                if not found_value:
                    new_record[internal_key] = None 
                    print(f"WARNING: [_normalize_data] Could not find a match for internal key '{internal_key}' in GSheet/unmapped CSV record {record_index}. Available original keys: {list(original_record.keys())}. Setting to None.")
        
        normalized_list.append(new_record)
    
    if normalized_list:
        print(f"DEBUG: [_normalize_data] First fully normalized record example: {normalized_list[0]}")
    return normalized_list


def get_sheet_data(sheet_id: Optional[str] = None, 
                   csv_file: Optional[Any] = None, 
                   column_mapping: Optional[Dict[str, str]] = None) -> Optional[List[Dict]]:
    # Використовуємо APP_INTERNAL_KEYS, імпортований або визначений вище
    global APP_INTERNAL_KEYS 

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
            data_from_sheet = sheet1.get_all_records() 
            
            if not data_from_sheet:
                print(f"WARNING: [gsheet.py] No data found in Google Sheet ID: {gsheet_id_to_open}")
                return []

            print(f"INFO: [gsheet.py] Successfully fetched {len(data_from_sheet)} records from Google Sheet: {spreadsheet.title}")
            return _normalize_data(data_from_sheet, APP_INTERNAL_KEYS, None) # column_mapping=None для Sheets
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
            
            return _normalize_data(data_from_csv, APP_INTERNAL_KEYS, column_mapping)
        except Exception as e:
            print(f"ERROR: [gsheet.py] Failed to read or map data from CSV file: {e}")
            traceback.print_exc()
            return None
    else:
        print("ERROR: [gsheet.py] No sheet_id or csv_file provided to get_sheet_data.")
        return None

