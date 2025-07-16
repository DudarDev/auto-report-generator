# /workspaces/auto-report-generator/app/context_builder.py
import logging
from typing import Dict
# ВИПРАВЛЕНО: відносні імпорти
from app.config import APP_INTERNAL_KEYS
from app.gpt_writer import generate_summary_data

def build_context(record: Dict) -> Dict:
    """Створює повний контекст для одного запису, включаючи висновок від Gemini."""
    if not isinstance(record, dict):
        logging.error(f"Очікувався словник, але отримано {type(record)}")
        return {}
    # ... решта коду функції залишається без змін ...
    client_name = record.get("client_name", "Невідомо")
    task = record.get("task", "-")
    status = record.get("status", "-")
    date_val = record.get("date", "-")
    comments = record.get("comments", "")
    amount = record.get("amount", 0)
    data_for_summary = { "Клієнт": client_name, "Завдання": task, "Статус": status, "Коментарі": comments, "Дата": date_val }
    data_for_summary = {k: v for k, v in data_for_summary.items() if v and str(v).strip() and str(v) != "-"}
    summary = "Недостатньо даних для автоматичного висновку."
    if data_for_summary:
        try:
            summary = generate_summary_data(data_for_summary)
        except Exception as e:
            summary = "Помилка під час генерації висновку."
    context = { "title": "Автоматичний звіт", "client": client_name, "task": task, "status": status, "summary": summary, "comments": comments, "date": date_val, "amount": amount }
    logging.info(f"Контекст успішно створено для клієнта: '{client_name}'")
    return context