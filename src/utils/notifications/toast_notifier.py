import subprocess
import time
import ctypes
from pathlib import Path
from configs.paths import TOAST_SOUND_AUDIO_FILE_PATH
from .base import BaseNotifier

def _play_custom_audio(file_path: str):
    """
    Phát file âm thanh cá nhân (.mp3, .wav) bằng API winmm của Windows.
    Sử dụng thay thế cho UWP ToastAudio vì Windows Action Center sandbox không cho phép load file:/// từ thư mục bên ngoài.
    """
    try:
        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            print(f"⚠️ Cảnh báo: Không tìm thấy file audio tại `{file_path}`.")
            return

        abs_path = str(path_obj)
        alias = "mod_toast_audio"
        winmm = ctypes.windll.winmm

        # Đóng alias nếu trước đó đang mở
        winmm.mciSendStringW(f'close {alias}', None, 0, 0)

        # Mở file audio
        res = winmm.mciSendStringW(f'open "{abs_path}" alias {alias}', None, 0, 0)
        if res == 0:
            # Lấy độ dài audio (millisecond)
            buf = ctypes.create_unicode_buffer(128)
            winmm.mciSendStringW(f'status {alias} length', buf, 128, 0)
            try:
                duration_ms = int(buf.value)
            except ValueError:
                duration_ms = 1500

            # Phát âm thanh
            winmm.mciSendStringW(f'play {alias}', None, 0, 0)

            # Chờ âm thanh phát xong (tối đa 3 giây để không block CLI quá lâu nếu file dài)
            wait_time = min(duration_ms / 1000.0, 3.0)
            if wait_time > 0:
                time.sleep(wait_time)

            winmm.mciSendStringW(f'close {alias}', None, 0, 0)
        else:
            print(f"⚠️ Không thể mở file audio qua winmm (mã lỗi: {res}).")
    except Exception as e:
        print(f"⚠️ Lỗi khi phát âm thanh tùy chỉnh: {e}")

def send_toast(title: str, *messages: str, audio_path: str | None = TOAST_SOUND_AUDIO_FILE_PATH) -> bool:
    """
    Gửi Windows Toast Notification bằng PowerShell cmdlet New-BurntToastNotification, có hỗ trợ âm thanh tùy chỉnh.
    """
    def escape_ps(s: str) -> str:
        return s.replace("'", "''")

    if not title:
        title = "Mod CLI Notification"

    texts = [f"'{escape_ps(title)}'"]
    for msg in messages:
        if msg:
            texts.append(f"'{escape_ps(msg)}'")

    text_arg = ", ".join(texts)

    if audio_path is None:
        audio_path = TOAST_SOUND_AUDIO_FILE_PATH

    system_sounds = {
        "default", "im", "mail", "reminder", "sms",
        "alarm", "alarm2", "alarm3", "alarm4", "alarm5", "alarm6", "alarm7", "alarm8", "alarm9", "alarm10",
        "call", "call2", "call3", "call4", "call5", "call6", "call7", "call8", "call9", "call10",
        "notification.looping.alarm", "notification.looping.alarm2", "notification.looping.alarm3", "notification.looping.alarm4", "notification.looping.alarm5", "notification.looping.alarm6", "notification.looping.alarm7", "notification.looping.alarm8", "notification.looping.alarm9", "notification.looping.alarm10",
        "notification.looping.call", "notification.looping.call2", "notification.looping.call3", "notification.looping.call4", "notification.looping.call5", "notification.looping.call6", "notification.looping.call7", "notification.looping.call8", "notification.looping.call9", "notification.looping.call10"
    }

    should_play_custom = False
    custom_audio_file = None

    if audio_path and audio_path.lower() not in ("none", "null", "false", "no", "off", "", "silent"):
        if audio_path.lower() in system_sounds or audio_path.lower().startswith("ms-winsoundevent:") or audio_path.lower().startswith("notification."):
            ps_command = f"New-BurntToastNotification -Text {text_arg} -Sound '{escape_ps(audio_path)}'"
        else:
            path_obj = Path(audio_path).resolve()
            if not path_obj.exists():
                print(f"⚠️ Cảnh báo: Không tìm thấy file audio tại `{audio_path}`. Phát âm thanh mặc định của hệ thống.")
                ps_command = f"New-BurntToastNotification -Text {text_arg}"
            else:
                # Gửi toast silent để Windows không kêu âm thanh mặc định
                ps_command = f"New-BurntToastNotification -Text {text_arg} -Silent"
                should_play_custom = True
                custom_audio_file = str(path_obj)
    elif audio_path and audio_path.lower() in ("none", "null", "false", "no", "off", "silent"):
        ps_command = f"New-BurntToastNotification -Text {text_arg} -Silent"
    else:
        ps_command = f"New-BurntToastNotification -Text {text_arg}"

    cmd = ["powershell.exe", "-NoProfile", "-Command", ps_command]

    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if should_play_custom and custom_audio_file:
            _play_custom_audio(custom_audio_file)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi hiển thị Toast Notification (Mã lỗi {e.returncode}).")
        if e.stderr and "New-BurntToastNotification" in e.stderr:
            print("💡 Gợi ý: Có vẻ bạn chưa cài đặt module BurntToast trong PowerShell.")
            print("   Hãy mở PowerShell và chạy lệnh: `Install-Module -Name BurntToast -Force -Scope CurrentUser`")
        elif e.stderr:
            print(f"Chi tiết PowerShell: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định khi gửi Toast Notification: {e}")
        return False

class ToastNotifier(BaseNotifier):
    def __init__(self, default_title: str = "Mod CLI Notification"):
        self.default_title = default_title

    def send_message(self, message: str) -> bool:
        return send_toast(self.default_title, message)
