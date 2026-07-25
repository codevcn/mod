import ctypes
import msvcrt
import time
import sys

# Các hằng số cho SetThreadExecutionState của Windows API
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

def main():
    if sys.platform != "win32":
        print(">>> Lỗi: Tính năng này chỉ hỗ trợ trên hệ điều hành Windows.")
        sys.exit(1)

    print(">>> Đang cấu hình hệ thống...")
    
    # Yêu cầu hệ thống giữ màn hình luôn sáng
    success = ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED
    )
    
    if not success:
        print(">>> Lỗi: Không thể thiết lập trạng thái giữ màn hình. API call bị từ chối.")
        sys.exit(1)

    print(">>> [SUCCESS] Đã kích hoạt chế độ giữ màn hình luôn sáng.")
    print(">>> Nhấn phím 'q' hoặc tổ hợp 'Ctrl+C' để thoát và trả lại cài đặt ban đầu.\n")

    try:
        while True:
            if msvcrt.kbhit():
                # Bắt phím nhấn
                char = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                if char == 'q':
                    print("\n>>> Đã nhận lệnh dừng từ phím 'q'.")
                    break
            # Nghỉ ngắn để không ngốn CPU
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n>>> Đã nhận lệnh dừng từ 'Ctrl+C'.")
    finally:
        # Xóa các cờ, khôi phục lại trạng thái sleep mặc định của hệ thống
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        print(">>> Đã khôi phục cài đặt hệ thống. Tắt chương trình.")

if __name__ == "__main__":
    main()
