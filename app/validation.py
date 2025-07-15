# /workspaces/auto-report-generator/app/validation.py

from typing import Dict, Any, Tuple

# Імпортуємо очікувані ключі, щоб порівняти з тим, що надав користувач
from .config import APP_INTERNAL_KEYS

def validate_inputs(
    texts: Dict, 
    sheet_id: str, 
    csv_file: Any, 
    email: str, 
    mapping: Dict
) -> Tuple[bool, str]:
    """
    Перевіряє, чи коректно заповнені всі поля перед генерацією звіту.
    Повертає кортеж (is_valid, error_message).
    """

    # --- 1. Перевірка Email ---
    # Перевіряємо, чи поле не порожнє і чи є в ньому символ '@'
    if not email or "@" not in email:
        return False, texts.get("error_invalid_email", "Будь ласка, введіть коректний Email.")

    # --- 2. Перевірка Джерела Даних ---
    # Перевіряємо, чи надано хоча б одне джерело даних
    if not sheet_id and not csv_file:
        return False, texts.get("error_no_data_source", "Будь ласка, введіть ID таблиці або завантажте CSV-файл.")

    # --- 3. Перевірка Зіставлення Полів (мапінгу) ---
    # Перевіряємо, чи всі необхідні поля були зіставлені користувачем.
    # Це надійніше, ніж просто перевіряти наявність None.
    if len(mapping) < len(APP_INTERNAL_KEYS):
        return False, texts.get("error_mapping_incomplete", "Будь ласка, зіставте всі необхідні поля.")

    # --- Успіх ---
    # Якщо всі перевірки пройшли, повертаємо успішний результат
    return True, ""