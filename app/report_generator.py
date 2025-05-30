# /workspaces/auto-report-generator/app/report_generator.py
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional # Потрібно для типізації csv_file

# Переконайтеся, що ці імпорти правильні і ведуть до ваших модулів
from app.gsheet import get_sheet_data 
from app.pdf_generator import generate_pdf
from app.email_sender import send_email
from app.zipper import zip_reports
from app.context_builder import build_context

# Завантаження змінних середовища з .env (залишаємо для локальної розробки)
load_dotenv()

# Оновлене визначення функції: додаємо sheet_id та csv_file
def generate_and_send_report(email: Optional[str] = None, 
                             sheet_id: Optional[str] = None, 
                             csv_file: Optional = None) -> None: # csv_file може бути UploadedFile або None
    """Генерує PDF-звіти з Google Sheets або CSV, архівує їх і надсилає на email"""

    print(f"INFO: [report_generator.py] Received request: email='{email}', sheet_id='{sheet_id}', csv_file provided: {csv_file is not None}")

    # 📅 Отримуємо сьогоднішню дату
    today = datetime.now().strftime("%Y-%m-%d")

    # 📂 Формуємо шляхи до директорій і файлів
    # Використовуємо os.path.abspath для надійності шляхів, особливо якщо REPORTS_DIR відносний
    base_dir_from_env = os.getenv("REPORTS_DIR", "reports")
    # Якщо шлях відносний, робимо його відносно кореня проекту (або поточної робочої директорії)
    # Припускаємо, що скрипт запускається з кореня проекту, або REPORTS_DIR - абсолютний шлях
    base_dir = os.path.abspath(base_dir_from_env) 
    
    reports_dir = os.path.join(base_dir, today)
    # ZIP-архів також краще зберігати в base_dir або reports_dir
    zip_name_only = os.getenv("ZIP_NAME", f"all_reports_{today}.zip")
    zip_full_path = os.path.join(reports_dir, zip_name_only) # Зберігаємо архів у папці з звітами за день

    # 🗂 Створюємо папку, якщо не існує
    try:
        os.makedirs(reports_dir, exist_ok=True)
        print(f"INFO: [report_generator.py] Reports directory ensured: {reports_dir}")
    except Exception as e:
        print(f"ERROR: [report_generator.py] Could not create reports directory {reports_dir}: {e}")
        # Тут можна або підняти виняток, або повернути помилку користувачу в Streamlit
        raise # Перекидаємо помилку далі, щоб Streamlit міг її показати

    # 🔄 Отримуємо дані, передаючи sheet_id або csv_file
    data = None
    if sheet_id:
        print(f"INFO: [report_generator.py] Getting data using sheet_id: {sheet_id}")
        data = get_sheet_data(sheet_id=sheet_id)
    elif csv_file:
        print(f"INFO: [report_generator.py] Getting data using csv_file: {csv_file.name if hasattr(csv_file, 'name') else 'Uploaded CSV'}")
        data = get_sheet_data(csv_file=csv_file)
    else:
        print("ERROR: [report_generator.py] No data source (sheet_id or csv_file) provided to generate_and_send_report.")
        # Потрібно повідомити користувача в Streamlit; тут можна кинути виняток
        raise ValueError("Не надано джерело даних (ID таблиці або CSV-файл).")

    if not data: # Якщо дані порожні або None
        print("ERROR: [report_generator.py] No data retrieved from the source.")
        raise ValueError("Не вдалося отримати дані з вказаного джерела або джерело порожнє.")

    pdf_paths = []
    print(f"INFO: [report_generator.py] Starting PDF generation for {len(data)} records.")
    for i, record in enumerate(data):
        try:
            context = build_context(record) # Припускаємо, що build_context приймає один запис
            # Формуємо ім'я файлу більш надійно, обробляючи можливі спецсимволи в context['client']
            client_name_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in str(context.get('client', 'UnknownClient')))
            filename = os.path.join(reports_dir, f"report_{i+1}_{client_name_sanitized.replace(' ', '_')}.pdf")
            
            generate_pdf(context, filename) # Припускаємо, що generate_pdf приймає контекст і шлях
            print(f"  [✅] Звіт збережено: {filename}")
            pdf_paths.append(filename)
        except Exception as e:
            print(f"ERROR: [report_generator.py] Failed to generate PDF for record {i+1} ({record}): {e}")
            # Можливо, продовжити для інших записів або зупинити процес
            # Тут можна додати st.warning() або зібрати помилки і показати в кінці

    if not pdf_paths:
        print("ERROR: [report_generator.py] No PDF reports were generated.")
        raise ValueError("Не вдалося згенерувати жодного PDF-звіту.")

    # 🗜 Архівуємо всі звіти
    print(f"INFO: [report_generator.py] Zipping reports into: {zip_full_path}")
    zip_reports(pdf_paths, zip_full_path) # Передаємо повний шлях до архіву

    # 📧 Надсилаємо на пошту
    # Переконуємося, що передаємо повний шлях до архіву
    if email:
        print(f"INFO: [report_generator.py] Sending email with archive {zip_full_path} to {email}")
        send_email(file_path=zip_full_path, recipient=email) 
    else:
        # Можливо, вам потрібен отримувач за замовчуванням, якщо email не вказано
        default_recipient = os.getenv("EMAIL_TO_DEFAULT") 
        if default_recipient:
            print(f"INFO: [report_generator.py] Sending email with archive {zip_full_path} to default recipient {default_recipient}")
            send_email(file_path=zip_full_path, recipient=default_recipient)
        else:
            print("WARNING: [report_generator.py] Email not provided and no default recipient set. Email not sent.")
    
    print("INFO: [report_generator.py] generate_and_send_report finished.")