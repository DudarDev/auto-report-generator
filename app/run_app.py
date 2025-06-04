# /workspaces/auto-report-generator/app/run_app.py
import streamlit as st
from dotenv import load_dotenv
import os
import json
import traceback
# pandas тут вже не потрібен, бо логіка читання заголовків перенесена в ui_components

# Імпортуємо конфігурацію полів першою, щоб вона була доступна іншим
from .config_fields import EXPECTED_APP_FIELDS, APP_INTERNAL_KEYS

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ СЕКРЕТІВ ТА GCP ---
# Цей блок має виконуватися один раз при старті або перезапуску скрипта
# st.set_page_config має бути першою командою Streamlit
# Тому ініціалізацію робимо всередині main(), але з прапорцем в session_state

def initialize_secrets_and_gcp():
    """Виконує ініціалізацію секретів та GCP, якщо ще не зроблено."""
    if 'secrets_initialized_run_app' not in st.session_state:
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
                st.session_state.gcp_creds_initialized_run_app = True
            except Exception as e:
                print(f"ERROR: [run_app.py] Failed to set up GCP credentials: {e}")
                traceback.print_exc()
                st.session_state.gcp_creds_initialized_run_app = False
        else:
            print("WARNING: [run_app.py] GOOGLE_CREDENTIALS_JSON env var not found.")
            st.session_state.gcp_creds_initialized_run_app = False

        if not os.environ.get('GEMINI_API_KEY'):
            print("WARNING: [run_app.py] GEMINI_API_KEY environment variable not found.")
        st.session_state.secrets_initialized_run_app = True
# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ ---

# Імпортуємо ваш основний модуль ПІСЛЯ потенційної ініціалізації
from app.report_generator import generate_and_send_report
# Імпортуємо компоненти UI та тексти
from app.ui_components import language_selector, get_texts, build_main_input_section

def main():
    # st.set_page_config має бути першою командою Streamlit
    # Тому спочатку отримуємо тексти для page_title, потім викликаємо set_page_config
    
    # Попереднє отримання мови для page_config, якщо це можливо без UI елементів
    # Або використовуємо значення за замовчуванням
    initial_lang_code = "uk" # Мова за замовчуванням для першого завантаження
    if 'selected_language_display' in st.session_state : # Якщо мова вже обрана
        lang_options_display = {"Українська": "uk", "English": "en"}
        initial_lang_code = lang_options_display.get(st.session_state.selected_language_display, "uk")
    
    initial_texts = get_texts(initial_lang_code)
    st.set_page_config(page_title=initial_texts.get("page_title", "Report Generator"), layout="wide", initial_sidebar_state="auto")

    # Тепер виконуємо ініціалізацію секретів
    initialize_secrets_and_gcp()
    
    # Мовна панель
    selected_language_code = language_selector() # Ця функція тепер в ui_components
    texts = get_texts(selected_language_code)   # Отримуємо актуальні тексти

    st.title(texts["app_title"])
    st.markdown(texts["app_subtitle"])

    # Ініціалізація змінних сесії, якщо вони ще не існують
    if 'sheet_id_input' not in st.session_state: st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state: st.session_state.email_input = ""
    if 'csv_file_uploader_key' not in st.session_state: st.session_state.csv_file_uploader_key = 0
    if 'user_column_mapping' not in st.session_state: 
        st.session_state.user_column_mapping = {key: '' for key in APP_INTERNAL_KEYS} # Використовуємо імпортовані ключі
    
    # Будуємо основну секцію вводу даних
    data_source_selected, sheet_id_from_ui, csv_file_object_from_ui, email_from_ui, final_column_mapping_to_pass = build_main_input_section(texts)


    if st.button(texts["generate_button"]):
        valid_input = True
        if not email_from_ui:
            st.warning(texts["warning_enter_email"])
            valid_input = False
        
        if data_source_selected == texts["google_sheet_id_option"]:
            if not sheet_id_from_ui:
                st.warning(texts["warning_enter_gsheet_id"])
                valid_input = False
        elif data_source_selected == texts["csv_file_option"]:
            if not csv_file_object_from_ui:
                st.warning(texts["warning_upload_csv"])
                valid_input = False
            elif csv_file_object_from_ui and not any(st.session_state.user_column_mapping.values()): 
                 st.warning(texts["warning_setup_mapping"])
                 valid_input = False
        
        if valid_input:
            if data_source_selected == texts["google_sheet_id_option"] and not st.session_state.get('gcp_creds_initialized_run_app', False) :
                st.error(texts["error_gcp_init"])
                return

            with st.spinner(texts["spinner_generating"]):
                try:
                    current_csv_to_pass = None
                    if csv_file_object_from_ui:
                        csv_file_object_from_ui.seek(0) 
                        current_csv_to_pass = csv_file_object_from_ui
                    
                    mapping_to_use = final_column_mapping_to_pass if data_source_selected == texts["csv_file_option"] else None

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
