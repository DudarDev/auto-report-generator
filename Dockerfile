# Базовий образ
FROM python:3.10

# Робоча директорія в контейнері
WORKDIR /app

# Копіюємо все
COPY . .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Запуск Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
