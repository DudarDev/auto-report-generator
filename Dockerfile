# Крок 1: Базовий образ Python
FROM python:3.12-slim

# Крок 2: Встановлення системних залежностей для weasyprint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Крок 3: Створення та встановлення робочої директорії
WORKDIR /app

# Крок 4: Встановлення залежностей Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Крок 5: Копіювання коду вашої програми
COPY . .

# Крок 6: Налаштування середовища та запуск
# ВАЖЛИВО: Встановлюємо PYTHONPATH, щоб вирішити проблеми з імпортами
ENV PYTHONPATH=/app

# Запускаємо Streamlit на правильному порті
# Новий, правильний варіант:
CMD streamlit run app/run_app.py --server.port ${PORT:-8501} --server.enableCORS false --server.enableXsrfProtection false