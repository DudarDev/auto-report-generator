# /workspaces/auto-report-generator/app/report_generator.py
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import traceback

# Переконайтеся, що ці імпорти правильні і ведуть до ваших модулів
from app.gsheet import get_sheet_data 
from app.pdf_generator import generate_pdf
from app.email_sender import send_email # Переконуємося, що імпортуємо саме цей
from app.zipper import zip_reports
from app.context_builder import build_context

load_dotenv()
print(f"INFO: [report_generator.py] Module loaded. Attempted to load .env file.")

def generate_and_send_report(email: Optional[str] = None, 
                             sheet_id: Optional[str] = None, 
                             csv_file: Optional[Any] = None,
                             column_mapping: Optional[Dict[str, str]] = None) -> None:
    
    print(f"INFO: [report_generator.py] Received request: email='{email}', sheet_id='{sheet_id}', csv_file is {'provided' if csv_file else 'not provided'}, mapping: {column_mapping}")

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        base_dir_from_env = os.getenv("REPORTS_DIR", "reports") # Директорія для звітів
        
        # Розрахунок кореневого каталогу проекту (на один рівень вище від папки 'app')
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        base_dir = os.path.join(project_root, base_dir_from_env) # Повний шлях до папки reports
        
        reports_dir_for_today = os.path.join(base_dir, today) # Папка для звітів за сьогодні
        zip_name_only = os.getenv("ZIP_NAME", f"all_reports_{today}.zip")
        zip_full_path = os.path.join(reports_dir_for_today, zip_name_only)

        print(f"INFO: [report_generator.py] Base reports directory: {base_dir}")
        print(f"INFO: [report_generator.py] Today's reports directory: {reports_dir_for_today}")
        print(f"INFO: [report_generator.py] Expected ZIP archive path: {zip_full_path}")

        os.makedirs(reports_dir_for_today, exist_ok=True)
        print(f"INFO: [report_generator.py] Reports directory ensured: {reports_dir_for_today}")

        data = None
        if sheet_id:
            print(f"INFO: [report_generator.py] Attempting to get data using sheet_id: {sheet_id}")
            data = get_sheet_data(sheet_id=sheet_id, column_mapping=column_mapping) # Передаємо мапування і для Sheets
        elif csv_file:
            print(f"INFO: [report_generator.py] Attempting to get data using csv_file.")
            data = get_sheet_data(csv_file=csv_file, column_mapping=column_mapping)
        else:
            error_msg = "No data source (sheet_id or csv_file) provided."
            print(f"ERROR: [report_generator.py] {error_msg}")
            raise ValueError(error_msg)

        if data is None:
            error_msg = "Failed to retrieve data (data is None)."
            print(f"ERROR: [report_generator.py] {error_msg}")
            raise ValueError(error_msg)
        
        if not data and isinstance(data, list):
            print("WARNING: [report_generator.py] No data records found in the source. Nothing to process.")
            return # Виходимо, якщо немає даних

        print(f"INFO: [report_generator.py] Data received. Starting PDF generation for {len(data)} records.")
        pdf_paths = []
        for i, record in enumerate(data):
            record_identifier = str(record.get("client_name", record.get("id", f"record_{i+1}"))) # Для логування
            print(f"INFO: [report_generator.py] Processing record {i+1}/{len(data)}: (first few fields) { {k: record.get(k) for k in list(record)[:3]} }...")
            try:
                context = build_context(record)
                print(f"INFO: [report_generator.py] Context built for record {i+1}: client='{context.get('client', 'N/A')}'")
                
                client_name_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in str(context.get('client', f'UnknownClient_{i+1}')))
                pdf_filename = os.path.join(reports_dir_for_today, f"report_{i+1}_{client_name_sanitized.replace(' ', '_')}.pdf")
                
                generate_pdf(context, pdf_filename) 
                print(f"  [✅] PDF report saved: {pdf_filename}")
                pdf_paths.append(pdf_filename)
            except Exception as e_record:
                print(f"ERROR: [report_generator.py] Error processing record {i+1} ('{record_identifier}'): {e_record}")
                traceback.print_exc() 
                # Вирішіть, чи продовжувати обробку інших записів (тут продовжуємо)
                continue 
        
        if not pdf_paths:
            error_msg = "No PDF reports were generated. Aborting."
            print(f"ERROR: [report_generator.py] {error_msg}")
            raise ValueError(error_msg)

        print(f"INFO: [report_generator.py] Zipping {len(pdf_paths)} PDF reports into: {zip_full_path}")
        zip_reports(pdf_paths, zip_full_path) 
        # Лог про створення архіву вже є всередині zip_reports, якщо ви його там залишили

        email_recipient_to_use = email or os.getenv("EMAIL_TO_DEFAULT")
        if email_recipient_to_use:
            print(f"INFO: [report_generator.py] Attempting to send email with archive {zip_full_path} to {email_recipient_to_use}")
            email_sent_successfully = send_email(file_path=zip_full_path, recipient=email_recipient_to_use)
            if email_sent_successfully:
                print(f"SUCCESS: [report_generator.py] Email process reported as successful for {email_recipient_to_use}.")
            else:
                print(f"ERROR: [report_generator.py] Email sending process reported as failed for {email_recipient_to_use} (check email_sender.py logs).")
        else:
            print("WARNING: [report_generator.py] No recipient email provided and no default. Email will not be sent.")
        
        print("INFO: [report_generator.py] generate_and_send_report finished.")

    except ValueError as ve: # Обробка наших власних помилок ValueError
        print(f"ERROR: [report_generator.py] Data validation or critical error: {ve}")
        traceback.print_exc()
        raise # Перекидаємо помилку далі, щоб Streamlit міг її коректно показати
    except Exception as e_main: # Інші непередбачені помилки
        print(f"CRITICAL ERROR in generate_and_send_report: {e_main}")
        traceback.print_exc()
        raise