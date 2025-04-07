import unittest
from unittest.mock import patch, MagicMock, mock_open
from email_sender import send_email

# Кастомний mock для двох файлів
def mocked_open(path, *args, **kwargs):
    if "email_template.html" in path:
        return mock_open(read_data="<html><body>Test HTML</body></html>").return_value
    elif "fake_path.zip" in path:
        return mock_open(read_data=b"FakeZIP").return_value
    else:
        raise FileNotFoundError(f"Mocked open: файл не знайдено: {path}")

class TestEmailSender(unittest.TestCase):

    @patch("smtplib.SMTP_SSL")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=lambda: mocked_open)
    def test_send_email_success(self, mock_exists, mock_open_func, mock_smtp):
        smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = smtp_instance

        send_email("fake_path.zip", recipient="test@example.com")

        smtp_instance.login.assert_called_once()
        smtp_instance.sendmail.assert_called_once()
