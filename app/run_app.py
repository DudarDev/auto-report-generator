# /workspaces/auto-report-generator/app/run_app.py
import streamlit as st
from dotenv import load_dotenv
import os
import json
import traceback
import pandas as pd # Потрібен для читання заголовків CSV

# --- ПОЧАТОК БЛОКУ ІНІЦІАЛІЗАЦІЇ СЕКРЕТІВ ТА GCP ---
# Цей блок має виконуватися один раз при старті або перезапуску скрипта
if 'secrets_initialized' not in st.session_state:
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
            
            temp_creds_file_path = os.path.join(temp_dir, "gcp_service_account_streamlit.json") # Унікальне ім'я файлу

            with open(temp_creds_file_path, 'w') as temp_file:
                temp_file.write(gcp_creds_json_string)
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_creds_file_path 
            print(f"SUCCESS: [run_app.py] GOOGLE_APPLICATION_CREDENTIALS set to: {temp_creds_file_path}")
            st.session_state.gcp_creds_initialized = True
        except Exception as e:
            print(f"ERROR: [run_app.py] Failed to set up GCP credentials from env var 'GOOGLE_CREDENTIALS_JSON': {e}")
            traceback.print_exc()
            st.session_state.gcp_creds_initialized = False
    else:
        print("WARNING: [run_app.py] GOOGLE_CREDENTIALS_JSON environment variable for Google Cloud not found.")
        st.session_state.gcp_creds_initialized = False

    if not os.environ.get('GEMINI_API_KEY'):
        print("WARNING: [run_app.py] GEMINI_API_KEY environment variable not found.")
    # Додайте інші перевірки секретів тут, якщо потрібно
    st.session_state.secrets_initialized = True # Позначаємо, що ініціалізація відбулася
# --- КІНЕЦЬ БЛОКУ ІНІЦІАЛІЗАЦІЇ ---

# Імпортуємо ваш основний модуль ПІСЛЯ потенційної ініціалізації
from app.report_generator import generate_and_send_report

# Внутрішні стандартні поля, які очікує ваш звіт (ключі) та їх опис для UI
# Ці ключі буде використовувати context_builder.py
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

    # Ініціалізація змінних сесії для збереження стану UI
    if 'sheet_id_input' not in st.session_state:
        st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state:
        st.session_state.email_input = ""
    if 'csv_file_uploader_key' not in st.session_state: # Для скидання стану file_uploader
        st.session_state.csv_file_uploader_key = 0
    if 'user_column_mapping' not in st.session_state: # Для збереження мапування користувача
        st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS}


    data_source = st.radio(
        "Оберіть джерело даних:", 
        ["Google Sheet ID", "CSV файл"], 
        key="data_source_radio",
        horizontal=True
    )
    
    sheet_id_from_ui = None
    csv_file_object_from_ui = None
    # user_column_mapping буде братися з st.session_state.user_column_mapping

    if data_source == "Google Sheet ID":
        st.session_state.sheet_id_input = st.text_input(
            "Введіть Google Sheet ID:", 
            value=st.session_state.sheet_id_input, 
            placeholder="Наприклад, 1abc2def3ghi_JKLMN...",
            key="sheet_id_text_input_main_v2" # Унікальний ключ
        )
        sheet_id_from_ui = st.session_state.sheet_id_input.strip()
        # Якщо обрано Google Sheet, мапування не потрібне (припускаємо, що структура таблиці відома
        # або gsheet.py обробляє це на основі назв стовпців з env vars, якщо вони є)
        # st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS} # Скидаємо мапування
    
    else: # data_source == "CSV файл"
        csv_file_object_from_ui = st.file_uploader(
            "Завантажте CSV файл", 
            type=["csv"], 
            key=f"file_uploader_{st.session_state.csv_file_uploader_key}" 
        )
        st.session_state.sheet_id_input = "" # Скидаємо sheet_id

        if csv_file_object_from_ui is not None:
            try:
                # Важливо: st.file_uploader повертає BytesIO або подібний об'єкт.
                # Pandas може читати його напряму.
                df_headers = pd.read_csv(csv_file_object_from_ui, nrows=0).columns.tolist()
                csv_file_object_from_ui.seek(0) # Дуже важливо "перемотати" файл на початок!

                st.subheader("⚙️ Зіставлення стовпців вашого CSV файлу")
                st.caption("Будь ласка, вкажіть, які стовпці з вашого файлу відповідають необхідним полям для звіту. Якщо відповідного стовпця немає, залиште поле порожнім.")
                
                temp_mapping = {}
                cols = st.columns(2) # Для кращого вигляду мапування
                col_idx = 0
                for internal_field, display_name in EXPECTED_APP_FIELDS.items():
                    with cols[col_idx % 2]:
                        # Відновлюємо попередній вибір користувача
                        prev_selection = st.session_state.user_column_mapping.get(internal_field, '')
                        # Якщо попереднього вибору немає в поточних заголовках, скидаємо його
                        current_index = 0
                        if prev_selection and prev_selection in df_headers:
                            current_index = (df_headers.index(prev_selection) + 1)
                        
                        selected_column = st.selectbox(
                            f"{display_name}:", # Коротший підпис
                            options=[''] + df_headers, # Порожній варіант для "не зіставляти"
                            index=current_index,
                            key=f"map_{internal_field}_v2" # Унікальний ключ
                        )
                        if selected_column: 
                            temp_mapping[internal_field] = selected_column
                    col_idx += 1
                
                st.session_state.user_column_mapping = temp_mapping

            except Exception as e:
                st.error(f"Помилка при читанні заголовків CSV або відображенні мапування: {e}")
                traceback.print_exc()
                csv_file_object_from_ui = None # Скидаємо файл, якщо помилка

    st.session_state.email_input = st.text_input(
        "Введіть email клієнта для надсилання звіту:", 
        value=st.session_state.email_input,
        placeholder="example@email.com",
        key="email_text_input_main_v2"
    )
    email_from_ui = st.session_state.email_input.strip()

    if st.button("🚀 Згенерувати та надіслати звіт"):
        valid_input = True
        if not email_from_ui:
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
            elif not any(st.session_state.user_column_mapping.values()): # Перевірка, чи хоча б одне поле зіставлено
                 st.warning("Будь ласка, налаштуйте зіставлення стовпців для CSV файлу (хоча б одне поле).")
                 valid_input = False
            else:
                final_column_mapping_to_pass = st.session_state.user_column_mapping
        
        if valid_input:
            # Перевірка ініціалізації GCP credentials перед викликом
            if not st.session_state.get('gcp_creds_initialized', False) and (data_source == "Google Sheet ID" or (data_source == "CSV файл" and any("google" in str(v).lower() for v in EXPECTED_APP_FIELDS.values()))): # Проста перевірка, якщо GCP потрібен
                st.error("Помилка ініціалізації ключів Google Cloud. Перевірте налаштування секретів та перезавантажте Codespace.")
                return

            with st.spinner("Генеруємо звіт... Це може зайняти деякий час. ⏳"):
                try:
                    print(f"DEBUG: Calling generate_and_send_report with email='{email_from_ui}', sheet_id='{sheet_id_from_ui}', csv_file is {'provided' if csv_file_object_from_ui else 'not provided'}, mapping: {final_column_mapping_to_pass}")
                    
                    # Передаємо об'єкт файлу, а не його вміст, якщо це CSV
                    current_csv_file_to_pass = csv_file_object_from_ui
                    if current_csv_file_to_pass:
                        current_csv_file_to_pass.seek(0) # Перемотуємо на початок перед передачею

                    generate_and_send_report(
                        email=email_from_ui, 
                        sheet_id=sheet_id_from_ui, 
                        csv_file=current_csv_file_to_pass, 
                        column_mapping=final_column_mapping_to_pass 
                    )
                    st.success(f"✅ Звіт успішно згенеровано та надіслано на {email_from_ui}")
                    
                    # Очищення полів після успішної відправки
                    st.session_state.sheet_id_input = ""
                    st.session_state.email_input = ""
                    st.session_state.csv_file_uploader_key += 1 
                    st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS} # Скидаємо мапування
                    
                    st.rerun()

                except Exception as e:
                    detailed_error_message = f"❌ Виникла помилка під час генерації або надсилання звіту:\n\n{e}\n\nTraceback:\n{traceback.format_exc()}"
                    st.error(detailed_error_message)
                    print(f"ERROR in generate_and_send_report call from Streamlit: {e}") 
                    # traceback.print_exc() вже буде у st.error

if __name__ == "__main__":
    main()
