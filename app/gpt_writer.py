# /workspaces/auto-report-generator/app/gpt_writer.py
import os
import traceback
import logging
import google.auth
from dotenv import load_dotenv

# ВИКОРИСТОВУЄМО БІБЛІОТЕКУ VERTEX AI
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()

_model_initialized = False

def _initialize_gemini_model():
    """
    Ініціалізує модель Gemini через Vertex AI, використовуючи явну
    автентифікацію сервісного акаунту.
    """
    global _model_initialized
    
    try:
        logging.info("Ініціалізація Gemini моделі через Vertex AI...")
        
        # 1. Отримуємо облікові дані з середовища (так само, як для gsheet)
        creds, project_id = google.auth.default()

        # 2. Ініціалізуємо клієнт Vertex AI
        vertexai.init(project=project_id, credentials=creds, location="europe-west1")
        
        _model_initialized = True
        logging.info("SUCCESS: Клієнт Vertex AI успішно ініціалізовано.")
        return True

    except Exception as e:
        logging.error(f"ERROR: Не вдалося ініціалізувати Vertex AI: {e}", exc_info=True)
        return False

def generate_summary_data(data_for_summary: dict) -> str:
    """ Генерує короткий аналітичний звіт. """
    global _model_initialized
    
    if not _model_initialized:
        if not _initialize_gemini_model():
            return "Помилка: Не вдалося ініціалізувати модель Gemini."

    try:
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-001")
        model = GenerativeModel.from_pretrained(model_name)
        
        prompt_parts = [f"{key}: {value}" for key, value in data_for_summary.items() if value and str(value).strip() and str(value) != "-"]
        if not prompt_parts:
            return "Немає даних для генерації резюме."

        prompt_input_str = "; ".join(prompt_parts)
        prompt = f"Склади короткий аналітичний висновок українською мовою на основі таких даних: {prompt_input_str}."
        
        logging.info(f"INFO: Генерація висновку з промптом: '{prompt[:100]}...'")
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        logging.error(f"ERROR: Помилка під час генерації висновку: {e}", exc_info=True)
        return f"Помилка під час генерації висновку: {e}"