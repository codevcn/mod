#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
skill_git_commit.py - Đóng gói và đẩy thay đổi của kho AI Skills lên Git:
  mod skill git-commit -m "{message}"
  mod skill commit -m "{message}"
Quy trình:
  1. Kiểm tra thư mục SKILLS_FOLDER_PATH tồn tại và là git repository.
  2. Parse tham số -m / --message. Nếu thiếu, báo lỗi.
  3. Lấy tên nhánh hiện tại (branch đang đứng) của repo SKILLS_FOLDER_PATH.
  4. Chạy `git add -A`
  5. Chạy `git commit -m "{message}"`
  6. Chạy `git push origin <current_branch>`
"""

import os
import sys
import subprocess
from pathlib import Path

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm project root vào sys.path để import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import SKILLS_FOLDER_PATH


def parse_commit_message(args: list[str]) -> str | None:
    """Parse cờ -m hoặc --message từ danh sách tham số."""
    message = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-m", "--message"):
            if i + 1 < len(args):
                message = args[i + 1]
                i += 2
            else:
                print(f"\033[91m❌ Lỗi: Thiếu nội dung commit message sau cờ {arg}.\033[0m")
                print('💡 Ví dụ: mod skill git-commit -m "update skills"')
                sys.exit(1)
        elif arg.startswith(("-m=", "--message=")):
            message = arg.split("=", 1)[1]
            i += 1
        else:
            i += 1
    return message


def run_skill_git_commit(args: list[str]) -> None:
    repo_dir = Path(SKILLS_FOLDER_PATH).resolve()

    if not repo_dir.is_dir():
        print(f"\033[91m❌ Lỗi: Thư mục kho AI Skills không tồn tại: {repo_dir}\033[0m")
        sys.exit(1)

    # 1. Kiểm tra git repository
    try:
        check_repo = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        print("\033[91m❌ Lỗi: Không tìm thấy lệnh 'git' trong PATH của hệ thống.\033[0m")
        sys.exit(1)

    if check_repo.returncode != 0 or check_repo.stdout.strip().lower() != "true":
        print(f"\033[91m❌ Lỗi: Thư mục AI Skills không phải là Git repository: {repo_dir}\033[0m")
        sys.exit(1)

    # 2. Parse commit message
    # Bỏ qua tham số đầu tiên nếu nó là action name ("git-commit" hoặc "commit")
    raw_args = args[1:] if args and args[0].lower() in ("git-commit", "commit") else args
    message = parse_commit_message(raw_args)

    if not message or not message.strip():
        print('\033[91m❌ Lỗi: Thiếu commit message. Bắt buộc truyền cờ -m "<message>".\033[0m')
        print('💡 Ví dụ: mod skill git-commit -m "feat: update core skills"')
        sys.exit(1)

    # 3. Lấy tên nhánh hiện tại
    branch_proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    current_branch = branch_proc.stdout.strip()
    if not current_branch or current_branch == "HEAD":
        current_branch = "main"

    # 4. Kiểm tra xem có thay đổi nào cần commit không
    status_proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if not status_proc.stdout.strip():
        print("\033[93m⚠️ Kho lưu trữ AI Skills không có thay đổi nào cần commit.\033[0m")
        print(f"   Thư mục: \033[96m{repo_dir}\033[0m")
        print(f"   Nhánh  : \033[92m{current_branch}\033[0m")
        sys.exit(0)

    # 5. Thực thi Git flow: add -> commit -> push
    print("\033[96;1m=== Bắt đầu đóng gói & tải code AI Skills (Commit & Push) ===\033[0m")
    print(f"📁 Thư mục: \033[96m{repo_dir}\033[0m")
    print(f"🌿 Nhánh  : \033[92m{current_branch}\033[0m")
    print(f"💬 Message: \033[97m{message.strip()}\033[0m\n")

    print("\033[93m[1/3] Đang thêm tất cả các thay đổi vào staging (git add -A)...\033[0m")
    add_result = subprocess.run(["git", "add", "-A"], cwd=str(repo_dir))
    if add_result.returncode != 0:
        print(f"\033[91m❌ Lỗi: Bước git add thất bại (mã thoát: {add_result.returncode}).\033[0m")
        sys.exit(add_result.returncode)

    print(f'\033[93m[2/3] Đang ghi nhận các thay đổi (git commit -m "{message.strip()}")...\033[0m')
    commit_result = subprocess.run(["git", "commit", "-m", message.strip()], cwd=str(repo_dir))
    if commit_result.returncode != 0:
        print(f"\033[91m❌ Cảnh báo: Bước git commit thất bại (mã thoát: {commit_result.returncode}). Dừng quy trình.\033[0m")
        sys.exit(commit_result.returncode)

    print(f"\033[93m[3/3] Đang đẩy lên máy chủ mã nguồn (git push origin {current_branch})...\033[0m")
    push_result = subprocess.run(["git", "push", "origin", current_branch], cwd=str(repo_dir))
    if push_result.returncode != 0:
        print(f"\033[91m❌ Cảnh báo: Quá trình git push gặp lỗi (mã thoát: {push_result.returncode}).\033[0m")
        sys.exit(push_result.returncode)

    print(f"\n\033[92;1m✅ Đã đóng gói và đẩy thành công kho AI Skills lên nhánh '{current_branch}'!\033[0m")
    sys.exit(0)


if __name__ == "__main__":
    run_skill_git_commit(sys.argv[1:])
