# /workspaces/auto-report-generator/app/context_builder.py
import os
from dotenv import load_dotenv
# Припускаємо, що gpt_writer.py знаходиться в корені проекту
from gpt_writer import generate_summary_data 

# load_dotenv() тут може бути не обов'язковим, якщо GEMINI_API_KEY 
# встановлюється глобально або в gpt_writer.py
load_dotenv() 

# Внутрішні стандартні ключі, які ця функція очікує отримати в `record`
# після того, як дані були оброблені (наприклад, через мапування в gsheet.py)
# Ці ключі мають співпадати з ключами в EXPECTED_APP_FIELDS у run_app.py
INTERNAL_CLIENT_NAME_KEY = "client_name"
INTERNAL_TASK_KEY = "task"
INTERNAL_STATUS_KEY = "status"
INTERNAL_DATE_KEY = "date"
INTERNAL_COMMENTS_KEY = "comments"
INTERNAL_AMOUNT_KEY = "amount" # Приклад

def build_context(record: dict) -> dict:
    """
    Будує контекст для одного запису звіту, використовуючи стандартизовані ключі.
    Викликає Gemini для генерації резюме.
    """
    print(f"INFO: [context_builder.py] Building context for record: {record}")

    client_name = record.get(INTERNAL_CLIENT_NAME_KEY, "Невідомо")
    task = record.get(INTERNAL_TASK_KEY, "-")
    status = record.get(INTERNAL_STATUS_KEY, "-")
    date = record.get(INTERNAL_DATE_KEY, "-")
    comments = record.get(INTERNAL_COMMENTS_KEY, "")
    amount = record.get(INTERNAL_AMOUNT_KEY, 0) 

    summary_data_for_gemini = {
        # Передаємо дані для Gemini, використовуючи наші внутрішні ключі
        # Важливо, щоб Gemini отримував значущі дані
        "Клієнт": client_name,
        "Завдання": task,
        "Статус": status,
        "Коментарі": comments,
        "Дата": date
    }
    # Видаляємо порожні значення перед відправкою в Gemini, щоб не засмічувати промпт
    summary_data_for_gemini = {k: v for k, v in summary_data_for_gemini.items() if v and str(v).strip() and v != "-"}


    summary = "Резюме не вдалося згенерувати." # Значення за замовчуванням
    if summary_data_for_gemini: # Генеруємо саммарі, тільки якщо є дані
        try:
            summary = generate_summary_data(summary_data_for_gemini)
        except Exception as e:
            print(f"ERROR: [context_builder.py] Failed to generate summary using Gemini: {e}")
            # traceback.print_exc() # Можна додати для детального логування
    else:
        print("INFO: [context_builder.py] Not enough data to generate summary with Gemini.")
        summary = "Недостатньо даних для автоматичного резюме."


    context = {
        "title": "Автоматичний звіт", 
        "client": client_name,
        "task": task,
        "status": status,
        "summary": summary, 
        "comments": comments,
        "date": date,
        "amount": amount 
    }
    print(f"INFO: [context_builder.py] Context built: {{'client': '{client_name}', 'task': '{task[:20]}...'}}")
    return context