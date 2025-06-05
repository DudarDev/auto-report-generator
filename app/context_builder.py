# /workspaces/auto-report-generator/app/context_builder.py
import os
from dotenv import load_dotenv
import traceback

# Імпортуємо APP_INTERNAL_KEYS з центрального конфігураційного файлу
from app.config_fields import APP_INTERNAL_KEYS # Змінено на абсолютний імпорт

try:
    from gpt_writer import generate_summary_data 
except ImportError:
    print("ERROR: [context_builder.py] Failed to import generate_summary_data from gpt_writer.py.")
    def generate_summary_data(data_for_summary: dict) -> str:
        return "Помилка: Модуль gpt_writer не завантажено."
load_dotenv() 

def build_context(record: dict) -> dict:
    # ... (код build_context() залишається таким, як я надавав раніше, 
    #      переконайтеся, що він використовує імпортований APP_INTERNAL_KEYS 
    #      для отримання значень з record, наприклад:
    #      client_name = record.get(APP_INTERNAL_KEYS[0], "Невідомо") ) ...
    # Ось повний код для context_builder.py з попереднього разу, з виправленим імпортом:
    if not isinstance(record, dict):
        print(f"ERROR: [context_builder.py] Expected a dictionary for 'record', but got {type(record)}")
        return {"title": "Помилка обробки запису", "client": "Н/Д", "task": "Н/Д", "status": "Н/Д", "summary": "Невірний формат запису", "comments": "", "date": "", "amount": 0}

    print(f"INFO: [context_builder.py] Building context for record (first 3 keys from APP_INTERNAL_KEYS): { {k: record.get(k) for k in APP_INTERNAL_KEYS[:3]} }...")

    client_name = record.get(APP_INTERNAL_KEYS[APP_INTERNAL_KEYS.index("client_name")], "Невідомо") if "client_name" in APP_INTERNAL_KEYS else "Невідомо"
    task = record.get(APP_INTERNAL_KEYS[APP_INTERNAL_KEYS.index("task")], "-") if "task" in APP_INTERNAL_KEYS else "-"
    status = record.get(APP_INTERNAL_KEYS[APP_INTERNAL_KEYS.index("status")], "-") if "status" in APP_INTERNAL_KEYS else "-"
    date_val = record.get(APP_INTERNAL_KEYS[APP_INTERNAL_KEYS.index("date")], "-") if "date" in APP_INTERNAL_KEYS else "-"
    comments = record.get(APP_INTERNAL_KEYS[APP_INTERNAL_KEYS.index("comments")], "") if "comments" in APP_INTERNAL_KEYS else ""
    amount = record.get(APP_INTERNAL_KEYS[APP_INTERNAL_KEYS.index("amount")], 0) if "amount" in APP_INTERNAL_KEYS else 0

    summary_data_for_gemini = {
        "Клієнт": client_name, 
        "Завдання": task,
        "Статус": status,
        "Коментарі": comments,
        "Дата": date_val
    }
    summary_data_for_gemini = {k: v for k, v in summary_data_for_gemini.items() if v and str(v).strip() and str(v) != "-"}

    summary = "Резюме не вдалося згенерувати." 
    if summary_data_for_gemini: 
        try:
            print(f"INFO: [context_builder.py] Calling Gemini for summary with data: {summary_data_for_gemini}")
            summary = generate_summary_data(summary_data_for_gemini)
        except Exception as e:
            print(f"ERROR: [context_builder.py] Failed to generate summary using Gemini: {e}")
            traceback.print_exc()
    else:
        print("INFO: [context_builder.py] Not enough data for Gemini summary.")
        summary = "Недостатньо даних для автоматичного резюме."

    context = {
        "title": "Автоматичний звіт", 
        "client": client_name,
        "task": task,
        "status": status,
        "summary": summary, 
        "comments": comments,
        "date": date_val,
        "amount": amount 
    }
    print(f"INFO: [context_builder.py] Context built: {{'client': '{client_name}', 'task': '{str(task)[:20]}...'}}")
    return context
