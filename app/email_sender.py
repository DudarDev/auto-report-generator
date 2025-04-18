import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_email(file_path: str, recipient: str = None) -> None:
    """Надсилає ZIP-файл на email."""
    msg = EmailMessage()
    msg["Subject"] = "Автоматичний звіт"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = recipient or os.getenv("EMAIL_TO")
    msg.set_content("У вкладенні ваш звіт.")

    with open(file_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(file_path)
        msg.add_attachment(file_data, maintype="application", subtype="zip", filename=file_name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_APP_PASSWORD"))
        smtp.send_message(msg)
