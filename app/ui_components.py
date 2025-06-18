import traceback
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import time # Додано для імітації затримки

# Імпортуємо конфігурацію полів
from app.config_fields import EXPECTED_APP_FIELDS

# Словники з текстами для різних мов
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
        "amount_label": "Сума (якщо є)",
        "google_sheet_id_help": "ID Google Таблиці можна знайти в URL після '/d/' та перед '/edit'."
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
        "error_csv_header_read": "Error reading CSV headers or displaying mapping",
        "client_name_label": "Client Name/Title",
        "task_label": "Task/Service",
        "status_label": "Status",
        "date_label": "Date",
        "comments_label": "Comments",
        "amount_label": "Amount (if any)",
        "google_sheet_id_help": "Google Sheet ID can be found in the URL after '/d/' and before '/edit'."
    }
}

def get_texts(language_code: str = "uk") -> Dict[str, str]:
    return LANGUAGES.get(language_code, LANGUAGES["uk"])

def language_selector() -> str:
    lang_options_display = {"Українська": "uk", "English": "en"}
    # Ініціалізація session_state, якщо її немає
    if 'selected_language_display' not in st.session_state:
        st.session_state.selected_language_display = "Українська"

    selected_lang_display = st.sidebar.selectbox(
        st.session_state.get('current_texts', LANGUAGES['uk'])["select_language"], # Динамічний текст
        options=list(lang_options_display.keys()),
        index=list(lang_options_display.keys()).index(st.session_state.selected_language_display),
        key="language_select_widget_main_v3" # Оновлений ключ
    )
    if st.session_state.selected_language_display != selected_lang_display:
        st.session_state.selected_language_display = selected_lang_display
        # Оновлюємо поточні тексти в session_state
        st.session_state.current_texts = LANGUAGES.get(lang_options_display[selected_lang_display], LANGUAGES["uk"])
        st.rerun()
    return lang_options_display.get(selected_lang_display, "uk")

def display_csv_column_mapping_ui(texts: Dict[str, str], csv_file_obj: Any) -> Optional[Dict[str, str]]:
    if csv_file_obj is None:
        return None
    user_column_mapping_result = None
    try:
        # Переконаємось, що курсор файлу на початку
        csv_file_obj.seek(0)
        df_headers = pd.read_csv(csv_file_obj, nrows=0, encoding='utf-8').columns.tolist()
        csv_file_obj.seek(0) # Знову переміщуємо курсор на початок після читання заголовків

        st.subheader(texts.get("mapping_header", "CSV Column Mapping"))
        st.caption(texts.get("mapping_caption", "Please map your CSV columns."))

        # Ініціалізація user_column_mapping, якщо її немає
        if 'user_column_mapping' not in st.session_state:
            st.session_state.user_column_mapping = {}

        temp_mapping = {}
        cols = st.columns(2)
        col_idx = 0
        for internal_field, display_name_key_in_texts in EXPECTED_APP_FIELDS.items():
            with cols[col_idx % 2]:
                display_name_for_ui = texts.get(display_name_key_in_texts, internal_field.replace("_", " ").title())
                prev_selection = st.session_state.user_column_mapping.get(internal_field, '')
                current_index = 0
                if prev_selection and prev_selection in df_headers:
                    current_index = (df_headers.index(prev_selection) + 1) # +1 через пустий елемент на початку options

                selected_column = st.selectbox(
                    f"{texts.get('select_csv_column_for', 'Select CSV column for')} '{display_name_for_ui}':",
                    options=[''] + df_headers, # Додаємо порожній елемент на початок
                    index=current_index,
                    key=f"map_ui_comp_{internal_field}_v7" # Оновлений ключ
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
    # Ініціалізація session_state для інпутів
    if 'sheet_id_input' not in st.session_state:
        st.session_state.sheet_id_input = ""
    if 'email_input' not in st.session_state:
        st.session_state.email_input = ""
    if 'csv_file_uploader_key' not in st.session_state:
        st.session_state.csv_file_uploader_key = 0 # Додаємо ключ для reset fule_uploader

    data_source = st.radio(
        texts.get("select_data_source", "Select data source:"),
        [texts.get("google_sheet_id_option","Google Sheet ID"), texts.get("csv_file_option","CSV File")],
        key="data_source_radio_ui_v3", # Оновлений ключ
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
            help=texts.get("google_sheet_id_help", "ID Google Sheet can be found in the URL after '/d/' and before '/edit'."), # Додана підказка
            key="sheet_id_text_input_ui_v3" # Оновлений ключ
        )
        sheet_id_val = st.session_state.sheet_id_input.strip()
        
        # Очищення мапування та завантаженого файлу, якщо переключилися на Google Sheet ID
        if 'user_column_mapping' in st.session_state and any(st.session_state.user_column_mapping.values()):
            st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS.keys()}
        if 'csv_file_obj' in st.session_state and st.session_state.csv_file_obj is not None:
            st.session_state.csv_file_obj = None # Очистити завантажений файл
            st.session_state.csv_file_uploader_key += 1 # Змінити ключ для reset file_uploader
            st.rerun() # Перезапустити, щоб оновити file_uploader

    else: # CSV File
        csv_file_obj_val = st.file_uploader(
            texts.get("upload_csv_file", "Upload CSV file"),
            type=["csv"],
            key=f"file_uploader_ui_v3_{st.session_state.csv_file_uploader_key}" # Оновлений ключ
        )
        st.session_state.csv_file_obj = csv_file_obj_val # Зберігаємо об'єкт файлу в session_state
        st.session_state.sheet_id_input = "" # Очищуємо поле Google Sheet ID

        if csv_file_obj_val is not None:
            column_mapping_val = display_csv_column_mapping_ui(texts, csv_file_obj_val)
            if column_mapping_val is None:
                # Якщо мапування не вдалося, скидаємо файл
                csv_file_obj_val = None
                st.session_state.csv_file_obj = None
                st.session_state.csv_file_uploader_key += 1 # Змінюємо ключ, щоб Streamlit скинув file_uploader
                st.rerun() # Перезапускаємо додаток для відображення змін

    st.session_state.email_input = st.text_input(
        texts.get("enter_client_email", "Enter client's email:"),
        value=st.session_state.email_input,
        placeholder="example@email.com",
        key="email_text_input_ui_v3" # Оновлений ключ
    )
    email_val = st.session_state.email_input.strip()

    return data_source, sheet_id_val, csv_file_obj_val, email_val, column_mapping_val

# Налаштування сторінки Streamlit
st.set_page_config(
    page_title=LANGUAGES["uk"]["page_title"], # Початкова назва, буде оновлена
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Ініціалізація current_texts у session_state
if 'current_texts' not in st.session_state:
    st.session_state.current_texts = LANGUAGES["uk"]
if 'user_column_mapping' not in st.session_state:
    st.session_state.user_column_mapping = {}
if 'csv_file_obj' not in st.session_state:
    st.session_state.csv_file_obj = None


# Оберіть мову (в сайдбарі)
# Цей рядок відповідає за вибір мови і оновлює st.session_state.current_texts
selected_lang_code = language_selector()
texts = st.session_state.current_texts # Отримуємо поточні тексти

# Основний контент сторінки
st.markdown(f"<h1 style='text-align: center; color: #2C3E50;'>{texts['app_title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #7F8C8D; font-size: 1.1em;'>{texts['app_subtitle']}</p>", unsafe_allow_html=True)

# Роздільник
st.markdown("---")

# Контейнер для повідомлень про стан
status_message_placeholder = st.empty()


data_source, sheet_id_val, csv_file_obj_val, email_val, column_mapping_val = build_main_input_section(texts)

# Додаємо візуальний роздільник перед кнопкою
st.markdown("<br>", unsafe_allow_html=True) # Додатковий відступ

if st.button(texts["generate_button"]):
    status_message_placeholder.empty() # Очищуємо попередні повідомлення

    # Перевірка введених даних
    is_valid = True
    if data_source == texts.get("google_sheet_id_option"):
        if not sheet_id_val:
            status_message_placeholder.warning(texts.get("warning_enter_gsheet_id"))
            is_valid = False
    elif data_source == texts.get("csv_file_option"):
        if csv_file_obj_val is None:
            status_message_placeholder.warning(texts.get("warning_upload_csv"))
            is_valid = False
        elif not column_mapping_val or not any(column_mapping_val.values()):
            status_message_placeholder.warning(texts.get("warning_setup_mapping"))
            is_valid = False

    if not email_val:
        status_message_placeholder.warning(texts.get("warning_enter_email"))
        is_valid = False

    if is_valid:
        try:
            with status_message_placeholder.spinner(texts.get("spinner_generating")):
                # Тут буде ваш реальний код для генерації та відправки звіту
                # Наразі це імітація:
                time.sleep(3) # Імітація роботи

                status_message_placeholder.success(f"{texts.get('success_report_sent')} {email_val}!")
                st.balloons() # Веселі кульки на честь успіху
                
                # Очищення полів форми після успішної відправки (за бажанням)
                st.session_state.sheet_id_input = ""
                st.session_state.email_input = ""
                st.session_state.user_column_mapping = {key: '' for key in EXPECTED_APP_FIELDS.keys()}
                # Для file_uploader потрібно змінити ключ, щоб скинути його
                st.session_state.csv_file_uploader_key += 1
                st.session_state.csv_file_obj = None # Очищуємо об'єкт файлу
                
                # Перезапускаємо додаток, щоб очистити UI (альтернатива - просто залишити повідомлення про успіх)
                # st.rerun() 

        except Exception as e:
            status_message_placeholder.error(f"{texts.get('error_report_generation')}\n\n```\n{e}\n```")
            traceback.print_exc()
    else:
        # Якщо is_valid == False, повідомлення вже було показано вище
        pass

st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #adb5bd; font-size: 0.9em;'>© 2024 {texts['app_title'].replace('📋 ', '')}. All rights reserved.</p>", unsafe_allow_html=True)