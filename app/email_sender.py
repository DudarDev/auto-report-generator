# /workspaces/auto-report-generator/app/email_sender.py

import os
import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# --- Конфигурация ---
# Настройка логирования для вывода информационных сообщений
logging.basicConfig(level=logging.INFO, format='INFO: [%(filename)s] %(message)s')

# Загружаем переменные окружения из .env файла
load_dotenv()

# Определяем абсолютные пути к файлам, чтобы избежать ошибок
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TMP_DIR = os.path.join(PROJECT_ROOT, '.tmp')
CREDENTIALS_FILE = os.path.join(TMP_DIR, 'credentials.json') # Файл с OAuth 2.0 Client ID
TOKEN_FILE = os.path.join(TMP_DIR, 'token.json')          # Файл для хранения токена доступа

# Определяем "области" доступа. Нам нужен доступ только к отправке писем.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# --- Основные функции ---

def get_gmail_service():
    """
    Аутентифицирует пользователя через консоль и возвращает сервис для работы с Gmail API.
    """
    creds = None
    # 1. Проверяем, есть ли у нас уже сохраненный и действительный токен
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # 2. Если токена нет или он недействителен, запускаем процесс аутентификации
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Если токен просто просрочен, обновляем его
            creds.refresh(Request())
        else:
            # Если токена нет совсем, запускаем полную аутентификацию
            if not os.path.exists(CREDENTIALS_FILE):
                logging.error(f"Файл учетных данных не найден: {CREDENTIALS_FILE}")
                raise FileNotFoundError(f"Файл учетных данных не найден: {CREDENTIALS_FILE}")

            # Создаем поток аутентификации
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            
            # ВАЖНО: Используем консольный метод, который надежно работает в удаленных средах
            creds = flow.run_console()
        
        # 3. Сохраняем новый (или обновленный) токен для будущих запусков
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            logging.info(f"Токен доступа сохранен в файл: {TOKEN_FILE}")

    # 4. Создаем и возвращаем готовый к работе объект сервиса
    service = build('gmail', 'v1', credentials=creds)
    logging.info("Сервис Gmail успешно инициализирован.")
    return service


def send_email(email_to: str, subject: str, body: str, attachment_path: str = None) -> tuple[bool, str | None]:
    """
    Формирует и отправляет email с вложением (или без) с использованием Gmail API.
    
    Возвращает:
        (True, None) в случае успеха.
        (False, error_message) в случае ошибки.
    """
    try:
        service = get_gmail_service()
        
        # Создаем объект письма
        message = MIMEMultipart()
        message['to'] = email_to
        message['from'] = 'me'  # 'me' - специальное значение, означает аутентифицированного пользователя
        message['subject'] = subject
        
        # Добавляем текстовую часть письма
        message.attach(MIMEText(body, 'plain'))
        
        # Если указан путь к вложению, добавляем его
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment_file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment_file.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            message.attach(part)
            logging.info(f"Вложение {os.path.basename(attachment_path)} добавлено к письму.")
            
        # Кодируем готовое письмо в нужный для API формат
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}
        
        # Отправляем сообщение через API
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        logging.info(f"✅ Сообщение успешно отправлено. ID: {send_message['id']}")
        return True, None

    except HttpError as error:
        logging.error(f'Произошла ошибка HTTP при отправке email: {error}')
        return False, str(error)
    except Exception as e:
        logging.error(f'Неожиданная ошибка: {e}')
        return False, str(e)