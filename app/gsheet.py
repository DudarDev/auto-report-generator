import gspread
import pandas as pd
import logging
import os
import json
from typing import Optional, List, Dict, Any
from google.oauth2 import service_account
from google.cloud import secretmanager

# Глобальна змінна для зберігання клієнта, щоб уникнути повторної ініціалізації
_gspread_client = None

def _get_credentials_from_secret_manager() -> Optional[service_account.Credentials]:
    """
    Отримує облікові дані сервісного акаунту з Google Secret Manager.
    """
    try:
        # ID проєкту GCP автоматично доступний у середовищі Cloud Run
        project_id = os.environ.get("GCP_PROJECT")
        # Назва секрету, яку ви створили в Secret Manager
        secret_name = "gcp-service-account-json" 

        if not project_id:
            logging.error("Змінна середовища GCP_PROJECT не встановлена.")
            raise ValueError("Не вдалося визначити ID проєкту Google Cloud.")

        # Створюємо клієнт для доступу до Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        
        # Формуємо повний шлях до останньої версії секрету
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        logging.info(f"Запит до Secret Manager для отримання секрету: {secret_name}")
        # Отримуємо доступ до секрету
        response = client.access_secret_version(request={"name": name})
        
        # Декодуємо дані секрету (це буде вміст вашого JSON-файлу)
        creds_json_str = response.payload.data.decode("UTF-8")
        creds_info = json.loads(creds_json_str)
        
        # Створюємо об'єкт credentials
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        logging.info("Облікові дані успішно отримано з Secret Manager.")
        return credentials

    except Exception as e:
        logging.error(f"Помилка під час отримання облікових даних з Secret Manager: {e}", exc_info=True)
        return None


def _get_gspread_client() -> Optional[gspread.Client]:
    """
    Ініціалізує gspread клієнт, використовуючи облікові дані з Secret Manager.
    """
    global _gspread_client
    if _gspread_client is None:
        try:
            logging.info("Ініціалізація gspread клієнта...")
            # Отримуємо облікові дані
            credentials = _get_credentials_from_secret_manager()
            if credentials:
                # Ініціалізуємо клієнт gspread з отриманими даними
                _gspread_client = gspread.authorize(credentials)
                logging.info("Клієнт gspread успішно ініціалізовано.")
            else:
                raise Exception("Не вдалося отримати облікові дані для gspread.")
        except Exception as e:
            logging.error(f"Не вдалося ініціалізувати gspread клієнт: {e}", exc_info=True)
            return None
    return _gspread_client


def get_sheet_headers(sheet_id: str) -> List[str]:
    """Отримує тільки заголовки (перший рядок) з Google Sheet."""
    gc = _get_gspread_client()
    if not gc:
        raise Exception("Клієнт gspread не ініціалізовано")
    
    logging.info(f"Отримання заголовків для таблиці: {sheet_id}")
    return gc.open_by_key(sheet_id).sheet1.row_values(1)


def get_sheet_data(sheet_id: str, csv_file: Optional[Any] = None, column_mapping: Optional[Dict[str, str]] = None) -> Optional[List[Dict]]:
    """Отримує дані з Google Sheet або CSV-файлу."""
    try:
        if csv_file is not None:
            logging.info("Читання даних з завантаженого CSV-файлу.")
            df = pd.read_csv(csv_file)
            if column_mapping:
                df = df.rename(columns=column_mapping)
            return df.to_dict('records')
            
        elif sheet_id:
            logging.info(f"Отримання даних з Google Sheet: {sheet_id}")
            gc = _get_gspread_client()
            if not gc:
                return None
            
            data = gc.open_by_key(sheet_id).sheet1.get_all_records()
            
            if column_mapping:
                # Застосовуємо мапінг, якщо він є
                return [{column_mapping.get(k, k): v for k, v in row.items()} for row in data]
            return data
            
        return None
    except Exception as e:
        logging.error(f"Сталася помилка при отриманні даних: {e}", exc_info=True)
        return None
