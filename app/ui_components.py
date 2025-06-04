import streamlit as st

# Словники з текстами для різних мов
LANGUAGES = {
    "uk": {
        "title": "📋 АВТО-ГЕНЕРАТОР ЗВІТІВ",
        "subtitle": "Згенеруйте звіт 🧾 і отримаєте його на email 📩",
        "select_data_source": "Оберіть джерело даних:",
        "google_sheet_id_option": "Google Sheet ID",
        "csv_file_option": "CSV файл",
        "enter_google_sheet_id": "Введіть Google Sheet ID:",
        "upload_csv_file": "Завантажте CSV файл",
        "enter_client_email": "Введіть email клієнта для надсилання звіту:",
        "generate_button": "🚀 Згенерувати та надіслати звіт",
        "mapping_header": "⚙️ Зіставлення стовпців вашого CSV файлу",
        "mapping_caption": "Будь ласка, вкажіть...",
        "report_field": "Поле для звіту",
        "select_csv_column": "Оберіть стовпець з вашого CSV:",
        # ... інші тексти ...
    },
    "en": {
        "title": "📋 AUTO-REPORT-GENERATOR",
        "subtitle": "Generate a report 🧾 and receive it via email 📩",
        "select_data_source": "Select data source:",
        "google_sheet_id_option": "Google Sheet ID",
        "csv_file_option": "CSV File",
        "enter_google_sheet_id": "Enter Google Sheet ID:",
        "upload_csv_file": "Upload CSV file",
        "enter_client_email": "Enter client's email to send the report:",
        "generate_button": "🚀 Generate and Send Report",
        "mapping_header": "⚙️ Map Columns from Your CSV File",
        "mapping_caption": "Please specify which columns...",
        "report_field": "Report Field",
        "select_csv_column": "Select column from your CSV:",
        # ... other texts ...
    }
}

def get_texts(language_code="uk"):
    """Повертає словник текстів для обраної мови."""
    return LANGUAGES.get(language_code, LANGUAGES["uk"]) # За замовчуванням українська

def language_selector():
    """Створює селектор мови."""
    # Мови можна винести в конфігурацію
    lang_options = {"Українська": "uk", "English": "en"}
    selected_lang_display = st.sidebar.selectbox(
        "Оберіть мову / Select language:", 
        options=list(lang_options.keys())
    )
    return lang_options.get(selected_lang_display, "uk")

def build_main_ui(texts, expected_app_fields):
    """Будує основні елементи UI, використовуючи надані тексти."""
    st.title(texts["title"])
    st.markdown(texts["subtitle"])

    # ... (решта вашого UI з app/run_app.py, але замість захардкоджених рядків 
    #      використовуйте texts["ключ_тексту"]) ...
    # Наприклад:
    # data_source = st.radio(
    #     texts["select_data_source"], 
    #     [texts["google_sheet_id_option"], texts["csv_file_option"]], 
    #     key="data_source_radio_main",
    #     horizontal=True
    # )
    # ... і так далі для всіх st.text_input, st.button, st.subheader ...

    # Логіка мапування стовпців також може бути тут або в окремій функції
    # for internal_field, display_name_key_in_texts in expected_app_fields.items():
    #     display_name_for_ui = texts.get(internal_field, display_name_key_in_texts) # Якщо є переклад для назви поля
    #     selected_column = st.selectbox(
    #                            f"{display_name_for_ui}:",
    #                            # ...
    #                        )

    # Ця функція може повертати зібрані дані з UI
    # return sheet_id_from_ui, csv_file_object_from_ui, email_from_ui, user_column_mapping
    pass # Заглушка, реалізуйте повернення значень