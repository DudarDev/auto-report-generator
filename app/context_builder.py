# /workspaces/auto-report-generator/app/context_builder.py
import os
from dotenv import load_dotenv
import traceback

# Якщо APP_INTERNAL_KEYS визначено в run_app.py і run_app.py в тій же папці 'app':
# from .run_app import APP_INTERNAL_KEYS
# Інакше, для узгодженості, визначте його тут так само, як у gsheet.py
# АБО створіть спільний config.py для таких констант
EXPECTED_INTERNAL_KEYS = ["client_name", "task", "status", "date", "comments", "amount"] 

try:
    from gpt_writer import generate_summary_data 
except ImportError:
    print("ERROR: [context_builder.py] Failed to import generate_summary_data from gpt_writer.py.")
    def generate_summary_data(data_for_summary: dict) -> str:
        return "Помилка: Модуль gpt_writer не завантажено."

load_dotenv() 

def build_context(record: dict) -> dict:
    if not isinstance(record, dict):
        print(f"ERROR: [context_builder.py] Expected a dictionary for 'record', but got {type(record)}")
        return {"title": "Помилка обробки запису", "client": "Н/Д", "task": "Н/Д", "status": "Н/Д", "summary": "Невірний формат запису", "comments": "", "date": "", "amount": 0}

    print(f"INFO: [context_builder.py] Building context for record (first 3 keys from EXPECTED): { {k: record.get(k) for k in EXPECTED_INTERNAL_KEYS[:3]} }...")

    client_name = record.get(EXPECTED_INTERNAL_KEYS[0], "Невідомо")
    task = record.get(EXPECTED_INTERNAL_KEYS[1], "-")
    status = record.get(EXPECTED_INTERNAL_KEYS[2], "-")
    date_val = record.get(EXPECTED_INTERNAL_KEYS[3], "-")
    comments = record.get(EXPECTED_INTERNAL_KEYS[4], "")
    amount = record.get(EXPECTED_INTERNAL_KEYS[5], 0) 

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
