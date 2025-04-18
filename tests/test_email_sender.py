import unittest
from unittest.mock import patch, MagicMock
from app.email_sender import send_email

class TestEmailSender(unittest.TestCase):

    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=b"FakeZIP")
    @patch("smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp_class, mock_open):
        smtp_instance = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = smtp_instance

        send_email("fake_path.zip", recipient="test@example.com")

        smtp_instance.login.assert_called_once()
        smtp_instance.send_message.assert_called_once()

if __name__ == "__main__":
    unittest.main()
