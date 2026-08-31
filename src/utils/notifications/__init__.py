import os
from .base import BaseNotifier
from .ntfy_notifier import NtfyNotifier, DEFAULT_NTFY_TOPIC, DEFAULT_NTFY_SERVER
from .telegram_notifier import TelegramNotifier
from .toast_notifier import ToastNotifier

SUPPORTED_CHANNELS = ["ntfy", "telegram", "toast"]

CHANNEL_ALIASES = {
    "ntfy": "ntfy",
    "app": "ntfy",
    "mobile": "ntfy",
    "telegram": "telegram",
    "tele": "telegram",
    "tg": "telegram",
    "toast": "toast",
    "windows": "toast",
    "win": "toast",
}

def get_notifier(platform: str = "ntfy", **kwargs) -> BaseNotifier:
    """
    Factory pattern để khởi tạo Notifier tương ứng với platform.
    Mặc định platform là 'ntfy'.
    """
    platform_norm = CHANNEL_ALIASES.get(platform.lower().strip(), platform.lower().strip())

    if platform_norm == "ntfy":
        return NtfyNotifier(
            default_topic=kwargs.get("topic", DEFAULT_NTFY_TOPIC),
            server_url=kwargs.get("server_url")
        )
    elif platform_norm == "telegram":
        return TelegramNotifier()
    elif platform_norm == "toast":
        return ToastNotifier(default_title=kwargs.get("title", "Mod CLI Notification"))
    else:
        print(f"❌ Cảnh báo: Kênh thông báo '{platform}' chưa được hỗ trợ.")
        print(f"💡 Các kênh hỗ trợ hiện tại: {', '.join(SUPPORTED_CHANNELS)}")
        
        class DummyNotifier(BaseNotifier):
            def send_message(self, message: str, title: str = None, **kwargs) -> bool:
                return False
                
        return DummyNotifier()

def get_channel_statuses() -> list[dict]:
    """
    Trả về thông tin chi tiết và trạng thái cấu hình của các kênh thông báo.
    """
    from configs.paths import PROJECT_ROOT
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    ntfy_server = os.environ.get("NTFY_SERVER_URL") or DEFAULT_NTFY_SERVER
    ntfy_token = os.environ.get("NTFY_TOKEN")

    return [
        {
            "id": "ntfy",
            "name": "Ntfy (Mobile App / ntfy.sh)",
            "is_default": True,
            "configured": True,
            "details": f"Server: {ntfy_server} | Default Topic: {DEFAULT_NTFY_TOPIC} | Auth: {'Có token' if ntfy_token else 'Public'}",
            "description": "Gửi thông báo đẩy đến ứng dụng ntfy trên điện thoại (iOS / Android) hoặc trình duyệt."
        },
        {
            "id": "telegram",
            "name": "Telegram Bot",
            "is_default": False,
            "configured": bool(tg_token and tg_chat),
            "details": f"Token: {'Đã cấu hình' if tg_token else 'Chưa có'} | Chat ID: {'Đã cấu hình' if tg_chat else 'Chưa có'}",
            "description": "Gửi tin nhắn thông báo qua Telegram Bot API (cấu hình trong file .env)."
        },
        {
            "id": "toast",
            "name": "Windows Toast (Desktop)",
            "is_default": False,
            "configured": True,
            "details": "PowerShell BurntToast + Windows Multimedia Audio (winmm)",
            "description": "Hiển thị thông báo Toast Notification trên màn hình máy tính Windows kèm âm thanh tùy chỉnh."
        }
    ]

