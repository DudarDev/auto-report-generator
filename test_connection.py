import os
from dotenv import load_dotenv
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

# 1. Перевірка Google Sheets
def check_gsheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file("gmail_credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
        data = sheet.sheet1.get_all_records()
        print("[✓] Google Sheets: з'єднання успішне, рядків:", len(data))
    except Exception as e:
        print("[X] Google Sheets: помилка ➤", e)

# 2. Перевірка Gemini
def check_gemini():
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        response = model.generate_content("Скажи Привіт!")
        print("[✓] Gemini API: відповідь ➤", response.text.strip())
    except Exception as e:
        print("[X] Gemini API: помилка ➤", e)

# 3. Перевірка Email
def check_email():
    try:
        msg = EmailMessage()
        msg["Subject"] = "Test Email"
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = os.getenv("EMAIL_TO")
        msg.set_content("Це тестове повідомлення для перевірки SMTP.")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_APP_PASSWORD"))
            smtp.send_message(msg)
        print("[✓] Email: повідомлення надіслано!")
    except Exception as e:
        print("[X] Email: помилка ➤", e)

# Запуск тестів
check_gsheet()
check_gemini()
check_email()
