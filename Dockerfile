# Базовий образ
FROM python:3.12-slim

# Встановлюємо системні бібліотеки для weasyprint
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    curl \
    && apt-get clean

# Робоча директорія
WORKDIR /app

# Копіюємо все
COPY . .

# Встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Запуск Streamlit (на Cloud Run потрібно 8080 порт!)
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false"]
