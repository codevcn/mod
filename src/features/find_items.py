#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
find_items.py - Thuật toán tìm kiếm file và folder tối ưu cho Mod CLI:
- mod find file [project path] --name <file_name> [--exact, -e]
- mod find folder [project path] --name <folder_name> [--exact, -e]
"""

import os
import sys
import time
import fnmatch
import argparse
from pathlib import Path
from colorama import init, Fore, Style

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

init(autoreset=True)

# Thêm project root vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Danh sách các thư mục rác / dung lượng lớn mặc định bỏ qua để tối ưu tốc độ tìm kiếm
DEFAULT_IGNORED_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "out",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    ".turbo",
    ".gradle",
}


def format_size(num_bytes: int) -> str:
    """Định dạng dung lượng file dễ đọc (B, KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def get_match_priority(name_lower: str, pattern_lower: str, is_dir: bool) -> int:
    """
    Xác định độ ưu tiên khớp để sắp xếp kết quả trực quan và thông minh:
    - Mức 1: Khớp chính xác 100% cả tên và đuôi (vd: 'cleanup' == 'cleanup')
    - Mức 2: Khớp chính xác phần tên (stem) trước phần mở rộng (vd: 'cleanup.md', 'cleanup.py' khi tìm 'cleanup')
    - Mức 3: Tên bắt đầu bằng từ khóa (prefix match, vd: 'cleanup_tasks.py')
    - Mức 4: Tên chứa từ khóa ở bất kỳ đâu (substring match, vd: 'antigravity-conversation-cleanup.md')
    """
    if name_lower == pattern_lower:
        return 1
    if not is_dir and Path(name_lower).stem == pattern_lower:
        return 2
    if name_lower.startswith(pattern_lower):
        return 3
    return 4


def search_filesystem(
    root_path: Path,
    target_type: str,
    pattern: str,
    ignore_dirs: set[str],
    exact_mode: bool = False,
    max_depth: int | None = None,
    limit: int = 200,
) -> tuple[list[dict], int, float]:
    """
    Thuật toán duyệt tìm kiếm tối ưu hóa cao:
    1. Sử dụng os.scandir(): Tận dụng Win32 FindFirstFile / FindNextFile caching trực tiếp
       metadata (is_dir, is_file) mà không gọi thêm lệnh stat() tốn kém.
    2. Cắt tỉa nhánh (Pruning): Bỏ qua ngay lập tức các thư mục nặng (node_modules, .git, .venv...)
       trước khi đệ quy, giảm hơn 95% thao tác I/O đĩa.
    3. Ngăn xếp DFS không đệ quy (Stack-based Iterative DFS): Không lo tràn call stack trên
       cây thư mục siêu sâu, tiết kiệm RAM.
    4. Xếp hạng ưu tiên (Smart Ranking): Đưa kết quả khớp chính xác 100% (hoặc khớp stem .md, .py)
       lên vị trí đầu tiên, sau đó tới các kết quả chứa từ khóa (substring match).
    """
    start_time = time.perf_counter()
    raw_matches = []
    total_scanned = 0

    is_glob = any(c in pattern for c in ("*", "?", "["))
    pattern_lower = pattern.lower()

    # Thu thập tối đa gấp đôi limit để đảm bảo sau khi sort theo độ ưu tiên sẽ lấy được kết quả tốt nhất
    collect_threshold = max(limit * 2, 400)

    # Stack lưu trữ tuple (current_dir_path, current_depth)
    stack = [(root_path, 0)]

    while stack and len(raw_matches) < collect_threshold:
        curr_dir, depth = stack.pop()

        try:
            with os.scandir(curr_dir) as it:
                subdirs = []
                for entry in it:
                    total_scanned += 1
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue

                    entry_name = entry.name
                    entry_name_lower = entry_name.lower()

                    if is_dir:
                        # Kiểm tra nếu mục tiêu tìm kiếm là FOLDER
                        if target_type == "folder":
                            if is_glob:
                                matched = fnmatch.fnmatch(entry_name_lower, pattern_lower)
                                prio = get_match_priority(entry_name_lower, pattern_lower, is_dir=True) if matched else 99
                            elif exact_mode:
                                matched = (entry_name_lower == pattern_lower)
                                prio = 1 if matched else 99
                            else:
                                # Mặc định: Substring match (chứa từ khóa)
                                matched = (pattern_lower in entry_name_lower)
                                prio = get_match_priority(entry_name_lower, pattern_lower, is_dir=True) if matched else 99

                            if matched:
                                raw_matches.append({
                                    "path": Path(entry.path),
                                    "name": entry_name,
                                    "is_dir": True,
                                    "priority": prio,
                                })
                                if len(raw_matches) >= collect_threshold:
                                    break

                        # Cắt tỉa thư mục bị bỏ qua (Pruning)
                        if entry_name_lower in ignore_dirs:
                            continue

                        # Kiểm tra độ sâu
                        if max_depth is None or depth + 1 <= max_depth:
                            subdirs.append((Path(entry.path), depth + 1))

                    elif target_type == "file":
                        # Kiểm tra nếu mục tiêu tìm kiếm là FILE
                        if is_glob:
                            matched = fnmatch.fnmatch(entry_name_lower, pattern_lower)
                            prio = get_match_priority(entry_name_lower, pattern_lower, is_dir=False) if matched else 99
                        elif exact_mode:
                            matched = (entry_name_lower == pattern_lower)
                            prio = 1 if matched else 99
                        else:
                            # Mặc định: Substring match (chứa từ khóa)
                            matched = (pattern_lower in entry_name_lower)
                            prio = get_match_priority(entry_name_lower, pattern_lower, is_dir=False) if matched else 99

                        if matched:
                            try:
                                size = entry.stat(follow_symlinks=False).st_size
                            except OSError:
                                size = 0
                            raw_matches.append({
                                "path": Path(entry.path),
                                "name": entry_name,
                                "size": size,
                                "is_dir": False,
                                "priority": prio,
                            })
                            if len(raw_matches) >= collect_threshold:
                                break

                # Đưa các thư mục con vào stack (đảo ngược để giữ thứ tự duyệt tự nhiên A-Z)
                if subdirs:
                    stack.extend(reversed(subdirs))

        except (PermissionError, OSError):
            continue

    # Sắp xếp kết quả: Ưu tiên khớp chính xác (priority 1, 2) lên đầu, tiếp theo là độ dài tên ngắn hơn
    raw_matches.sort(key=lambda m: (m["priority"], len(m["name"]), m["name"].lower()))
    matches = raw_matches[:limit]

    elapsed = time.perf_counter() - start_time
    return matches, total_scanned, elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Thuật toán tìm kiếm file và folder tối ưu trong dự án."
    )

    parser.add_argument(
        "action",
        choices=["file", "folder"],
        help="Loại mục tiêu cần tìm: 'file' hoặc 'folder'.",
    )

    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Đường dẫn thư mục dự án cần tìm (mặc định: thư mục hiện tại '.').",
    )

    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default=None,
        help="Tên file hoặc folder cần tìm (mặc định tìm chứa từ khóa, hỗ trợ wildcard '*', '?').",
    )

    parser.add_argument(
        "--exact",
        "-e",
        action="store_true",
        help="Chỉ khớp chính xác 100% tên file/folder (tắt chế độ tìm kiếm chứa từ khóa substring).",
    )

    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Quét toàn bộ, không bỏ qua các thư mục rác (node_modules, .git, .venv...).",
    )

    parser.add_argument(
        "--depth",
        "-d",
        type=int,
        default=None,
        help="Giới hạn độ sâu thư mục cần quét (mặc định: không giới hạn).",
    )

    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=200,
        help="Số lượng kết quả tối đa hiển thị (mặc định: 200).",
    )

    args = parser.parse_args()

    # Kiểm tra tham số bắt buộc --name
    if not args.name or not args.name.strip():
        target_name_vi = "tên file" if args.action == "file" else "tên folder"
        print(f"{Fore.RED}❌ Lỗi: Thiếu cờ '--name <tên>' để chỉ định {target_name_vi} cần tìm.{Style.RESET_ALL}")
        print(f"Cú pháp: mod find {args.action} [project_path] --name <tên_cần_tìm> [--exact, -e]")
        if args.action == "file":
            print(f"Ví dụ  : mod find file --name \"cleanup\"")
            print(f"         mod find file \"D:/projects\" --name \"*.ts\"")
            print(f"         mod find file --name \"main.py\" --exact")
        else:
            print(f"Ví dụ  : mod find folder --name \"configs\"")
            print(f"         mod find folder \"src\" --name \"*util*\"")
        sys.exit(1)

    # Chuẩn hóa đường dẫn dự án (nếu không truyền -> lấy cwd)
    resolved_path = Path(args.project_path).expanduser().resolve()

    if not resolved_path.exists():
        print(f"{Fore.RED}❌ Lỗi: Thư mục dự án không tồn tại:{Style.RESET_ALL} {resolved_path}")
        sys.exit(1)

    if not resolved_path.is_dir():
        print(f"{Fore.RED}❌ Lỗi: Đường dẫn dự án phải là một THƯ MỤC:{Style.RESET_ALL} {resolved_path}")
        sys.exit(1)

    ignore_dirs = set() if args.all else DEFAULT_IGNORED_DIRS

    target_label = "tập tin (file)" if args.action == "file" else "thư mục (folder)"

    # Mô tả chế độ tìm kiếm
    is_glob = any(c in args.name for c in ("*", "?", "["))
    if is_glob:
        mode_str = "Khớp mẫu Wildcard"
    elif args.exact:
        mode_str = "Khớp chính xác 100% (--exact)"
    else:
        mode_str = "Chứa từ khóa (Substring match)"

    print(f"\n{Fore.CYAN}🔍 Đang tìm kiếm {target_label.upper()} trong: {Style.BRIGHT}{resolved_path}{Style.RESET_ALL}")
    print(f"   Từ khóa: {Fore.YELLOW}'{args.name}'{Style.RESET_ALL} │ Chế độ: {Fore.CYAN}{mode_str}{Style.RESET_ALL} │ Bộ lọc thư mục rác: {Fore.GREEN if not args.all else Fore.RED}{'BẬT' if not args.all else 'TẮT'}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}{'─' * 76}{Style.RESET_ALL}")

    matches, total_scanned, elapsed = search_filesystem(
        root_path=resolved_path,
        target_type=args.action,
        pattern=args.name.strip(),
        ignore_dirs=ignore_dirs,
        exact_mode=args.exact,
        max_depth=args.depth,
        limit=args.limit,
    )

    if matches:
        for idx, m in enumerate(matches, 1):
            try:
                rel_path = m["path"].relative_to(resolved_path)
            except ValueError:
                rel_path = m["path"]

            # Huy hiệu khớp chính xác
            exact_badge = f" {Fore.YELLOW}★ [Chính xác]{Style.RESET_ALL}" if m.get("priority", 99) in (1, 2) else ""

            if args.action == "file":
                size_str = format_size(m.get("size", 0))
                print(f"  {Fore.GREEN}[{idx}]{Style.RESET_ALL} {Style.BRIGHT}{rel_path}{Style.RESET_ALL}{exact_badge} {Fore.LIGHTBLACK_EX}({size_str}){Style.RESET_ALL}")
                print(f"      {Fore.LIGHTBLACK_EX}📂 {m['path']}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.GREEN}[{idx}]{Style.RESET_ALL} {Style.BRIGHT}{rel_path}/{Style.RESET_ALL}{exact_badge}")
                print(f"      {Fore.LIGHTBLACK_EX}📂 {m['path']}{Style.RESET_ALL}")

        print(f"{Fore.LIGHTBLACK_EX}{'─' * 76}{Style.RESET_ALL}")
        hit_limit = " (đã chạm giới hạn tối đa)" if len(matches) >= args.limit else ""
        print(f"{Fore.GREEN}✅ Đã tìm thấy {len(matches)} kết quả{hit_limit} (đã quét {total_scanned:,} mục) trong {elapsed:.3f} giây.{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.YELLOW}⚠️ Không tìm thấy {target_label} nào khớp với '--name {args.name}'.{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLACK_EX}   (Đã quét {total_scanned:,} mục trong {elapsed:.3f} giây){Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}💡 Gợi ý tìm kiếm:{Style.RESET_ALL}")
        if args.exact:
            print(f"   1. Bạn đang bật cờ {Fore.WHITE}--exact{Style.RESET_ALL}. Bỏ cờ này để tìm kiếm linh hoạt theo kiểu chứa từ khóa (substring).")
        else:
            print(f"   1. Thử dùng ký tự đại diện '*' (ví dụ: {Fore.WHITE}--name '*{args.name}*'{Style.RESET_ALL}) nếu muốn định dạng linh hoạt hơn.")
        if not args.all:
            print(f"   2. Thêm cờ {Fore.WHITE}--all{Style.RESET_ALL} (hoặc {Fore.WHITE}-a{Style.RESET_ALL}) nếu file/folder nằm trong thư mục ẩn, node_modules, .git, hoặc .venv.")
        print()


if __name__ == "__main__":
    main()
