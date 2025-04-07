import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("email_sender.log"),
        logging.StreamHandler()
    ]
)

def send_email(attachment_path, recipient=None):
    from_email = os.getenv("EMAIL_USER")
    to_email = recipient or os.getenv("EMAIL_TO")

    if not to_email:
        logging.error("❌ Email отримувача не вказано.")
        raise ValueError("Email отримувача не вказано.")

    if not os.path.exists(attachment_path):
        logging.error(f"❌ Файл не знайдено: {attachment_path}")
        raise FileNotFoundError(f"Файл не знайдено: {attachment_path}")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "📤 Ваш автоматичний звіт"
        msg["From"] = from_email
        msg["To"] = to_email

        text = "Звіт прикріплено до листа."

        with open("templates/email_template.html", "r", encoding="utf-8") as f:
            email_html = f.read()

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(email_html, "html"))

        with open(attachment_path, "rb") as f:
            file_part = MIMEApplication(f.read(), _subtype="zip")
            file_part.add_header(
                "Content-Disposition", "attachment",
                filename=os.path.basename(attachment_path)
            )
            msg.attach(file_part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_email, os.getenv("EMAIL_APP_PASSWORD"))
            smtp.sendmail(from_email, to_email, msg.as_string())

        logging.info(f"✅ Email надіслано до {to_email}")
    except Exception as e:
        logging.exception(f"❌ Помилка при надсиланні email: {e}")
        raise
