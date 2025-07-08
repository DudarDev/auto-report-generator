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
# Копіюємо тільки requirements.txt для кешування цього шару
COPY requirements.txt .

# Оновлюємо pip та встановлюємо залежності
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Крок 5: Копіювання коду вашої програми
# Цей важливий крок копіює всі ваші файли (папку app, main.py і т.д.) всередину образу
COPY . .

# Крок 6: Запуск Streamlit на правильному порті
# Використовуємо $PORT, який надає Cloud Run, і додаємо прапори для роботи за проксі
CMD streamlit run app/run_app.py --server.port $PORT --server.enableCORS false --server.enableXsrfProtection false