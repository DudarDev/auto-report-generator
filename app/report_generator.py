# /workspaces/auto-report-generator/app/report_generator.py
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Tuple
import traceback

from app.gsheet import get_sheet_data
from app.pdf_generator import generate_pdf
from app.email_sender import send_email
from app.zipper import zip_reports
from app.context_builder import build_context

load_dotenv()
print(f"INFO: [report_generator.py] Module loaded. Attempted to load .env file.")

def generate_and_send_report(email: Optional[str] = None,
                             sheet_id: Optional[str] = None,
                             csv_file: Optional[Any] = None,
                             column_mapping: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:

    print(f"INFO: [report_generator.py] Received request: email='{email}', sheet_id='{sheet_id}', csv_file is {'provided' if csv_file else 'not provided'}, mapping: {column_mapping}")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        base_dir_from_env = os.getenv("REPORTS_DIR", "reports")
        base_dir = os.path.join(project_root, base_dir_from_env)
        reports_dir_for_today = os.path.join(base_dir, today)
        zip_name_only = os.getenv("ZIP_NAME", f"all_reports_{today}.zip")
        zip_full_path = os.path.join(reports_dir_for_today, zip_name_only)

        os.makedirs(reports_dir_for_today, exist_ok=True)
        print(f"INFO: [report_generator.py] Reports directory: {reports_dir_for_today}, ZIP path: {zip_full_path}")

        data = None
        if sheet_id:
            print(f"INFO: [report_generator.py] Attempting to get data using sheet_id: {sheet_id}")
            data = get_sheet_data(sheet_id=sheet_id, column_mapping=column_mapping)
        elif csv_file:
            print(f"INFO: [report_generator.py] Attempting to get data using csv_file.")
            data = get_sheet_data(csv_file=csv_file, column_mapping=column_mapping)
        else:
            return False, "No data source (sheet_id or csv_file) provided."

        if data is None:
            return False, "Failed to retrieve data (data is None)."
        if not data and isinstance(data, list):
            print("WARNING: [report_generator.py] No data records found. Nothing to process.")
            return True, "No data records found to process."

        print(f"INFO: [report_generator.py] Data received. Starting PDF generation for {len(data)} records.")
        pdf_paths = []
        for i, record in enumerate(data):
            record_identifier = str(record.get("client_name", f"record_{i+1}"))
            print(f"INFO: [report_generator.py] Processing record {i+1}/{len(data)} for '{record_identifier}'...")
            try:
                context = build_context(record)
                client_name_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in str(context.get('client', f'UnknownClient_{i+1}')))
                pdf_filename = os.path.join(reports_dir_for_today, f"report_{i+1}_{client_name_sanitized.replace(' ', '_')}.pdf")

                generate_pdf(context, pdf_filename)
                print(f"  [✅] PDF report saved: {pdf_filename}")
                pdf_paths.append(pdf_filename)
            except Exception as e_record:
                print(f"ERROR: [report_generator.py] Error processing record {i+1} ('{record_identifier}'): {e_record}")
                traceback.print_exc()
                continue

        if not pdf_paths:
            return False, "No PDF reports were generated. Aborting."

        print(f"INFO: [report_generator.py] Zipping {len(pdf_paths)} PDF reports into: {zip_full_path}")
        zip_reports(pdf_paths, zip_full_path)

        # +++ НАЧАЛО ИСПРАВЛЕННОГО БЛОКА +++
        email_recipient_to_use = email or os.getenv("EMAIL_TO_DEFAULT")
        if email_recipient_to_use:
            print(f"INFO: [report_generator.py] Attempting to send email with archive {zip_full_path} to {email_recipient_to_use}")

            # Определяем тему и тело письма
            subject = f"Ваші звіти за {today}"
            body = "Вітаю! У вкладенні ви знайдете автоматично згенеровані звіти."

            # ВЫЗЫВАЕМ ФУНКЦИЮ С ПРАВИЛЬНЫМИ АРГУМЕНТАМИ
            email_sent_successfully, error_message = send_email(
                email_to=email_recipient_to_use,
                subject=subject,
                body=body,
                attachment_path=zip_full_path
            )

            if not email_sent_successfully:
                print(f"ERROR: [report_generator.py] Email sending process reported as failed for {email_recipient_to_use}. Details: {error_message}")
        else:
            print("WARNING: [report_generator.py] No recipient email and no default. Email not sent.")
        # +++ КОНЕЦ ИСПРАВЛЕННОГО БЛОКА +++

        return True, "Reports generated and sent successfully."

    except Exception as e_main:
        print(f"CRITICAL ERROR in generate_and_send_report: {e_main}")
        traceback.print_exc()