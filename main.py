from gsheet import get_sheet_data
from pdf_generator import generate_pdf  # функція генерації PDF
import os

# Отримуємо всі записи з таблиці
data = get_sheet_data()

# Створюємо директорію для звітів, якщо її ще нема
os.makedirs("reports", exist_ok=True)

# Проходимося по кожному запису
for i, record in enumerate(data):
    client_name = record.get("Ім'я клієнта", "Невідомо")
    task = record.get("Задача", "—")
    status = record.get("Статус", "—")
    date = record.get("Дата", "—")
    comments = record.get("Коментарі", "")

    # Формуємо контекст для шаблону
    context = {
        "title": "Автоматичний звіт",
        "client": client_name,
        "task": task,
        "status": status,
        "summary": f"{task} для клієнта {client_name} {status.lower()}.",
        "comments": comments,
        "date": date,
    }

    # Збереження під унікальним ім’ям
    output_path = f"reports/report_{i+1}_{client_name}.pdf"
    generate_pdf(context, output_path)

    print(f"[✓] Звіт збережено: {output_path}")
