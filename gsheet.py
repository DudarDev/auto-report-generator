import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Визначення області доступу
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Завантаження облікових даних з файлу JSON
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

# Авторизація
client = gspread.authorize(creds)

# Відкриття таблиці
sheet = client.open("SEO-Звіт").sheet1  # Або змінити назву за потребою

# Функція для отримання всіх даних
def get_sheet_data():
    return sheet.get_all_records()

# Функція для додавання нового рядка
def add_new_lead(client_name, task, status, date, comments):
    sheet.append_row([client_name, task, status, date, comments])
