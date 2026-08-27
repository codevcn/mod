import sys
import os
import shlex
from typing import Callable, Optional

# Enable ANSI escape sequences on Windows terminals
if sys.platform.startswith("win"):
    os.system("")

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"

# Danh mục Type và danh sách Action tương ứng (được sắp xếp A-Z)
TYPE_ACTION_MAP = {
    "code": ["ext", "js", "nestjs", "py", "test", "ts", "ts-template", "ws"],
    "compress": ["folder", "init-ignore"],
    "edit": ["cmds", "proms", "to"],

    "file": ["create", "delete", "keep", "rename"],
    "folder": ["create", "dld-path", "merge", "tree"],
    "gdrive": ["del-fd", "dl", "guide", "link", "list", "remote", "reset", "sync", "url"],
    "gist": ["audit", "create", "delete", "get", "list", "rate", "reset", "update"],

    "git": ["commit", "remote"],

    "init": [],
    "mcp": ["set"],
    "open": ["env", "proms", "ws"],
    "print": ["cmds", "curl", "dir", "os", "stts", "ws"],
    "proxy": ["test"],
    "py": ["env"],
    "run": ["gen-qr", "keep-awake", "keep-screen", "srt-count-line", "unikey"],
    "skill": ["set"],
    "toast": ["--syntax"],
    "tunnel": [],
}

TYPE_DESCRIPTIONS = {
    "open": "Mở thư mục gốc hoặc các tài nguyên trong Explorer/IDE",
    "code": "Mở các dự án, template, workspace trong IDE",
    "compress": "Nén toàn bộ dự án hoặc nén thư mục theo cấu hình JSON",
    "file": "Thao tác xử lý file hàng loạt (create, rename, delete, keep)",
    "folder": "Thao tác xử lý folder (create, dld-path, merge, tree)",
    "run": "Thực thi các script tiện ích (unikey, gen-qr, keep-awake...)",
    "git": "Tự động hóa các thao tác Git (commit & push, remote)",
    "gdrive": "Quản lý và đồng bộ Google Drive qua rclone",
    "gist": "Quản lý CRUD và kiểm toán dung lượng GitHub Gist",
    "edit": "Mở và chỉnh sửa nhanh cấu hình hoặc profile PowerShell",

    "print": "In thông tin cấu hình hệ thống, cURL, status, lệnh hữu ích",
    "tunnel": "Mở Cloudflare Quick Tunnel cho cổng cục bộ",
    "proxy": "Kiểm tra kết nối và tính hợp lệ của proxy",
    "mcp": "Thiết lập và copy các thư mục MCP",
    "skill": "Thiết lập và copy các thư mục Skill AI từ kho lưu trữ",
    "toast": "Gửi Windows Toast notification kèm âm thanh tùy chỉnh",
    "py": "Thiết lập môi trường ảo Python (venv) cho dự án",
    "init": "Dọn dẹp các tiến trình Windows chạy ngầm và khởi động Unikey",
}

SORTED_TYPES = sorted(TYPE_ACTION_MAP.keys())

def print_types_overview():
    """Hiển thị danh sách toàn bộ các type hiện có và dòng hướng dẫn ở cuối."""
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}=== DANH SÁCH CÁC NHÓM LỆNH (TYPES) HIỆN CÓ ==={Colors.RESET}")
    print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")

    for t in SORTED_TYPES:
        desc = TYPE_DESCRIPTIONS.get(t, "")
        actions = TYPE_ACTION_MAP.get(t, [])
        actions_str = f"({', '.join(actions)})" if actions else "(không có action)"
        print(f"  {Colors.GREEN}{Colors.BOLD}{t:<8}{Colors.RESET} {Colors.GRAY}│{Colors.RESET} {Colors.WHITE}{desc:<50}{Colors.RESET}")
        if actions:
            print(f"           {Colors.GRAY}└── actions: {Colors.CYAN}{', '.join(actions)}{Colors.RESET}")

    print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
    print(f"{Colors.YELLOW}{Colors.BOLD}💡 Gợi ý:{Colors.RESET} Nhập {Colors.WHITE}{Colors.BOLD}'help'{Colors.RESET} hoặc {Colors.WHITE}{Colors.BOLD}'h'{Colors.RESET} để xem toàn bộ tài liệu chi tiết.")
    print(f"          Nhấn {Colors.CYAN}{Colors.BOLD}[Tab]{Colors.RESET} để tự động điền {Colors.GREEN}Type{Colors.RESET} / {Colors.CYAN}Action{Colors.RESET}, nhập {Colors.RED}{Colors.BOLD}'q'{Colors.RESET} hoặc {Colors.RED}{Colors.BOLD}'exit'{Colors.RESET} để thoát.")
    print()

def get_tab_completion(buffer: str, last_was_tab: bool, original_prefix: str, cycle_idx: int) -> tuple[str, str, int, bool]:
    """
    Xử lý logic Tab completion:
    - Nếu ở token 0 (type): tìm type khớp prefix A-Z và xoay vòng.
    - Nếu ở token 1 (action): tìm action của type đó khớp prefix A-Z và xoay vòng.
    """
    # Phân tích buffer thành các token
    # Trường hợp 1: Đang nhập token đầu tiên (type)
    if " " not in buffer:
        if not last_was_tab:
            original_prefix = buffer.strip().lower()
            cycle_idx = 0
            candidates = [t for t in SORTED_TYPES if t.startswith(original_prefix)]
        else:
            candidates = [t for t in SORTED_TYPES if t.startswith(original_prefix)]
            if candidates:
                cycle_idx = (cycle_idx + 1) % len(candidates)

        if candidates:
            completed_type = candidates[cycle_idx]
            return completed_type, original_prefix, cycle_idx, True
        return buffer, original_prefix, cycle_idx, False

    # Trường hợp 2: Đã có space -> Đang nhập token thứ hai trở đi (action / args)
    parts = buffer.split(" ")
    cmd_type = parts[0].strip().lower()
    
    # Chỉ autocomplete action nếu đang ở vị trí token thứ 2 (hoặc vừa gõ space sau type)
    if len(parts) == 2 or (len(parts) > 2 and parts[2] == ""):
        valid_actions = sorted(TYPE_ACTION_MAP.get(cmd_type, []))
        if not valid_actions:
            return buffer, original_prefix, cycle_idx, False

        action_part = parts[1]
        if not last_was_tab:
            original_prefix = action_part.strip().lower()
            cycle_idx = 0
            candidates = [a for a in valid_actions if a.startswith(original_prefix)]
        else:
            candidates = [a for a in valid_actions if a.startswith(original_prefix)]
            if candidates:
                cycle_idx = (cycle_idx + 1) % len(candidates)

        if candidates:
            completed_action = candidates[cycle_idx]
            rest = " " + " ".join(parts[2:]) if len(parts) > 2 and parts[2] != "" else ""
            new_buffer = f"{parts[0]} {completed_action}{rest}"
            return new_buffer, original_prefix, cycle_idx, True

    return buffer, original_prefix, cycle_idx, False

def autocomplete_input(prompt: str) -> Optional[str]:
    """
    Đọc input từ người dùng trên Windows với hỗ trợ Tab Autocomplete mượt mà.
    Fallback sang input() nếu không phải Windows hoặc không import được msvcrt.
    """
    if not sys.platform.startswith("win"):
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return None

    import msvcrt

    sys.stdout.write(prompt)
    sys.stdout.flush()

    buffer: list[str] = []
    last_was_tab = False
    original_prefix = ""
    cycle_idx = 0

    while True:
        try:
            ch = msvcrt.getwch()
        except KeyboardInterrupt:
            print()
            return None

        # Handle Enter (\r or \n)
        if ch in ("\r", "\n"):
            print()
            return "".join(buffer).strip()

        # Handle Ctrl+C / Ctrl+D / Escape
        elif ch in ("\x03", "\x04", "\x1b"):
            print()
            return None

        # Handle Backspace (\x08 or \x7f)
        elif ch in ("\x08", "\x7f"):
            last_was_tab = False
            if buffer:
                buffer.pop()
                # Xóa dòng hiện tại và vẽ lại prompt + buffer
                sys.stdout.write("\r\033[K" + prompt + "".join(buffer))
                sys.stdout.flush()

        # Handle Tab (\t or \x09)
        elif ch in ("\t", "\x09"):
            current_str = "".join(buffer)
            new_str, original_prefix, cycle_idx, matched = get_tab_completion(
                current_str, last_was_tab, original_prefix, cycle_idx
            )
            if matched:
                buffer = list(new_str)
                last_was_tab = True
                sys.stdout.write("\r\033[K" + prompt + "".join(buffer))
                sys.stdout.flush()

        # Handle Special Keys (Arrows, F-keys, etc. start with \x00 or \xe0)
        elif ch in ("\x00", "\xe0"):
            # Consume the next scan code char
            msvcrt.getwch()
            continue

        # Normal printable characters
        elif ch.isprintable():
            last_was_tab = False
            buffer.append(ch)
            sys.stdout.write(ch)
            sys.stdout.flush()

def run_interactive_session(dispatch_callback: Callable[[list[str], bool, bool], None], print_help_callback: Callable[[], None]):
    """
    Vòng lặp tương tác chính khi user chạy lệnh `mod` không có tham số.
    """
    print_types_overview()

    prompt = f"{Colors.GREEN}{Colors.BOLD}mod > {Colors.RESET}"

    while True:
        try:
            user_input = autocomplete_input(prompt)
        except KeyboardInterrupt:
            print(f"\n{Colors.GRAY}Đã thoát phiên tương tác.{Colors.RESET}")
            return

        if user_input is None:
            print(f"\n{Colors.GRAY}Đã thoát phiên tương tác.{Colors.RESET}")
            return

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("exit", "q", "quit"):
            print(f"{Colors.GRAY}Đã thoát phiên tương tác.{Colors.RESET}")
            return

        if user_input.lower() in ("h", "help", "--help", "-h"):
            try:
                print_help_callback()
            except SystemExit:
                pass
            print()
            continue

        if user_input.lower() in ("type", "types", "list", "ls"):
            print_types_overview()
            continue

        # Phân tách lệnh thành danh sách tham số
        try:
            args = shlex.split(user_input, posix=False)
        except Exception:
            args = user_input.split()

        # Nếu người dùng gõ cả chữ 'mod' ở đầu lệnh, tự loại bỏ
        if args and args[0].lower() == "mod":
            args = args[1:]

        if not args:
            continue

        # Tách dispatcher flags
        des_flag = False
        antigravity_flag = False
        feature_args = []

        for arg in args:
            if arg == "--des":
                des_flag = True
            elif arg in ("-a", "--antigravity-IDE"):
                antigravity_flag = True
            else:
                feature_args.append(arg)

        print()
        try:
            dispatch_callback(feature_args, des_flag, antigravity_flag)
        except SystemExit:
            # Khi subprocess hoặc lệnh con gọi sys.exit(0), quay lại prompt tiếp tục session
            pass
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}>>> Lệnh đã bị hủy bởi người dùng.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Lỗi: {e}{Colors.RESET}")
        print()
