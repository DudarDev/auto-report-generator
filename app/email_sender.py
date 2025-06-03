# /workspaces/auto-report-generator/app/email_sender.py
import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import traceback

load_dotenv()
print(f"INFO: [email_sender.py] Module loaded. Attempted to load .env file.")

def send_email(file_path: str, recipient: str = None) -> bool:
    """Надсилає ZIP-файл на email та повертає True у разі успіху, False - у разі помилки."""
    
    print(f"INFO: [email_sender.py] Preparing to send email with attachment: {file_path}")

    email_subject = "Ваш автоматичний звіт"
    email_from_user = os.getenv("EMAIL_USER")
    email_to_address = recipient or os.getenv("EMAIL_TO_DEFAULT") or os.getenv("EMAIL_TO")
    email_host = os.getenv("EMAIL_HOST")
    email_port_str = os.getenv("EMAIL_PORT")
    email_app_password = os.getenv("EMAIL_APP_PASSWORD")

    print(f"  Attempting Send Details:")
    print(f"    From: {email_from_user}")
    print(f"    To: {email_to_address}")
    print(f"    Subject: {email_subject}")
    print(f"    Attachment path: {file_path}")
    print(f"    SMTP Host: {email_host}")
    print(f"    SMTP Port: {email_port_str}")
    print(f"    SMTP User (for login): {email_from_user}")
    print(f"    SMTP App Password: {'********' if email_app_password else 'NOT SET'}")

    required_vars = {
        "EMAIL_USER (for From & Login)": email_from_user,
        "EMAIL_TO (effective)": email_to_address,
        "EMAIL_HOST": email_host,
        "EMAIL_PORT": email_port_str,
        "EMAIL_APP_PASSWORD": email_app_password
    }

    missing_vars = [name for name, value in required_vars.items() if not value]
    if missing_vars:
        print(f"ERROR: [email_sender.py] Not all required email configuration variables are set: {', '.join(missing_vars)}")
        for name, value in required_vars.items():
             print(f"    {name}: {'Set' if value else 'NOT SET'}")
        return False

    try:
        email_port = int(email_port_str)
    except (ValueError, TypeError):
        print(f"ERROR: [email_sender.py] Invalid EMAIL_PORT value: '{email_port_str}'. Must be an integer.")
        return False

    msg = EmailMessage()
    msg["Subject"] = email_subject
    msg["From"] = email_from_user
    msg["To"] = email_to_address
    msg.set_content(f"Шановний отримувач,\n\nУ вкладенні ваш автоматично згенерований звіт '{os.path.basename(file_path)}'.\n\nЗ найкращими побажаннями,\nВаш Автоматичний Генератор Звітів")

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
        print(f"ERROR: [email_sender.py] Could not read or attach file '{file_path}': {e}")
        traceback.print_exc()
        return False
        
    context = ssl.create_default_context()
    try:
        print(f"INFO: [email_sender.py] Attempting to connect to SMTP server: {email_host}:{email_port}")
        with smtplib.SMTP_SSL(email_host, email_port, context=context) as smtp:
            smtp.set_debuglevel(1)
            print(f"INFO: [email_sender.py] Attempting to login to SMTP server as user: {email_from_user}")
            smtp.login(email_from_user, email_app_password)
            print("INFO: [email_sender.py] Logged in successfully. Attempting to send message...")
            smtp.send_message(msg)
            print(f"SUCCESS: [email_sender.py] Email successfully sent to {email_to_address}!")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: [email_sender.py] SMTP Authentication Error: {e}. Check EMAIL_USER and EMAIL_APP_PASSWORD.")
        traceback.print_exc()
        return False
    except smtplib.SMTPException as e:
        print(f"ERROR: [email_sender.py] SMTP Error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"ERROR: [email_sender.py] Failed to send email due to an unexpected error: {e}")
        traceback.print_exc()
        return False

# ... (ваш тестовий блок if __name__ == '__main__':, якщо потрібен) ...