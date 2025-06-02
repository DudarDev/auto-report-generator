# /workspaces/auto-report-generator/app/email_sender.py
import os
import smtplib
import ssl # Потрібен для ssl.create_default_context()
from email.message import EmailMessage
from dotenv import load_dotenv
import traceback # Для детального виводу помилок

load_dotenv()

def send_email(file_path: str, recipient: str = None) -> bool: # Змінено повернення на bool
    """Надсилає ZIP-файл на email та повертає True у разі успіху, False - у разі помилки."""
    
    email_subject = "Ваш автоматичний звіт" # Можна зробити динамічнішим, якщо потрібно
    email_from = os.getenv("EMAIL_USER")
    # Використовуємо переданого отримувача, або EMAIL_TO_DEFAULT, якщо є
    email_to = recipient or os.getenv("EMAIL_TO_DEFAULT", os.getenv("EMAIL_TO")) # EMAIL_TO_DEFAULT - як отримувач за замовчуванням
    
    email_host = os.getenv("EMAIL_HOST")
    email_port_str = os.getenv("EMAIL_PORT")
    email_password = os.getenv("EMAIL_APP_PASSWORD")

    print(f"INFO: [email_sender.py] Preparing to send email.")
    print(f"  From: {email_from}")
    print(f"  To: {email_to}")
    print(f"  Subject: {email_subject}")
    print(f"  Attachment path: {file_path}")
    print(f"  SMTP Host: {email_host}")
    print(f"  SMTP Port: {email_port_str}")
    print(f"  SMTP User: {email_user}")
    print(f"  SMTP App Password: {'********' if email_password else 'NOT SET'}")


    if not all([email_from, email_to, email_host, email_port_str, email_password]):
        print("ERROR: [email_sender.py] Not all required email configuration variables are set in environment.")
        print(f"  EMAIL_FROM: {'Set' if email_from else 'NOT SET'}")
        print(f"  EMAIL_TO (effective): {'Set' if email_to else 'NOT SET'}")
        print(f"  EMAIL_HOST: {'Set' if email_host else 'NOT SET'}")
        print(f"  EMAIL_PORT: {'Set' if email_port_str else 'NOT SET'}")
        print(f"  EMAIL_APP_PASSWORD: {'Set' if email_password else 'NOT SET'}")
        return False

    try:
        email_port = int(email_port_str)
    except ValueError:
        print(f"ERROR: [email_sender.py] Invalid EMAIL_PORT value: '{email_port_str}'. Must be an integer.")
        return False

    msg = EmailMessage()
    msg["Subject"] = email_subject
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content("У вкладенні ваш автоматично згенерований звіт.")

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)
            msg.add_attachment(file_data, maintype="application", subtype="zip", filename=file_name)
            print(f"INFO: [email_sender.py] Attached file: {file_name} ({len(file_data)} bytes)")
    except FileNotFoundError:
        print(f"ERROR: [email_sender.py] Attachment file not found: {file_path}")
        return False
    except Exception as e:
        print(f"ERROR: [email_sender.py] Could not read or attach file: {e}")
        traceback.print_exc()
        return False
        
    context = ssl.create_default_context()
    try:
        print("INFO: [email_sender.py] Attempting to connect to SMTP server...")
        with smtplib.SMTP_SSL(email_host, email_port, context=context) as smtp:
            smtp.set_debuglevel(1)  # Вмикає детальне логування SMTP команд
            print("INFO: [email_sender.py] Attempting to login to SMTP server...")
            smtp.login(email_user, email_password)
            print("INFO: [email_sender.py] Logged in. Attempting to send message...")
            smtp.send_message(msg)
            print(f"SUCCESS: [email_sender.py] Email successfully sent to {email_to}!")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: [email_sender.py] SMTP Authentication Error: {e}. Check EMAIL_USER and EMAIL_APP_PASSWORD.")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"ERROR: [email_sender.py] Failed to send email: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Блок для тестування самого send_email, якщо потрібно
    # Переконайтеся, що всі змінні середовища встановлені, або використовуйте .env
    print("Testing send_email function directly...")
    # Потрібно створити тимчасовий zip файл для тестування
    test_zip_path = "test_report.zip"
    if not os.path.exists(test_zip_path):
        with open(test_zip_path, "w") as f:
            f.write("This is a test zip content.") # Створюємо фейковий zip для тесту
    
    # Переконайтеся, що EMAIL_TO_DEFAULT або отримувач встановлені
    test_recipient_email = os.getenv("EMAIL_TEST_RECIPIENT", "your_test_email@example.com")
    if send_email(test_zip_path, recipient=test_recipient_email):
        print("Direct test: Email sent successfully.")
    else:
        print("Direct test: Email sending failed.")
    if os.path.exists(test_zip_path):
        os.remove(test_zip_path)