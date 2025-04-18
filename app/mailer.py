# app/mailer.py
import os
import smtplib
from email.message import EmailMessage

def send_email(zip_path, recipient=None):
    """
    Надсилає ZIP-файл на пошту.
    """
    msg = EmailMessage()
    msg["Subject"] = "Ваш звіт"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = recipient or os.getenv("EMAIL_TO")

    msg.set_content("Ваш звіт у вкладенні.")
    with open(zip_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="zip", filename=os.path.basename(zip_path))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_APP_PASSWORD"))
        smtp.send_message(msg)
