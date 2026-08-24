import os
import sys
import subprocess

# Enable ANSI escape sequences on Windows terminals
if sys.platform.startswith("win"):
    os.system("")

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"

VALID_TYPES = [
    "open", "code", "run", "print", "git", "gdrive",
    "init", "py", "edit", "file", "folder", "tunnel", "proxy", "mcp", "skill", "toast", "compress"
]

class ModCLIError(Exception):
    """Base exception cho Mod CLI."""
    def __init__(self, title: str, reason: str, suggestion: str = "", details: str = ""):
        super().__init__(reason)
        self.title = title
        self.reason = reason
        self.suggestion = suggestion
        self.details = details

class InvalidTypeError(ModCLIError):
    def __init__(self, type_name: str):
        types_str = ", ".join(f"`{t}`" for t in VALID_TYPES)
        super().__init__(
            title=f"Sai nhóm lệnh (type): '{type_name}'",
            reason=f"Nhóm lệnh '{type_name}' không tồn tại trong hệ thống Mod CLI.",
            suggestion=f"Các nhóm lệnh hỗ trợ: {types_str}.\n💡 Gõ `mod --help` để xem chi tiết tài liệu."
        )

class MissingTypeError(ModCLIError):
    def __init__(self):
        super().__init__(
            title="Thiếu nhóm lệnh (type)",
            reason="Bạn chưa nhập nhóm lệnh nào sau `mod`.",
            suggestion="Ví dụ hợp lệ: `mod run keep-awake <url>` hoặc `mod print os`.\n💡 Gõ `mod --help` để xem danh sách lệnh."
        )

class InvalidActionError(ModCLIError):
    def __init__(self, type_name: str, action_name: str, valid_actions: list[str] = None):
        actions_hint = ""
        if valid_actions:
            actions_str = ", ".join(f"`{a}`" for a in valid_actions)
            actions_hint = f"Các action hợp lệ cho `{type_name}`: {actions_str}.\n💡 "
        super().__init__(
            title=f"Sai action '{action_name}' trong nhóm '{type_name}'",
            reason=f"Action '{action_name}' không hợp lệ hoặc chưa được hỗ trợ trong nhóm lệnh `{type_name}`.",
            suggestion=f"{actions_hint}Gõ `mod {type_name} <action> --des` hoặc `mod --help` để xem chi tiết."
        )

class MissingActionError(ModCLIError):
    def __init__(self, type_name: str, valid_actions: list[str] = None):
        actions_hint = ""
        if valid_actions:
            actions_str = ", ".join(f"`{a}`" for a in valid_actions)
            actions_hint = f"Các action hợp lệ cho `{type_name}`: {actions_str}.\n💡 "
        super().__init__(
            title=f"Thiếu action cho nhóm lệnh '{type_name}'",
            reason=f"Nhóm lệnh `{type_name}` yêu cầu bắt buộc phải truyền tên action đi kèm.",
            suggestion=f"{actions_hint}Ví dụ: `mod {type_name} {valid_actions[0] if valid_actions else '<action>'}`."
        )

class FeatureExecutionError(ModCLIError):
    def __init__(self, cmd: str, return_code: int, details: str = ""):
        super().__init__(
            title="Lỗi thực thi script tính năng",
            reason=f"Lệnh `{cmd}` thất bại với mã lỗi (exit code) {return_code}.",
            suggestion="Vui lòng kiểm tra lại tham số truyền vào hoặc file cấu hình liên quan.",
            details=details
        )

class ConfigError(ModCLIError):
    def __init__(self, param: str, env_file: str = ".env"):
        super().__init__(
            title="Lỗi cấu hình",
            reason=f"Thiếu biến cấu hình `{param}` trong file `{env_file}` hoặc môi trường hệ thống.",
            suggestion=f"Vui lòng kiểm tra và bổ sung `{param}` vào file `{env_file}` tại thư mục gốc."
        )

def handle_cli_error(e: Exception):
    """Hàm xử lý lỗi tập trung cho Mod CLI, format output trực quan và dễ hiểu."""
    print()
    print(f"{Colors.RED}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    
    if isinstance(e, ModCLIError):
        print(f"{Colors.RED}{Colors.BOLD}❌ {e.title}{Colors.RESET}")
        print(f"{Colors.GRAY}{'-' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}Nguyên nhân : {Colors.RESET}{e.reason}")
        if e.suggestion:
            print(f"{Colors.YELLOW}{Colors.BOLD}Gợi ý      : {Colors.RESET}{e.suggestion}")
        if e.details:
            print(f"{Colors.CYAN}Chi tiết   : {Colors.RESET}{e.details}")
    elif isinstance(e, subprocess.CalledProcessError):
        print(f"{Colors.RED}{Colors.BOLD}❌ Lỗi thi hành lệnh tiến trình (Subprocess Error){Colors.RESET}")
        print(f"{Colors.GRAY}{'-' * 70}{Colors.RESET}")
        cmd_str = " ".join(str(c) for c in e.cmd) if isinstance(e.cmd, (list, tuple)) else str(e.cmd)
        print(f"{Colors.BOLD}Lệnh thực thi : {Colors.RESET}`{cmd_str}`")
        print(f"{Colors.BOLD}Mã thoát      : {Colors.RESET}{Colors.RED}{e.returncode}{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}Gợi ý        : {Colors.RESET}Script tính năng trên đã dừng do lỗi bên trong. Vui lòng kiểm tra tham số hoặc output phía trên.")
    elif isinstance(e, FileNotFoundError):
        print(f"{Colors.RED}{Colors.BOLD}❌ Không tìm thấy file hoặc lệnh (FileNotFoundError){Colors.RESET}")
        print(f"{Colors.GRAY}{'-' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}Nguyên nhân : {Colors.RESET}{str(e)}")
        print(f"{Colors.YELLOW}{Colors.BOLD}Gợi ý      : {Colors.RESET}Kiểm tra lại đường dẫn file hoặc đảm bảo công cụ (như git, rclone, py, code) đã có trong PATH.")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Lỗi không mong muốn ({type(e).__name__}){Colors.RESET}")
        print(f"{Colors.GRAY}{'-' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}Chi tiết   : {Colors.RESET}{str(e)}")
        print(f"{Colors.YELLOW}{Colors.BOLD}Gợi ý      : {Colors.RESET}Nếu đây là lỗi bug của hệ thống, vui lòng kiểm tra lại log hoặc báo cáo cho người duy trì Mod CLI.")
        
    print(f"{Colors.RED}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print()
    sys.exit(1)
