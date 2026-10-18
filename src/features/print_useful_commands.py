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


def parse_blocks(text: str) -> list[str]:
    """Phân tách văn bản thành danh sách các block (mục) có ý nghĩa.
    Nếu gặp banner tiêu đề lớn (################...), tự động gom các mục con/lệnh
    thuộc cùng section đó vào một block duy nhất để không làm mất ngữ cảnh và nội dung.
    """
    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n+", text.strip()) if b.strip()]

    def is_pure_banner(block: str) -> bool:
        """Kiểm tra xem block có phải chỉ là khung banner đơn thuần (chưa có content)."""
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) >= 3 and re.match(r"^#{5,}", lines[0]) and re.match(r"^#{5,}", lines[-1]):
            inner_lines = lines[1:-1]
            return all(l.startswith("#") for l in inner_lines)
        return False

    def extract_banner_keywords(block: str) -> set[str]:
        """Trích xuất các từ khóa ngữ nghĩa từ tiêu đề banner."""
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        inner_text = " ".join(lines[1:-1]).lower()
        words = re.findall(r"[a-zA-Z0-9_\u00C0-\u024F\u1EA0-\u1EF9]+", inner_text)
        stopwords = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "vps", "local", "to"}
        return {w for w in words if len(w) > 2 and w not in stopwords}

    merged_blocks = []
    i = 0
    while i < len(raw_blocks):
        block = raw_blocks[i]

        if is_pure_banner(block):
            banner_block = block
            banner_keywords = extract_banner_keywords(block)
            section_items = [banner_block]
            i += 1

            # Block ngay sau pure banner luôn thuộc về section này
            if i < len(raw_blocks) and not re.match(r"^#{5,}", raw_blocks[i].strip()):
                section_items.append(raw_blocks[i])
                i += 1

                # Gom tiếp các block con tiếp theo nếu thỏa mãn điều kiện
                while i < len(raw_blocks):
                    next_block = raw_blocks[i]
                    # Nếu gặp banner mới -> dừng ngay
                    if re.match(r"^#{5,}", next_block.strip()):
                        break

                    next_lower = next_block.lower()
                    has_common_keyword = any(kw in next_lower for kw in banner_keywords)
                    has_using_marker = bool(re.search(r"#\s*using\s+", next_lower))

                    if has_common_keyword or has_using_marker:
                        section_items.append(next_block)
                        i += 1
                    else:
                        break

            merged_blocks.append("\n\n".join(section_items))
        else:
            merged_blocks.append(block)
            i += 1

    return merged_blocks


def print_useful_commands(args=None):
    """In danh sách các lệnh hữu ích với cú pháp tô màu,
    hoặc xuất ra Notepad nếu có cờ --notepad / -n,
    hoặc tìm kiếm các mục khớp nếu có cờ --find / -f.
    """
    if args is None:
        args = sys.argv[1:]

    use_notepad = False
    find_text = None

    # Parse arguments
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--notepad", "-n"):
            use_notepad = True
            i += 1
        elif arg in ("--find", "-f"):
            if i + 1 < len(args):
                find_text = args[i + 1]
                i += 2
            else:
                print(f"\033[91m❌ Lỗi: Thiếu từ khóa tìm kiếm sau cờ {arg}. (Ví dụ: mod print note --find \"git\")\033[0m")
                sys.exit(1)
        elif arg.startswith("--find="):
            find_text = arg.split("=", 1)[1]
            i += 1
        elif arg.startswith("-f="):
            find_text = arg.split("=", 1)[1]
            i += 1
        else:
            i += 1

    if find_text is not None and not find_text.strip():
        print("\033[91m❌ Lỗi: Từ khóa tìm kiếm không được để trống.\033[0m")
        sys.exit(1)

    content_file = Path(CONTENTS_FOLDER) / "note.txt"
    if not content_file.exists():
        print(f"\033[91m❌ Không tìm thấy file: {content_file}\033[0m")
        sys.exit(1)

    raw_text = content_file.read_text(encoding="utf-8")

    # Xử lý khi có cờ --find
    if find_text is not None:
        keyword = find_text.strip().lower()
        # Phân tách thành các block theo ngữ cảnh section thông minh
        raw_blocks = parse_blocks(raw_text)
        matched_blocks = [b for b in raw_blocks if keyword in b.lower()]

        if not matched_blocks:
            print(f"\033[93m>>> Không tìm thấy mục nào khớp với từ khóa: '{find_text}'\033[0m")
            sys.exit(0)

        result_text = "\n\n".join(matched_blocks)

        if use_notepad:
            try:
                out_dir = Path(APPDATA_FOLDER)
                out_dir.mkdir(parents=True, exist_ok=True)
                target_file = out_dir / "note.txt"

                # Xóa file txt cũ trước đó nếu tồn tại
                if target_file.exists():
                    try:
                        target_file.unlink()
                    except Exception:
                        pass

                target_file.write_text(result_text + "\n", encoding="utf-8")
                subprocess.Popen(["notepad.exe", str(target_file)])
                print(f">>> Đã tìm thấy {len(matched_blocks)} mục khớp với từ khóa '{find_text}'.")
                print(">>> Đã xuất kết quả ra file và mở bằng Notepad:")
                print(f"    {target_file}")
            except Exception as err:
                print(f"\033[91m❌ Lỗi khi xuất ra Notepad: {err}\033[0m")
                print("Đang in ra màn hình CLI thay thế:\n")
                print(f">>> Tìm thấy {len(matched_blocks)} mục khớp với từ khóa '{find_text}':\n")
                for idx, block in enumerate(matched_blocks):
                    for line in block.splitlines():
                        print(highlight_line(line))
                    if idx < len(matched_blocks) - 1:
                        print()
        else:
            print(f">>> Tìm thấy {len(matched_blocks)} mục khớp với từ khóa '{find_text}':\n")
            for idx, block in enumerate(matched_blocks):
                for line in block.splitlines():
                    print(highlight_line(line))
                if idx < len(matched_blocks) - 1:
                    print()
        sys.exit(0)

    # Xử lý khi in toàn bộ note
    if use_notepad:
        try:
            out_dir = Path(APPDATA_FOLDER)
            out_dir.mkdir(parents=True, exist_ok=True)
            target_file = out_dir / "note.txt"

            # Xóa file txt cũ trước đó nếu tồn tại
            if target_file.exists():
                try:
                    target_file.unlink()
                except Exception:
                    pass

            target_file.write_text(raw_text, encoding="utf-8")
            subprocess.Popen(["notepad.exe", str(target_file)])
            print(">>> Đã xuất nội dung note ra file và mở bằng Notepad:")
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
