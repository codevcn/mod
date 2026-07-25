import sys
from pathlib import Path

# Thêm đường dẫn src vào sys.path để import utils
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from configs.paths import TOAST_SOUND_AUDIO_FILE_PATH
from utils.notifications.toast_notifier import send_toast
from utils.errors import ModCLIError, handle_cli_error

def main():
    try:
        args = sys.argv[1:]
        if "--syntax" in args or "-s" in args:
            print("💡 Cú pháp sử dụng lệnh Toast Notification (trên 1 dòng để dễ copy):\n")
            print('mod toast "<title>" "[message...]" [--audio <path>]\n')
            sys.exit(0)

        audio_path = None
        filtered_args = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--audio":
                if i + 1 < len(args):
                    audio_path = args[i + 1]
                    i += 2
                else:
                    raise ModCLIError(
                        title="Thiếu tham số cho cờ --audio",
                        reason="Cờ `--audio` yêu cầu phải có đường dẫn file âm thanh đi kèm phía sau.",
                        suggestion="Ví dụ: `mod toast 'Hoàn thành' 'Xong việc.' --audio 'D:/sound.mp3'`"
                    )
            elif arg.startswith("--audio="):
                audio_path = arg.split("=", 1)[1]
                i += 1
            else:
                filtered_args.append(arg)
                i += 1

        if not filtered_args:
            raise ModCLIError(
                title="Thiếu tiêu đề thông báo",
                reason="Lệnh `toast` yêu cầu ít nhất phải có tham số tiêu đề (title).",
                suggestion="Ví dụ: `mod toast 'Hoàn thành' 'Product updated successfully.'`"
            )

        title = filtered_args[0]
        messages = filtered_args[1:] if len(filtered_args) > 1 else []

        if audio_path is None:
            audio_path = TOAST_SOUND_AUDIO_FILE_PATH

        success = send_toast(title, *messages, audio_path=audio_path)
        if success:
            print(f"✅ Đã hiển thị Toast Notification: '{title}'")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        handle_cli_error(e)

if __name__ == "__main__":
    main()

