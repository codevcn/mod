import os
import requests
from dotenv import load_dotenv

from configs.paths import PROJECT_ROOT
from .base import BaseNotifier

# Tải cấu hình từ .env ở thư mục gốc
env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=env_path)

class TelegramNotifier(BaseNotifier):
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            print("Cảnh báo: TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID chưa được cấu hình trong file .env")

    def send_message(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("Đã gửi thông báo qua Telegram thành công!")
                return True
            else:
                print(f"Lỗi khi gửi Telegram (HTTP {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"Lỗi kết nối khi gửi Telegram: {e}")
            return False
