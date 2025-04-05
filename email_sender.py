def send_email(attachment_path, recipient=None):
    from_email = os.getenv("EMAIL_USER")
    to_email = recipient if recipient else os.getenv("EMAIL_TO")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚀 Ваш автоматичний звіт"
    msg["From"] = from_email
    msg["To"] = to_email

    # Текстова версія
    text = "Звіт прикріплено до листа."

    # HTML шаблон
    with open("templates/email_template.html", "r", encoding="utf-8") as f:
        email_html = f.read()

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(email_html, "html"))

    # ZIP-вкладення
    with open(attachment_path, "rb") as f:
        file_part = MIMEApplication(f.read(), _subtype="zip")
        file_part.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment_path))
        msg.attach(file_part)

    # Відправка
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(from_email, os.getenv("EMAIL_APP_PASSWORD"))
        smtp.sendmail(from_email, to_email, msg.as_string())

    print(f"[✔] Email з HTML: {attachment_path} надіслано!")
