# /workspaces/auto-report-generator/app/ui_components.py

import streamlit as st
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

# --- КОНФІГУРАЦІЯ ТА ІМПОРТИ ---
# Імпортуємо все з єдиного файлу конфігурації app.config
from app.config import EXPECTED_APP_FIELDS, SUPPORTED_LANGUAGES
# Імпортуємо нову функцію для отримання лише заголовків
from app.gsheet import get_sheet_headers

# --- КОНСТАНТИ ---
TEXTS_DIR = Path(__file__).parent.parent / "texts"
DEFAULT_LANG = "uk"

# --- ФУНКЦІЇ ---

@st.cache_data
def get_texts(language_code: str) -> dict:
    """Завантажує та кешує тексти інтерфейсу для обраної мови з JSON-файлів."""
    path = TEXTS_DIR / f"{language_code}.json"
    if not path.is_file():
        logging.warning(f"Файл мови '{path}' не знайдено, використовується мова за замовчуванням.")
        path = TEXTS_DIR / f"{DEFAULT_LANG}.json"
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Критична помилка: не вдалося завантажити файл мови '{path}': {e}")
        st.error(f"Не вдалося завантажити мовні ресурси.")
        return {}

def setup_page_config(texts: dict):
    """Встановлює базові налаштування сторінки Streamlit."""
    st.set_page_config(
        page_title=texts.get("page_title", "Auto Report Generator"),
        page_icon="📋",
        layout="centered"
    )

def language_selector():
    """Створює віджет для вибору мови і оновлює стан."""
    def _language_changed():
        st.session_state.lang_code = SUPPORTED_LANGUAGES[st.session_state.lang_widget]
    
    display_options = list(SUPPORTED_LANGUAGES.keys())
    # Знаходимо ключ (назву мови) за поточним кодом мови
    current_lang_display = next((lang for lang, code in SUPPORTED_LANGUAGES.items() if code == st.session_state.get('lang_code', DEFAULT_LANG)), display_options[0])
    current_index = display_options.index(current_lang_display)

    st.sidebar.selectbox(
        label="Оберіть мову / Select language:",
        options=display_options,
        index=current_index,
        key="lang_widget",
        on_change=_language_changed
    )

def display_main_ui(texts: dict) -> Tuple:
    """Відображає основний інтерфейс і повертає введені користувачем дані."""
    st.title(texts.get("app_title", "Генератор Звітів"))
    st.markdown(texts.get("app_subtitle", "Завантажте дані та отримайте готовий звіт."))

    source_options = [
        texts.get("google_sheet_option", "Google Sheets"), 
        texts.get("csv_file_option", "CSV-файл")
    ]
    data_source = st.radio(
        label=texts.get("select_data_source", "Оберіть джерело даних:"),
        options=source_options,
        horizontal=True,
    )

    sheet_id, csv_file, column_mapping = None, None, {}
    headers = []

    # Визначаємо, яке джерело обрано
    is_google_sheets = (data_source == texts.get("google_sheet_option"))
    is_csv = (data_source == texts.get("csv_file_option"))

    if is_google_sheets:
        sheet_id = st.text_input(
            label=texts.get("enter_google_sheet_id", "Введіть ID Google-таблиці:"),
            help=texts.get("google_sheet_id_help", "Скопіюйте ID з URL вашої таблиці.")
        )
        if sheet_id:
            try:
                with st.spinner(texts.get("spinner_get_headers", "Отримання стовпців...")):
                    # ВИКОРИСТОВУЄМО НОВУ ЕФЕКТИВНУ ФУНКЦІЮ
                    headers = get_sheet_headers(sheet_id=sheet_id)
            except Exception as e:
                st.warning(f"{texts.get('error_google_sheet_data', 'Не вдалося отримати заголовки')}: {e}")
    elif is_csv:
        csv_file = st.file_uploader(label=texts.get("upload_csv_file", "Завантажте ваш CSV-файл:"), type=["csv"])
        if csv_file:
            try:
                headers = pd.read_csv(csv_file, nrows=0, encoding='utf-8').columns.tolist()
                csv_file.seek(0)
            except Exception as e:
                st.error(f"{texts.get('error_csv_header_read', 'Не вдалося прочитати заголовки CSV')}: {e}")

    # Відображаємо UI для зіставлення, якщо вдалося отримати заголовки
    if headers:
        column_mapping = _display_mapping_ui(texts, headers)

    email = st.text_input(
        label=texts.get("enter_client_email", "Email для відправки звіту:"), 
    )
    
    # Кнопка стає активною тільки якщо є джерело даних і вказано email
    is_ready = bool((sheet_id or csv_file) and email)
    generate_button_pressed = st.button(
        texts.get("generate_button", "Сгенерувати та надіслати звіт"),
        use_container_width=True,
        disabled=not is_ready
    )

    return generate_button_pressed, sheet_id, csv_file, email, column_mapping

def _display_mapping_ui(texts: dict, headers: List[str]) -> Dict[str, Optional[str]]:
    """Відображає UI для зіставлення стовпців."""
    mapping = {}
    
    with st.expander(texts.get("mapping_header", "Зіставлення полів"), expanded=True):
        st.caption(texts.get("mapping_caption", "Вкажіть, який стовпець відповідає кожному полю звіту."))
        
        cols = st.columns(2)
        # Динамічно створюємо селектори на основі полів з app.config
        for i, (internal_key, text_key) in enumerate(EXPECTED_APP_FIELDS.items()):
            with cols[i % 2]:
                display_name = texts.get(text_key, internal_key.replace('_', ' ').title())
                # Додаємо порожній варіант, щоб можна було не обирати нічого
                options = [""] + headers 
                selected_col = st.selectbox(
                    label=f"{display_name}:",
                    options=options,
                    key=f"map_{internal_key}"
                )
                if selected_col:
                    mapping[internal_key] = selected_col
                    
    return mapping