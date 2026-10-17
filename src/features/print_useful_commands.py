#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
print_useful_commands.py - In danh sách các lệnh hữu ích với cú pháp tô màu trực quan,
hoặc mở trên Notepad nếu có cờ --notepad / -n.
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from colorama import init, Fore, Style

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

init(autoreset=True)

# Thêm đường dẫn src vào sys.path để import configs/utils
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import CONTENTS_FOLDER, APPDATA_FOLDER


def colorize_command_line(cmd: str) -> str:
    """Tô màu từng thành phần của dòng lệnh CLI mà không làm thay đổi ký tự."""
    # 1. Tách phần ghi chú trong ngoặc đơn ở cuối (nếu có), ví dụ: (if previous command is successful...)
    note_match = re.search(r"(\s*\([a-zA-Z].*?\))$", cmd)
    note_part = ""
    if note_match:
        note_part = f"{Fore.LIGHTBLACK_EX}{note_match.group(1)}{Style.RESET_ALL}"
        cmd = cmd[:note_match.start()]

    # 2. Tokenize dòng lệnh bằng regex
    pattern = re.compile(
        r'("(?:\\.|[^"\\])*")|'                # Nhóm 1: Chuỗi trong dấu ngoặc kép
        r'(<[^>]+>)|'                          # Nhóm 2: Placeholder <PID>, <process_name>
        r'(\b\d+\.\d+\.\d+\.\d+(?::\d+)?\b)|'   # Nhóm 3: Địa chỉ IP
        r'(\s*\|\||\s*&&|\s*\||\s*;)|'         # Nhóm 4: Toán tử pipeline / logic
        r'(--[a-zA-Z0-9_-]+(?:=[^\s]+)?|-[a-zA-Z0-9_-]+|/[a-zA-Z0-9_:]+)|' # Nhóm 5: Flags / options
        r'(\S+)|'                              # Nhóm 6: Các từ khác
        r'(\s+)'                               # Nhóm 7: Khoảng trắng
    )

    tokens = []
    is_first_word = True

    for match in pattern.finditer(cmd):
        g_str, g_ph, g_ip, g_op, g_flag, g_word, g_space = match.groups()

        if g_space:
            tokens.append(g_space)
        elif g_str:
            tokens.append(f"{Fore.LIGHTGREEN_EX}{g_str}{Style.RESET_ALL}")
            is_first_word = False
        elif g_ph:
            tokens.append(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}{g_ph}{Style.RESET_ALL}")
            is_first_word = False
        elif g_ip:
            tokens.append(f"{Fore.LIGHTBLUE_EX}{g_ip}{Style.RESET_ALL}")
            is_first_word = False
        elif g_op:
            tokens.append(f"{Fore.YELLOW}{Style.BRIGHT}{g_op}{Style.RESET_ALL}")
            is_first_word = True  # Sau pipe/operator thì từ kế tiếp là lệnh mới
        elif g_flag:
            tokens.append(f"{Fore.LIGHTCYAN_EX}{g_flag}{Style.RESET_ALL}")
            is_first_word = False
        elif g_word:
            if is_first_word:
                tokens.append(f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{g_word}{Style.RESET_ALL}")
                is_first_word = False
            else:
                tokens.append(f"{Fore.WHITE}{g_word}{Style.RESET_ALL}")

    return "".join(tokens) + note_part


def highlight_line(line: str) -> str:
    """Tô màu một dòng văn bản dựa theo cấu trúc dòng."""
    stripped = line.strip()
    if not stripped:
        return line

    # Banner separator
    if re.match(r"^#{5,}", stripped):
        return f"{Fore.CYAN}{Style.BRIGHT}{line}{Style.RESET_ALL}"

    # Section title
    if re.match(r"^#+\s*\d+\)", stripped) or re.match(r"^##+\s*", stripped):
        return f"{Fore.YELLOW}{Style.BRIGHT}{line}{Style.RESET_ALL}"

    # Comments
    if stripped.startswith("#"):
        return f"{Fore.GREEN}{line}{Style.RESET_ALL}"

    # Keyboard shortcut
    if re.match(r"^\[.*\]\s*\+", stripped):
        return f"{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT}{line}{Style.RESET_ALL}"

    # Executable command line
    return colorize_command_line(line)


def print_useful_commands(args=None):
    """In danh sách các lệnh hữu ích với cú pháp tô màu,
    hoặc xuất ra Notepad nếu có cờ --notepad / -n.
    """
    if args is None:
        args = sys.argv[1:]

    use_notepad = "--notepad" in args or "-n" in args

    content_file = Path(CONTENTS_FOLDER) / "list_useful_commands.txt"
    if not content_file.exists():
        print(f"\033[91m❌ Không tìm thấy file: {content_file}\033[0m")
        sys.exit(1)

    raw_text = content_file.read_text(encoding="utf-8")

    if use_notepad:
        try:
            out_dir = Path(APPDATA_FOLDER)
            out_dir.mkdir(parents=True, exist_ok=True)
            target_file = out_dir / "useful_commands.txt"

            # Xóa file txt cũ trước đó nếu tồn tại
            if target_file.exists():
                try:
                    target_file.unlink()
                except Exception:
                    pass

            target_file.write_text(raw_text, encoding="utf-8")
            subprocess.Popen(["notepad.exe", str(target_file)])
            print(">>> Đã xuất danh sách lệnh hữu ích ra file và mở bằng Notepad:")
            print(f"    {target_file}")
        except Exception as err:
            print(f"\033[91m❌ Lỗi khi xuất ra Notepad: {err}\033[0m")
            print("Đang in ra màn hình CLI thay thế:\n")
            for line in raw_text.splitlines():
                print(highlight_line(line))
    else:
        for line in raw_text.splitlines():
            print(highlight_line(line))


if __name__ == "__main__":
    print_useful_commands()
    sys.exit(0)
