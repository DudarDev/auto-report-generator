# /workspaces/auto-report-generator/app/run_app.py

import streamlit as st
import traceback

# Імпортуємо наші модулі
from app.ui_components import setup_page_config, language_selector, get_texts, display_main_ui
from app.report_generator import generate_and_send_report
from app.validation import validate_inputs

def initialize_session_state():
    """Ініціалізує всі ключі session_state в одному місці."""
    if 'lang_code' not in st.session_state:
        st.session_state.lang_code = 'uk'

def main():
    """Головна функція запуску додатку."""
    initialize_session_state()
    
    # 1. Мова та базові налаштування UI
    language_selector()
    texts = get_texts(st.session_state.lang_code)
    setup_page_config(texts)

    # 2. Відображення основного UI та отримання даних від користувача
    # ВИПРАВЛЕНО: прибрали 'data_source', очікуємо 5 значень
    (generate_pressed, 
     sheet_id, 
     csv_file, 
     email, 
     mapping) = display_main_ui(texts)

    # 3. Головна логіка: запускається тільки при натисканні кнопки
    if generate_pressed:
        # 3.1 Валідація введених даних
        # ВИПРАВЛЕНО: більше не передаємо 'data_source'
        is_valid, error_message = validate_inputs(texts, sheet_id, csv_file, email, mapping)
        
        if not is_valid:
            st.warning(error_message)
            return # Зупиняємо виконання, якщо дані невалідні

        # 3.2 Основний процес генерації та відправки
        try:
            with st.spinner(texts.get("spinner_generating", "Генерація звітів...")):
                # Викликаємо головну бізнес-логіку
                # ВИПРАВЛЕНО: використовуємо 'email' замість 'email_to' для узгодженості
                success, message = generate_and_send_report(
                    email=email,
                    sheet_id=sheet_id,
                    csv_file=csv_file,
                    column_mapping=mapping
                )
            
            # 3.3 Показ результату
            if success:
                st.success(f"{texts.get('success_report_sent', 'Звіт успішно згенеровано та надіслано на:')} {email}")
                st.balloons()
            else:
                st.error(f"{texts.get('error_report_generation', 'Під час генерації звіту сталася помилка:')} {message}")

        except Exception as e:
            # Глобальний обробник непередбачуваних помилок
            st.error(texts.get("error_unknown", "Сталася непередбачувана помилка."))
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()