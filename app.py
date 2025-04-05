import streamlit as st
from report_generator import generate_and_send_report # імпортуй свою функцію
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="AUTO-REPORT-GENERATOR", layout="centered")

st.title("📊 AUTO-REPORT-GENERATOR")
st.markdown("Згенеруйте звіт і отримайте його на email.")

# Введення email
email = st.text_input("Введіть email клієнта:")

# Кнопка запуску
if st.button("🚀 Згенерувати та надіслати звіт"):
    if email:
        with st.spinner("Генеруємо звіт..."):
            try:
                generate_and_send_report(email=email)  # твоя функція генерації
                st.success(f"Звіт надіслано на {email} 📩")
            except Exception as e:
                st.error(f"Сталася помилка: {e}")
    else:
        st.warning("Будь ласка, введіть email")
