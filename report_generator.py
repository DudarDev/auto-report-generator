import os
from datetime import datetime
from dotenv import load_dotenv
from gsheet import get_sheet_data
from pdf_generator import generate_pdf
from email_sender import send_email
from zipper import zip_reports
from context_builder import build_context

load_dotenv()

def generate_and_send_report(email=None):
    # 🔹 Отримуємо сьогоднішню дату
    today = datetime.now().strftime("%Y-%m-%d")

    # 🔹 Формуємо динамічні шляхи
    BASE_REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
    REPORTS_DIR = os.path.join(BASE_REPORTS_DIR, today)
    ZIP_NAME = os.getenv("ZIP_NAME", f"all_reports_{today}.zip")

    # 🔹 Створюємо папку для збереження
    os.makedirs(REPORTS_DIR, exist_ok=True)

    data = get_sheet_data()
    pdf_paths = []

    for i, record in enumerate(data):
        context = build_context(record)
        filename = os.path.join(REPORTS_DIR, f"report_{i+1}_{context['client']}.pdf")
        generate_pdf(context, filename)
        print(f"[✔] Звіт збережено: {filename}")
        pdf_paths.append(filename)

    zip_reports(pdf_paths, ZIP_NAME)

    if email:
        send_email(ZIP_NAME, recipient=email)
    else:
        send_email(ZIP_NAME)
