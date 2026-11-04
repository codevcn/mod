#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
git_stash.py - Quản lý và xử lý Git Stash trong Mod CLI:
- mod git stash list (hoặc mod git stash ls) : Liệt kê các stash trong kho lưu trữ mod.
- mod git drop [stash_index]                 : Xóa 1 stash khỏi kho lưu trữ (menu tương tác hoặc chỉ định trực tiếp).
- mod git stash drop [stash_index]           : Alias tương đương mod git drop.
"""

import os
import re
import sys
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

# Thêm project root vào sys.path để import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import PROJECT_ROOT


def get_stashes() -> list[dict]:
    """
    Lấy danh sách các Git stash trong kho lưu trữ của Mod CLI.
    Trả về danh sách dict: [{'ref': 'stash@{0}', 'hash': '...', 'time': '...', 'msg': '...'}]
    """
    try:
        cmd = ["git", "stash", "list", '--pretty=format:%gd|%h|%cr|%gs']
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            print(f"{Fore.RED}❌ Lỗi khi đọc danh sách Git stash:{Style.RESET_ALL} {result.stderr.strip()}")
            sys.exit(result.returncode)

        lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        stashes = []
        for line in lines:
            parts = line.split("|", 3)
            if len(parts) >= 4:
                stashes.append({
                    "ref": parts[0].strip(),
                    "hash": parts[1].strip(),
                    "time": parts[2].strip(),
                    "msg": parts[3].strip(),
                })
            else:
                # Fallback parse nếu format khác
                ref_match = re.match(r"^(stash@\{(\d+)\}):?\s*(.*)$", line)
                if ref_match:
                    stashes.append({
                        "ref": ref_match.group(1),
                        "hash": "",
                        "time": "",
                        "msg": ref_match.group(3),
                    })
        return stashes
    except Exception as e:
        print(f"{Fore.RED}❌ Không thể lấy danh sách Git stash:{Style.RESET_ALL} {e}")
        sys.exit(1)


def show_stash_list(stashes: list[dict]):
    """
    In danh sách stash ra màn hình terminal một cách trực quan, có màu sắc.
    """
    count = len(stashes)
    print(f"\n{Fore.CYAN}{Style.BRIGHT}📦 DANH SÁCH GIT STASH CỦA MOD TOOL ({count} stash{'es' if count > 1 else ''}):{Style.RESET_ALL}")
    print(f"   Thư mục: {Fore.YELLOW}{PROJECT_ROOT}{Style.RESET_ALL}")
    print("─" * 76)

    if count == 0:
        print(f"  {Fore.YELLOW}ℹ️ Hiện không có stash nào trong kho lưu trữ.{Style.RESET_ALL}")
        print("─" * 76)
        print(f"💡 Gợi ý: Bạn có thể cất thay đổi bằng: {Fore.GREEN}git stash push -u -m \"ghi chú\"{Style.RESET_ALL}\n")
        return

    for idx, s in enumerate(stashes, 1):
        ref = s["ref"]
        time_str = f" ({s['time']})" if s["time"] else ""
        msg = s["msg"]
        print(f"  [{Fore.GREEN}{idx:2d}{Style.RESET_ALL}] {Fore.CYAN}{Style.BRIGHT}{ref}{Style.RESET_ALL}{Fore.LIGHTBLACK_EX}{time_str}{Style.RESET_ALL}")
        print(f"       └─ {msg}")

    print("─" * 76)
    print(f"💡 Dùng lệnh {Fore.GREEN}mod git drop{Style.RESET_ALL} để chọn và xóa 1 stash không còn dùng nữa.\n")


def execute_drop_stash(stash_ref: str, stash_msg: str = "") -> bool:
    """
    Thực hiện lệnh git stash drop <stash_ref>.
    """
    try:
        cmd = ["git", "stash", "drop", stash_ref]
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode == 0:
            print(f"\n{Fore.GREEN}✅ Đã drop thành công {Style.BRIGHT}{stash_ref}{Style.RESET_ALL}!")
            if stash_msg:
                print(f"   • Nội dung: {stash_msg}")
            return True
        else:
            print(f"\n{Fore.RED}❌ Lỗi khi drop {stash_ref}:{Style.RESET_ALL} {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"\n{Fore.RED}❌ Lỗi không xác định khi drop stash:{Style.RESET_ALL} {e}")
        return False


def run_drop_interactive(args: list[str]):
    """
    Xử lý lệnh drop stash: Nếu có tham số thì xử lý trực tiếp, nếu không thì hiển thị menu tương tác.
    """
    stashes = get_stashes()
    count = len(stashes)

    if count == 0:
        print(f"\n{Fore.YELLOW}ℹ️ Hiện không có stash nào trong kho lưu trữ để drop.{Style.RESET_ALL}\n")
        sys.exit(0)

    # 1. Kiểm tra cờ --yes / -y
    force_yes = False
    clean_args = []
    for a in args:
        if a in ("-y", "--yes"):
            force_yes = True
        else:
            clean_args.append(a)

    target_stash = None

    # 2. Nếu người dùng truyền tham số trực tiếp (ví dụ: `mod git drop 1` hoặc `mod git drop stash@{0}`)
    if clean_args:
        user_param = clean_args[0].strip()
        # Trường hợp 1: Nhập số thứ tự 1..N
        if user_param.isdigit():
            idx = int(user_param)
            if 1 <= idx <= count:
                target_stash = stashes[idx - 1]
            else:
                print(f"\n{Fore.RED}❌ Lỗi: Số thứ tự {idx} nằm ngoài phạm vi (1..{count}).{Style.RESET_ALL}\n")
                sys.exit(1)
        # Trường hợp 2: Nhập trực tiếp ref (vd: stash@{0})
        elif user_param.startswith("stash@{"):
            for s in stashes:
                if s["ref"] == user_param:
                    target_stash = s
                    break
            if not target_stash:
                print(f"\n{Fore.RED}❌ Lỗi: Không tìm thấy stash '{user_param}' trong danh sách hiện có.{Style.RESET_ALL}\n")
                sys.exit(1)
        else:
            print(f"\n{Fore.RED}❌ Lỗi: Tham số không hợp lệ '{user_param}'. Vui lòng nhập số thứ tự (1..{count}) hoặc ref (stash@{{N}}).{Style.RESET_ALL}\n")
            sys.exit(1)

    # 3. Chế độ tương tác (Interactive menu giống mod skill set)
    if not target_stash:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}📦 DANH SÁCH CÁC GIT STASH CÓ THỂ DROP ({count} stash{'es' if count > 1 else ''}):{Style.RESET_ALL}")
        print(f"   Thư mục: {Fore.YELLOW}{PROJECT_ROOT}{Style.RESET_ALL}")
        print("─" * 76)

        for idx, s in enumerate(stashes, 1):
            ref = s["ref"]
            time_str = f" ({s['time']})" if s["time"] else ""
            msg = s["msg"]
            print(f"  [{Fore.GREEN}{idx:2d}{Style.RESET_ALL}] {Fore.CYAN}{Style.BRIGHT}{ref}{Style.RESET_ALL}{Fore.LIGHTBLACK_EX}{time_str}{Style.RESET_ALL}")
            print(f"       └─ {msg}")

        print("─" * 76)
        print()

        try:
            prompt_msg = f"Nhập số thứ tự stash muốn drop (1..{count}), hoặc 'q' để hủy: "
            user_choice = input(prompt_msg).strip()
        except EOFError:
            print("\n>>> Đã hủy thao tác.")
            sys.exit(0)

        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Đã hủy thao tác.")
            sys.exit(0)

        if user_choice.isdigit():
            idx = int(user_choice)
            if 1 <= idx <= count:
                target_stash = stashes[idx - 1]
            else:
                print(f"{Fore.RED}❌ Lỗi: Số thứ tự {idx} không hợp lệ.{Style.RESET_ALL}")
                sys.exit(1)
        elif user_choice.startswith("stash@{"):
            for s in stashes:
                if s["ref"] == user_choice:
                    target_stash = s
                    break
            if not target_stash:
                print(f"{Fore.RED}❌ Lỗi: Không tìm thấy stash '{user_choice}'.{Style.RESET_ALL}")
                sys.exit(1)
        else:
            print(f"{Fore.RED}❌ Lỗi: Lựa chọn không hợp lệ '{user_choice}'.{Style.RESET_ALL}")
            sys.exit(1)

    # 4. Xác nhận an toàn trước khi xóa
    ref = target_stash["ref"]
    msg = target_stash["msg"]

    if not force_yes:
        try:
            confirm = input(f"\n⚠️  Bạn có chắc chắn muốn DROP vĩnh viễn {Fore.CYAN}{ref}{Style.RESET_ALL} không? [y/N]: ").strip().lower()
        except EOFError:
            confirm = "n"

        if confirm not in ("y", "yes"):
            print(">>> Đã hủy thao tác. Stash vẫn được giữ nguyên.\n")
            sys.exit(0)

    # 5. Thực thi drop
    success = execute_drop_stash(ref, msg)
    sys.exit(0 if success else 1)


def main():
    if len(sys.argv) < 2:
        # Mặc định: hiện danh sách stash
        stashes = get_stashes()
        show_stash_list(stashes)
        sys.exit(0)

    action = sys.argv[1].lower()
    remaining_args = sys.argv[2:]

    if action in ("stash", "stashes"):
        # mod git stash [list|ls|drop...]
        sub_action = remaining_args[0].lower() if remaining_args else "list"
        sub_args = remaining_args[1:] if remaining_args else []

        if sub_action in ("list", "ls"):
            stashes = get_stashes()
            show_stash_list(stashes)
            sys.exit(0)
        elif sub_action in ("drop", "rm", "delete"):
            run_drop_interactive(sub_args)
        else:
            # Nếu người dùng gõ `mod git stash` mà không có sub-action hợp lệ, mặc định hiện list
            stashes = get_stashes()
            show_stash_list(stashes)
            sys.exit(0)

    elif action in ("drop", "drop-stash"):
        # mod git drop [args...]
        run_drop_interactive(remaining_args)

    else:
        print(f"{Fore.RED}❌ Action không hợp lệ '{action}'. Chỉ hỗ trợ 'stash list' hoặc 'drop'.{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
