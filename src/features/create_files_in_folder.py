#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
create_files_in_folder.py - Khởi tạo các tệp mã nguồn mẫu từ kho template:
- mod file create
Kho template được cấu hình tại SOURCE_FILES_FOLDER trong configs/paths.py.
"""

import os
import re
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


def list_template_files(base_folder: str) -> list[str]:
    """Quét toàn bộ danh sách tệp trong thư mục template (bỏ qua tệp/thư mục ẩn)."""
    template_files = []
    if not os.path.exists(base_folder):
        return []

    for root, dirs, files in os.walk(base_folder):
        # Bỏ qua thư mục ẩn hoặc thư mục hệ thống
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for f in files:
            if f.startswith("."):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, base_folder).replace("\\", "/")
            template_files.append(rel_path)

    return sorted(template_files, key=lambda x: x.lower())


def main():
    if not os.path.exists(SOURCE_FILES_FOLDER):
        print(f"{Fore.RED}❌ Lỗi: Thư mục kho template không tồn tại: {SOURCE_FILES_FOLDER}{Style.RESET_ALL}")
        sys.exit(1)

    template_files = list_template_files(SOURCE_FILES_FOLDER)
    if not template_files:
        print(f"{Fore.YELLOW}⚠️ Kho template đang rỗng: Chưa có tệp nào trong {SOURCE_FILES_FOLDER}.{Style.RESET_ALL}")
        sys.exit(0)

    print(f"\n{Fore.CYAN}=== KHỞI TẠO TỆP TỪ KHO TEMPLATE (MOD FILE CREATE) ==={Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}Kho template: {SOURCE_FILES_FOLDER}{Style.RESET_ALL}\n")
    print(f"Danh sách các tệp mẫu có sẵn ({len(template_files)} tệp):")
    print(f"  [ 0] Thoát (quit / 'q')")
    for idx, f in enumerate(template_files, 1):
        print(f"  [{idx:2d}] {f}")
    if len(template_files) > 1:
        print(f"  [ a] Tạo TẤT CẢ các tệp trên ({len(template_files)} tệp)")
    print()

    try:
        user_input = input(
            "Nhập số thứ tự (vd: 1 hoặc 1 2), tên tệp, hoặc 'a' để tạo tất cả ('q' hoặc '0' để hủy): "
        ).strip()
    except (KeyboardInterrupt, EOFError):
        print("\n>>> Hủy thao tác.")
        sys.exit(0)

    if not user_input or user_input.lower() in ("0", "q", "quit", "exit"):
        print(">>> Hủy thao tác an toàn.")
        sys.exit(0)

    chosen_files = []

    if user_input.lower() in ("a", "all", "*"):
        chosen_files = list(template_files)
    else:
        num_tokens = re.findall(r"\d+", user_input)
        if num_tokens and not re.sub(r"[\d\s,]", "", user_input):
            chosen_indices = [int(n) for n in num_tokens]
            for idx in chosen_indices:
                if idx == 0:
                    print(">>> Hủy thao tác an toàn.")
                    sys.exit(0)
                elif 1 <= idx <= len(template_files):
                    f_cand = template_files[idx - 1]
                    if f_cand not in chosen_files:
                        chosen_files.append(f_cand)
                else:
                    print(f"{Fore.YELLOW}⚠️ Bỏ qua số thứ tự ngoài phạm vi: {idx}{Style.RESET_ALL}")
            if not chosen_files:
                print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                sys.exit(1)
        else:
            # Tìm kiếm theo tên file
            matched_file = None
            for f in template_files:
                if f.lower() == user_input.lower() or os.path.basename(f).lower() == user_input.lower():
                    matched_file = f
                    break
            if not matched_file:
                print(f"{Fore.RED}❌ Lỗi: Không tìm thấy tệp '{user_input}' trong kho template.{Style.RESET_ALL}")
                sys.exit(1)
            chosen_files.append(matched_file)

    current_dir = os.getcwd()
    print(f"\n📂 Thư mục đích: {current_dir}")
    print(f"🔄 Đang tiến hành tạo {len(chosen_files)} tệp...")

    created_count = 0
    overwrite_all = False

    for rel_name in chosen_files:
        src_path = os.path.normpath(os.path.join(SOURCE_FILES_FOLDER, rel_name))
        dest_path = os.path.normpath(os.path.join(current_dir, rel_name))

        # Kiểm tra nếu file đã tồn tại tại nơi đứng
        if os.path.exists(dest_path) and not overwrite_all:
            print(f"\n{Fore.YELLOW}⚠️ Tệp đã tồn tại: {dest_path}{Style.RESET_ALL}")
            try:
                ans = input("   Bạn có muốn ghi đè? (y: Có / n: Bỏ qua / a: Ghi đè tất cả): ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\n>>> Đã hủy tiến trình.")
                sys.exit(0)

            if ans == "a":
                overwrite_all = True
            elif ans != "y":
                print(f"   {Fore.LIGHTBLACK_EX}⏩ Đã bỏ qua tệp: {rel_name}{Style.RESET_ALL}")
                continue

        dest_parent = os.path.dirname(dest_path)
        if dest_parent:
            os.makedirs(dest_parent, exist_ok=True)

        try:
            shutil.copy2(src_path, dest_path)
            print(f"  {Fore.GREEN}✔ Đã tạo thành công:{Style.RESET_ALL} {rel_name}")
            created_count += 1
        except Exception as e:
            print(f"  {Fore.RED}❌ Lỗi khi tạo tệp '{rel_name}':{Style.RESET_ALL} {e}")

    print(f"\n{Fore.GREEN}🎉 Hoàn tất: Đã tạo thành công {created_count}/{len(chosen_files)} tệp tại thư mục hiện hành.{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
