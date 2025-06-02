# /workspaces/auto-report-generator/gpt_writer.py
import os
from dotenv import load_dotenv
import google.generativeai as genai
import traceback # Для детального виводу помилок

load_dotenv() 

GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", 'models/gemini-1.5-pro-latest') # Можна теж винести в env

model = None 

print(f"INFO: [gpt_writer.py] Attempting to load Gemini API key from env var '{GEMINI_API_KEY_ENV_VAR}'...")
gemini_api_key = os.getenv(GEMINI_API_KEY_ENV_VAR)

if gemini_api_key:
    try:
        print(f"INFO: [gpt_writer.py] Configuring Gemini API with key.")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(MODEL_NAME)
        print(f"SUCCESS: [gpt_writer.py] Gemini API model '{MODEL_NAME}' initialized.")
    except Exception as e:
        print(f"ERROR: [gpt_writer.py] Failed to configure Gemini API or initialize model: {e}")
        traceback.print_exc()
else:
    print(f"WARNING: [gpt_writer.py] Environment variable '{GEMINI_API_KEY_ENV_VAR}' not found. Gemini functionality will be unavailable.")

# Ось функція з правильною назвою
def generate_summary_data(data_for_summary: dict) -> str:
    """
    Генерує короткий аналітичний звіт на основі наданих даних за допомогою Gemini API.
    """
    global model # Вказуємо, що використовуємо глобальну змінну model
    if not model:
        error_message = "ERROR: [gpt_writer.py] Gemini model is not initialized. Cannot generate summary."
        print(error_message)
        return "Помилка: Модель Gemini не ініціалізована."

    try:
        # Формуємо промпт зі словника даних
        prompt_parts = []
        for key, value in data_for_summary.items():
            if value and str(value).strip(): # Додаємо тільки непусті значення
                prompt_parts.append(f"{key}: {value}")
        
        if not prompt_parts:
            print("WARNING: [gpt_writer.py] No data provided for summary generation prompt.")
            return "Немає даних для генерації резюме."

        prompt_input_str = "; ".join(prompt_parts)
        prompt = f"Склади короткий аналітичний звіт українською мовою на основі таких даних: {prompt_input_str}."
        
        print(f"INFO: [gpt_writer.py] Generating summary with prompt (first 100 chars): '{prompt[:100]}...'")
        response = model.generate_content(prompt)
        # Перевірка, чи є текст у відповіді (залежить від структури response об'єкта)
        summary_text = response.text if hasattr(response, 'text') else str(response) 
        print("INFO: [gpt_writer.py] Summary generated successfully.")
        return summary_text
    except Exception as e:
        print(f"ERROR: [gpt_writer.py] Error during Gemini content generation: {e}")
        traceback.print_exc()
        return f"Помилка під час генерації резюме Gemini: {e}"