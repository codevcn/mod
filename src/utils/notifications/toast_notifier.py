import subprocess
from pathlib import Path
from configs.paths import TOAST_SOUND_AUDIO_FILE_PATH
from .base import BaseNotifier

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

    if audio_path and audio_path.lower() not in ("none", "null", "false", "no", "off", ""):
        path_obj = Path(audio_path).resolve()
        if not path_obj.exists():
            print(f"⚠️ Cảnh báo: Không tìm thấy file audio tại `{audio_path}`. Phát âm thanh mặc định của hệ thống.")
            ps_command = f"New-BurntToastNotification -Text {text_arg}"
        else:
            abs_audio = str(path_obj).replace("\\", "/")
            audio_uri = f"file:///{abs_audio}"
            
            texts_cmd = []
            all_texts = [title] + [msg for msg in messages if msg]
            for i, txt in enumerate(all_texts):
                texts_cmd.append(f"$t{i} = New-BTText -Text '{escape_ps(txt)}'")
            
            t_vars = ", ".join(f"$t{i}" for i in range(len(texts_cmd)))
            
            ps_command = (
                "; ".join(texts_cmd) + "; "
                f"$binding = New-BTBinding -Children {t_vars}; "
                f"$visual = New-BTVisual -BindingGeneric $binding; "
                f"$audio = [Microsoft.Toolkit.Uwp.Notifications.ToastAudio]::new(); "
                f"$audio.Src = '{escape_ps(audio_uri)}'; "
                f"$content = New-BTContent -Visual $visual -Audio $audio; "
                f"Submit-BTNotification -Content $content"
            )
    else:
        ps_command = f"New-BurntToastNotification -Text {text_arg}"

    cmd = ["powershell.exe", "-NoProfile", "-Command", ps_command]

    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
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


