"""Handle git actions for mod in the current terminal tab."""

import sys
import subprocess
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/mod/.env")

mod_GIT_TYPE = "commit"
mod_GIT_REMOTE = "remote"


def resolve_mod_root_dir() -> str:
    env_root = os.getenv("ROOT_FOLDER_PATH")
    if env_root:
        return env_root

    # Fallback: this file is at <root>/src/system-codes/mod_git.py
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


mod_ROOT_DIR = resolve_mod_root_dir()


def validate_working_repository() -> int:
    if not os.path.isdir(mod_ROOT_DIR):
        print(f">>> Lỗi: Không tìm thấy thư mục làm việc: {mod_ROOT_DIR}")
        return 2

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=mod_ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        print(">>> Lỗi: Không tìm thấy lệnh 'git' trong PATH.")
        return 127

    if result.returncode != 0 or result.stdout.strip().lower() != "true":
        print(f">>> Lỗi: Thư mục không phải git repository: {mod_ROOT_DIR}")
        print(">>> Gợi ý: Kiểm tra ROOT_FOLDER_PATH trong .env hoặc clone/init repo trước khi commit.")
        return 128

    return 0


def git_commit_and_push(message: str) -> int:
    if not message:
        print(">>> Lỗi: Thông điệp commit không được để trống!")
        return 1

    repo_status = validate_working_repository()
    if repo_status != 0:
        return repo_status

    print("=== Bắt đầu đóng gói và tải code (Commit & Push) ===")
    print(f"Thư mục làm việc: {mod_ROOT_DIR}")
    print(f"Commit Message  : {message}")

    print("\n[1/3] Đang thêm file vào staging (git add .)...")
    add_result = subprocess.run(["git", "add", "."], cwd=mod_ROOT_DIR)
    if add_result.returncode != 0:
        print(f"\n>>> Lỗi: Bước git add thất bại (exit code {add_result.returncode}).")
        return add_result.returncode

    print("\n[2/3] Đang ghi nhận các thay đổi (git commit)...")
    commit_result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=mod_ROOT_DIR,
    )
    if commit_result.returncode != 0:
        print(
            f"\n>>> Cảnh báo: Bước git commit thất bại (exit code {commit_result.returncode}). Dừng quy trình."
        )
        return commit_result.returncode

    print("\n[3/3] Đang đẩy lên máy chủ mã nguồn (git push origin main)...")
    result = subprocess.run(["git", "push", "origin", "main"], cwd=mod_ROOT_DIR)

    if result.returncode == 0:
        print("\n=== Hoàn tất thành công! ===")
    else:
        print("\n>>> Cảnh báo: Quá trình push (hoặc commit) có thể đã gặp lỗi.")

    return result.returncode


def print_git_remote() -> int:
    repo_status = validate_working_repository()
    if repo_status != 0:
        return repo_status

    result = subprocess.run(["git", "remote", "-v"], cwd=mod_ROOT_DIR)
    return result.returncode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(">>> No valid git command found.")
        sys.exit(1)

    git_type = sys.argv[1]

    if git_type == mod_GIT_TYPE:
        if len(sys.argv) < 3:
            print(">>> Missing commit message.")
            sys.exit(1)

        commit_message = " ".join(sys.argv[2:])
        sys.exit(git_commit_and_push(commit_message))
    elif git_type == mod_GIT_REMOTE:
        sys.exit(print_git_remote())
    else:
        print(">>> No valid git command found.")
        sys.exit(1)
