#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
add_source_file.py - Thêm tệp vào kho lưu trữ template tiện ích:
- mod file add-src <file_path> [--folder <folder_path>]
Hỗ trợ tạo đệ quy thư mục nhiều cấp (ví dụ: --folder "coding/farm").
"""

import os
import sys
import shutil
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
from configs.paths import SOURCE_FILES_FOLDER


def parse_arguments():
    raw_args = sys.argv[1:]
    file_path = None
    subfolder = None

    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if arg in ("--folder", "--dir", "-d"):
            if i + 1 < len(raw_args):
                subfolder = raw_args[i + 1].strip()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên thư mục sau cờ {arg}.{Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--folder=", "--dir=", "-d=")):
            subfolder = arg.split("=", 1)[1].strip()
            i += 1
        elif file_path is None:
            file_path = arg
            i += 1
        else:
            i += 1

    return file_path, subfolder


def main():
    file_path, subfolder = parse_arguments()

    if not file_path:
        print(f"{Fore.RED}❌ Lỗi: Thiếu đường dẫn tệp cần thêm vào kho.{Style.RESET_ALL}")
        print("Cú pháp: mod file add-src <đường_dẫn_tệp> [--folder <đường_dẫn_thư_mục_con>]")
        print("Ví dụ:")
        print("  mod file add-src ./my_script.py")
        print('  mod file add-src ./farm.py --folder "coding/farm"')
        print('  mod file add-src D:/tools/helper.py -d "utils/helpers/python"')
        sys.exit(1)

    src_abs = os.path.abspath(file_path)
    if not os.path.exists(src_abs):
        print(f"{Fore.RED}❌ Lỗi: Tệp nguồn không tồn tại: {file_path}{Style.RESET_ALL}")
        sys.exit(1)

    if os.path.isdir(src_abs):
        print(f"{Fore.RED}❌ Lỗi: Đường dẫn '{file_path}' là một thư mục, không phải tệp.{Style.RESET_ALL}")
        print("💡 Gợi ý: Lệnh 'mod file add-src' dùng để thêm tệp đơn lẻ vào kho template.")
        sys.exit(1)

    # Đảm bảo kho template tồn tại
    if not os.path.exists(SOURCE_FILES_FOLDER):
        try:
            os.makedirs(SOURCE_FILES_FOLDER, exist_ok=True)
        except Exception as e:
            print(f"{Fore.RED}❌ Lỗi không thể tạo thư mục kho template: {e}{Style.RESET_ALL}")
            sys.exit(1)

    # Xác định thư mục đích trong kho (hỗ trợ tạo đệ quy nhiều cấp, vd: coding/farm)
    base_repo_norm = os.path.normpath(SOURCE_FILES_FOLDER)
    if subfolder:
        # Chuẩn hóa đường dẫn thư mục con và chống path traversal
        clean_subfolder = subfolder.strip().strip("/\\").replace("\\", "/")
        target_dir = os.path.normpath(os.path.join(base_repo_norm, clean_subfolder))
        # Kiểm tra bảo mật: đảm bảo target_dir nằm trọn vẹn bên trong kho template
        if not os.path.abspath(target_dir).startswith(base_repo_norm):
            print(f"{Fore.RED}❌ Lỗi: Thư mục chỉ định '{subfolder}' nằm ngoài phạm vi kho template.{Style.RESET_ALL}")
            sys.exit(1)
    else:
        target_dir = base_repo_norm

    os.makedirs(target_dir, exist_ok=True)

    filename = os.path.basename(src_abs)
    dest_path = os.path.normpath(os.path.join(target_dir, filename))

    # Kiểm tra trùng lặp
    if os.path.exists(dest_path):
        rel_existing = os.path.relpath(dest_path, SOURCE_FILES_FOLDER).replace("\\", "/")
        print(f"\n{Fore.YELLOW}⚠️ Tệp '{rel_existing}' đã tồn tại trong kho template.{Style.RESET_ALL}")
        print(f"   Đường dẫn đích: {dest_path}")
        try:
            ans = input("   Bạn có muốn ghi đè tệp này không? (y/N): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n>>> Hủy thao tác.")
            sys.exit(0)

        if ans != "y":
            print(">>> Hủy thao tác an toàn (không ghi đè).")
            sys.exit(0)

    # Tiến hành sao chép
    try:
        shutil.copy2(src_abs, dest_path)
        rel_saved = os.path.relpath(dest_path, SOURCE_FILES_FOLDER).replace("\\", "/")
        print(f"\n{Fore.GREEN}✅ Đã thêm tệp thành công vào kho template!{Style.RESET_ALL}")
        print(f"   • Tệp nguồn:       {src_abs}")
        print(f"   • Vị trí trong kho: {Fore.CYAN}{rel_saved}{Style.RESET_ALL} ({dest_path})")
        print(f"\n💡 Bạn có thể khởi tạo tệp này tại bất kỳ dự án nào bằng lệnh: {Fore.YELLOW}mod file create{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi khi sao chép tệp vào kho: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
