import sys
import os
import shlex
from pathlib import Path
from typing import Callable, Optional

# Enable ANSI escape sequences on Windows terminals
if sys.platform.startswith("win"):
    os.system("")

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from configs.paths import PROJECT_ROOT, MOD_HISTORY_FILE_PATH

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
    "notify": ["channels", "config", "send", "test"],
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
    "notify": "Gửi thông báo qua các kênh ntfy (mặc định), Telegram, Toast...",
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
MAX_HISTORY_ITEMS = 200

def load_history() -> list[str]:
    """Nạp lịch sử lệnh từ file .mod_history."""
    try:
        history_path = Path(MOD_HISTORY_FILE_PATH)
        if not history_path.exists():
            return []
        with open(history_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [line.strip() for line in f if line.strip()]
            return lines[-MAX_HISTORY_ITEMS:]
    except Exception:
        return []

def save_history(history: list[str]) -> None:
    """Lưu danh sách lịch sử lệnh vào file .mod_history."""
    try:
        history_path = Path(MOD_HISTORY_FILE_PATH)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        items = history[-MAX_HISTORY_ITEMS:]
        with open(history_path, "w", encoding="utf-8") as f:
            f.write("\n".join(items) + "\n")
    except Exception:
        pass

def append_history(history: list[str], line: str) -> None:
    """Thêm một câu lệnh vào lịch sử và lưu ra file nếu thỏa điều kiện."""
    clean_line = line.strip()
    if not clean_line:
        return
    # Bỏ qua các lệnh điều khiển session
    if clean_line.lower() in ("q", "quit", "exit", "cls", "clear", "h", "help"):
        return
    # Bỏ qua nếu trùng lặp liền kề
    if history and history[-1] == clean_line:
        return
    history.append(clean_line)
    save_history(history)

def print_types_overview():
    """Hiển thị danh sách toàn bộ các type hiện có và dòng hướng dẫn ở cuối."""
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}=== DANH SÁCH CÁC NHÓM LỆNH (TYPES) HIỆN CÓ ==={Colors.RESET}")
    print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")

    for t in SORTED_TYPES:
        desc = TYPE_DESCRIPTIONS.get(t, "")
        actions = TYPE_ACTION_MAP.get(t, [])
        print(f"  {Colors.GREEN}{Colors.BOLD}{t:<8}{Colors.RESET} {Colors.GRAY}│{Colors.RESET} {Colors.WHITE}{desc:<50}{Colors.RESET}")
        if actions:
            print(f"           {Colors.GRAY}└── actions: {Colors.CYAN}{', '.join(actions)}{Colors.RESET}")

    print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
    print(f"{Colors.YELLOW}{Colors.BOLD}💡 Gợi ý:{Colors.RESET} Nhập {Colors.WHITE}{Colors.BOLD}'help'{Colors.RESET} hoặc {Colors.WHITE}{Colors.BOLD}'h'{Colors.RESET} để xem toàn bộ tài liệu chi tiết.")
    print(f"          Thêm {Colors.CYAN}{Colors.BOLD}'--info'{Colors.RESET} vào sau bất kỳ lệnh nào (vd: {Colors.WHITE}gdrive sync --info{Colors.RESET}) để tra cứu cú pháp & điều kiện.")
    print(f"          Nhấn {Colors.YELLOW}[↑]/[↓]{Colors.RESET} duyệt lịch sử, nhấn {Colors.CYAN}{Colors.BOLD}[Tab]{Colors.RESET} tự động điền {Colors.GREEN}Type{Colors.RESET} & {Colors.CYAN}Action{Colors.RESET}, nhập {Colors.RED}'q'{Colors.RESET} để thoát.")
    print()

def format_buffer_colored(buffer: str) -> str:
    """
    Phân tích cú pháp chuỗi buffer và tô màu theo thời gian thực:
    - Type hợp lệ: Xanh lá đậm (\033[92;1m)
    - Action hợp lệ: Xanh ngọc đậm (\033[96;1m)
    - Tham số / cờ phía sau: Trắng sáng (\033[97m)
    - Chưa hợp lệ / đang gõ dở: Trắng (\033[97m)
    """
    if not buffer:
        return ""

    parts = buffer.split(" ", 2)
    if len(parts) == 1:
        cmd_type = parts[0]
        type_color = f"\033[92;1m{cmd_type}\033[0m" if cmd_type.lower() in TYPE_ACTION_MAP else f"\033[97m{cmd_type}\033[0m"
        return type_color
    elif len(parts) == 2:
        cmd_type, cmd_action = parts[0], parts[1]
        type_color = f"\033[92;1m{cmd_type}\033[0m" if cmd_type.lower() in TYPE_ACTION_MAP else f"\033[97m{cmd_type}\033[0m"
        valid_actions = TYPE_ACTION_MAP.get(cmd_type.lower(), [])
        action_color = f"\033[96;1m{cmd_action}\033[0m" if cmd_action.lower() in valid_actions else f"\033[97m{cmd_action}\033[0m"
        return f"{type_color} {action_color}"
    else:
        cmd_type, cmd_action, rest = parts[0], parts[1], parts[2]
        type_color = f"\033[92;1m{cmd_type}\033[0m" if cmd_type.lower() in TYPE_ACTION_MAP else f"\033[97m{cmd_type}\033[0m"
        valid_actions = TYPE_ACTION_MAP.get(cmd_type.lower(), [])
        action_color = f"\033[96;1m{cmd_action}\033[0m" if cmd_action.lower() in valid_actions else f"\033[97m{cmd_action}\033[0m"
        return f"{type_color} {action_color} \033[97m{rest}\033[0m"

def render_input_line(prompt: str, buffer: list[str], cursor_pos: int) -> None:
    """
    Đồng bộ buffer, tô màu cú pháp và định vị con trỏ terminal chính xác.
    """
    buf_str = "".join(buffer)
    colored_text = format_buffer_colored(buf_str)

    # Xóa sạch dòng hiện tại từ đầu và vẽ lại
    sys.stdout.write("\r\033[K" + prompt + colored_text)

    # Di chuyển con trỏ lùi về vị trí cursor_pos
    offset = len(buffer) - cursor_pos
    if offset > 0:
        sys.stdout.write(f"\033[{offset}D")
    sys.stdout.flush()

def get_tab_completion(
    buffer: str,
    last_was_tab: bool,
    original_prefix: str,
    cycle_idx: int,
) -> tuple[str, str, int, bool]:
    """
    Xử lý logic Tab completion thông minh:
    - NGỮ CẢNH 1: Đang ở Token 0 (Chưa có dấu cách -> Điền/Xoay vòng Type).
    - NGỮ CẢNH 2: Đã có Type -> Đang ở Token 1 (Điền/Xoay vòng Action).
    """
    sorted_types = SORTED_TYPES

    # NGỮ CẢNH 1: Đang ở Token 0 (Chưa có dấu cách -> Điền/Xoay vòng Type)
    if " " not in buffer:
        cleaned_buf = buffer.strip().lower()
        if not last_was_tab:
            if cleaned_buf in sorted_types:
                original_prefix = ""
                candidates = sorted_types
                cycle_idx = (sorted_types.index(cleaned_buf) + 1) % len(sorted_types)
                return f"{candidates[cycle_idx]} ", original_prefix, cycle_idx, True
            else:
                original_prefix = cleaned_buf
                cycle_idx = 0
        else:
            cycle_idx += 1

        candidates = [t for t in sorted_types if t.startswith(original_prefix)]
        if not candidates:
            return buffer, original_prefix, cycle_idx, False

        cycle_idx = cycle_idx % len(candidates)
        return f"{candidates[cycle_idx]} ", original_prefix, cycle_idx, True

    # NGỮ CẢNH 2: Đã có Type -> Đang ở Token 1 (Điền/Xoay vòng Action)
    else:
        parts = buffer.split(" ")
        cmd_type = parts[0].strip().lower()
        valid_actions = sorted(TYPE_ACTION_MAP.get(cmd_type, []))
        if not valid_actions:
            return buffer, original_prefix, cycle_idx, False

        action_part = parts[1].strip().lower() if len(parts) > 1 else ""
        rest_of_args = (" " + " ".join(parts[2:])) if len(parts) > 2 else ""

        if not last_was_tab:
            if action_part in valid_actions:
                original_prefix = ""
                candidates = valid_actions
                cycle_idx = (valid_actions.index(action_part) + 1) % len(valid_actions)
                return f"{cmd_type} {candidates[cycle_idx]}{rest_of_args} ", original_prefix, cycle_idx, True
            else:
                original_prefix = action_part
                cycle_idx = 0
        else:
            cycle_idx += 1

        candidates = [a for a in valid_actions if a.startswith(original_prefix)]
        if not candidates:
            return buffer, original_prefix, cycle_idx, False

        cycle_idx = cycle_idx % len(candidates)
        selected_action = candidates[cycle_idx]
        return f"{cmd_type} {selected_action}{rest_of_args} ", original_prefix, cycle_idx, True

def autocomplete_input(prompt: str, history: list[str]) -> Optional[str]:
    """
    Đọc input từ người dùng trên Windows với hỗ trợ:
    - Tab Autocomplete & Cycle
    - In-line Cursor Navigation (Left, Right, Home, End, Delete, Backspace, Insert)
    - Command History (Up, Down) với Draft Preservation
    - Real-time Syntax Highlighting
    Fallback sang input() nếu không phải Windows hoặc không import được msvcrt.
    """
    if not sys.platform.startswith("win") or not sys.stdin.isatty():
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return None

    import msvcrt

    buffer: list[str] = []
    cursor_pos: int = 0
    last_was_tab: bool = False
    original_prefix: str = ""
    cycle_idx: int = 0
    history_index: int = len(history)
    saved_draft: str = ""

    render_input_line(prompt, buffer, cursor_pos)

    while True:
        try:
            ch = msvcrt.getwch()
        except KeyboardInterrupt:
            print()
            return None

        # 1. Handle Enter (\r or \n)
        if ch in ("\r", "\n"):
            print()
            return "".join(buffer).strip()

        # 2. Handle Ctrl+C / Ctrl+D
        elif ch in ("\x03", "\x04"):
            print()
            return None

        # 3. Handle Esc (\x1b)
        elif ch == "\x1b":
            last_was_tab = False
            if buffer:
                buffer.clear()
                cursor_pos = 0
                render_input_line(prompt, buffer, cursor_pos)
            else:
                print()
                return None

        # 4. Handle Backspace (\x08 or \x7f)
        elif ch in ("\x08", "\x7f"):
            last_was_tab = False
            if cursor_pos > 0:
                buffer.pop(cursor_pos - 1)
                cursor_pos -= 1
                render_input_line(prompt, buffer, cursor_pos)

        # 5. Handle Tab (\t or \x09)
        elif ch in ("\t", "\x09"):
            current_str = "".join(buffer)
            new_str, original_prefix, cycle_idx, matched = get_tab_completion(
                current_str, last_was_tab, original_prefix, cycle_idx
            )
            if matched:
                buffer = list(new_str)
                cursor_pos = len(buffer)
                last_was_tab = True
                render_input_line(prompt, buffer, cursor_pos)

        # 6. Handle Special Keys (Prefix \x00 or \xe0: Arrows, Home, End, Delete)
        elif ch in ("\x00", "\xe0"):
            last_was_tab = False
            sc = msvcrt.getwch()

            # Up Arrow: \x48 / 'H'
            if sc in ("H", "\x48"):
                if history:
                    if history_index == len(history):
                        saved_draft = "".join(buffer)
                    if history_index > 0:
                        history_index -= 1
                        buffer = list(history[history_index])
                        cursor_pos = len(buffer)
                        render_input_line(prompt, buffer, cursor_pos)

            # Down Arrow: \x50 / 'P'
            elif sc in ("P", "\x50"):
                if history:
                    if history_index < len(history) - 1:
                        history_index += 1
                        buffer = list(history[history_index])
                        cursor_pos = len(buffer)
                        render_input_line(prompt, buffer, cursor_pos)
                    elif history_index == len(history) - 1:
                        history_index = len(history)
                        buffer = list(saved_draft)
                        cursor_pos = len(buffer)
                        render_input_line(prompt, buffer, cursor_pos)

            # Left Arrow: \x4B / 'K'
            elif sc in ("K", "\x4B"):
                cursor_pos = max(0, cursor_pos - 1)
                render_input_line(prompt, buffer, cursor_pos)

            # Right Arrow: \x4D / 'M'
            elif sc in ("M", "\x4D"):
                cursor_pos = min(len(buffer), cursor_pos + 1)
                render_input_line(prompt, buffer, cursor_pos)

            # Home: \x47 / 'G'
            elif sc in ("G", "\x47"):
                cursor_pos = 0
                render_input_line(prompt, buffer, cursor_pos)

            # End: \x4F / 'O'
            elif sc in ("O", "\x4F"):
                cursor_pos = len(buffer)
                render_input_line(prompt, buffer, cursor_pos)

            # Delete: \x53 / 'S'
            elif sc in ("S", "\x53"):
                if cursor_pos < len(buffer):
                    buffer.pop(cursor_pos)
                    render_input_line(prompt, buffer, cursor_pos)

        # 7. Normal printable characters
        elif ch.isprintable():
            last_was_tab = False
            buffer.insert(cursor_pos, ch)
            cursor_pos += 1
            render_input_line(prompt, buffer, cursor_pos)

def run_interactive_session(
    dispatch_callback: Callable[[list[str], bool, bool], None],
    print_help_callback: Callable[[], None]
):
    """
    Vòng lặp tương tác chính khi user chạy lệnh `mod` không có tham số.
    """
    print_types_overview()
    history = load_history()

    prompt = f"{Colors.GREEN}{Colors.BOLD}mod > {Colors.RESET}"

    while True:
        try:
            user_input = autocomplete_input(prompt, history)
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

        if user_input.lower() in ("cls", "clear"):
            os.system("cls" if os.name == "nt" else "clear")
            print_types_overview()
            continue

        # Ghi vào lịch sử
        append_history(history, user_input)

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
        info_flag = False
        antigravity_flag = False
        feature_args = []

        for arg in args:
            if arg in ("--info", "--des"):
                info_flag = True
            elif arg in ("-a", "--antigravity-IDE"):
                antigravity_flag = True
            else:
                feature_args.append(arg)

        print()
        try:
            dispatch_callback(feature_args, info_flag, antigravity_flag)
        except SystemExit:
            # Khi subprocess hoặc lệnh con gọi sys.exit(0), quay lại prompt tiếp tục session
            pass
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}>>> Lệnh đã bị hủy bởi người dùng.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Lỗi: {e}{Colors.RESET}")
        print()
