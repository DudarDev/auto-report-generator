# /workspaces/auto-report-generator/main.py
import os
import json 
from dotenv import load_dotenv
import traceback # Для детального виводу помилок
from datetime import datetime # Потрібно для формування шляхів з датою

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ GOOGLE CLOUD CREDENTIALS ---
# Цей блок має бути після import os, json, load_dotenv
# і перед імпортами ваших модулів, що використовують GCP/Gemini

load_dotenv() 
print(f"INFO: [{os.path.basename(__file__)}] Attempted to load .env file.")

print(f"INFO: [{os.path.basename(__file__)}] Attempting to set up Google Cloud credentials...")
gcp_creds_json_string = os.environ.get('GOOGLE_CREDENTIALS_JSON') 

if gcp_creds_json_string:
    try:
        # Визначаємо корінь проекту (оскільки main.py в корені, це поточна директорія)
        project_root = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
        temp_dir = os.path.join(project_root, ".tmp") 
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            print(f"INFO: [{os.path.basename(__file__)}] Created directory: {temp_dir}")
        
        temp_creds_file_path = os.path.join(temp_dir, "gcp_service_account_main.json") # Унікальне ім'я

        with open(temp_creds_file_path, 'w') as temp_file:
            temp_file.write(gcp_creds_json_string)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_file_path 
        print(f"SUCCESS: [{os.path.basename(__file__)}] GOOGLE_APPLICATION_CREDENTIALS set to: {temp_creds_file_path}")
    except Exception as e:
        print(f"ERROR: [{os.path.basename(__file__)}] Failed to set up GCP credentials from env var 'GOOGLE_CREDENTIALS_JSON': {e}")
        traceback.print_exc()
else:
    print(f"WARNING: [{os.path.basename(__file__)}] GOOGLE_CREDENTIALS_JSON environment variable for Google Cloud not found.")

# Перевірка інших важливих секретів (просто для логування)
if not os.environ.get('GEMINI_API_KEY'):
    print(f"WARNING: [{os.path.basename(__file__)}] GEMINI_API_KEY environment variable not found.")
# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ GOOGLE CLOUD CREDENTIALS ---

# Імпорти ваших модулів програми ПІСЛЯ блоку ініціалізації
from app.gsheet import get_sheet_data
from app.pdf_generator import generate_pdf # Переконайтеся, що цей файл/функція існують
from app.email_sender import send_email
from app.zipper import zip_reports
from app.context_builder import build_context
# from app.report_generator import generate_and_send_report # Можна викликати цю функцію, якщо вона підходить

def run_main_processing():
    """Основна логіка для main.py"""
    print("INFO: [main.py] Starting main report generation process...")
    
    try:
        # 📅 Отримуємо сьогоднішню дату
        today = datetime.now().strftime("%Y-%m-%d")

        # 📂 Формуємо шляхи до директорій і файлів
        # Використовуємо абсолютні шляхи або шляхи відносно кореня проекту
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
        # Потрібно передати sheet_id. Беремо його з змінної середовища.
        sheet_id_to_use = os.getenv("GOOGLE_SHEET_ID")
        if not sheet_id_to_use:
            print("ERROR: [main.py] GOOGLE_SHEET_ID environment variable not set. Cannot fetch sheet data.")
            return

        print(f"INFO: [main.py] Fetching data from Google Sheet ID: {sheet_id_to_use}")
        # Припускаємо, що для main.py мапування не потрібне, або gsheet.py обробляє це
        # на основі назв стовпців у таблиці або інших змінних середовища для назв стовпців.
        data = get_sheet_data(sheet_id=sheet_id_to_use, csv_file=None, column_mapping=None) 

        if data is None: # get_sheet_data повертає None у разі помилки
            print("ERROR: [main.py] Failed to retrieve data from Google Sheet. Aborting.")
            return
        if not data and isinstance(data, list): # Порожній список
            print("WARNING: [main.py] No data records found in the Google Sheet. Nothing to process.")
            return

        print(f"INFO: [main.py] Data received, {len(data)} records. Starting PDF generation...")
        pdf_paths = []
        for i, record in enumerate(data):
            record_identifier = str(record.get("client_name", record.get("id", f"record_{i+1}")))
            print(f"INFO: [main.py] Processing record {i+1}/{len(data)} for '{record_identifier}'...")
            try:
                context = build_context(record) # context_builder має очікувати стандартизовані ключі
                
                client_name_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in str(context.get('client', f'UnknownClient_{i+1}')))
                filename = os.path.join(reports_dir_for_today, f"report_{i+1}_{client_name_sanitized.replace(' ', '_')}.pdf")
                
                generate_pdf(context, filename)
                print(f"  [✅] Звіт збережено: {filename}")
                pdf_paths.append(filename)
            except Exception as e_record:
                print(f"ERROR: [main.py] Error processing record {i+1} ('{record_identifier}'): {e_record}")
                traceback.print_exc()
                continue # Продовжуємо з наступним записом

        if not pdf_paths:
            print("ERROR: [main.py] No PDF reports were generated. Aborting email send.")
            return

        print(f"INFO: [main.py] Zipping {len(pdf_paths)} PDF reports into: {zip_full_path}")
        zip_reports(pdf_paths, zip_full_path)
        # Лог про створення архіву має бути всередині zip_reports

        # 📧 Надсилаємо на пошту
        # Визначаємо отримувача (наприклад, з змінної середовища)
        email_recipient = os.getenv("EMAIL_MAIN_PY_RECIPIENT", os.getenv("EMAIL_TO_DEFAULT"))
        if not email_recipient:
            print("WARNING: [main.py] No recipient email configured (EMAIL_MAIN_PY_RECIPIENT or EMAIL_TO_DEFAULT). Email not sent.")
        else:
            print(f"INFO: [main.py] Attempting to send email with archive {zip_full_path} to {email_recipient}")
            email_sent = send_email(file_path=zip_full_path, recipient=email_recipient)
            if email_sent:
                print(f"SUCCESS: [main.py] Email process reported as successful for {email_recipient}.")
            else:
                print(f"ERROR: [main.py] Email sending process reported as failed for {email_recipient}.")
        
        print("INFO: [main.py] Main processing finished.")

    except Exception as e:
        print(f"CRITICAL ERROR in main.py run_main_processing: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_main_processing()
