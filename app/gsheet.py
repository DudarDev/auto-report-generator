# /workspaces/auto-report-generator/app/gsheet.py
import os
import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials 
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import pandas as pd # Для обробки CSV
import traceback # Для детального виводу помилок

# Завантажуємо змінні середовища (корисно для локальної розробки)
load_dotenv()

# Області видимості для Google API
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file" 
]

# Визначаємо функцію ініціалізації клієнта Google Sheets ПЕРЕД її використанням
def init_gsheet():
    """Ініціалізує та повертає авторизований клієнт gspread."""
    print("INFO: [gsheet.py] Initializing gspread client...")
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not creds_path or not os.path.exists(creds_path):
        error_msg = "ERROR: [gsheet.py] GOOGLE_APPLICATION_CREDENTIALS environment variable is not set, or the key file path is invalid. Ensure the GCP credentials initialization block has run successfully."
        print(error_msg)
        raise ValueError(error_msg) # Кидаємо виняток, щоб зупинити виконання, якщо немає ключів
    
    try:
        # Використовуємо шлях до тимчасового файлу, який встановлено змінною середовища
        gc = gspread.service_account(filename=creds_path)
        print("SUCCESS: [gsheet.py] gspread client initialized successfully.")
        return gc
    except Exception as e:
        print(f"ERROR: [gsheet.py] Failed to initialize gspread client: {e}")
        traceback.print_exc()
        raise # Перекидаємо виняток далі

# Тепер визначаємо функцію отримання даних
def get_sheet_data(sheet_id: Optional[str] = None, 
                   csv_file: Optional[Any] = None, # Any для UploadedFile Streamlit
                   column_mapping: Optional[Dict[str, str]] = None) -> Optional[List[Dict]]:
    """
    Отримує дані з Google Sheet за ID або з наданого CSV файлу.
    Для CSV файлу застосовує мапування стовпців, якщо воно надано.
    Повертає список словників або None у разі помилки.
    """
    if sheet_id:
        try:
            print(f"INFO: [gsheet.py] Attempting to fetch data for sheet_id: {sheet_id}")
            client = init_gsheet() # Викликаємо ініціалізацію клієнта
            
            gsheet_id_to_open = os.getenv("GOOGLE_SHEET_ID") # Беремо ID з env var
            if not gsheet_id_to_open: # Якщо не задано глобально, використовуємо переданий sheet_id
                if not sheet_id: # Якщо і sheet_id не передано, то помилка
                     print("ERROR: [gsheet.py] No Google Sheet ID provided (neither as argument nor as GOOGLE_SHEET_ID env var).")
                     return None
                gsheet_id_to_open = sheet_id # Використовуємо sheet_id з аргументу
            
            spreadsheet = client.open_by_key(gsheet_id_to_open)
            sheet1 = spreadsheet.sheet1 # Або інший аркуш, якщо потрібно
            data = sheet1.get_all_records() # Повертає список словників
            
            if not data:
                print(f"WARNING: [gsheet.py] No data found in Google Sheet ID: {gsheet_id_to_open}")
                return [] # Повертаємо порожній список, якщо таблиця порожня

            print(f"INFO: [gsheet.py] Successfully fetched {len(data)} records from Google Sheet: {spreadsheet.title}")
            
            # **Важливо для Google Sheets:**
            # Якщо ваш context_builder.py очікує фіксовані ключі (наприклад, 'client_name', 'task'),
            # а назви стовпців у вашій Google Таблиці інші, вам потрібно буде тут додати
            # логіку перейменування стовпців для `data` (списку словників),
            # аналогічно до того, як це робиться для CSV нижче.
            # Або переконайтеся, що стовпці в Google Sheet вже мають назви 'client_name', 'task' і т.д.
            # Наприклад, якщо column_mapping передається і для Sheets:
            # if column_mapping:
            #     renamed_data = []
            #     for record in data:
            #         new_record = {}
            #         for internal_key, sheet_header in column_mapping.items():
            #             if sheet_header in record:
            #                 new_record[internal_key] = record[sheet_header]
            #             else:
            #                 new_record[internal_key] = None # Або інше значення за замовчуванням
            #         renamed_data.append(new_record)
            #     return renamed_data
            return data
        except Exception as e:
            print(f"ERROR: [gsheet.py] Failed to fetch data from Google Sheet ID {sheet_id}: {e}")
            traceback.print_exc()
            return None

    elif csv_file:
        if not column_mapping:
            print("WARNING: [gsheet.py] CSV column mapping not provided. Trying to use original headers.")
            # Якщо мапування немає, намагаємося прочитати як є.
            # context_builder має бути готовий до оригінальних заголовків або мати дефолти.
            try:
                df = pd.read_csv(csv_file)
                csv_file.seek(0) # Важливо, якщо файл буде читатися ще раз
                return df.to_dict('records')
            except Exception as e:
                print(f"ERROR: [gsheet.py] Failed to read CSV file without mapping: {e}")
                traceback.print_exc()
                return None

        try:
            print(f"INFO: [gsheet.py] Reading and mapping data from uploaded CSV file. Mapping: {column_mapping}")
            df = pd.read_csv(csv_file)
            csv_file.seek(0) 

            # column_mapping: {'внутрішній_ключ_додатку': 'назва_стовпця_в_CSV_користувача'}
            # Нам потрібно: {'назва_стовпця_в_CSV_користувача': 'внутрішній_ключ_додатку'} для df.rename
            rename_map = {user_header: internal_key 
                          for internal_key, user_header in column_mapping.items() 
                          if user_header in df.columns and user_header} # Ігноруємо порожні user_header
            
            df_renamed = df.rename(columns=rename_map)

            # Залишаємо тільки ті стовпці, які відповідають внутрішнім ключам нашого додатку
            # і для яких було надано мапування (тобто вони є ключами в column_mapping)
            internal_keys_to_keep = [key for key in column_mapping.keys() if key in df_renamed.columns]
            
            if not internal_keys_to_keep:
                print("ERROR: [gsheet.py] No columns were kept after mapping. Check your mapping and CSV headers.")
                return [] # Повертаємо порожній список

            df_final = df_renamed[internal_keys_to_keep]
            
            # Заповнюємо відсутні очікувані стовпці значеннями None (або іншим дефолтом)
            # EXPECTED_APP_FIELDS - це словник {'internal_key': 'display_name'}, який ви визначили в run_app.py
            # Його потрібно або передати сюди, або визначити глобально/імпортувати.
            # Для прикладу, припустимо, він визначений тут:
            EXPECTED_INTERNAL_KEYS = ["client_name", "task", "status", "date", "comments", "amount"] 
            for key in EXPECTED_INTERNAL_KEYS:
                if key not in df_final.columns:
                    df_final[key] = None # Або інше значення за замовчуванням

            data = df_final.to_dict('records')
            print(f"INFO: [gsheet.py] Successfully read and mapped {len(data)} records from CSV.")
            return data
        except Exception as e:
            print(f"ERROR: [gsheet.py] Failed to read or map data from CSV file: {e}")
            traceback.print_exc()
            return None
    else:
        print("ERROR: [gsheet.py] No sheet_id or csv_file provided to get_sheet_data.")
        return None

# Тут може бути ваша функція add_new_lead, якщо вона є
# def add_new_lead(...):
# client = init_gsheet()
# ...