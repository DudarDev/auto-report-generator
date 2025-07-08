# /workspaces/auto-report-generator/app/gpt_writer.py
import os
import traceback
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Глобальна змінна для зберігання моделі, щоб не ініціалізувати її щоразу
_model = None

def _initialize_gemini_model():
    """
    Внутрішня функція для одноразової ініціалізації моделі Gemini.
    """
    global _model
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: [gpt_writer.py] GEMINI_API_KEY not found in environment variables.")
        return False

    try:
        print("INFO: [gpt_writer.py] Configuring Gemini API...")
        genai.configure(api_key=api_key)
        
        model_name = os.getenv("GEMINI_MODEL_NAME", 'models/gemini-1.5-pro-latest')
        _model = genai.GenerativeModel(model_name)
        
        print(f"SUCCESS: [gpt_writer.py] Gemini model '{model_name}' initialized.")
        return True
    except Exception as e:
        print(f"ERROR: [gpt_writer.py] Failed to initialize Gemini model: {e}")
        traceback.print_exc()
        return False

def generate_summary_data(data_for_summary: dict) -> str:
    """
    Генерує короткий аналітичний звіт. Ініціалізує модель Gemini при першому виклику.
    """
    global _model
    
    # "Лінива ініціалізація": створюємо модель тільки якщо її ще не існує.
    if _model is None:
        if not _initialize_gemini_model():
            return "Помилка: Не вдалося ініціалізувати модель Gemini. Перевірте API ключ."

    try:
        # Формуємо промпт (запит) для моделі
        prompt_parts = [f"{key}: {value}" for key, value in data_for_summary.items() if value and str(value).strip()]
        if not prompt_parts:
            return "Немає даних для генерації резюме."

        prompt_input_str = "; ".join(prompt_parts)
        prompt = f"Склади короткий аналітичний висновок українською мовою на основі таких даних: {prompt_input_str}."
        
        print(f"INFO: [gpt_writer.py] Generating summary with prompt: '{prompt[:100]}...'")
        response = _model.generate_content(prompt)
        
        summary_text = response.text
        print("INFO: [gpt_writer.py] Summary generated successfully.")
        return summary_text
    except Exception as e:
        print(f"ERROR: [gpt_writer.py] Error during content generation: {e}")
        traceback.print_exc()
        return f"Помилка під час генерації висновку: {e}"