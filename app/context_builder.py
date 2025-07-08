# /workspaces/auto-report-generator/app/context_builder.py
import logging
import traceback
from typing import Dict

# Імпортуємо конфігурацію
from app.config import APP_INTERNAL_KEYS

# Намагаємося імпортувати функцію з gpt_writer.
# Якщо імпорт не вдасться (напр. не встановлена бібліотека),
# створюється функція-заглушка, щоб програма не "впала".
try:
    from app.gpt_writer import generate_summary_data
except ImportError:
    logging.error("Не вдалося імпортувати generate_summary_data з app.gpt_writer.")
    def generate_summary_data(data_for_summary: dict) -> str:
        return "Помилка: Модуль gpt_writer не завантажено."

def build_context(record: Dict) -> Dict:
    """
    Створює повний контекст для одного запису, включаючи висновок від Gemini.
    """
    if not isinstance(record, dict):
        logging.error(f"Очікувався словник, але отримано {type(record)}")
        return {}

    logging.info(f"Створення контексту для запису: { {k: record.get(k) for k in APP_INTERNAL_KEYS[:3] if k in record} }")

    # Безпечно отримуємо дані з запису
    client_name = record.get("client_name", "Невідомо")
    task = record.get("task", "-")
    status = record.get("status", "-")
    date_val = record.get("date", "-")
    comments = record.get("comments", "")
    amount = record.get("amount", 0)

    # Готуємо дані для відправки в AI, виключаючи порожні поля
    data_for_summary = {
        "Клієнт": client_name,
        "Завдання": task,
        "Статус": status,
        "Коментарі": comments,
        "Дата": date_val
    }
    data_for_summary = {k: v for k, v in data_for_summary.items() if v and str(v).strip() and str(v) != "-"}

    # Генеруємо висновок (summary)
    summary = "Недостатньо даних для автоматичного висновку."
    if data_for_summary:
        try:
            logging.info(f"Виклик Gemini для генерації висновку з даними: {data_for_summary}")
            summary = generate_summary_data(data_for_summary)
        except Exception as e:
            logging.error(f"Помилка генерації висновку: {e}", exc_info=True)
            summary = "Помилка під час генерації висновку."

    # Збираємо фінальний контекст для передачі у PDF-шаблон
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
    
    logging.info(f"Контекст успішно створено для клієнта: '{client_name}'")
    return context