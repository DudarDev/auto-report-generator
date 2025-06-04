# /workspaces/auto-report-generator/app/config_fields.py

# Внутрішні стандартні поля (ключі), які очікує ваш звіт,
# та ключі для їхніх перекладених назв у словнику `texts` в ui_components.py
EXPECTED_APP_FIELDS = {
    "client_name": "client_name_label", # Ключ у словнику texts для "Ім'я/Назва Клієнта"
    "task": "task_label",
    "status": "status_label",
    "date": "date_label",
    "comments": "comments_label",
    "amount": "amount_label" 
}

# Список внутрішніх ключів, який буде використовуватися в gsheet.py та context_builder.py
APP_INTERNAL_KEYS = list(EXPECTED_APP_FIELDS.keys())