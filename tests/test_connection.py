# /workspaces/auto-report-generator/app/test_connection.py
import os
from dotenv import load_dotenv
import google.generativeai as genai
import smtplib
import ssl # Додано для context в SMTP
from email.message import EmailMessage
import gspread
# Замість oauth2client, використовуємо сучаснішу бібліотеку google-auth, 
# gspread зазвичай працює з нею "під капотом" або дозволяє передати credentials.
# from google.oauth2.service_account import Credentials # Може знадобитися, якщо gspread.service_account() не спрацює напряму

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ GOOGLE CLOUD CREDENTIALS (для tests/test_connection.py) ---
import os
import json 
from dotenv import load_dotenv

load_dotenv() 
print("INFO: [tests/test_connection.py] Attempted to load .env file.")

print("INFO: [tests/test_connection.py] Attempting to set up Google Cloud credentials...")
gcp_creds_json_string = os.environ.get('GOOGLE_CREDENTIALS_JSON') 

if gcp_creds_json_string:
    try:
        # Визначаємо корінь проекту (на один рівень вище від папки 'tests')
        current_script_path = os.path.abspath(__file__) # шлях до tests/test_connection.py
        project_root = os.path.dirname(os.path.dirname(current_script_path)) # /workspaces/auto-report-generator
        
        temp_dir = os.path.join(project_root, ".tmp") 
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            print(f"INFO: [tests/test_connection.py] Created directory: {temp_dir}")
        
        temp_creds_file_path = os.path.join(temp_dir, "gcp_service_account_for_test.json")

        with open(temp_creds_file_path, 'w') as temp_file:
            temp_file.write(gcp_creds_json_string)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_file_path 
        print(f"SUCCESS: [tests/test_connection.py] GOOGLE_APPLICATION_CREDENTIALS set to: {temp_creds_file_path}")
    except Exception as e:
        print(f"ERROR: [tests/test_connection.py] Failed to set up GCP credentials: {e}")
        import traceback
        traceback.print_exc()
else:
    print("WARNING: [tests/test_connection.py] GOOGLE_CREDENTIALS_JSON env var for Google Cloud not found.")

if not os.environ.get('GEMINI_API_KEY'):
    print("WARNING: [tests/test_connection.py] GEMINI_API_KEY environment variable not found.")
# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ GOOGLE CLOUD CREDENTIALS ---


# 1. Перевірка Google Sheets
def check_gsheet():
    print("\n[TESTING] 1. Google Sheets Connection...")
    try:
        # Тепер gspread має автоматично знайти GOOGLE_APPLICATION_CREDENTIALS,
        # встановлену блоком ініціалізації вище.
        # Або, якщо ви хочете бути абсолютно впевненими, що використовується файл, створений цим скриптом:
        creds_file_for_test = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') # Ця змінна вже вказує на наш тимчасовий файл
        
        if not creds_file_for_test or not os.path.exists(creds_file_for_test):
            print("  [❌] Помилка: GOOGLE_APPLICATION_CREDENTIALS не встановлено або файл ключів для тестування не знайдено у вказаному шляху.")
            return

        # Використовуємо gspread.service_account() з явним зазначенням файлу (хоча він мав би знайти і сам)
        client = gspread.service_account(filename=creds_file_for_test)
        
        # Отримуємо ID таблиці з змінної середовища
        sheet_id = os.getenv("GOOGLE_SHEET_ID_TEST", os.getenv("GOOGLE_SHEET_ID")) # Використовуйте тестовий ID, якщо є
        if not sheet_id:
            print("  [❌] Помилка: GOOGLE_SHEET_ID_TEST (або GOOGLE_SHEET_ID) не встановлено в змінних середовища.")
            return
            
        sheet = client.open_by_key(sheet_id)
        data = sheet.sheet1.get_all_records() # Або інша тестова операція
        print(f"  [✅] Google Sheets: з'єднання успішне з таблицею '{sheet.title}', рядків: {len(data)}")
    except Exception as e:
        print(f"  [❌] Google Sheets: помилка ► {e}")
        import traceback
        traceback.print_exc()

# 2. Перевірка Gemini
def check_gemini():
    print("\n[TESTING] 2. Gemini API Connection...")
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print("  [❌] Помилка: GEMINI_API_KEY не встановлено в змінних середовища.")
            return
            
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest") # Або 'gemini-pro'
        response = model.generate_content("Скажи Привіт!")
        print(f"  [✅] Gemini API: відповідь — {response.text.strip()}")
    except Exception as e:
        print(f"  [❌] Gemini API: помилка ► {e}")
        import traceback
        traceback.print_exc()

# 3. Перевірка Email SMTP
def check_email():
    print("\n[TESTING] 3. Email SMTP Connection...")
    try:
        email_host = os.getenv("EMAIL_HOST")
        email_port_str = os.getenv("EMAIL_PORT")
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_APP_PASSWORD")
        # Використовуйте тестового отримувача, або свій же email для тесту
        email_recipient_test = os.getenv("EMAIL_TEST_RECIPIENT", email_user) 

        if not all([email_host, email_port_str, email_user, email_password, email_recipient_test]):
            print("  [❌] Помилка: Не всі змінні для SMTP встановлені (EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_APP_PASSWORD, EMAIL_TEST_RECIPIENT).")
            return
        
        try:
            email_port = int(email_port_str)
        except ValueError:
            print(f"  [❌] Помилка: Некоректне значення для EMAIL_PORT: {email_port_str}. Має бути число.")
            return

        msg = EmailMessage()
        msg["Subject"] = "Тестовий лист SMTP з GitHub Codespace"
        msg["From"] = email_user
        msg["To"] = email_recipient_test
        msg.set_content("Це автоматичний тестовий лист для перевірки налаштувань SMTP.")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(email_host, email_port, context=context) as smtp:
            smtp.login(email_user, email_password)
            smtp.send_message(msg)
        print(f"  [✅] Email: тестове повідомлення успішно надіслано на {email_recipient_test}!")
    except Exception as e:
        print(f"  [❌] Email: помилка ► {e}")
        import traceback
        traceback.print_exc()

# Запуск
if __name__ == "__main__":
    print("--- Запуск тестів з'єднання ---")
    # Блок ініціалізації GCP вже на початку файлу, тому він виконається при імпорті/запуску
    check_gsheet()
    check_gemini()
    check_email()
    print("\n--- Тести з'єднання завершено ---")