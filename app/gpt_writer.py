# /workspaces/auto-report-generator/app/gpt_writer.py
import os
import traceback
import logging
import google.auth
from dotenv import load_dotenv

# Використовуємо бібліотеку Vertex AI для надійної роботи в хмарі
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()

_model_initialized = False

def _initialize_gemini_model():
    """
    Ініціалізує клієнт Vertex AI, використовуючи автентифікацію
    сервісного акаунту, прив'язаного до середовища Cloud Run.
    """
    global _model_initialized
    
    try:
        logging.info("Ініціалізація Gemini моделі через Vertex AI...")
        
        # Автоматично знаходимо доступи в середовищі Google Cloud
        creds, project_id = google.auth.default()

        # Ініціалізуємо клієнт Vertex AI
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
    
    # Виконуємо ініціалізацію тільки один раз
    if not _model_initialized:
        if not _initialize_gemini_model():
            return "Помилка: Не вдалося ініціалізувати модель Gemini."

    try:
        # ВИПРАВЛЕНО: Створюємо модель напряму, без .from_pretrained
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-001")
        model = GenerativeModel(model_name)
        
        # Формуємо запит до моделі
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