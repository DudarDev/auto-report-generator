# /workspaces/auto-report-generator/Dockerfile

# Крок 1: Базовий образ Python
# Використовуємо офіційний легкий образ. Переконайтеся, що версія 3.12 відповідає вашому середовищу.
FROM python:3.12-slim

# Крок 2: Встановлення системних залежностей
# Це критично для бібліотеки weasyprint, яка генерує PDF з HTML/CSS.
# Вона потребує бібліотеки для рендерингу графіки та роботи зі шрифтами.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    curl \
    && apt-get clean

# 🔹 Робоча директорія
WORKDIR /app

# Крок 4: Копіюємо файл залежностей та встановлюємо їх
# Спочатку копіюємо тільки requirements.txt, щоб Docker міг кешувати цей шар,
# якщо сам файл не змінюється. Це прискорює наступні збірки.
COPY requirements.txt requirements.txt

# Оновлюємо pip та встановлюємо залежності
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/config/autoreportbot-5392a52edec4.json"


# 🔹 Запуск Streamlit
CMD ["streamlit", "run", "app/app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false"]
