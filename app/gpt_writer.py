# /workspaces/auto-report-generator/app/gpt_writer.py
import os
import traceback
import logging
import google.auth
import google.auth.transport.requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_model = None

def _initialize_gemini_model():
    """
    Ініціалізує модель Gemini, використовуючи явну автентифікацію
    через Application Default Credentials (ADC).
    """
    global _model
    
    try:
        logging.info("Ініціалізація Gemini моделі через google-auth...")
        
        # Явно отримуємо облікові дані з середовища Cloud Run
        creds, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Створюємо автентифіковану сесію
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        
        # Ініціалізуємо модель, передаючи їй дані для автентифікації
        genai.configure(api_key=None, transport='rest', client_options={'credentials': creds})

        model_name = os.getenv("GEMINI_MODEL_NAME", 'models/gemini-1.5-pro-latest')
        _model = genai.GenerativeModel(model_name)
        
        logging.info(f"SUCCESS: Gemini модель '{model_name}' успішно ініціалізовано.")
        return True

    except Exception as e:
        logging.error(f"ERROR: Не вдалося ініціалізувати Gemini модель: {e}", exc_info=True)
        return False

def generate_summary_data(data_for_summary: dict) -> str:
    """
    Генерує короткий аналітичний звіт.
    """
    global _model
    
    if _model is None:
        if not _initialize_gemini_model():
            return "Помилка: Не вдалося ініціалізувати модель Gemini."

    try:
        prompt_parts = [f"{key}: {value}" for key, value in data_for_summary.items() if value and str(v).strip() and str(v) != "-"]
        if not prompt_parts:
            return "Немає даних для генерації резюме."

        prompt_input_str = "; ".join(prompt_parts)
        prompt = f"Склади короткий аналітичний висновок українською мовою на основі таких даних: {prompt_input_str}."
        
        logging.info(f"INFO: Генерація висновку з промптом: '{prompt[:100]}...'")
        response = _model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        logging.error(f"ERROR: Помилка під час генерації висновку: {e}", exc_info=True)
        return f"Помилка під час генерації висновку: {e}"