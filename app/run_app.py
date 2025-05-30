# /workspaces/auto-report-generator/app/run_app.py 
# Або якщо цей файл у корені проекту, то шляхи до .tmp треба буде скоригувати

import streamlit as st
from dotenv import load_dotenv # ✅ Залишаємо для локальної розробки
import os
import json # Може знадобитися для роботи з JSON, якщо будете його парсити

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ ---

# Завантажуємо змінні з .env файлу (якщо він є)
# Це має бути один з перших рядків у вашому головному скрипті
load_dotenv() 
print("INFO: Attempted to load .env file.")

# Налаштування для Google Cloud Credentials (з GitHub Secret -> env var -> temp file)
print("INFO: Attempting to set up Google Cloud credentials...")
gcp_creds_json_string = os.environ.get('GOOGLE_CREDENTIALS_JSON')

if gcp_creds_json_string:
    try:
        # Визначаємо шлях до кореня проекту, щоб папка .tmp була там
        # Якщо run_app.py в папці app/, то корінь проекту на один рівень вище
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        temp_dir = os.path.join(project_root, ".tmp") 
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            print(f"INFO: Created directory: {temp_dir}")
        
        temp_creds_file_path = os.path.join(temp_dir, "gcp_service_account.json")

        with open(temp_creds_file_path, 'w') as temp_file:
            temp_file.write(gcp_creds_json_string)
        
        # Встановлюємо стандартну змінну середовища, яку шукають бібліотеки Google
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_file_path 
        print(f"SUCCESS: GOOGLE_APPLICATION_CREDENTIALS set to temporary file: {temp_creds_file_path}")
    except Exception as e:
        print(f"ERROR: Failed to set up GCP credentials from env var: {e}")
        # Можна додати st.error() якщо це критично для запуску streamlit, але print краще для логів
else:
    print("WARNING: GCP_CREDENTIALS_JSON_CONTENT environment variable for Google Cloud not found.")
    print("         Google Sheets functionality might be affected if not configured otherwise.")

# Перевірка інших важливих секретів (просто для логування, сам код їх використовує напряму)
if not os.environ.get('GEMINI_API_KEY'):
    print("WARNING: GEMINI_API_KEY environment variable not found.")
if not os.environ.get('EMAIL_USER'): # Приклад
    print("WARNING: EMAIL_USER environment variable not found.")

# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ ---


# Імпорт вашого основного модуля ПІСЛЯ ініціалізації змінних середовища, 
# особливо якщо він одразу намагається ініціалізувати клієнти сервісів
from app.report_generator import generate_and_send_report  # ✅ Абсолютний імпорт

def main():
    st.set_page_config(page_title="AUTO-REPORT-GENERATOR", layout="centered")
    st.title("📋 AUTO-REPORT-GENERATOR")
    st.markdown("Згенеруйте звіт 🧾 і отримаєте його на email 📩")

    # Ініціалізація змінних сесії для збереження стану
    if 'sheet_id_input' not in st.session_state:
        st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state:
        st.session_state.email_input = ""
    if 'csv_file_uploader_key' not in st.session_state:
        st.session_state.csv_file_uploader_key = 0 # Для скидання стану file_uploader

    data_source = st.radio(
        "Оберіть джерело даних:", 
        ["Google Sheet ID", "CSV файл"], 
        key="data_source_radio"
    )
    
    sheet_id = None
    csv_file = None

    if data_source == "Google Sheet ID":
        st.session_state.sheet_id_input = st.text_input(
            "Введіть Google Sheet ID:", 
            value=st.session_state.sheet_id_input, 
            key="sheet_id_text_input"
        )
        sheet_id = st.session_state.sheet_id_input
        # Скидаємо завантажувач файлів, якщо обрано Google Sheet
        if st.session_state.get('csv_file_state') is not None:
             st.session_state.csv_file_uploader_key +=1 
             st.session_state.csv_file_state = None

    else: # data_source == "CSV файл"
        csv_file_obj = st.file_uploader(
            "Завантажте CSV файл", 
            type=["csv"], 
            key=f"file_uploader_{st.session_state.csv_file_uploader_key}" # Динамічний ключ для скидання
        )
        if csv_file_obj is not None:
            csv_file = csv_file_obj # Передаємо об'єкт файлу
            st.session_state.csv_file_state = csv_file_obj # Зберігаємо стан
        # Скидаємо sheet_id, якщо обрано CSV
        st.session_state.sheet_id_input = ""


    st.session_state.email_input = st.text_input(
        "Введіть email клієнта:", 
        value=st.session_state.email_input,
        key="email_text_input"
    )
    email = st.session_state.email_input

    if st.button("🚀 Згенерувати та надіслати звіт"):
        if not email:
            st.warning("Будь ласка, введіть email")
        elif data_source == "Google Sheet ID" and not sheet_id:
            st.warning("Будь ласка, введіть Google Sheet ID")
        elif data_source == "CSV файл" and not csv_file: # Перевіряємо чи є об'єкт файлу
            st.warning("Будь ласка, завантажте CSV файл")
        else:
            with st.spinner("Генеруємо звіт... Це може зайняти деякий час. ⏳"):
                try:
                    # Передаємо або sheet_id, або об'єкт csv_file
                    generate_and_send_report(email=email, sheet_id=sheet_id, csv_file=csv_file)
                    st.success(f"✅ Звіт успішно згенеровано та надіслано на {email}")
                    # Очищення полів після успішної відправки
                    st.session_state.sheet_id_input = ""
                    st.session_state.email_input = ""
                    st.session_state.csv_file_uploader_key += 1 # Змінюємо ключ для скидання file_uploader
                    st.session_state.csv_file_state = None
                    st.experimental_rerun() # Оновити сторінку для очищення полів вводу

                except Exception as e:
                    st.error(f"❌ Виникла помилка під час генерації або надсилання звіту: {e}")
                    # Можна додати більш детальне логування помилки для себе
                    print(f"ERROR in generate_and_send_report: {e}") 
                    import traceback
                    traceback.print_exc()


if __name__ == "__main__":
    # Переконайтеся, що логіка налаштування ключів GCP виконується до main()
    # У цьому прикладі вона вже на початку файлу, тому це буде зроблено при імпорті/запуску
    main()