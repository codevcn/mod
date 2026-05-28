import time
import random
import requests
import argparse
from datetime import datetime
import re

# ==========================================
# CẤU HÌNH THÔNG SỐ MẶC ĐỊNH
# ==========================================
DEFAULT_HEALTHCHECK_URL = (
    "https://b6-remote-server-kaggle-2026.onrender.com/healthcheck"
)

# Thời gian random mặc định nếu người dùng không truyền cờ -i
RANDOM_MIN_INTERVAL_SECONDS = 3 * 60
RANDOM_MAX_INTERVAL_SECONDS = 6 * 60

# Khoảng thời gian chờ khẩn cấp khi máy chủ phản hồi quá chậm
TIMEOUT_RETRY_INTERVAL_SECONDS = 2 * 60

# ==========================================


def parse_interval_config(value: str) -> tuple:
    """
    Phân tích tham số đầu vào của cờ -i.

    Hỗ trợ 2 dạng:
    1. Khoảng random (mm:ss-mm:ss) -> Trả về: ("random", min_seconds, max_seconds)
       Ví dụ: "03:00-06:00", "01:30-02:45"
    2. Cố định (có hoặc không có đơn vị s, m, h) -> Trả về: ("fixed", seconds)
       Ví dụ: "6s", "2m", "1.5h", "300"
    """

    # Kiểm tra định dạng mm:ss-mm:ss
    range_pattern = r"^\s*(\d+):(\d{1,2})\s*-\s*(\d+):(\d{1,2})\s*$"
    range_match = re.match(range_pattern, value)

    if range_match:
        m1, s1, m2, s2 = map(int, range_match.groups())
        min_sec = (m1 * 60) + s1
        max_sec = (m2 * 60) + s2

        if min_sec >= max_sec:
            raise argparse.ArgumentTypeError(
                "Khoảng thời gian không hợp lệ. Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc."
            )
        return ("random", min_sec, max_sec)

    # Kiểm tra định dạng đơn lẻ cố định
    single_pattern = r"^\s*(\d+(?:\.\d+)?)\s*([smhSMH]?)\s*$"
    single_match = re.match(single_pattern, value)

    if single_match:
        number = float(single_match.group(1))
        unit = single_match.group(2).lower() or "s"

        if number <= 0:
            raise argparse.ArgumentTypeError("Thời gian phải lớn hơn 0.")

        unit_to_seconds = {
            "s": 1,
            "m": 60,
            "h": 60 * 60,
        }
        return ("fixed", int(number * unit_to_seconds[unit]))

    # Nếu không khớp định dạng nào
    raise argparse.ArgumentTypeError(
        "Tham số -i không hợp lệ. Vui lòng nhập số cố định (Ví dụ: 6s, 2m, 300) "
        "hoặc khoảng thời gian theo định dạng mm:ss-mm:ss (Ví dụ: 03:00-06:00)."
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


def ping_server(healthcheck_url: str, request_index: int) -> bool:
    """
    Gửi yêu cầu HTTP GET đến máy chủ.
    Trả về True nếu xảy ra lỗi Timeout (máy chủ phản hồi quá chậm).
    Trả về False đối với trạng thái thành công hoặc các lỗi hệ thống khác.
    """
    current_time = datetime.now().strftime("%H:%M:%S")

    print(
        f"[{current_time}] [REQ #{request_index}] Đang gửi yêu cầu đánh thức đến máy chủ..."
    )

    try:
        response = requests.get(healthcheck_url, timeout=15)
        response.raise_for_status()

        # Xử lý lỗi giải mã JSON tiềm ẩn
        try:
            data = response.json()
            timestamp_info = data.get("timestamp", "Không có dữ liệu thời gian")
            print(
                f"[{current_time}] [REQ #{request_index}] THÀNH CÔNG: "
                f"Máy chủ phản hồi ổn định (JSON) - {timestamp_info}"
            )
        except ValueError:
            print(
                f"[{current_time}] [REQ #{request_index}] THÀNH CÔNG: "
                f"Máy chủ phản hồi ổn định (Text/HTML) - Mã trạng thái: {response.status_code}"
            )

        return False

    except requests.exceptions.Timeout:
        print(
            f"[{current_time}] [REQ #{request_index}] CẢNH BÁO: "
            f"Máy chủ phản hồi quá chậm."
        )
        return True

    except requests.exceptions.RequestException as e:
        print(
            f"[{current_time}] [REQ #{request_index}] LỖI HỆ THỐNG: "
            f"Không thể kết nối đến máy chủ. Chi tiết: {e}"
        )
        return False


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
        type=parse_interval_config,
        default=None,
        help=(
            "Thời gian nghỉ giữa các lần request. "
            "Nhập thời gian cố định (Ví dụ: 6s, 2m) hoặc khoảng thời gian random (Ví dụ: 03:00-06:00). "
            "Nếu không truyền, chương trình sẽ ngẫu nhiên trong khoảng 3 phút đến 6 phút."
        ),
    )

    args = parser.parse_args()

    HEALTHCHECK_URL = args.healthcheck_url

    # Thiết lập khoảng thời gian dựa trên tham số người dùng
    if args.interval is None:
        interval_config = (
            "random",
            RANDOM_MIN_INTERVAL_SECONDS,
            RANDOM_MAX_INTERVAL_SECONDS,
        )
    else:
        interval_config = args.interval

    print("=" * 70)
    print("🚀 KHỞI ĐỘNG TRÌNH GIỮ NHỊP (KEEP-ALIVE) CHO MÁY CHỦ TỪ XA")
    print(f"Mục tiêu giám sát : {HEALTHCHECK_URL}")

    if interval_config[0] == "fixed":
        print("Chế độ interval : CỐ ĐỊNH")
        print(f"Thời gian nghỉ   : {format_seconds(interval_config[1])}")
    else:
        print("Chế độ interval : NGẪU NHIÊN")
        print(
            f"Thời gian nghỉ   : Nằm trong khoảng {format_seconds(interval_config[1])} "
            f"đến {format_seconds(interval_config[2])}"
        )

    print(
        "Quy tắc an toàn   : Giảm thời gian chờ xuống 2 phút nếu máy chủ phản hồi chậm."
    )
    print("Nhấn tổ hợp phím [Ctrl + C] để dừng chương trình.")
    print("=" * 70 + "\n")

    request_index: int = 1

    try:
        while True:
            # ping_server sẽ trả về True nếu bị Timeout
            is_timeout = ping_server(HEALTHCHECK_URL, request_index)
            current_time = datetime.now().strftime("%H:%M:%S")

            # Quyết định thời gian chờ tiếp theo dựa trên kết quả của lần gửi vừa rồi
            if is_timeout:
                next_interval_seconds = TIMEOUT_RETRY_INTERVAL_SECONDS
                print(
                    f"[{current_time}] Chế độ PHỤC HỒI: "
                    f"Rút ngắn lần gọi tiếp theo xuống còn {format_seconds(next_interval_seconds)}."
                )
            else:
                if interval_config[0] == "fixed":
                    next_interval_seconds = interval_config[1]
                    print(
                        f"[{current_time}] Chế độ CỐ ĐỊNH: "
                        f"Lần gọi tiếp theo sau {format_seconds(next_interval_seconds)}."
                    )
                else:
                    next_interval_seconds = random.randint(
                        interval_config[1], interval_config[2]
                    )
                    print(
                        f"[{current_time}] Chế độ NGẪU NHIÊN: "
                        f"Đã chọn lần gọi tiếp theo sau {format_seconds(next_interval_seconds)}."
                    )

            print("-" * 70)

            request_index += 1
            time.sleep(next_interval_seconds)

    except KeyboardInterrupt:
        print("\n[HỆ THỐNG] Đã nhận lệnh dừng từ người dùng. Đang tắt chương trình...")
