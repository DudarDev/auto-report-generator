# /app/config.py

import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Встановлюємо базове логування
logging.basicConfig(level=logging.INFO)

# --- ЦЕ ЄДИНЕ МІСЦЕ, ДЕ ВІДБУВАЄТЬСЯ РОБОТА З .ENV ФАЙЛАМИ ---

# 1. Визначаємо поточне середовище (local, test), яке приходить з Makefile
APP_ENV = os.getenv('APP_ENV', 'local')
logging.info(f"✅ Запущено в середовищі: {APP_ENV}")

# 2. Завантажуємо загальні секрети з .env.local
load_dotenv(dotenv_path=Path('.') / '.env.local')

# 3. Динамічно обираємо назву файлу ключів
key_filename = ""
if APP_ENV == 'local':
    key_filename = "gcp_service_account_main.json"
elif APP_ENV == 'test':
    key_filename = "gcp_service_account_for_test.json"

# 4. Формуємо повний шлях до ключа і зберігаємо в Python-змінну
GOOGLE_APPLICATION_CREDENTIALS = ""
if key_filename:
    key_path = Path('.') / '.tmp' / key_filename
    if key_path.exists():
        GOOGLE_APPLICATION_CREDENTIALS = str(key_path.resolve())
        logging.info(f"🔑 Використовується ключ: {key_filename}")
    else:
        logging.error(f"🔴 ПОМИЛКА: Файл ключів не знайдено: {key_path}")
else:
    logging.warning(f"🟡 Увага: Для середовища '{APP_ENV}' ключ не визначено.")

# --- З ЦЬОГО МОМЕНТУ ВСІ НАЛАШТУВАННЯ - ЦЕ ПРОСТО ЗМІННІ PYTHON ---

# Завантажуємо решту змінних, які тепер доступні іншим модулям
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