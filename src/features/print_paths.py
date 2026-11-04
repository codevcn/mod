#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
print_paths.py - In danh sách toàn bộ các đường dẫn cấu hình tập trung trong paths.py:
- mod paths
- mod paths --keyword <text>
- mod paths --key <text>
- mod paths -k <text>
Hỗ trợ tìm kiếm không phân biệt hoa thường (case-insensitive) theo tên biến hoặc giá trị đường dẫn.
"""

import os
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

init(autoreset=True)

# Thêm project root vào sys.path để import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import paths


def parse_arguments(args: list[str]) -> str | None:
    """
    Parse cờ --keyword, --key, -k từ danh sách đối số.
    Hỗ trợ cả cú pháp có dấu bằng (--key="my text") và tham số kế tiếp.
    """
    keyword = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--keyword", "--key", "-k"):
            if i + 1 < len(args):
                keyword = args[i + 1].strip()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu từ khóa sau cờ {arg}.{Style.RESET_ALL}")
                print(f"💡 Ví dụ: mod paths {arg} \"skill\"")
                sys.exit(1)
        elif arg.startswith(("--keyword=", "--key=", "-k=")):
            keyword = arg.split("=", 1)[1].strip()
            i += 1
        elif keyword is None and not arg.startswith("-"):
            # Cho phép truyền trực tiếp keyword không cần cờ
            keyword = arg.strip()
            i += 1
        else:
            i += 1
    return keyword


def get_all_configured_paths() -> list[tuple[str, str]]:
    """
    Trích xuất toàn bộ các biến cấu hình đường dẫn (tên UPPERCASE, giá trị kiểu chuỗi hoặc Path)
    từ module configs.paths theo đúng thứ tự khai báo trong mã nguồn.
    """
    results = []
    for key, val in paths.__dict__.items():
        if key.isupper() and isinstance(val, (str, Path)):
            results.append((key, str(val)))
    return results


def main():
    raw_args = sys.argv[1:]
    keyword = parse_arguments(raw_args)

    all_paths = get_all_configured_paths()
    total_count = len(all_paths)

    # Lọc danh sách theo keyword nếu có
    if keyword:
        kw_lower = keyword.lower()
        filtered_paths = [
            (name, val)
            for name, val in all_paths
            if kw_lower in name.lower() or kw_lower in val.lower()
        ]
    else:
        filtered_paths = all_paths

    match_count = len(filtered_paths)

    # In tiêu đề
    print(f"\n{Fore.CYAN}{Style.BRIGHT}📂 DANH SÁCH ĐƯỜNG DẪN CẤU HÌNH TẬP TRUNG (paths.py){Style.RESET_ALL}")
    if keyword:
        print(f"   {Fore.LIGHTBLACK_EX}Bộ lọc: {Fore.YELLOW}'{keyword}'{Fore.LIGHTBLACK_EX} | Khớp: {Fore.GREEN}{match_count}{Fore.LIGHTBLACK_EX}/{total_count} đường dẫn{Style.RESET_ALL}")
    else:
        print(f"   {Fore.LIGHTBLACK_EX}Tổng cộng: {Fore.GREEN}{total_count}{Fore.LIGHTBLACK_EX} đường dẫn cấu hình{Style.RESET_ALL}")
    print("─" * 80)

    if match_count == 0:
        print(f"  {Fore.YELLOW}ℹ️ Không tìm thấy đường dẫn nào khớp với từ khóa '{keyword}'.{Style.RESET_ALL}")
        print("─" * 80)
        print(f"💡 Gợi ý: Gõ {Fore.GREEN}mod paths{Style.RESET_ALL} để xem toàn bộ danh sách đường dẫn.\n")
        sys.exit(0)

    # Tính độ dài lớn nhất của tên biến để căn lề thẳng hàng
    max_name_len = max(len(name) for name, _ in filtered_paths)
    max_name_len = max(max_name_len, 25)

    for idx, (name, val) in enumerate(filtered_paths, 1):
        # Kiểm tra đường dẫn có tồn tại thực tế trên máy hay không
        exists = Path(val).exists()
        status_tag = f"{Fore.GREEN}[TỒN TẠI]{Style.RESET_ALL}" if exists else f"{Fore.YELLOW}[CHƯA TẠO]{Style.RESET_ALL}"

        print(f"  [{Fore.CYAN}{idx:2d}{Style.RESET_ALL}] {Fore.YELLOW}{Style.BRIGHT}{name:<{max_name_len}}{Style.RESET_ALL} {status_tag}")
        print(f"       └─ {Fore.WHITE}{val}{Style.RESET_ALL}")

    print("─" * 80)
    print(f"💡 File cấu hình: {Fore.LIGHTBLUE_EX}src/configs/paths.py{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
