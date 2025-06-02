# /workspaces/auto-report-generator/app/report_generator.py
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any # <--- ДОДАЙТЕ ЦЕЙ РЯДОК

# Переконайтеся, що ці імпорти правильні і ведуть до ваших модулів
from app.gsheet import get_sheet_data # <--- ДОДАЙТЕ ЦЕЙ РЯДОК
from app.pdf_generator import generate_pdf
from app.email_sender import send_email
from app.zipper import zip_reports
from app.context_builder import build_context

# Завантаження змінних середовища з .env (залишаємо для локальної розробки)
load_dotenv()

# Оновлене визначення функції
def generate_and_send_report(email: Optional[str] = None, 
                             sheet_id: Optional[str] = None, 
                             csv_file: Optional[Any] = None, # Тип UploadedFile Streamlit
                             column_mapping: Optional[Dict[str, str]] = None) -> None:
    # ... (початок функції, шляхи, створення папок - залишається) ...
    print(f"INFO: [report_generator.py] Received request with mapping: {column_mapping}")

    data = None
    if sheet_id:
        print(f"INFO: [report_generator.py] Getting data using sheet_id: {sheet_id}")
        # Для Google Sheets, якщо ви теж хочете мапування, логіка буде складніша
        # Поки припустимо, що Google Sheet має фіксовані стовпці або використовує env vars для назв
        data = get_sheet_data(sheet_id=sheet_id) 
    elif csv_file:
        print(f"INFO: [report_generator.py] Getting data using csv_file with mapping.")
        data = get_sheet_data(csv_file=csv_file, column_mapping=column_mapping) # Передаємо мапування
    # ... (решта логіки обробки data, генерації PDF, архівування, надсилання email - залишається) ...
    # АЛЕ, build_context тепер буде отримувати дані вже з правильними ключами,
    # якщо get_sheet_data (для CSV) правильно застосує мапування.