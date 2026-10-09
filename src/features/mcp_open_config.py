import os
import sys
import subprocess
from pathlib import Path

# Đảm bảo encoding utf-8 trên Windows console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Bật ANSI escape sequence trên Windows
if sys.platform.startswith("win"):
    os.system("")

# Thêm project root vào sys.path để import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import (
    ANTIGRAVITY_MCP_CONFIG_PATH,
    CODEX_MCP_CONFIG_PATH,
    CLAUDE_MCP_CONFIG_PATH,
)


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    GRAY = "\033[90m"


AGENT_CONFIGS = {
    "anti": {
        "name": "Google Antigravity",
        "aliases": ["anti", "antigravity", "gemini"],
        "path": Path(ANTIGRAVITY_MCP_CONFIG_PATH),
        "default_content": '{\n  "mcpServers": {}\n}\n',
    },
    "codex": {
        "name": "OpenAI Codex",
        "aliases": ["codex", "openai"],
        "path": Path(CODEX_MCP_CONFIG_PATH),
        "default_content": "# Codex Configuration & MCP Servers\n[mcp_servers]\n",
    },
    "claude": {
        "name": "Claude Code",
        "aliases": ["claude", "claude-code"],
        "path": Path(CLAUDE_MCP_CONFIG_PATH),
        "default_content": '{\n  "mcpServers": {}\n}\n',
    },
}


def print_usage():
    print(f"{Colors.YELLOW}Cú pháp:{Colors.RESET} mod mcp open-config <agent alias>")
    print(f"\n{Colors.CYAN}Các Agent được hỗ trợ:{Colors.RESET}")
    print(f"  {Colors.BOLD}anti{Colors.RESET}   (antigravity, gemini) : Google Antigravity ({Colors.GRAY}~/.gemini/config/mcp_config.json{Colors.RESET})")
    print(f"  {Colors.BOLD}codex{Colors.RESET}  (openai)              : OpenAI Codex ({Colors.GRAY}~/.codex/config.toml{Colors.RESET})")
    print(f"  {Colors.BOLD}claude{Colors.RESET} (claude-code)         : Claude Code ({Colors.GRAY}~/.claude.json{Colors.RESET})")
    print(f"\n{Colors.GRAY}Ví dụ: mod mcp open-config anti{Colors.RESET}")


def resolve_agent(alias: str):
    alias_lower = alias.strip().lower()
    for key, cfg in AGENT_CONFIGS.items():
        if alias_lower in cfg["aliases"]:
            return cfg
    return None


def open_mcp_config(agent_alias: str):
    agent_info = resolve_agent(agent_alias)
    if not agent_info:
        print(f"{Colors.RED}>>> Lỗi: Agent alias '{agent_alias}' không hợp lệ.{Colors.RESET}\n")
        print_usage()
        sys.exit(1)

    target_path = agent_info["path"]

    # Nếu file cấu hình không tồn tại, log thông báo lỗi và dừng tiến trình
    if not target_path.exists():
        print(f"{Colors.RED}❌ Không tìm thấy file: {target_path}{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.GREEN}>>> Đang mở file cấu hình MCP của {agent_info['name']} bằng Notepad...{Colors.RESET}")
    print(f"    {Colors.CYAN}{target_path}{Colors.RESET}")

    try:
        subprocess.Popen(["notepad.exe", str(target_path)])
    except Exception as e:
        print(f"{Colors.RED}>>> Lỗi khi khởi chạy Notepad: {e}{Colors.RESET}")
        sys.exit(1)

    sys.exit(0)


def main():
    args = sys.argv[1:]
    # Nếu được gọi với 'open-config' ở đầu, bỏ qua
    if args and args[0] == "open-config":
        args = args[1:]

    if not args:
        print(f"{Colors.RED}>>> Lỗi: Thiếu tham số <agent alias>.{Colors.RESET}\n")
        print_usage()
        sys.exit(1)

    agent_alias = args[0]
    open_mcp_config(agent_alias)


if __name__ == "__main__":
    main()
