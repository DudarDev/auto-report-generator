# /workspaces/auto-report-generator/app/run_app.py
import streamlit as st
from dotenv import load_dotenv
import os
import json
import traceback
import pandas as pd

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ СЕКРЕТІВ ТА GCP ---
# Цей блок має виконуватися один раз при старті або перезапуску скрипта
if 'secrets_initialized_run_app' not in st.session_state: # Унікальний ключ для session_state
    load_dotenv() 
    print("INFO: [run_app.py] Attempted to load .env file.")

    print("INFO: [run_app.py] Attempting to set up Google Cloud credentials...")
    # Використовуємо назву секрету, яку ви підтвердили: GOOGLE_CREDENTIALS_JSON
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
            print(f"ERROR: [run_app.py] Failed to set up GCP credentials from env var 'GOOGLE_CREDENTIALS_JSON': {e}")
            traceback.print_exc()
            st.session_state.gcp_creds_initialized_run_app = False
    else:
        print("WARNING: [run_app.py] GOOGLE_CREDENTIALS_JSON environment variable for Google Cloud not found.")
        st.session_state.gcp_creds_initialized_run_app = False

    if not os.environ.get('GEMINI_API_KEY'):
        print("WARNING: [run_app.py] GEMINI_API_KEY environment variable not found.")
    st.session_state.secrets_initialized_run_app = True
# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ ---

# Імпортуємо ваш основний модуль ПІСЛЯ потенційної ініціалізації
from app.report_generator import generate_and_send_report

# Внутрішні стандартні поля (ключі), які очікує ваш звіт, та їх опис для UI
EXPECTED_APP_FIELDS = {
    "client_name": "Ім'я/Назва Клієнта",
    "task": "Завдання/Послуга",
    "status": "Статус",
    "date": "Дата",
    "comments": "Коментарі",
    "amount": "Сума (якщо є)" 
}

def main():
    st.set_page_config(page_title="AUTO-REPORT-GENERATOR", layout="wide", initial_sidebar_state="auto")
    st.title("📋 AUTO-REPORT-GENERATOR")
    st.markdown("Згенеруйте звіт 🧾 і отримаєте його на email 📩")

    if 'sheet_id_input' not in st.session_state:
        st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state:
        st.session_state.email_input = ""
    if 'csv_file_uploader_key' not in st.session_state:
        st.session_state.csv_file_uploader_key = 0
    if 'user_column_mapping' not in st.session_state:
        st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS}


    data_source = st.radio(
        "Оберіть джерело даних:", 
        ["Google Sheet ID", "CSV файл"], 
        key="data_source_radio_main", # Унікальний ключ
        horizontal=True
    )
    
    sheet_id_from_ui = None
    csv_file_object_from_ui = None
    
    if data_source == "Google Sheet ID":
        st.session_state.sheet_id_input = st.text_input(
            "Введіть Google Sheet ID:", 
            value=st.session_state.sheet_id_input, 
            placeholder="Наприклад, 1abc2def3ghi_JKLMN...",
            key="sheet_id_text_input_main_v3"
        )
        sheet_id_from_ui = st.session_state.sheet_id_input.strip()
        # Якщо обрано Google Sheet, скидаємо мапування для CSV, якщо воно було
        if any(st.session_state.user_column_mapping.values()):
            st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS}
            # Можна додати st.rerun() якщо потрібно негайно оновити UI
    
    else: # data_source == "CSV файл"
        csv_file_object_from_ui = st.file_uploader(
            "Завантажте CSV файл", 
            type=["csv"], 
            key=f"file_uploader_main_{st.session_state.csv_file_uploader_key}" 
        )
        st.session_state.sheet_id_input = "" 

        if csv_file_object_from_ui is not None:
            try:
                df_headers = pd.read_csv(csv_file_object_from_ui, nrows=0, encoding='utf-8').columns.tolist()
                csv_file_object_from_ui.seek(0) 

                st.subheader("⚙️ Зіставлення стовпців вашого CSV файлу")
                st.caption("Будь ласка, вкажіть, які стовпці з вашого файлу відповідають необхідним полям для звіту. Якщо відповідного стовпця немає, залиште поле порожнім.")
                
                temp_mapping = {}
                cols = st.columns(2) 
                col_idx = 0
                for internal_field, display_name in EXPECTED_APP_FIELDS.items():
                    with cols[col_idx % 2]:
                        prev_selection = st.session_state.user_column_mapping.get(internal_field, '')
                        current_index = 0
                        if prev_selection and prev_selection in df_headers:
                            current_index = (df_headers.index(prev_selection) + 1)
                        
                        selected_column = st.selectbox(
                            f"{display_name}:",
                            options=[''] + df_headers, 
                            index=current_index,
                            key=f"map_main_{internal_field}_v3"
                        )
                        if selected_column: 
                            temp_mapping[internal_field] = selected_column
                    col_idx += 1
                st.session_state.user_column_mapping = temp_mapping
            except Exception as e:
                st.error(f"Помилка при читанні заголовків CSV або відображенні мапування: {e}")
                traceback.print_exc()
                csv_file_object_from_ui = None 
    
    st.session_state.email_input = st.text_input(
        "Введіть email клієнта для надсилання звіту:", 
        value=st.session_state.email_input,
        placeholder="example@email.com",
        key="email_text_input_main_v3"
    )
    email_from_ui = st.session_state.email_input.strip()

    if st.button("🚀 Згенерувати та надіслати звіт"):
        valid_input = True
        if not email_from_ui: # Перевірка, чи введено email
            st.warning("Будь ласка, введіть email клієнта.")
            valid_input = False
        
        final_column_mapping_to_pass = None
        if data_source == "Google Sheet ID":
            if not sheet_id_from_ui:
                st.warning("Будь ласка, введіть Google Sheet ID.")
                valid_input = False
        elif data_source == "CSV файл":
            if not csv_file_object_from_ui:
                st.warning("Будь ласка, завантажте CSV файл.")
                valid_input = False
            # Перевіряємо, чи хоча б одне поле зіставлено, якщо обрано CSV
            elif not any(st.session_state.user_column_mapping.values()): 
                 st.warning("Будь ласка, налаштуйте зіставлення стовпців для CSV файлу (хоча б одне поле).")
                 valid_input = False
            else:
                final_column_mapping_to_pass = st.session_state.user_column_mapping
        
        if valid_input:
            if not st.session_state.get('gcp_creds_initialized_run_app', False) and data_source == "Google Sheet ID":
                st.error("Помилка ініціалізації ключів Google Cloud. Перевірте налаштування секретів та перезавантажте Codespace.")
                return

            with st.spinner("Генеруємо звіт... Це може зайняти деякий час. ⏳"):
                try:
                    current_csv_to_pass = None
                    if csv_file_object_from_ui:
                        csv_file_object_from_ui.seek(0) # Перемотуємо на початок перед передачею
                        current_csv_to_pass = csv_file_object_from_ui

                    print(f"DEBUG: [run_app.py] Calling generate_and_send_report with email='{email_from_ui}', sheet_id='{sheet_id_from_ui}', csv_file is {'provided' if current_csv_to_pass else 'not provided'}, mapping: {final_column_mapping_to_pass}")
                    
                    generate_and_send_report(
                        email=email_from_ui, 
                        sheet_id=sheet_id_from_ui, 
                        csv_file=current_csv_to_pass, 
                        column_mapping=final_column_mapping_to_pass 
                    )
                    st.success(f"✅ Звіт успішно згенеровано та надіслано на {email_from_ui}")
                    
                    st.session_state.sheet_id_input = ""
                    st.session_state.email_input = ""
                    st.session_state.csv_file_uploader_key += 1 
                    st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS}
                    
                    st.rerun()

                except Exception as e:
                    detailed_error_message = f"❌ Виникла помилка під час генерації або надсилання звіту:\n\n{type(e).__name__}: {e}\n\nTraceback:\n{traceback.format_exc()}"
                    st.error(detailed_error_message)
                    print(f"ERROR: [run_app.py] Exception in generate_and_send_report call: {e}") 
                    # traceback.print_exc() вже буде у st.error

if __name__ == "__main__":
    main()