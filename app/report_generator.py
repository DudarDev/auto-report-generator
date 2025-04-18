import os
from datetime import datetime
from dotenv import load_dotenv

from app.gsheet import get_sheet_data
from app.pdf_generator import generate_pdf
from app.email_sender import send_email
from app.zipper import zip_reports
from app.context_builder import build_context

# Завантаження змінних середовища з .env
load_dotenv()

def generate_and_send_report(email: str | None = None) -> None:
    """Генерує PDF-звіти з Google Sheets, архівує їх і надсилає на email"""

    # 📅 Отримуємо сьогоднішню дату
    today = datetime.now().strftime("%Y-%m-%d")

    # 📂 Формуємо шляхи до директорій і файлів
    base_dir = os.getenv("REPORTS_DIR", "reports")
    reports_dir = os.path.join(base_dir, today)
    zip_name = os.getenv("ZIP_NAME", f"all_reports_{today}.zip")

    # 🗂 Створюємо папку, якщо не існує
    os.makedirs(reports_dir, exist_ok=True)

    # 🔄 Отримуємо всі записи з таблиці
    data = get_sheet_data()
    pdf_paths = []

    for i, record in enumerate(data):
        context = build_context(record)
        filename = os.path.join(reports_dir, f"report_{i+1}_{context['client']}.pdf")
        generate_pdf(context, filename)
        print(f"[✅] Звіт збережено: {filename}")
        pdf_paths.append(filename)

    # 🗜 Архівуємо всі звіти
    zip_reports(pdf_paths, zip_name)

    # 📧 Надсилаємо на пошту
    if email:
        send_email(zip_name, recipient=email)
    else:
        send_email(zip_name)
