import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email(attachment_path):
    # створюємо лист з підтримкою тексту і HTML
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📎 Ваш автоматичний звіт"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("EMAIL_TO")

    # текстова версія для сумісності зі старими поштовиками
    text = "Звіт прикріплено до листа."

    # читаємо HTML шаблон із файлу
    with open("templates/email_template.html", "r", encoding="utf-8") as f:
        email_html = f.read()

    # додаємо обидві версії в лист
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(email_html, "html"))

    # додаємо ZIP-файл як вкладення
    with open(attachment_path, "rb") as f:
        file_part = MIMEApplication(f.read(), _subtype="zip")
        file_part.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment_path))
        msg.attach(file_part)

    # надсилаємо лист через Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_APP_PASSWORD"))
        smtp.sendmail(msg["From"], msg["To"], msg.as_string())

    print(f"[✓] Email з HTML: {attachment_path} надіслано!")
