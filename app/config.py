# /app/config.py

import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Встановлюємо базове логування
logging.basicConfig(level=logging.INFO)

# --- РОБОТА З .ENV ФАЙЛАМИ ---

# 1. Визначаємо поточне середовище (наприклад, для локальної розробки)
APP_ENV = os.getenv('APP_ENV', 'local')
logging.info(f"✅ Запущено в середовищі: {APP_ENV}")

# 2. Завантажуємо секрети з .env.local (це корисно для локального запуску)
load_dotenv(dotenv_path=Path('.') / '.env.local')

# --- З ЦЬОГО МОМЕНТУ ВСІ НАЛАШТУВАННЯ - ЦЕ ПРОСТО ЗМІННІ PYTHON ---

# Завантажуємо решту змінних, які тепер доступні іншим модулям
# При деплої на Cloud Run ці змінні будуть взяті з Secret Manager, а не з .env
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')
EMAIL_USER = os.getenv('EMAIL_USER')

# Статичні конфігурації
APP_INTERNAL_KEYS = ["client_name", "task", "status", "date", "comments", "amount"]
SUPPORTED_LANGUAGES = {"Українська": "uk", "English": "en"}
EXPECTED_APP_FIELDS = {
    "client_name": "client_name_label",
    "task": "task_label",
    "status": "status_label",
    "date": "date_label",
    "comments": "comments_label",
    "amount": "amount_label"
}