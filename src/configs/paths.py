"""
Cấu hình đường dẫn cho mod CLI.
Khi chuyển máy, chỉ cần sửa 2 path ngoài project ở cuối file.
"""

from pathlib import Path


def get_project_root() -> str:
    """Tự tính root folder từ vị trí file này.
    File này nằm tại: <project_root>/src/configs/paths.py
    """
    return str(Path(__file__).resolve().parent.parent.parent)


# === Đường dẫn nội bộ (TỰ ĐỘNG từ root, không cần sửa) ===
PROJECT_ROOT = get_project_root()
SRC_FOLDER = f"{PROJECT_ROOT}/src"
FEATURES_FOLDER = f"{PROJECT_ROOT}/src/features"
CONTENTS_FOLDER = f"{PROJECT_ROOT}/src/contents"
TOAST_SOUND_AUDIO_FILE_PATH = (
    f"{PROJECT_ROOT}/data/media/audio/burnttoast-notification-sound.mp3"
)

# === Đường dẫn ngoài project (SỬA KHI CHUYỂN MÁY) ===
APPDATA_FOLDER = "D:/D-AppData/me-mod"
TEMPLATE_REPLACER_FOLDER = (
    "D:/D-Documents/Browser-Extensions/codevoicainay/template_replacer"
)
LOCAL_ABSOLUTE_FOLDER_PATH = "D:/D-Documents/MCP"
