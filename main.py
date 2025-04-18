from dotenv import load_dotenv
from app.gsheet import get_sheet_data
from app.pdf_generator import generate_pdf
from app.email_sender import send_email
from app.zipper import zip_reports
from app.context_builder import build_context
import os

load_dotenv()

REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
ZIP_NAME = os.getenv("ZIP_NAME", "all_reports.zip")

os.makedirs(REPORTS_DIR, exist_ok=True)

data = get_sheet_data()
pdf_paths = []

for i, record in enumerate(data):
    context = build_context(record)
    filename = f"{REPORTS_DIR}/report_{i+1}_{context['client']}.pdf"
    generate_pdf(context, filename)
    print(f"[✓] Звіт збережено: {filename}")
    pdf_paths.append(filename)

zip_reports(pdf_paths, ZIP_NAME)
send_email(ZIP_NAME)
