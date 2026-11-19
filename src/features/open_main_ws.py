import os
import sys
import subprocess
from pathlib import Path

# Đảm bảo UTF-8 cho Windows console
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm project root vào sys.path để import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import VSCODE_MAIN_WS_FOLDER


def open_main_workspace(ide_prefix: str = "code") -> None:
    folder = Path(VSCODE_MAIN_WS_FOLDER)
    if not folder.exists():
        print(f"\033[91m❌ Lỗi: Thư mục không tồn tại: {folder}\033[0m")
        sys.exit(1)

    # Tìm file có đuôi .code-workspace trong thư mục main-ws
    workspace_files = list(folder.glob("*.code-workspace"))
    if not workspace_files:
        print(
            f"\033[91m❌ Lỗi: Không tìm thấy file workspace (*.code-workspace) nào trong: {folder}\033[0m"
        )
        sys.exit(1)

    workspace_file = workspace_files[0]
    print(
        f"\033[92m>>> Đang mở workspace trong {ide_prefix}:\033[0m \033[96m{workspace_file}\033[0m"
    )
    subprocess.run([ide_prefix, str(workspace_file)], shell=True)
    sys.exit(0)


if __name__ == "__main__":
    ide_prefix = "code"
    # Lấy ide_prefix từ tham số đầu tiên nếu không bắt đầu bằng '-'
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        ide_prefix = sys.argv[1]

    open_main_workspace(ide_prefix)
