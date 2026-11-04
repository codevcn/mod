"""
Cấu hình đường dẫn tập trung cho Mod CLI.
Khi chuyển sang máy khác hoặc thay đổi ổ đĩa, chỉ cần cập nhật các biến đường dẫn ngoài project tại file này.
"""

from pathlib import Path


def get_project_root() -> str:
    """Tự tính root folder từ vị trí file này.
    File này nằm tại: <project_root>/src/configs/paths.py
    """
    return str(Path(__file__).resolve().parent.parent.parent)


# === 1. Đường dẫn nội bộ (TỰ ĐỘNG từ root, không cần sửa) ===
PROJECT_ROOT = get_project_root()
SRC_FOLDER = f"{PROJECT_ROOT}/src"
FEATURES_FOLDER = f"{PROJECT_ROOT}/src/features"
CONTENTS_FOLDER = f"{PROJECT_ROOT}/src/contents"
TOAST_SOUND_AUDIO_FILE_PATH = f"{PROJECT_ROOT}/data/media/audio/burnttoast-notification-sound.mp3"
MOD_HISTORY_FILE_PATH = f"{PROJECT_ROOT}/data/credentials/.mod_history"


# === 2. Đường dẫn kho dữ liệu & Tài nguyên ngoài project (SỬA KHI CHUYỂN MÁY) ===
APPDATA_FOLDER = "D:/D-AppData/me-mod"
OPEN_ALIASES_FILE_PATH = f"{APPDATA_FOLDER}/open_aliases.json"
LOCAL_ABSOLUTE_FOLDER_PATH = "D:/D-Documents/MCP"
MCP_FOLDER_PATH = LOCAL_ABSOLUTE_FOLDER_PATH
SKILLS_FOLDER_PATH = "D:/D-Documents/SKILLs"
VSCODE_WORKSPACES_FOLDER = "D:/D-Documents/VSCode-Workspaces"
SOURCE_FILES_FOLDER = "D:/D-Documents/Souce-Files"
SOURCE_FILES_UTILITY_FOLDER = "D:/D-Documents/Souce-Files/utilty"
TEMPLATE_REPLACER_FOLDER = "D:/D-Documents/Browser-Extensions/codevoicainay/template_replacer"


# === 3. Đường dẫn ứng dụng ngoài & Môi trường tải xuống (SỬA KHI CHUYỂN MÁY) ===
UNIKEY_PATH = "C:/Users/dell/Downloads/UniKeyNT.exe"
CHROME_EXE_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"
CHROME_USER_DATA_DIR = str(Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data")
DEFAULT_DOWNLOAD_DIR = "D:/D-Downloads"


# === 4. Thư mục Template & Code cá nhân (SỬA KHI CHUYỂN MÁY) ===
BROWSER_EXTENSIONS_FOLDER = "D:/D-Documents/Browser-Extensions"
TESTING_FOLDER = "D:/D-Documents/Testing"
TESTING_JS_TS_FOLDER = f"{TESTING_FOLDER}/js-ts"
TESTING_PY_FOLDER = f"{TESTING_FOLDER}/py"
NESTJS_TEMPLATE_FOLDER = "D:/D-Documents/Code_VCN/nestjs"
EXPRESS_TS_TEMPLATE_FOLDER = "D:/D-Documents/Templates/standard-express-server-ts"


# === 5. Đường dẫn Workspaces cá nhân (SỬA KHI CHUYỂN MÁY) ===
WS_PHOTOBOOTH_PTM = "D:/D-Documents/Code_VCN/Photobooth/code/ptm"
WS_PHOTOBOOTH_RECOVER = "D:/D-Documents/Code_VCN/Photobooth/recover-image"
WS_GDRIVE_TOOL = "D:/D-Documents/TOOLs/gdrive-tool/sync-with-gdrive"


# === 6. Đường dẫn MCP Config của các AI Agent (Tự động theo User Home) ===
ANTIGRAVITY_MCP_CONFIG_PATH = str(Path.home() / ".gemini" / "config" / "mcp_config.json")
CODEX_MCP_CONFIG_PATH = str(Path.home() / ".codex" / "config.toml")
CLAUDE_MCP_CONFIG_PATH = str(Path.home() / ".claude.json")


# === 7. Đường dẫn cấu hình hệ thống (Tự động theo User Home) ===
SSH_CONFIG_PATH = str(Path.home() / ".ssh" / "config")


# === 8. Đường dẫn Skills của các AI Agent (Tự động theo User Home) ===
ANTIGRAVITY_SKILLS_PATH = str(Path.home() / ".gemini" / "config" / "skills")
CODEX_SKILLS_PATH = str(Path.home() / ".codex" / "skills")
CLAUDE_SKILLS_PATH = str(Path.home() / ".claude" / "skills")
