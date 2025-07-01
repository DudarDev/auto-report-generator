# /workspaces/auto-report-generator/app/config.py

# --- Налаштування Моделі Gemini ---
GEMINI_MODEL_NAME = "gemini-1.5-pro-latest"

# --- Налаштування Email ---
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

# --- Мови, що підтримуються ---
SUPPORTED_LANGUAGES = {
    "Українська": "uk", 
    "English": "en"
}