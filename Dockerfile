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
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    curl \
    fonts-dejavu \
    # fonts-dejavu додає підтримку широкого набору символів, включаючи кирилицю.
    && rm -rf /var/lib/apt/lists/*

# Крок 3: Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Крок 4: Копіюємо файл залежностей та встановлюємо їх
# Спочатку копіюємо тільки requirements.txt, щоб Docker міг кешувати цей шар,
# якщо сам файл не змінюється. Це прискорює наступні збірки.
COPY requirements.txt requirements.txt

# Оновлюємо pip та встановлюємо залежності
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Крок 5: Копіюємо решту коду додатку в контейнер
COPY . .

# Крок 6: Встановлюємо PYTHONPATH
# Це важливо, щоб Python міг знаходити ваші модулі (наприклад, з папки 'app')
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Крок 7: Вказуємо порт, який буде слухати додаток
# Cloud Run за замовчуванням очікує порт 8080, але він також надає змінну $PORT.
# Ми будемо використовувати $PORT у команді запуску.
EXPOSE 8080

# Крок 8: Команда для запуску Streamlit додатку при старті контейнера
# --server.port $PORT: Вказівка Streamlit використовувати порт, наданий Cloud Run.
# --server.address 0.0.0.0: Робить додаток доступним ззовні контейнера.
# --server.enableCORS=false: Часто допомагає уникнути проблем з CORS у хмарних середовищах.
CMD ["python", "-m", "streamlit", "run", "app/run_app.py", "--server.port", "$PORT", "--server.address", "0.0.0.0", "--server.enableCORS=false"]
