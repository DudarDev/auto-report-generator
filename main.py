# /workspaces/auto-report-generator/main.py
import os
import json
from dotenv import load_dotenv
import traceback
from datetime import datetime

# Завантажуємо змінні середовища для локального запуску.
# На Cloud Run вони будуть підставлені з Secret Manager.
load_dotenv()
print(f"INFO: [{os.path.basename(__file__)}] Attempted to load .env file.")

# Перевірка важливих секретів (просто для логування при старті)
if not os.environ.get('GEMINI_API_KEY'):
    print(f"WARNING: [{os.path.basename(__file__)}] GEMINI_API_KEY environment variable not found.")

# Імпорти ваших модулів програми
from app.gsheet import get_sheet_data
from app.pdf_generator import generate_pdf
from app.email_sender import send_email
from app.zipper import zip_reports
from app.context_builder import build_context

def run_main_processing():
    """Основна логіка для main.py"""
    print("INFO: [main.py] Starting main report generation process...")

    try:
        # 📅 Отримуємо сьогоднішню дату
        today = datetime.now().strftime("%Y-%m-%d")

        # 📂 Формуємо шляхи до директорій і файлів
        project_root = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
        base_dir_from_env = os.getenv("REPORTS_DIR", "reports")
        base_dir = os.path.join(project_root, base_dir_from_env)
        
        reports_dir_for_today = os.path.join(base_dir, today)
        zip_name_only = os.getenv("ZIP_NAME", f"all_reports_{today}.zip")
        zip_full_path = os.path.join(reports_dir_for_today, zip_name_only)

        os.makedirs(reports_dir_for_today, exist_ok=True)
        print(f"INFO: [main.py] Reports directory: {reports_dir_for_today}")
        print(f"INFO: [main.py] ZIP archive path: {zip_full_path}")

        # 🔄 Отримуємо дані з Google Sheet
        sheet_id_to_use = os.getenv("GOOGLE_SHEET_ID")
        if not sheet_id_to_use:
            print("ERROR: [main.py] GOOGLE_SHEET_ID environment variable not set. Cannot fetch sheet data.")
            return

        print(f"INFO: [main.py] Fetching data from Google Sheet ID: {sheet_id_to_use}")
        data = get_sheet_data(sheet_id=sheet_id_to_use, csv_file=None, column_mapping=None)

        if data is None:
            print("ERROR: [main.py] Failed to retrieve data from Google Sheet. Aborting.")
            return
        if not data and isinstance(data, list):
            print("WARNING: [main.py] No data records found in the Google Sheet. Nothing to process.")
            return

        print(f"INFO: [main.py] Data received, {len(data)} records. Starting PDF generation...")
        pdf_paths = []
        for i, record in enumerate(data):
            record_identifier = str(record.get("client_name", record.get("id", f"record_{i+1}")))
            print(f"INFO: [main.py] Processing record {i+1}/{len(data)} for '{record_identifier}'...")
            try:
                context = build_context(record)
                client_name_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in str(context.get('client', f'UnknownClient_{i+1}')))
                filename = os.path.join(reports_dir_for_today, f"report_{i+1}_{client_name_sanitized.replace(' ', '_')}.pdf")
                
                generate_pdf(context, filename)
                print(f"  [✅] Звіт збережено: {filename}")
                pdf_paths.append(filename)
            except Exception as e_record:
                print(f"ERROR: [main.py] Error processing record {i+1} ('{record_identifier}'): {e_record}")
                traceback.print_exc()
                continue

        if not pdf_paths:
            print("ERROR: [main.py] No PDF reports were generated. Aborting email send.")
            return

        print(f"INFO: [main.py] Zipping {len(pdf_paths)} PDF reports into: {zip_full_path}")
        zip_reports(pdf_paths, zip_full_path)

        # 📧 Надсилаємо на пошту
        email_recipient = os.getenv("EMAIL_MAIN_PY_RECIPIENT", os.getenv("EMAIL_TO_DEFAULT"))
        if not email_recipient:
            print("WARNING: [main.py] No recipient email configured. Email not sent.")
        else:
            print(f"INFO: [main.py] Attempting to send email with archive {zip_full_path} to {email_recipient}")
            # Припускаємо, що send_email тепер приймає стандартизовані аргументи
            subject = f"Щоденний звіт за {today}"
            body = "Архів зі звітами у вкладенні."
            email_sent, error_msg = send_email(email_to=email_recipient, subject=subject, body=body, attachment_path=zip_full_path)
            
            if email_sent:
                print(f"SUCCESS: [main.py] Email process reported as successful for {email_recipient}.")
            else:
                print(f"ERROR: [main.py] Email sending process reported as failed for {email_recipient}. Details: {error_msg}")
        
        print("INFO: [main.py] Main processing finished.")

    except Exception as e:
        print(f"CRITICAL ERROR in main.py run_main_processing: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_main_processing()