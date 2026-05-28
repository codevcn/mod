from .base import BaseNotifier
from .telegram_notifier import TelegramNotifier

def get_notifier(platform: str) -> BaseNotifier:
    """
    Factory pattern để khởi tạo Notifier tương ứng với platform.
    """
    platform = platform.lower()
    if platform == "telegram":
        return TelegramNotifier()
    else:
        # Nếu platform không được hỗ trợ, có thể trả về một Dummy Notifier hoặc raise Exception.
        # Ở đây ta print cảnh báo và trả về một Dummy Notifier.
        print(f"Cảnh báo: Nền tảng thông báo '{platform}' chưa được hỗ trợ.")
        
        class DummyNotifier(BaseNotifier):
            def send_message(self, message: str) -> bool:
                return False
                
        return DummyNotifier()
