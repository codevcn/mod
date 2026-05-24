import time
import requests
import argparse
from datetime import datetime

DEFAULT_HEALTHCHECK_URL = (
    "https://b6-remote-server-kaggle-2026.onrender.com/healthcheck"
)

INTERVAL_SECONDS = 6 * 60


def ping_server(healthcheck_url, request_index: int):
    current_time = datetime.now().strftime("%H:%M:%S")

    print(
        f"[{current_time}] [REQUEST #{request_index}] Đang gửi yêu cầu đánh thức đến máy chủ..."
    )

    try:
        response = requests.get(healthcheck_url, timeout=15)
        response.raise_for_status()

        data = response.json()
        print(
            f"[{current_time}] [REQUEST #{request_index}] THÀNH CÔNG: "
            f"Máy chủ phản hồi ổn định - {data.get('timestamp')}"
        )

    except requests.exceptions.Timeout:
        print(
            f"[{current_time}] [REQUEST #{request_index}] CẢNH BÁO: "
            f"Máy chủ phản hồi quá chậm."
        )

    except requests.exceptions.RequestException as e:
        print(
            f"[{current_time}] [REQUEST #{request_index}] LỖI HỆ THỐNG: "
            f"Không thể kết nối đến máy chủ. Chi tiết: {e}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keep-alive tool cho remote server")

    parser.add_argument(
        "healthcheck_url",
        nargs="?",
        default=DEFAULT_HEALTHCHECK_URL,
        help=f"URL healthcheck của server cần giữ nhịp. Mặc định: {DEFAULT_HEALTHCHECK_URL}",
    )

    args = parser.parse_args()
    HEALTHCHECK_URL = args.healthcheck_url

    print("=" * 60)
    print("🚀 KHỞI ĐỘNG TRÌNH GIỮ NHỊP (KEEP-ALIVE) CHO MÁY CHỦ TỪ XA")
    print(f"Mục tiêu giám sát : {HEALTHCHECK_URL}")
    print(f"Tần suất hoạt động: Mỗi {INTERVAL_SECONDS // 60} phút / lần")
    print("Nhấn tổ hợp phím [Ctrl + C] để dừng chương trình.")
    print("=" * 60 + "\n")

    request_index: int = 1

    try:
        while True:
            ping_server(HEALTHCHECK_URL, request_index)
            request_index += 1
            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[HỆ THỐNG] Đã nhận lệnh dừng từ người dùng. Đang tắt chương trình...")
