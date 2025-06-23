# /workspaces/auto-report-generator/app/ui_components.py

import streamlit as st
import pandas as pd
import traceback
from typing import Dict, Optional, Any, Tuple

# Імпортуємо конфігурацію полів
from app.config_fields import EXPECTED_APP_FIELDS, APP_INTERNAL_KEYS

# Словники з текстами для різних мов (це їхнє правильне місце)
LANGUAGES = {
    "uk": {
        "page_title": "Генератор Звітів",
        "app_title": "📋 Авто-генератор Звітів",
        "app_subtitle": "Згенеруйте звіт 🧾 і отримайте його на email 📩",
        "select_language": "Оберіть мову:",
        "select_data_source": "Оберіть джерело даних:",
        "google_sheet_id_option": "Google Sheet ID",
        "csv_file_option": "CSV файл",
        "enter_google_sheet_id": "Введіть Google Sheet ID:",
        "upload_csv_file": "Завантажте CSV файл",
        "enter_client_email": "Введіть email для надсилання звіту:",
        "generate_button": "🚀 Згенерувати та надіслати звіт",
        "mapping_header": "⚙️ Зіставлення стовпців вашого CSV",
        "mapping_caption": "Будь ласка, вкажіть, які стовпці з вашого файлу відповідають необхідним полям.",
        "select_csv_column_for": "Оберіть стовпець CSV для",
        "warning_enter_email": "Будь ласка, введіть email.",
        "warning_enter_gsheet_id": "Будь ласка, введіть Google Sheet ID.",
        "warning_upload_csv": "Будь ласка, завантажте CSV файл.",
        "warning_setup_mapping": "Будь ласка, налаштуйте зіставлення стовпців (хоча б одне поле).",
        "error_gcp_init": "Помилка ініціалізації ключів Google Cloud. Перевірте налаштування.",
        "spinner_generating": "Генеруємо звіт... Це може зайняти деякий час. ⏳",
        "success_report_sent": "✅ Звіт успішно надіслано на",
        "error_report_generation": "❌ Виникла помилка під час генерації звіту:",
        "error_csv_header_read": "Помилка при читанні заголовків CSV",
        "google_sheet_id_help": "ID Google Таблиці можна знайти в URL після '/d/' та перед '/edit'."
    },
    "en": {
        # ... тут англійські переклади ...
        "page_title": "Report Generator",
        "app_title": "📋 Auto-Report Generator",
        "app_subtitle": "Generate a report 🧾 and receive it via email 📩",
        "select_language": "Select language:",
        "select_data_source": "Select data source:",
        "google_sheet_id_option": "Google Sheet ID",
        "csv_file_option": "CSV File",
        "enter_google_sheet_id": "Enter Google Sheet ID:",
        "upload_csv_file": "Upload CSV file",
        "enter_client_email": "Enter email to send the report:",
        "generate_button": "🚀 Generate and Send Report",
        "mapping_header": "⚙️ Map Columns from Your CSV",
        "mapping_caption": "Please specify which columns from your file correspond to the required fields.",
        "select_csv_column_for": "Select CSV column for",
        "warning_enter_email": "Please enter an email.",
        "warning_enter_gsheet_id": "Please enter the Google Sheet ID.",
        "warning_upload_csv": "Please upload a CSV file.",
        "warning_setup_mapping": "Please set up column mapping (at least one field).",
        "error_gcp_init": "Error initializing Google Cloud keys. Check your settings.",
        "spinner_generating": "Generating report... This may take some time. ⏳",
        "success_report_sent": "✅ Report successfully sent to",
        "error_report_generation": "❌ An error occurred while generating the report:",
        "error_csv_header_read": "Error reading CSV headers",
        "google_sheet_id_help": "Google Sheet ID can be found in the URL after '/d/' and before '/edit'."
    }
}

def get_texts(language_code: str = "uk") -> Dict[str, str]:
    """Повертає словник з текстами для вказаної мови."""
    return LANGUAGES.get(language_code, LANGUAGES["uk"])

def language_selector() -> str:
    """Створює віджет для вибору мови і повертає код вибраної мови."""
    lang_options_display = {"Українська": "uk", "English": "en"}
    
    # Визначаємо поточний індекс для selectbox
    # Це робить код стійким, навіть якщо st.session_state ще не ініціалізовано
    current_lang_display = st.session_state.get('selected_language_display', "Українська")
    try:
        current_index = list(lang_options_display.keys()).index(current_lang_display)
    except ValueError:
        current_index = 0 # За замовчуванням 'Українська'

    # Отримуємо текст для віджета на поточній мові
    texts = get_texts(st.session_state.get('selected_language_code', 'uk'))

    selected_lang_display = st.sidebar.selectbox(
        label=texts["select_language"],
        options=list(lang_options_display.keys()),
        index=current_index,
        key="language_select_widget_main_v3" # Цей ключ тепер буде унікальним
    )

    # Оновлюємо стан і перезапускаємо додаток, ТІЛЬКИ ЯКЩО мова змінилася
    if st.session_state.get('selected_language_display') != selected_lang_display:
        st.session_state.selected_language_display = selected_lang_display
        st.session_state.selected_language_code = lang_options_display[selected_lang_display]
        st.rerun()
        
    return lang_options_display.get(selected_lang_display, "uk")

def display_csv_column_mapping_ui(texts: Dict[str, str], csv_file_obj: Any) -> Optional[Dict[str, str]]:
    """Створює UI для зіставлення стовпців CSV файлу."""
    if csv_file_obj is None:
        return None

    try:
        csv_file_obj.seek(0)
        df_headers = pd.read_csv(csv_file_obj, nrows=0, encoding='utf-8').columns.tolist()
        csv_file_obj.seek(0)

        st.subheader(texts["mapping_header"])
        st.caption(texts["mapping_caption"])

        temp_mapping = {}
        cols = st.columns(2)
        for i, (internal_field, display_name_key) in enumerate(EXPECTED_APP_FIELDS.items()):
            with cols[i % 2]:
                display_name = texts.get(display_name_key, internal_field.replace("_", " ").title())
                
                # Попередній вибір, якщо він є в session_state
                prev_selection = st.session_state.user_column_mapping.get(internal_field, '')
                index = 0
                if prev_selection and prev_selection in df_headers:
                    index = df_headers.index(prev_selection) + 1 # +1 бо options починається з ''

                selected_column = st.selectbox(
                    label=f"{texts['select_csv_column_for']} '{display_name}':",
                    options=[''] + df_headers,
                    index=index,
                    key=f"map_select_{internal_field}" # Унікальний ключ для кожного поля
                )
                if selected_column:
                    temp_mapping[internal_field] = selected_column
        
        # Оновлюємо стан лише якщо щось змінилося
        if temp_mapping != st.session_state.user_column_mapping:
            st.session_state.user_column_mapping = temp_mapping
            st.rerun() # Перезапуск для фіксації змін

        return st.session_state.user_column_mapping

    except Exception as e:
        st.error(f"{texts['error_csv_header_read']}: {e}")
        traceback.print_exc()
        return None

def build_main_input_section(texts: Dict[str, str]) -> Tuple[str, Optional[str], Optional[Any], Optional[str], Optional[Dict[str, str]]]:
    """Будує основну секцію вводу даних і повертає введені значення."""
    data_source = st.radio(
        label=texts["select_data_source"],
        options=[texts["google_sheet_id_option"], texts["csv_file_option"]],
        key="data_source_radio",
        horizontal=True
    )

    sheet_id_val, csv_file_obj_val, column_mapping_val = None, None, None

    if data_source == texts["google_sheet_id_option"]:
        sheet_id_val = st.text_input(
            label=texts["enter_google_sheet_id"],
            value=st.session_state.get('sheet_id_input', ''),
            placeholder="Наприклад, 1abc2def3ghi_JKLMN...",
            help=texts["google_sheet_id_help"],
            key="sheet_id_input"
        ).strip()
    else: # CSV File
        csv_file_obj_val = st.file_uploader(
            label=texts["upload_csv_file"],
            type=["csv"],
            key=f"file_uploader_{st.session_state.csv_file_uploader_key}"
        )
        if csv_file_obj_val:
            column_mapping_val = display_csv_column_mapping_ui(texts, csv_file_obj_val)

    email_val = st.text_input(
        label=texts["enter_client_email"],
        value=st.session_state.get('email_input', ''),
        placeholder="example@email.com",
        key="email_input"
    ).strip()

    return data_source, sheet_id_val, csv_file_obj_val, email_val, column_mapping_val