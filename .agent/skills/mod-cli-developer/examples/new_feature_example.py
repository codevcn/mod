"""
Feature Script Template mẫu dành cho Mod CLI.
"""
import os
import sys
from pathlib import Path

# Thêm project root vào sys.path để import configs / utils
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import PROJECT_ROOT

def execute_feature(target_path: str, is_dry_run: bool = False):
    print(f">>> Đang xử lý: {target_path} (dry-run: {is_dry_run})")
    # Thực hiện logic nghiệp vụ tại đây...
    print(">>> Hoàn tất thành công!")

def main():
    # Nhận args từ sys.argv (sys.argv[1] là action nếu gọi từ main dispatcher)
    raw_args = sys.argv[1:]
    
    if not raw_args:
        print(">>> Lỗi: Thiếu tham số.")
        sys.exit(1)

    action = raw_args[0]
    remaining = raw_args[1:]

    is_dry_run = "--dry-run" in remaining
    clean_args = [a for a in remaining if a != "--dry-run"]
    target_path = clean_args[0] if clean_args else "."

    if action == "run":
        execute_feature(target_path, is_dry_run)
    else:
        print(f">>> Lỗi: Action '{action}' không hợp lệ.")
        sys.exit(1)

if __name__ == "__main__":
    main()
