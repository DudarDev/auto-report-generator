# /workspaces/auto-report-generator/app/run_app.py

import streamlit as st
import os
import traceback
from dotenv import load_dotenv

# Імпортуємо компоненти та конфігурацію
from app.ui_components import get_texts, language_selector, build_main_input_section
from app.config_fields import APP_INTERNAL_KEYS
from app.report_generator import generate_and_send_report

# ... (код для st.set_page_config та initialize_secrets_and_gcp залишається без змін) ...
# --- НАЛАШТУВАННЯ СТОРІНКИ (МАЄ БУТИ ПЕРШОЮ КОМАНДОЮ STREAMLIT) ---
if 'selected_language_code' not in st.session_state:
    st.session_state.selected_language_code = "uk"
if 'selected_language_display' not in st.session_state:
    st.session_state.selected_language_display = "Українська"

initial_texts = get_texts(st.session_state.selected_language_code)
st.set_page_config(
    page_title=initial_texts.get("page_title", "Report Generator"),
    layout="wide",
    initial_sidebar_state="auto"
)

# --- ІНІЦІАЛІЗАЦІЯ СЕКРЕТІВ (ЗАПУСКАЄТЬСЯ ОДИН РАЗ) ---
def initialize_secrets_and_gcp():
    if 'secrets_initialized' not in st.session_state:
        load_dotenv()
        gcp_creds_json_string = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if gcp_creds_json_string:
            try:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                temp_dir = os.path.join(project_root, ".tmp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_creds_file_path = os.path.join(temp_dir, "gcp_creds.json")
                with open(temp_creds_file_path, 'w') as temp_file:
                    temp_file.write(gcp_creds_json_string)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_file_path
                st.session_state.gcp_creds_initialized = True
            except Exception as e:
                print(f"ERROR: Failed to set up GCP credentials: {e}")
                st.session_state.gcp_creds_initialized = False
        else:
            st.session_state.gcp_creds_initialized = False
        st.session_state.secrets_initialized = True

# --- ОСНОВНА ФУНКЦІЯ ДОДАТКУ ---
def main():
    initialize_secrets_and_gcp()

    if 'csv_file_uploader_key' not in st.session_state:
        st.session_state.csv_file_uploader_key = 0
    if 'user_column_mapping' not in st.session_state:
        st.session_state.user_column_mapping = {key: '' for key in APP_INTERNAL_KEYS}
    # Ініціалізуємо поля вводу, якщо їх немає
    if 'sheet_id_input' not in st.session_state:
        st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state:
        st.session_state.email_input = ""

    selected_language_code = language_selector()
    texts = get_texts(selected_language_code)

    st.title(texts["app_title"])
    st.markdown(texts["app_subtitle"])

    data_source, sheet_id, csv_file, email, column_mapping = build_main_input_section(texts)

    # ======== ПОЧАТОК ЗМІН ========

    # 1. Створюємо функцію для очищення форми (callback)
    def clear_form():
        st.session_state.sheet_id_input = ""
        st.session_state.email_input = ""
        st.session_state.user_column_mapping = {key: '' for key in APP_INTERNAL_KEYS}
        st.session_state.csv_file_uploader_key += 1
        # st.rerun() тут не потрібен, бо callback і так його запустить

    # 2. Передаємо цю функцію в on_click кнопки
    if st.button(texts["generate_button"], on_click=clear_form):
        is_valid = True
        # ... (Ваша логіка валідації залишається тут без змін) ...
        if data_source == texts["google_sheet_id_option"]:
            if not sheet_id:
                st.warning(texts["warning_enter_gsheet_id"])
                is_valid = False
            elif not st.session_state.get('gcp_creds_initialized'):
                 st.error(texts["error_gcp_init"])
                 is_valid = False
        elif data_source == texts["csv_file_option"]:
            if not csv_file:
                st.warning(texts["warning_upload_csv"])
                is_valid = False
            elif not column_mapping or not any(column_mapping.values()):
                st.warning(texts["warning_setup_mapping"])
                is_valid = False
        
        if not email:
            st.warning(texts["warning_enter_email"])
            is_valid = False

        if is_valid:
            with st.spinner(texts["spinner_generating"]):
                try:
                    generate_and_send_report(
                        email=email,
                        sheet_id=sheet_id,
                        csv_file=csv_file,
                        column_mapping=column_mapping
                    )
                    st.success(f"{texts['success_report_sent']} {email}")
                    
                    # 3. ВИДАЛЯЄМО рядки, що змінюють st.session_state, звідси
                    # Вони тепер у функції clear_form()

                except Exception as e:
                    error_msg = f"{texts['error_report_generation']}\n\n```\n{traceback.format_exc()}\n```"
                    st.error(error_msg)

    # ======== КІНЕЦЬ ЗМІН ========

if __name__ == "__main__":
    main()