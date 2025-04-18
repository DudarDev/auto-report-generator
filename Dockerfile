# 🔹 Базовий образ
FROM python:3.12-slim

# 🔹 Встановлюємо системні бібліотеки для WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    curl \
    && apt-get clean

# 🔹 Робоча директорія
WORKDIR /app

# 🔹 Копіюємо проєкт
COPY . .

# 🔹 Встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/config/autoreportbot-5392a52edec4.json"


# 🔹 Запуск Streamlit
CMD ["streamlit", "run", "app/app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false"]
