# /workspaces/auto-report-generator/app/run_app.py
import streamlit as st # Має бути одним з перших імпортів
from dotenv import load_dotenv
import os
import json
import traceback
# pandas тут більше не потрібен, він використовується в ui_components

# Імпортуємо конфігурацію полів першою
from app.config_fields import EXPECTED_APP_FIELDS, APP_INTERNAL_KEYS

# Ініціалізація Streamlit сторінки має бути першою командою Streamlit
# Оскільки тексти для page_title залежать від мови, ми зробимо попереднє завантаження
# або використаємо значення за замовчуванням.
_initial_lang_code = "uk" # Мова за замовчуванням для першого завантаження title
# (Можна покращити, зчитуючи мову з st.query_params, якщо вона там є)
_temp_texts_for_config = {"uk": {"page_title": "Генератор Звітів"}, "en": {"page_title": "Report Generator"}}
st.set_page_config(
    page_title=_temp_texts_for_config.get(_initial_lang_code, {}).get("page_title", "Report Generator"), 
    layout="wide", 
    initial_sidebar_state="auto"
)

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ СЕКРЕТІВ ТА GCP ---
def initialize_secrets_and_gcp():
    if 'secrets_initialized_run_app_v2' not in st.session_state: # Новий ключ для session_state
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
        st.session_state.secrets_initialized_run_app_v2 = True
initialize_secrets_and_gcp() # Викликаємо ініціалізацію
# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ ---

from app.report_generator import generate_and_send_report
from app.ui_components import language_selector, get_texts, build_main_input_section

def main():
    selected_language_code = language_selector()
    texts = get_texts(selected_language_code)   

    # Оновлюємо page_title, якщо мова змінилася
    # Це може не спрацювати ідеально, якщо st.set_page_config вже викликано.
    # Краще встановити title один раз на початку.
    # st.set_page_config(page_title=texts.get("page_title", "Report Generator")) # Цей рядок тут вже не потрібен

    st.title(texts["app_title"])
    st.markdown(texts["app_subtitle"])

    if 'sheet_id_input' not in st.session_state: st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state: st.session_state.email_input = ""
    if 'csv_file_uploader_key' not in st.session_state: st.session_state.csv_file_uploader_key = 0
    if 'user_column_mapping' not in st.session_state: 
        st.session_state.user_column_mapping = {key: '' for key in APP_INTERNAL_KEYS}
    
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
            elif csv_file_object_from_ui and (final_column_mapping_to_pass is None or not any(final_column_mapping_to_pass.values())): 
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
