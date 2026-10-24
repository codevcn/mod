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
MOD_HISTORY_FILE_PATH = f"{PROJECT_ROOT}/data/credentials/.mod_history"

# === Đường dẫn ngoài project (SỬA KHI CHUYỂN MÁY) ===
APPDATA_FOLDER = "D:/D-AppData/me-mod"
OPEN_ALIASES_FILE_PATH = f"{APPDATA_FOLDER}/open_aliases.json"
TEMPLATE_REPLACER_FOLDER = (
    "D:/D-Documents/Browser-Extensions/codevoicainay/template_replacer"
)
LOCAL_ABSOLUTE_FOLDER_PATH = "D:/D-Documents/MCP"
MCP_FOLDER_PATH = LOCAL_ABSOLUTE_FOLDER_PATH
SKILLS_FOLDER_PATH = "D:/D-Documents/SKILLs"
VSCODE_WORKSPACES_FOLDER = "D:/D-Documents/VSCode-Workspaces"

# === Đường dẫn MCP Config của các AI Agent (Tự động theo User Home) ===
ANTIGRAVITY_MCP_CONFIG_PATH = str(Path.home() / ".gemini" / "config" / "mcp_config.json")
CODEX_MCP_CONFIG_PATH = str(Path.home() / ".codex" / "config.toml")
CLAUDE_MCP_CONFIG_PATH = str(Path.home() / ".claude.json")

# === Đường dẫn cấu hình hệ thống (Tự động theo User Home) ===
SSH_CONFIG_PATH = str(Path.home() / ".ssh" / "config")

# === Đường dẫn Skills của các AI Agent (Tự động theo User Home) ===
ANTIGRAVITY_SKILLS_PATH = str(Path.home() / ".gemini" / "config" / "skills")
CODEX_SKILLS_PATH = str(Path.home() / ".codex" / "skills")
CLAUDE_SKILLS_PATH = str(Path.home() / ".claude" / "skills")
