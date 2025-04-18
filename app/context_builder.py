import os
from gpt_writer import generate_summary

def build_context(record):
    client_name = record.get(os.getenv("CLIENT_NAME_FIELD", "Ім'я клієнта"), "Невідомо")
    task = record.get(os.getenv("TASK_FIELD", "Задача"), "-")
    status = record.get(os.getenv("STATUS_FIELD", "Статус"), "-")
    date = record.get(os.getenv("DATE_FIELD", "Дата"), "-")
    comments = record.get(os.getenv("COMMENTS_FIELD", "Коментарі"), "")

    summary_data = {
        "client": client_name,
        "task": task,
        "status": status,
        "comments": comments,
        "date": date
    }
    summary = generate_summary(summary_data)

    context = {
        "title": "Автоматичний звіт",
        "client": client_name,
        "task": task,
        "status": status,
        "summary": summary,
        "comments": comments,
        "date": date,
    }
    return context