#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
manage_open_aliases.py - Quản lý danh sách alias mở thư mục cá nhân trên máy tính:
- mod open add <alias> <path>
- mod open list
- mod open rm <alias>
"""

import os
import re
import sys
import json
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
from configs.paths import OPEN_ALIASES_FILE_PATH

# Danh sách các từ khóa hệ thống không được phép dùng làm alias (tránh che lấp tính năng có sẵn của mod open)
RESERVED_ALIASES = {
    "add",
    "list",
    "ls",
    "rm",
    "remove",
    "del",
    "aliases",
    "ws",
    "env",
    "proms",
    "appdata",
    "mcp",
    "mcps",
    "skills",
    "skill",
    "ssh-conf",
    "agy-mcp-conf",
    "codex-mcp-conf",
    "clau-mcp-conf",
    "agy-skills",
    "codex-skills",
    "clau-skills",
}

ALIAS_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")


def load_aliases() -> dict[str, str]:
    """Đọc danh sách alias từ file JSON."""
    aliases_path = Path(OPEN_ALIASES_FILE_PATH)
    if not aliases_path.exists():
        return {}
    try:
        with open(aliases_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


def save_aliases(aliases: dict[str, str]) -> bool:
    """Lưu danh sách alias vào file JSON an toàn."""
    aliases_path = Path(OPEN_ALIASES_FILE_PATH)
    try:
        aliases_path.parent.mkdir(parents=True, exist_ok=True)
        with open(aliases_path, "w", encoding="utf-8") as f:
            json.dump(aliases, f, ensure_ascii=False, indent=2)
        return True
    except Exception as err:
        print(f"{Fore.RED}❌ Lỗi khi ghi file dữ liệu alias:{Style.RESET_ALL} {err}")
        return False


def action_add(args: list[str]):
    """Thêm một alias mới trỏ tới đường dẫn thư mục."""
    if len(args) < 1:
        print(f"{Fore.RED}❌ Lỗi: Thiếu đối số <folder alias> và <folder absolute path>.{Style.RESET_ALL}")
        print("Cú pháp: mod open add <folder_alias> <folder_absolute_path>")
        print("Ví dụ  : mod open add lolping \"D:\\D-Temps\\module-4\"")
        sys.exit(1)

    alias = args[0].strip()

    # Kiểm tra format alias theo regex [A-Za-z0-9_-]
    if not ALIAS_REGEX.match(alias):
        print(f"{Fore.RED}❌ Lỗi: Alias '{alias}' không hợp lệ.{Style.RESET_ALL}")
        print("Quy tắc: Chỉ chấp nhận các ký tự chữ cái (a-z, A-Z), chữ số (0-9), gạch ngang (-) và gạch dưới (_).")
        sys.exit(1)

    # Chống xung đột với built-in actions
    if alias.lower() in RESERVED_ALIASES:
        print(f"{Fore.RED}❌ Lỗi: Alias '{alias}' trùng với từ khóa hệ thống của lệnh 'mod open'.{Style.RESET_ALL}")
        print("Vui lòng chọn một alias khác để tránh xung đột tính năng.")
        sys.exit(1)

    if len(args) < 2:
        print(f"{Fore.RED}❌ Lỗi: Thiếu đối số đường dẫn thư mục <folder absolute path>.{Style.RESET_ALL}")
        print(f"Cú pháp: mod open add {alias} <folder_absolute_path>")
        sys.exit(1)

    # Gộp các token còn lại nếu đường dẫn có khoảng trắng không bọc nháy
    raw_path = " ".join(args[1:]).strip().strip('"').strip("'")
    if not raw_path:
        print(f"{Fore.RED}❌ Lỗi: Đường dẫn thư mục không được để trống.{Style.RESET_ALL}")
        sys.exit(1)

    target_path = Path(raw_path).expanduser().resolve()

    if target_path.is_file():
        print(f"{Fore.RED}❌ Lỗi: Đường dẫn là một FILE, tính năng này chỉ dùng để mở FOLDER.{Style.RESET_ALL}")
        print(f"   {target_path}")
        sys.exit(1)

    # Nếu thư mục chưa tồn tại trên máy tính
    if not target_path.exists():
        print(f"{Fore.YELLOW}⚠️ Thư mục chưa tồn tại trên máy tính:{Style.RESET_ALL} {target_path}")
        ans = input("Bạn có muốn tự động tạo mới thư mục này không? [y/n]: ").strip().lower()
        if ans == "y":
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                print(f"{Fore.GREEN}✅ Đã tạo mới thư mục thành công:{Style.RESET_ALL} {target_path}")
            except Exception as e:
                print(f"{Fore.RED}❌ Không thể tạo thư mục:{Style.RESET_ALL} {e}")
                sys.exit(1)
        else:
            ans_save = input("Bạn vẫn muốn lưu alias trỏ tới đường dẫn này chứ? [y/n]: ").strip().lower()
            if ans_save != "y":
                print(">>> Hủy thao tác.")
                sys.exit(0)

    aliases = load_aliases()

    # Kiểm tra nếu alias đã có sẵn
    if alias in aliases:
        old_path = aliases[alias]
        print(f"{Fore.YELLOW}⚠️ Alias '{alias}' đã tồn tại và đang trỏ tới:{Style.RESET_ALL} {old_path}")
        ans = input("Bạn có muốn cập nhật sang đường dẫn mới không? [y/n]: ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)

    # Lưu alias
    aliases[alias] = str(target_path)
    if save_aliases(aliases):
        print(f"\n{Fore.GREEN}✅ Đã lưu thành công alias '{alias}':{Style.RESET_ALL}")
        print(f"   📂 {target_path}")
        print(f"\n{Fore.CYAN}💡 Bây giờ bạn có thể mở thư mục này bất kỳ lúc nào bằng lệnh:{Style.RESET_ALL}")
        print(f"   mod open {alias}         # Mở trong File Explorer")
        print(f"   mod open {alias} -c      # Mở trong IDE (VS Code / Antigravity)")


def action_list():
    """Liệt kê toàn bộ danh sách alias mở thư mục đã lưu."""
    aliases = load_aliases()
    if not aliases:
        print(f"{Fore.YELLOW}>>> Chưa có alias mở thư mục nào được lưu trên máy tính này.{Style.RESET_ALL}")
        print("💡 Thêm mới bằng cú pháp:")
        print("   mod open add <folder_alias> <folder_absolute_path>")
        print("   (Ví dụ: mod open add lolping \"D:\\D-Temps\\module-4\")")
        sys.exit(0)

    print(f"\n{Fore.CYAN}=== Danh sách Folder Alias đã lưu trên máy tính ({len(aliases)} mục) ==={Style.RESET_ALL}\n")
    print(f"{'STT':<5} {'Alias':<20} {'Trạng thái':<14} {'Đường dẫn'}")
    print("-" * 80)

    for idx, (alias, path_str) in enumerate(sorted(aliases.items()), 1):
        path_obj = Path(path_str)
        if path_obj.exists() and path_obj.is_dir():
            status = f"{Fore.GREEN}[Tồn tại]{Style.RESET_ALL}"
        elif path_obj.exists() and path_obj.is_file():
            status = f"{Fore.YELLOW}[Là file]{Style.RESET_ALL}"
        else:
            status = f"{Fore.RED}[Bị thiếu]{Style.RESET_ALL}"

        print(f"{idx:<5} {Style.BRIGHT}{alias:<20}{Style.RESET_ALL} {status:<23} {path_str}")

    print(f"\n{Fore.LIGHTBLACK_EX}Cách mở: mod open <alias> | mod open <alias> -c{Style.RESET_ALL}")


def action_remove(args: list[str]):
    """Xóa một alias khỏi danh sách."""
    if not args:
        print(f"{Fore.RED}❌ Lỗi: Thiếu tên alias cần xóa.{Style.RESET_ALL}")
        print("Cú pháp: mod open rm <folder_alias>")
        print("Ví dụ  : mod open rm lolping")
        sys.exit(1)

    alias = args[0].strip()
    aliases = load_aliases()

    if alias not in aliases:
        print(f"{Fore.RED}❌ Lỗi: Không tìm thấy alias '{alias}' trong danh sách đã lưu.{Style.RESET_ALL}")
        print("Dùng lệnh 'mod open list' để kiểm tra các alias đang có.")
        sys.exit(1)

    target_path = aliases[alias]
    del aliases[alias]

    if save_aliases(aliases):
        print(f"{Fore.GREEN}✅ Đã xóa thành công alias '{alias}' (từng trỏ tới: {target_path}).{Style.RESET_ALL}")


def main():
    if len(sys.argv) < 2:
        print("Cú pháp quản lý alias mở thư mục:")
        print("  mod open add <folder_alias> <folder_path>   # Thêm alias mới")
        print("  mod open list                               # Xem danh sách alias")
        print("  mod open rm <folder_alias>                  # Xóa alias")
        sys.exit(1)

    subaction = sys.argv[1].lower()
    remaining = sys.argv[2:]

    if subaction == "add":
        action_add(remaining)
    elif subaction in ("list", "ls", "aliases"):
        action_list()
    elif subaction in ("rm", "remove", "del"):
        action_remove(remaining)
    else:
        print(f"{Fore.RED}❌ Lỗi: Hành động '{subaction}' không hợp lệ cho quản lý alias.{Style.RESET_ALL}")
        print("Các lệnh hợp lệ: add, list, rm")
        sys.exit(1)


if __name__ == "__main__":
    main()
