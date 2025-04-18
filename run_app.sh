#!/bin/bash

# Додаємо поточний шлях до PYTHONPATH
export PYTHONPATH=$(pwd)

# Запускаємо Streamlit
streamlit run app/run_app.py
