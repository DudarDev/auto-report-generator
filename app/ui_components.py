# /workspaces/auto-report-generator/app/ui_components.py

import streamlit as st
import pandas as pd
from typing import Dict, Optional, Any, Tuple

# Імпортуємо конфігурацію
from app.config import EXPECTED_APP_FIELDS
from app.internationalization import LANGUAGES # Виносимо тексти в окремий файл

def get_texts(language_code: str) -> Dict[str, str]:
    """Повертає словник з текстами для вказаної мови."""
    return LANGUAGES.get(language_code, LANGUAGES["uk"])

def setup_page_config(texts: Dict[str, str]):
    """Встановлює базові налаштування сторінки Streamlit."""
    st.set_page_config(
        page_title=texts.get("page_title", "Report Generator"),
        page_icon="📋",
        layout="centered"
    )

def language_selector():
    """Створює віджет для вибору мови і оновлює стан."""
    
    def _language_changed():
        # Ця функція викликається автоматично при зміні значення в selectbox
        st.session_state.lang_code = st.session_state.lang_options[st.session_state.lang_widget]

    # Зберігаємо опції в session_state, щоб не перераховувати їх щоразу
    st.session_state.lang_options = {"Українська": "uk", "English": "en"}
    display_options = list(st.session_state.lang_options.keys())
    
    # Визначаємо поточний індекс, щоб віджет показував правильне значення
    current_lang_display = next((lang for lang, code in st.session_state.lang_options.items() if code == st.session_state.lang_code), "Українська")
    current_index = display_options.index(current_lang_display)

    st.sidebar.selectbox(
        label="Оберіть мову / Select language:",
        options=display_options,
        index=current_index,
        key="lang_widget", # Простий, статичний ключ
        on_change=_language_changed # Колбек, який оновлює стан
    )

def display_main_ui(texts: Dict[str, str]) -> Tuple:
    """Відображає основний інтерфейс і повертає введені користувачем дані."""
    st.title(texts.get("app_title"))
    st.markdown(texts.get("app_subtitle"))

    data_source = st.radio(
        label=texts.get("select_data_source"),
        options=[texts.get("google_sheet_id_option"), texts.get("csv_file_option")],
        horizontal=True,
        key="data_source"
    )

    sheet_id, csv_file, column_mapping = None, None, None

    if st.session_state.data_source == texts.get("google_sheet_id_option"):
        sheet_id = st.text_input(
            label=texts.get("enter_google_sheet_id"),
            placeholder="1abc2def3ghi_JKLMN...",
            help=texts.get("google_sheet_id_help")
        )
    else:
        csv_file = st.file_uploader(label=texts.get("upload_csv_file"), type=["csv"])
        if csv_file:
            column_mapping = _display_csv_mapping_ui(texts, csv_file)

    email = st.text_input(label=texts.get("enter_client_email"), placeholder="example@email.com")
    
    generate_button_pressed = st.button(texts.get("generate_button"), use_container_width=True)

    return generate_button_pressed, data_source, sheet_id, csv_file, email, column_mapping

def _display_csv_mapping_ui(texts: Dict[str, str], csv_file: Any) -> Dict[str, str]:
    """Допоміжна функція для відображення UI зіставлення стовпців."""
    mapping = {}
    try:
        csv_file.seek(0)
        df_headers = pd.read_csv(csv_file, nrows=0, encoding='utf-8').columns.tolist()
        csv_file.seek(0)

        with st.expander(texts.get("mapping_header"), expanded=True):
            st.caption(texts.get("mapping_caption"))
            cols = st.columns(2)
            for i, (internal_key, display_key) in enumerate(EXPECTED_APP_FIELDS.items()):
                with cols[i % 2]:
                    display_name = texts.get(display_key, internal_key)
                    selected_col = st.selectbox(
                        label=f"{texts.get('select_csv_column_for')} '{display_name}':",
                        options=[''] + df_headers,
                        key=f"map_{internal_key}"
                    )
                    if selected_col:
                        mapping[internal_key] = selected_col
    except Exception as e:
        st.error(f"{texts.get('error_csv_header_read')}: {e}")
        return {} # Повертаємо порожній словник у разі помилки
        
    return mapping