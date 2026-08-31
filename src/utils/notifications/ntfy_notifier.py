import os
import requests
from dotenv import load_dotenv
from configs.paths import PROJECT_ROOT
from .base import BaseNotifier

# Tải cấu hình từ .env ở thư mục gốc (nếu có)
env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=env_path)

DEFAULT_NTFY_TOPIC = "any-mod-automation-N3RT8P2L"
DEFAULT_NTFY_SERVER = "https://ntfy.sh"


class NtfyNotifier(BaseNotifier):
    """
    Notifier gửi thông báo tới app ntfy (ntfy.sh hoặc self-hosted ntfy server).
    Hỗ trợ gửi qua JSON payload giúp tương thích 100% tiếng Việt UTF-8,
    kèm theo tiêu đề, độ ưu tiên (priority), tags/emoji, và liên kết click.
    """

    def __init__(self, default_topic: str = DEFAULT_NTFY_TOPIC, server_url: str = None):
        self.server_url = (server_url or os.environ.get("NTFY_SERVER_URL") or DEFAULT_NTFY_SERVER).rstrip("/")
        self.default_topic = default_topic or DEFAULT_NTFY_TOPIC
        self.token = os.environ.get("NTFY_TOKEN")

    def send_message(
        self,
        message: str,
        title: str = None,
        topic: str = None,
        priority: str | int = None,
        tags: str | list[str] = None,
        url: str = None,
        **kwargs,
    ) -> bool:
        target_topic = topic or self.default_topic
        if not target_topic:
            print("❌ Lỗi: Topic cho ntfy không được để trống.")
            return False

        # Chuẩn hóa tags nếu truyền vào dưới dạng chuỗi phân cách bởi dấu phẩy
        tag_list = []
        if isinstance(tags, str):
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        elif isinstance(tags, list):
            tag_list = tags

        # Chuẩn hóa priority
        priority_val = None
        if priority is not None:
            priority_map = {
                "min": 1, "1": 1,
                "low": 2, "2": 2,
                "default": 3, "3": 3,
                "high": 4, "4": 4,
                "urgent": 5, "max": 5, "5": 5
            }
            priority_val = priority_map.get(str(priority).lower(), 3)

        payload = {
            "topic": target_topic,
            "message": message,
        }
        if title:
            payload["title"] = title
        if priority_val:
            payload["priority"] = priority_val
        if tag_list:
            payload["tags"] = tag_list
        if url:
            payload["click"] = url

        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        target_url = f"{self.server_url}"
        try:
            response = requests.post(target_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ Đã gửi thông báo qua ntfy thành công! [Topic: {target_topic}]")
                return True
            else:
                print(f"❌ Lỗi khi gửi ntfy (HTTP {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"❌ Lỗi kết nối khi gửi thông báo ntfy: {e}")
            return False
