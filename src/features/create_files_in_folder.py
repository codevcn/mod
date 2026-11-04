#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
create_files_in_folder.py - Khởi tạo các tệp mã nguồn mẫu từ kho template:
- mod file create                   : Mặc định chỉ tạo tệp đích tại thư mục hiện hành (không tạo folder cha).
- mod file create --full-path       : Tạo tệp giữ nguyên toàn bộ cấu trúc đường dẫn thư mục cha.
- mod file create --full            : Alias tương đương của --full-path.
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
    # Phân tích cờ dòng lệnh
    is_full_path = False
    cli_tokens = []
    for arg in sys.argv[1:]:
        if arg.lower() in ("--full-path", "--full"):
            is_full_path = True
        else:
            cli_tokens.append(arg)

    if not os.path.exists(SOURCE_FILES_FOLDER):
        print(f"{Fore.RED}❌ Lỗi: Thư mục kho template không tồn tại: {SOURCE_FILES_FOLDER}{Style.RESET_ALL}")
        sys.exit(1)

    template_files = list_template_files(SOURCE_FILES_FOLDER)
    if not template_files:
        print(f"{Fore.YELLOW}⚠️ Kho template đang rỗng: Chưa có tệp nào trong {SOURCE_FILES_FOLDER}.{Style.RESET_ALL}")
        sys.exit(0)

    mode_label = (
        f"{Fore.CYAN}[Chế độ: Đầy đủ đường dẫn (--full-path)]{Style.RESET_ALL}"
        if is_full_path
        else f"{Fore.LIGHTBLACK_EX}[Mặc định: Chỉ tạo tệp tại thư mục hiện hành - Dùng --full-path để giữ thư mục]{Style.RESET_ALL}"
    )

    print(f"\n{Fore.CYAN}=== KHỞI TẠO TỆP TỪ KHO TEMPLATE (MOD FILE CREATE) ==={Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}Kho template: {SOURCE_FILES_FOLDER}{Style.RESET_ALL}")
    print(f"{mode_label}\n")

    user_input = ""
    if cli_tokens:
        user_input = " ".join(cli_tokens).strip()
        print(f"Nhận diện đối số từ dòng lệnh: {Fore.YELLOW}{user_input}{Style.RESET_ALL}")
    else:
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
            # Tìm kiếm theo tên file hoặc đường dẫn tương đối
            matched_file = None
            clean_search = user_input.replace("\\", "/").strip().lower()
            for f in template_files:
                if f.lower() == clean_search or os.path.basename(f).lower() == clean_search:
                    matched_file = f
                    break
            if not matched_file:
                print(f"{Fore.RED}❌ Lỗi: Không tìm thấy tệp '{user_input}' trong kho template.{Style.RESET_ALL}")
                sys.exit(1)
            chosen_files.append(matched_file)

    # Cảnh báo xung đột tên tệp ở chế độ mặc định (Flat mode) nếu có nhiều tệp cùng basename
    if not is_full_path and len(chosen_files) > 1:
        seen_names = {}
        duplicates = []
        for f in chosen_files:
            bname = os.path.basename(f).lower()
            if bname in seen_names:
                duplicates.append((seen_names[bname], f))
            else:
                seen_names[bname] = f
        if duplicates:
            print(f"\n{Fore.YELLOW}⚠️ CẢNH BÁO TRÙNG TÊN TỆP ĐÍCH:{Style.RESET_ALL}")
            print("Ở chế độ mặc định (tạo phẳng), các tệp sau sẽ ghi đè lên nhau vì có cùng tên:")
            for orig, dup in duplicates:
                print(f"  - {orig}  <==>  {dup}  -> {os.path.basename(dup)}")
            print(f"{Fore.CYAN}💡 Gợi ý: Dùng cờ '--full-path' hoặc '--full' để giữ nguyên cấu trúc thư mục riêng.{Style.RESET_ALL}")
            try:
                ans = input("Bạn có muốn tiếp tục không? (y: Tiếp tục / n: Hủy): ").strip().lower()
                if ans != "y":
                    print(">>> Hủy thao tác.")
                    sys.exit(0)
            except (KeyboardInterrupt, EOFError):
                print("\n>>> Hủy thao tác.")
                sys.exit(0)

    current_dir = os.getcwd()
    print(f"\n📂 Thư mục đích: {current_dir}")
    print(f"🔄 Đang tiến hành tạo {len(chosen_files)} tệp...")

    created_count = 0
    overwrite_all = False

    for rel_name in chosen_files:
        src_path = os.path.normpath(os.path.join(SOURCE_FILES_FOLDER, rel_name))

        if is_full_path:
            dest_rel = rel_name
            dest_path = os.path.normpath(os.path.join(current_dir, rel_name))
        else:
            dest_rel = os.path.basename(rel_name)
            dest_path = os.path.normpath(os.path.join(current_dir, dest_rel))

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
                print(f"   {Fore.LIGHTBLACK_EX}⏩ Đã bỏ qua tệp: {dest_rel}{Style.RESET_ALL}")
                continue

        dest_parent = os.path.dirname(dest_path)
        if dest_parent:
            os.makedirs(dest_parent, exist_ok=True)

        try:
            shutil.copy2(src_path, dest_path)
            print(f"  {Fore.GREEN}✔ Đã tạo thành công:{Style.RESET_ALL} {dest_rel}")
            created_count += 1
        except Exception as e:
            print(f"  {Fore.RED}❌ Lỗi khi tạo tệp '{dest_rel}':{Style.RESET_ALL} {e}")

    print(f"\n{Fore.GREEN}🎉 Hoàn tất: Đã tạo thành công {created_count}/{len(chosen_files)} tệp tại thư mục hiện hành.{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
