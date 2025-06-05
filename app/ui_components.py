# /workspaces/auto-report-generator/app/ui_components.py
import traceback
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple

# Імпортуємо конфігурацію полів
from app.config_fields import EXPECTED_APP_FIELDS # Змінено на абсолютний імпорт

# Словники з текстами для різних мов (LANGUAGES) ...
# ... (Код для LANGUAGES, get_texts, language_selector залишається таким, як у попередній версії Canvas) ...
# Ось повний код для ui_components.py з попереднього разу, з виправленим імпортом:

LANGUAGES = {
    "uk": {
        "page_title": "Генератор Звітів",
        "app_title": "📋 АВТО-ГЕНЕРАТОР ЗВІТІВ",
        "app_subtitle": "Згенеруйте звіт 🧾 і отримаєте його на email 📩",
        "select_language": "Оберіть мову:",
        "select_data_source": "Оберіть джерело даних:",
        "google_sheet_id_option": "Google Sheet ID",
        "csv_file_option": "CSV файл",
        "enter_google_sheet_id": "Введіть Google Sheet ID:",
        "upload_csv_file": "Завантажте CSV файл",
        "enter_client_email": "Введіть email клієнта для надсилання звіту:",
        "generate_button": "🚀 Згенерувати та надіслати звіт",
        "mapping_header": "⚙️ Зіставлення стовпців вашого CSV файлу",
        "mapping_caption": "Будь ласка, вкажіть, які стовпці з вашого файлу відповідають необхідним полям. Якщо відповідного стовпця немає, залиште порожнім.",
        "report_field_prefix": "Поле звіту",
        "select_csv_column_for": "Оберіть стовпець CSV для",
        "warning_enter_email": "Будь ласка, введіть email клієнта.",
        "warning_enter_gsheet_id": "Будь ласка, введіть Google Sheet ID.",
        "warning_upload_csv": "Будь ласка, завантажте CSV файл.",
        "warning_setup_mapping": "Будь ласка, налаштуйте зіставлення стовпців для CSV файлу (хоча б одне поле).",
        "error_gcp_init": "Помилка ініціалізації ключів Google Cloud. Перевірте налаштування секретів та перезавантажте Codespace.",
        "spinner_generating": "Генеруємо звіт... Це може зайняти деякий час. ⏳",
        "success_report_sent": "✅ Звіт успішно згенеровано та надіслано на",
        "error_report_generation": "❌ Виникла помилка під час генерації або надсилання звіту:",
        "error_csv_header_read": "Помилка при читанні заголовків CSV або відображенні мапування",
        "client_name_label": "Ім'я/Назва Клієнта",
        "task_label": "Завдання/Послуга",
        "status_label": "Статус",
        "date_label": "Дата",
        "comments_label": "Коментарі",
        "amount_label": "Сума (якщо є)"
    },
    "en": { # Додайте сюди повні переклади для англійської, якщо потрібно
        "page_title": "Report Generator",
        "app_title": "📋 AUTO-REPORT-GENERATOR",
        "app_subtitle": "Generate a report 🧾 and receive it via email 📩",
        "select_language": "Select language:",
        "select_data_source": "Select data source:",
        "google_sheet_id_option": "Google Sheet ID",
        "csv_file_option": "CSV File",
        "enter_google_sheet_id": "Enter Google Sheet ID:",
        "upload_csv_file": "Upload CSV file",
        "enter_client_email": "Enter client's email to send the report:",
        "generate_button": "🚀 Generate and Send Report",
        "mapping_header": "⚙️ Map Columns from Your CSV File",
        "mapping_caption": "Please specify which columns from your file correspond to the required report fields. If a corresponding column does not exist, leave the selection blank.",
        "report_field_prefix": "Report field",
        "select_csv_column_for": "Select CSV column for",
        "warning_enter_email": "Please enter the client's email.",
        "warning_enter_gsheet_id": "Please enter the Google Sheet ID.",
        "warning_upload_csv": "Please upload a CSV file.",
        "warning_setup_mapping": "Please set up column mapping for the CSV file (at least one field).",
        "error_gcp_init": "Error initializing Google Cloud keys. Check secret settings and reload Codespace.",
        "spinner_generating": "Generating report... This may take some time. ⏳",
        "success_report_sent": "✅ Report successfully generated and sent to",
        "error_report_generation": "❌ An error occurred while generating or sending the report:",
        "error_csv_header_read": "Error reading CSV headers or displaying mapping",
        "client_name_label": "Client Name/Title",
        "task_label": "Task/Service",
        "status_label": "Status",
        "date_label": "Date",
        "comments_label": "Comments",
        "amount_label": "Amount (if any)"
    }
}

def get_texts(language_code: str = "uk") -> Dict[str, str]:
    return LANGUAGES.get(language_code, LANGUAGES["uk"])

def language_selector() -> str:
    lang_options_display = {"Українська": "uk", "English": "en"}
    if 'selected_language_display' not in st.session_state:
        st.session_state.selected_language_display = "Українська" 
    selected_lang_display = st.sidebar.selectbox(
        "Оберіть мову / Select language:", 
        options=list(lang_options_display.keys()),
        index=list(lang_options_display.keys()).index(st.session_state.selected_language_display),
        key="language_select_widget_main_v2" # Оновлений ключ
    )
    if st.session_state.selected_language_display != selected_lang_display:
        st.session_state.selected_language_display = selected_lang_display
        st.rerun()
    return lang_options_display.get(selected_lang_display, "uk")

def display_csv_column_mapping_ui(texts: Dict[str, str], csv_file_obj: Any) -> Optional[Dict[str, str]]:
    if csv_file_obj is None:
        return None
    user_column_mapping_result = None
    try:
        df_headers = pd.read_csv(csv_file_obj, nrows=0, encoding='utf-8').columns.tolist()
        csv_file_obj.seek(0) 
        st.subheader(texts.get("mapping_header", "CSV Column Mapping"))
        st.caption(texts.get("mapping_caption", "Please map your CSV columns."))
        temp_mapping = {}
        cols = st.columns(2) 
        col_idx = 0
        for internal_field, display_name_key_in_texts in EXPECTED_APP_FIELDS.items(): # Використовуємо імпортований EXPECTED_APP_FIELDS
            with cols[col_idx % 2]:
                display_name_for_ui = texts.get(display_name_key_in_texts, internal_field.replace("_", " ").title())
                prev_selection = st.session_state.user_column_mapping.get(internal_field, '')
                current_index = 0
                if prev_selection and prev_selection in df_headers:
                    current_index = (df_headers.index(prev_selection) + 1)
                selected_column = st.selectbox(
                    f"{texts.get('select_csv_column_for', 'Map for')} '{display_name_for_ui}':",
                    options=[''] + df_headers, 
                    index=current_index,
                    key=f"map_ui_comp_{internal_field}_v6" 
                )
                if selected_column: 
                    temp_mapping[internal_field] = selected_column
            col_idx += 1
        st.session_state.user_column_mapping = temp_mapping
        user_column_mapping_result = temp_mapping
    except Exception as e:
        st.error(f"{texts.get('error_csv_header_read', 'Error reading CSV headers')}: {e}")
        traceback.print_exc()
        return None 
    return user_column_mapping_result

def build_main_input_section(texts: Dict[str, str]) -> Tuple[str, Optional[str], Optional[Any], Optional[str], Optional[Dict[str,str]]]:
    data_source = st.radio(
        texts.get("select_data_source", "Select data source:"), 
        [texts.get("google_sheet_id_option","Google Sheet ID"), texts.get("csv_file_option","CSV File")], 
        key="data_source_radio_ui_v2",
        horizontal=True
    )
    sheet_id_val = None
    csv_file_obj_val = None
    column_mapping_val = None

    if data_source == texts.get("google_sheet_id_option","Google Sheet ID"):
        st.session_state.sheet_id_input = st.text_input(
            texts.get("enter_google_sheet_id","Enter Google Sheet ID:"), 
            value=st.session_state.sheet_id_input, 
            placeholder="Наприклад, 1abc2def3ghi_JKLMN...",
            key="sheet_id_text_input_ui_v2"
        )
        sheet_id_val = st.session_state.sheet_id_input.strip()
        if any(st.session_state.user_column_mapping.values()):
            st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS.keys()}
    else: 
        csv_file_obj_val = st.file_uploader(
            texts.get("upload_csv_file", "Upload CSV file"), 
            type=["csv"], 
            key=f"file_uploader_ui_v2_{st.session_state.csv_file_uploader_key}" 
        )
        st.session_state.sheet_id_input = "" 
        if csv_file_obj_val is not None:
            column_mapping_val = display_csv_column_mapping_ui(texts, csv_file_obj_val)
            if column_mapping_val is None: 
                csv_file_obj_val = None 
    st.session_state.email_input = st.text_input(
        texts.get("enter_client_email", "Enter client's email:"), 
        value=st.session_state.email_input,
        placeholder="example@email.com",
        key="email_text_input_ui_v2"
    )
    email_val = st.session_state.email_input.strip()
    return data_source, sheet_id_val, csv_file_obj_val, email_val, column_mapping_val
