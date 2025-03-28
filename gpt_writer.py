import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ ВИКОРИСТОВУЙ САМЕ ЦЮ МОДЕЛЬ:
model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

def generate_summary(data):
    prompt = f"Ось список даних: {data}. Сформуй короткий аналітичний звіт."
    response = model.generate_content(prompt)
    return response.text
