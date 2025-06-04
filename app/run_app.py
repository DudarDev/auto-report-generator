# /workspaces/auto-report-generator/app/run_app.py
import streamlit as st
from dotenv import load_dotenv
import os
import json
import traceback
import pandas as pd

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ СЕКРЕТІВ ТА GCP ---
# Цей блок має виконуватися один раз при старті або перезапуску скрипта
# Використовуємо прапорець у st.session_state, щоб уникнути повторної ініціалізації при кожному rerun
if 'secrets_initialized_main_app' not in st.session_state:
    load_dotenv() 
    print("INFO: [run_app.py] Attempted to load .env file.")

    print("INFO: [run_app.py] Attempting to set up Google Cloud credentials...")
    gcp_creds_json_string = os.environ.get('GOOGLE_CREDENTIALS_JSON') 

    if gcp_creds_json_string:
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            temp_dir = os.path.join(project_root, ".tmp") 
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                print(f"INFO: [run_app.py] Created directory: {temp_dir}")
            temp_creds_file_path = os.path.join(temp_dir, "gcp_service_account_streamlit.json")
            with open(temp_creds_file_path, 'w') as temp_file:
                temp_file.write(gcp_creds_json_string)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_file_path 
            print(f"SUCCESS: [run_app.py] GOOGLE_APPLICATION_CREDENTIALS set to: {temp_creds_file_path}")
            st.session_state.gcp_creds_initialized_run_app = True # Позначаємо успішну ініціалізацію
        except Exception as e:
            print(f"ERROR: [run_app.py] Failed to set up GCP credentials from env var 'GOOGLE_CREDENTIALS_JSON': {e}")
            traceback.print_exc()
            st.session_state.gcp_creds_initialized_run_app = False
    else:
        print("WARNING: [run_app.py] GOOGLE_CREDENTIALS_JSON environment variable for Google Cloud not found.")
        st.session_state.gcp_creds_initialized_run_app = False

    # Перевірка інших важливих секретів
    if not os.environ.get('GEMINI_API_KEY'):
        print("WARNING: [run_app.py] GEMINI_API_KEY environment variable not found.")
    # Додайте тут перевірки для EMAIL_USER, EMAIL_APP_PASSWORD, EMAIL_HOST, EMAIL_PORT
    
    st.session_state.secrets_initialized_run_app = True # Позначаємо, що блок ініціалізації виконався
# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ ---

# Імпортуємо ваш основний модуль ПІСЛЯ потенційної ініціалізації
from app.report_generator import generate_and_send_report
# Імпортуємо компоненти UI та тексти
from app.ui_components import language_selector, get_texts, display_csv_column_mapping_ui

# Внутрішні стандартні поля (ключі) та ключі для їхніх перекладених назв у словнику `texts`
EXPECTED_APP_FIELDS = {
    "client_name": "client_name_label", # Ключ у словнику texts для "Ім'я/Назва Клієнта"
    "task": "task_label",
    "status": "status_label",
    "date": "date_label",
    "comments": "comments_label",
    "amount": "amount_label" 
}
# Список внутрішніх ключів, який буде використовуватися в gsheet.py та context_builder.py
APP_INTERNAL_KEYS = list(EXPECTED_APP_FIELDS.keys())


def main():
    # Мовна панель (має бути на початку, щоб тексти були доступні для решти UI)
    selected_language_code = language_selector()
    texts = get_texts(selected_language_code)

    st.set_page_config(page_title=texts.get("page_title", "Report Generator"), layout="wide", initial_sidebar_state="auto")
    st.title(texts["app_title"])
    st.markdown(texts["app_subtitle"])

    # Ініціалізація змінних сесії, якщо вони ще не існують
    if 'sheet_id_input' not in st.session_state:
        st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state:
        st.session_state.email_input = ""
    if 'csv_file_uploader_key' not in st.session_state:
        st.session_state.csv_file_uploader_key = 0
    if 'user_column_mapping' not in st.session_state: # Для збереження мапування користувача
        st.session_state.user_column_mapping = {key: '' for key in APP_INTERNAL_KEYS}

    data_source = st.radio(
        texts["select_data_source"], 
        [texts["google_sheet_id_option"], texts["csv_file_option"]], 
        key="data_source_radio_main_v2",
        horizontal=True
    )
    
    sheet_id_from_ui = None
    csv_file_object_from_ui = None
    final_column_mapping_to_pass = None # Мапування, яке передається в report_generator

    if data_source == texts["google_sheet_id_option"]:
        st.session_state.sheet_id_input = st.text_input(
            texts["enter_google_sheet_id"], 
            value=st.session_state.sheet_id_input, 
            placeholder="Наприклад, 1abc2def3ghi_JKLMN...",
            key="sheet_id_text_input_main_v4"
        )
        sheet_id_from_ui = st.session_state.sheet_id_input.strip()
        if any(st.session_state.user_column_mapping.values()): # Скидаємо мапування CSV
            st.session_state.user_column_mapping = {key: '' for key in APP_INTERNAL_KEYS}
            # st.rerun() # Якщо потрібно негайно оновити UI
    
    else: # data_source == texts["csv_file_option"]
        csv_file_object_from_ui = st.file_uploader(
            texts["upload_csv_file"], 
            type=["csv"], 
            key=f"file_uploader_main_v2_{st.session_state.csv_file_uploader_key}" 
        )
        st.session_state.sheet_id_input = "" 

        if csv_file_object_from_ui is not None:
            # Відображаємо UI для мапування стовпців
            current_mapping = display_csv_column_mapping_ui(texts, csv_file_object_from_ui, EXPECTED_APP_FIELDS)
            if current_mapping is not None: # Якщо мапування успішне (не було помилки в display_csv_column_mapping_ui)
                final_column_mapping_to_pass = current_mapping
            else: # Якщо була помилка при читанні заголовків CSV
                csv_file_object_from_ui = None # Не обробляємо цей файл далі
    
    st.session_state.email_input = st.text_input(
        texts["enter_client_email"], 
        value=st.session_state.email_input,
        placeholder="example@email.com",
        key="email_text_input_main_v4"
    )
    email_from_ui = st.session_state.email_input.strip()

    if st.button(texts["generate_button"]):
        valid_input = True
        if not email_from_ui:
            st.warning(texts["warning_enter_email"])
            valid_input = False
        
        if data_source == texts["google_sheet_id_option"]:
            if not sheet_id_from_ui:
                st.warning(texts["warning_enter_gsheet_id"])
                valid_input = False
        elif data_source == texts["csv_file_option"]:
            if not csv_file_object_from_ui:
                st.warning(texts["warning_upload_csv"])
                valid_input = False
            # Перевіряємо, чи хоча б одне поле зіставлено, ЯКЩО файл завантажено
            elif csv_file_object_from_ui and not any(st.session_state.user_column_mapping.values()): 
                 st.warning(texts["warning_setup_mapping"])
                 valid_input = False
        
        if valid_input:
            # Перевірка ініціалізації GCP credentials перед викликом, якщо дані з Google Sheets
            if data_source == texts["google_sheet_id_option"] and not st.session_state.get('gcp_creds_initialized_run_app', False) :
                st.error(texts["error_gcp_init"])
                return # Не продовжуємо, якщо GCP ключі не ініціалізовані

            with st.spinner(texts["spinner_generating"]):
                try:
                    current_csv_to_pass = None
                    if csv_file_object_from_ui:
                        csv_file_object_from_ui.seek(0) 
                        current_csv_to_pass = csv_file_object_from_ui
                    
                    # Для Google Sheets column_mapping буде None
                    mapping_to_use = final_column_mapping_to_pass if data_source == texts["csv_file_option"] else None

                    print(f"DEBUG: [run_app.py] Calling generate_and_send_report with email='{email_from_ui}', sheet_id='{sheet_id_from_ui}', csv_file is {'provided' if current_csv_to_pass else 'not provided'}, mapping: {mapping_to_use}")
                    
                    generate_and_send_report(
                        email=email_from_ui, 
                        sheet_id=sheet_id_from_ui, 
                        csv_file=current_csv_to_pass, 
                        column_mapping=mapping_to_use 
                    )
                    st.success(f"{texts['success_report_sent']} {email_from_ui}")
                    
                    st.session_state.sheet_id_input = ""
                    st.session_state.email_input = ""
                    st.session_state.csv_file_uploader_key += 1 
                    st.session_state.user_column_mapping = {key: '' for key in APP_INTERNAL_KEYS}
                    
                    st.rerun()

                except Exception as e:
                    error_text = texts.get('error_report_generation', "❌ An error occurred:")
                    detailed_error_message = f"{error_text}\n\n{type(e).__name__}: {e}\n\nTraceback:\n{traceback.format_exc()}"
                    st.error(detailed_error_message)
                    print(f"ERROR: [run_app.py] Exception in generate_and_send_report call: {e}") 

if __name__ == "__main__":
    main()
