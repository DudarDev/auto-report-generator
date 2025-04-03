import os
import smtplib
from email.message import EmailMessage

def send_email(attachment_path):
    msg = EmailMessage()
    msg["Subject"] = "Автоматичний звіт"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("EMAIL_TO")
    msg.set_content("У вкладенні звіт у форматі .zip")

    with open(attachment_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="zip",
            filename=os.path.basename(attachment_path)
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_APP_PASSWORD"))
        smtp.send_message(msg)

    print(f"[✓] Email: {attachment_path} надіслано!")
