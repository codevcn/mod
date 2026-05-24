import time
import random
import requests
import argparse
from datetime import datetime
import re

DEFAULT_HEALTHCHECK_URL = (
    "https://b6-remote-server-kaggle-2026.onrender.com/healthcheck"
)

RANDOM_MIN_INTERVAL_SECONDS = 3 * 60
RANDOM_MAX_INTERVAL_SECONDS = 6 * 60


def parse_readable_interval(value: str) -> float:
    """
    Parse interval dạng dễ đọc sang giây.

    Hỗ trợ:
    - 6s    -> 6 giây
    - 2m    -> 120 giây
    - 1.5h  -> 5400 giây
    - 300   -> 300 giây, nếu không ghi unit thì mặc định là giây
    """

    pattern = r"^\s*(\d+(?:\.\d+)?)\s*([smhSMH]?)\s*$"
    match = re.match(pattern, value)

    if not match:
        raise argparse.ArgumentTypeError(
            "interval không hợp lệ. Ví dụ hợp lệ: 6s, 2m, 1.5h, 300"
        )

    number = float(match.group(1))
    unit = match.group(2).lower() or "s"

    if number <= 0:
        raise argparse.ArgumentTypeError("interval phải lớn hơn 0.")

    unit_to_seconds = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
    }

    return number * unit_to_seconds[unit]


def get_random_interval_seconds() -> int:
    return random.randint(
        RANDOM_MIN_INTERVAL_SECONDS,
        RANDOM_MAX_INTERVAL_SECONDS,
    )


def format_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:g} giây"

    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remain_seconds = total_seconds % 60

    parts = []

    if hours > 0:
        parts.append(f"{hours} giờ")

    if minutes > 0:
        parts.append(f"{minutes} phút")

    if remain_seconds > 0:
        parts.append(f"{remain_seconds} giây")

    return " ".join(parts)


def get_next_interval_seconds(fixed_interval_seconds: int | None) -> int:
    if fixed_interval_seconds is not None:
        return fixed_interval_seconds

    return get_random_interval_seconds()


def ping_server(healthcheck_url: str, request_index: int):
    current_time = datetime.now().strftime("%H:%M:%S")

    print(
        f"[{current_time}] [REQ #{request_index}] Đang gửi yêu cầu đánh thức đến máy chủ..."
    )

    try:
        response = requests.get(healthcheck_url, timeout=15)
        response.raise_for_status()

        # Xử lý lỗi giải mã JSON tiềm ẩn tại đây
        try:
            data = response.json()
            timestamp_info = data.get("timestamp", "Không có dữ liệu thời gian")
            print(
                f"[{current_time}] [REQ #{request_index}] THÀNH CÔNG: "
                f"Máy chủ phản hồi ổn định (JSON) - {timestamp_info}"
            )
        except ValueError:
            # Nếu phản hồi không phải là JSON (ví dụ: Text hoặc HTML)
            print(
                f"[{current_time}] [REQ #{request_index}] THÀNH CÔNG: "
                f"Máy chủ phản hồi ổn định (Text/HTML) - Mã trạng thái: {response.status_code}"
            )

    except requests.exceptions.Timeout:
        print(
            f"[{current_time}] [REQ #{request_index}] CẢNH BÁO: "
            f"Máy chủ phản hồi quá chậm."
        )

    except requests.exceptions.RequestException as e:
        print(
            f"[{current_time}] [REQ #{request_index}] LỖI HỆ THỐNG: "
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

    parser.add_argument(
        "-i",
        "--interval",
        type=parse_readable_interval,
        default=None,
        help=(
            "Thời gian cố định giữa các lần request. "
            "Hỗ trợ dạng readable: 6s, 2m, 1.5h. "
            "Nếu không truyền, chương trình sẽ random mỗi lần trong khoảng 180-360 giây."
        ),
    )

    args = parser.parse_args()

    HEALTHCHECK_URL = args.healthcheck_url
    FIXED_INTERVAL_SECONDS = args.interval

    print("=" * 70)
    print("🚀 KHỞI ĐỘNG TRÌNH GIỮ NHỊP (KEEP-ALIVE) CHO MÁY CHỦ TỪ XA")
    print(f"Mục tiêu giám sát : {HEALTHCHECK_URL}")

    if FIXED_INTERVAL_SECONDS is not None:
        print("Chế độ interval : CỐ ĐỊNH")
        print(
            f"Thời gian nghỉ   : {FIXED_INTERVAL_SECONDS} giây "
            f"({format_seconds(FIXED_INTERVAL_SECONDS)})"
        )
    else:
        print("Chế độ interval : RANDOM")
        print(
            "Thời gian nghỉ   : Random sau mỗi request trong khoảng "
            f"{RANDOM_MIN_INTERVAL_SECONDS}-{RANDOM_MAX_INTERVAL_SECONDS} giây "
            f"({format_seconds(RANDOM_MIN_INTERVAL_SECONDS)} - "
            f"{format_seconds(RANDOM_MAX_INTERVAL_SECONDS)})"
        )

    print("Nhấn tổ hợp phím [Ctrl + C] để dừng chương trình.")
    print("=" * 70 + "\n")

    request_index: int = 1

    try:
        while True:
            ping_server(HEALTHCHECK_URL, request_index)

            next_interval_seconds = get_next_interval_seconds(FIXED_INTERVAL_SECONDS)
            current_time = datetime.now().strftime("%H:%M:%S")

            if FIXED_INTERVAL_SECONDS is not None:
                print(
                    f"[{current_time}] Chế độ CỐ ĐỊNH: "
                    f"lần gọi tiếp theo sau {format_seconds(next_interval_seconds)}."
                )
            else:
                print(
                    f"[{current_time}] Chế độ RANDOM: "
                    f"đã random lần gọi tiếp theo sau {format_seconds(next_interval_seconds)}."
                )

            print("-" * 70)

            request_index += 1
            time.sleep(next_interval_seconds)

    except KeyboardInterrupt:
        print("\n[HỆ THỐNG] Đã nhận lệnh dừng từ người dùng. Đang tắt chương trình...")
