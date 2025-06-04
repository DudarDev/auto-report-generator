# /workspaces/auto-report-generator/app/ui_components.py
import traceback
import streamlit as st
import pandas as pd # Для читання заголовків CSV у функції мапування
from typing import Dict, List, Optional, Any # Додано Any

# Словники з текстами для різних мов
# Ви можете розширити цей словник або завантажувати тексти з JSON/YAML файлів
LANGUAGES = {
    "uk": {
        "page_title": "Генератор Звітів",
        "app_title": "📋 АВТО-ГЕНЕРАТОР ЗВІТІВ",
        "app_subtitle": "Згенеруйте звіт 🧾 і отримайте його на email 📩",
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
        # Додайте сюди переклади для назв полів з EXPECTED_APP_FIELDS
        "client_name_label": "Ім'я/Назва Клієнта",
        "task_label": "Завдання/Послуга",
        "status_label": "Статус",
        "date_label": "Дата",
        "comments_label": "Коментарі",
        "amount_label": "Сума (якщо є)"
    },
    "en": {
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
        "client_name_label": "Client Name/Title",
        "task_label": "Task/Service",
        "status_label": "Status",
        "date_label": "Date",
        "comments_label": "Comments",
        "amount_label": "Amount (if any)"
    }
}

def get_texts(language_code: str = "uk") -> Dict[str, str]:
    """Повертає словник текстів для обраної мови."""
    return LANGUAGES.get(language_code, LANGUAGES["uk"])

def language_selector() -> str:
    """Створює селектор мови у бічній панелі та повертає код обраної мови."""
    lang_options_display = {"Українська": "uk", "English": "en"}
    
    # Використовуємо st.session_state для збереження обраної мови
    if 'selected_language_display' not in st.session_state:
        st.session_state.selected_language_display = "Українська" # Мова за замовчуванням

    # Отримуємо поточні тексти для підпису селектора
    # Це створить невелику залежність, але дозволить перекласти сам селектор
    # Можна обійти, якщо підпис селектора буде двомовним одразу
    temp_texts = get_texts(lang_options_display.get(st.session_state.selected_language_display, "uk"))

    selected_lang_display = st.sidebar.selectbox(
        temp_texts.get("select_language", "Оберіть мову / Select language:"), 
        options=list(lang_options_display.keys()),
        key="language_select_widget" # Ключ для віджета
    )
    st.session_state.selected_language_display = selected_lang_display # Оновлюємо стан
    return lang_options_display.get(selected_lang_display, "uk")

def display_csv_column_mapping_ui(texts: Dict[str, str], csv_file_obj: Any, expected_app_fields: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Відображає UI для мапування стовпців CSV та повертає мапування."""
    if csv_file_obj is None:
        return None
    
    user_column_mapping = None
    try:
        df_headers = pd.read_csv(csv_file_obj, nrows=0, encoding='utf-8').columns.tolist()
        csv_file_obj.seek(0) 

        st.subheader(texts["mapping_header"])
        st.caption(texts["mapping_caption"])
        
        temp_mapping = {}
        # Використовуємо st.columns для кращого розташування
        num_fields = len(expected_app_fields)
        cols_per_row = 2 
        
        field_keys = list(expected_app_fields.keys())

        for i in range(0, num_fields, cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < num_fields:
                    with cols[j]:
                        internal_field = field_keys[i+j]
                        # Отримуємо перекладену назву поля з `texts` або використовуємо `display_name` з `expected_app_fields`
                        display_name_for_field = texts.get(expected_app_fields[internal_field], expected_app_fields[internal_field])
                        
                        # Відновлюємо попередній вибір користувача
                        prev_selection = st.session_state.user_column_mapping.get(internal_field, '')
                        current_index = 0
                        if prev_selection and prev_selection in df_headers:
                            current_index = (df_headers.index(prev_selection) + 1)
                        
                        selected_column = st.selectbox(
                            f"{texts.get('select_csv_column_for', 'Select CSV column for')} '{display_name_for_field}':",
                            options=[''] + df_headers, 
                            index=current_index,
                            key=f"map_ui_{internal_field}_v4" # Унікальні ключі
                        )
                        if selected_column: 
                            temp_mapping[internal_field] = selected_column
        
        st.session_state.user_column_mapping = temp_mapping
        user_column_mapping = temp_mapping

    except Exception as e:
        st.error(f"{texts.get('error_csv_header_read', 'Помилка при читанні заголовків CSV')}: {e}")
        traceback.print_exc()
        return None # Повертаємо None у разі помилки
        
    return user_column_mapping
