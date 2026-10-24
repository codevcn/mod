#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
create_linear_path.py - Tạo folder hoặc file theo path được truyền vào theo phương thức linear (tạo xuyên suốt).
Tự động tạo mới toàn bộ các folder cha chưa tồn tại trên máy tính.
Hỗ trợ cờ --content / -c để ghi sẵn nội dung ban đầu khi tạo file mới.
Nếu folder/file đã tồn tại: Thông báo và TUYỆT ĐỐI không ghi đè hay thay thế file/folder đang có.
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

# Danh sách tên các file đặc biệt phổ biến không có phần mở rộng (extension)
KNOWN_EXTENSIONLESS_FILES = {
    "dockerfile",
    "makefile",
    "license",
    "procfile",
    "readme",
    "gemfile",
    "vagrantfile",
    "jenkinsfile",
    "cname",
    "brewfile",
}


def is_likely_file(path_str: str, path_obj: Path) -> bool:
    """Xác định xem một đường dẫn chưa tồn tại có khả năng là File hay Folder."""
    # Nếu kết thúc bằng slash / hoặc \ -> Chắc chắn là Folder
    if path_str.endswith(("/", "\\")):
        return False

    # Nếu có extension (ví dụ .txt, .py, .json, .md...) -> File
    if path_obj.suffix != "":
        return True

    name = path_obj.name.strip()

    # Nếu là dotfile (bắt đầu bằng dấu chấm như .env, .gitignore, .prettierrc...) -> File
    if name.startswith(".") and name not in (".", ".."):
        return True

    # Nếu tên file nằm trong danh sách các file đặc biệt không đuôi -> File
    if name.lower() in KNOWN_EXTENSIONLESS_FILES:
        return True

    # Mặc định còn lại: coi là Folder
    return False


def create_linear(args=None):
    if args is None:
        args = sys.argv[1:]

    force_file = False
    force_folder = False
    file_content = None
    path_tokens = []

    # Parse arguments
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--file", "-f"):
            force_file = True
            i += 1
        elif arg in ("--folder", "-d"):
            force_folder = True
            i += 1
        elif arg in ("--content", "-c"):
            if i + 1 < len(args):
                file_content = args[i + 1]
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu nội dung sau cờ {arg}. (Ví dụ: --content \"nội dung file\"){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith("--content="):
            file_content = arg.split("=", 1)[1]
            i += 1
        elif arg.startswith("-c="):
            file_content = arg.split("=", 1)[1]
            i += 1
        else:
            path_tokens.append(arg)
            i += 1

    if not path_tokens:
        print(f"{Fore.RED}❌ Lỗi: Thiếu đối số đường dẫn <file path or folder path>.{Style.RESET_ALL}")
        print("Cách dùng:")
        print("   mod folder cr-linear <path>")
        print("   mod folder cr-linear <path> --content \"nội dung\"   # Tạo File kèm nội dung")
        print("   mod folder cr-linear <path> --file                 # Ép kiểu tạo File")
        print("   mod folder cr-linear <path> --folder               # Ép kiểu tạo Folder")
        sys.exit(1)

    # Ghép lại đề phòng đường dẫn có khoảng trắng không bọc trong ngoặc kép
    raw_path_str = " ".join(path_tokens).strip().strip('"').strip("'")
    if not raw_path_str:
        print(f"{Fore.RED}❌ Lỗi: Đường dẫn không được để trống.{Style.RESET_ALL}")
        sys.exit(1)

    target_path = Path(raw_path_str).expanduser().resolve()

    # 1. Kiểm tra nếu đối tượng ĐÃ TỒN TẠI trên máy tính
    # TUYỆT ĐỐI KHÔNG GHI ĐÈ HAY THAY THẾ DÙ CÓ TRUYỀN CỜ --content
    if target_path.exists():
        if target_path.is_file():
            print(f"{Fore.YELLOW}⚠️ File đang tồn tại trên thiết bị này (không thay thế hay ghi đè):{Style.RESET_ALL}")
            print(f"   {target_path}")
            sys.exit(0)
        elif target_path.is_dir():
            print(f"{Fore.YELLOW}⚠️ Folder đã tồn tại trên thiết bị này:{Style.RESET_ALL}")
            print(f"   {target_path}")
            sys.exit(0)
        else:
            print(f"{Fore.YELLOW}⚠️ Đường dẫn đã tồn tại trên thiết bị này:{Style.RESET_ALL}")
            print(f"   {target_path}")
            sys.exit(0)

    # 2. Xử lý escape ký tự trong file_content (nếu có)
    if file_content is not None:
        file_content = file_content.replace("\\n", "\n").replace("\\t", "\t")

    # 3. Xác định kiểu cần tạo: File hay Folder
    if force_file and not force_folder:
        target_is_file = True
    elif force_folder and not force_file:
        target_is_file = False
    elif file_content is not None:
        # Nếu có truyền content mà không ép kiểu folder thì chắc chắn là File
        target_is_file = True
    else:
        target_is_file = is_likely_file(raw_path_str, target_path)

    # 4. Tiến hành tạo theo kiểu đã xác định
    if target_is_file:
        # Tạo File và các folder cha nếu chưa có
        parent_dir = target_path.parent
        missing_parents = []
        curr = parent_dir
        while curr != curr.parent and not curr.exists():
            missing_parents.append(curr)
            curr = curr.parent
        missing_parents.reverse()

        try:
            # Tạo các thư mục cha
            if missing_parents:
                parent_dir.mkdir(parents=True, exist_ok=True)

            # Tạo file mới với chế độ exclusive 'x' để đảm bảo tuyệt đối không ghi đè
            with open(target_path, "x", encoding="utf-8") as f:
                if file_content is not None:
                    f.write(file_content)

            if file_content is not None:
                print(f"{Fore.GREEN}✅ Đã tạo mới file thành công (kèm nội dung khởi tạo):{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ Đã tạo mới file thành công (file trống):{Style.RESET_ALL}")
            print(f"   {target_path}")
            if missing_parents:
                print(f"{Fore.CYAN}📁 Đã tự động tạo {len(missing_parents)} thư mục cha còn thiếu (Linear):{Style.RESET_ALL}")
                for p in missing_parents:
                    print(f"   + {p}")
            sys.exit(0)
        except FileExistsError:
            print(f"{Fore.YELLOW}⚠️ File đang tồn tại trên thiết bị này (không thay thế hay ghi đè):{Style.RESET_ALL}")
            print(f"   {target_path}")
            sys.exit(0)
        except Exception as err:
            print(f"{Fore.RED}❌ Lỗi khi tạo file: {err}{Style.RESET_ALL}")
            sys.exit(1)
    else:
        # Tạo Folder và các folder cha nếu chưa có
        missing_dirs = []
        curr = target_path
        while curr != curr.parent and not curr.exists():
            missing_dirs.append(curr)
            curr = curr.parent
        missing_dirs.reverse()

        try:
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"{Fore.GREEN}✅ Đã tạo mới folder thành công:{Style.RESET_ALL}")
            print(f"   {target_path}")
            if file_content is not None:
                print(f"{Fore.YELLOW}⚠️ Lưu ý: Đường dẫn được tạo dưới dạng Folder nên cờ --content đã được bỏ qua.{Style.RESET_ALL}")
            if len(missing_dirs) > 1:
                print(f"{Fore.CYAN}📁 Đã tự động tạo chuỗi {len(missing_dirs)} thư mục (Linear):{Style.RESET_ALL}")
                for p in missing_dirs:
                    print(f"   + {p}")
            sys.exit(0)
        except Exception as err:
            print(f"{Fore.RED}❌ Lỗi khi tạo folder: {err}{Style.RESET_ALL}")
            sys.exit(1)


if __name__ == "__main__":
    create_linear()
