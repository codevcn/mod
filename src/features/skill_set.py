import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path to import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import SKILLS_FOLDER_PATH

def list_folders_recursive(base_path: str) -> list[str]:
    folders = []
    ignore_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".vscode", "dist", "build"}
    base_path = os.path.abspath(base_path)
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for d in dirs:
            full_d = os.path.join(root, d)
            rel_path = os.path.relpath(full_d, base_path)
            folders.append(rel_path.replace("\\", "/"))
    return sorted(folders)

def find_skill_folder(base_path: str, target_name: str) -> str | None:
    # 1. Thử tìm trực tiếp nếu target_name là đường dẫn tương đối (vd: coding/split-code)
    direct_path = os.path.join(base_path, target_name)
    if os.path.exists(direct_path) and os.path.isdir(direct_path):
        return direct_path
        
    # 2. Tìm theo tên folder ở bất kỳ độ sâu nào (bỏ qua các thư mục không cần thiết)
    ignore_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".vscode", "dist", "build"}
    base_path = os.path.abspath(base_path)
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        if target_name in dirs:
            return os.path.join(root, target_name)
            
    return None

def main():
    if len(sys.argv) < 2 or sys.argv[1] != "set":
        print(">>> Lỗi: Lệnh không hợp lệ.")
        sys.exit(1)

    skill_folder_name = sys.argv[2] if len(sys.argv) > 2 else None
    dest_folder_path = sys.argv[3] if len(sys.argv) > 3 else "."

    # UX Improvement: Nếu user chỉ truyền 1 arg dạng path (vd: ./path, D:/path), coi như đó là dest_folder_path và bật chế độ chọn Skill
    if skill_folder_name and len(sys.argv) == 3:
        if skill_folder_name.startswith((".", "/", "\\")) or ":" in skill_folder_name:
            dest_folder_path = skill_folder_name
            skill_folder_name = None

    if not os.path.exists(SKILLS_FOLDER_PATH):
        print(f">>> Cảnh báo: Thư mục kho lưu trữ SKILLs `{SKILLS_FOLDER_PATH}` chưa tồn tại.")
        ans = input("Bạn có muốn tạo thư mục này không? [y/n]: ").strip().lower()
        if ans == "y":
            os.makedirs(SKILLS_FOLDER_PATH, exist_ok=True)
            print(f">>> Đã tạo thư mục kho lưu trữ: {SKILLS_FOLDER_PATH}")
            print(f">>> Vui lòng thêm các thư mục SKILL vào `{SKILLS_FOLDER_PATH}` và thử lại.")
        sys.exit(0)

    if not skill_folder_name:
        print(">>> Đang quét thư mục SKILLs...")
        folders = list_folders_recursive(SKILLS_FOLDER_PATH)
        if not folders:
            print(f">>> Không tìm thấy thư mục SKILL nào trong {SKILLS_FOLDER_PATH}.")
            sys.exit(0)

        print("\nDanh sách các thư mục SKILL có sẵn:")
        for f in folders:
            print(f"  - {f}")
        print()
        
        skill_folder_name = input("Nhập tên Skill và nhấn enter để chọn: ").strip()
        if not skill_folder_name:
            print(">>> Hủy thao tác.")
            sys.exit(0)

    # Resolve src path
    src_path = find_skill_folder(SKILLS_FOLDER_PATH, skill_folder_name)
    if not src_path:
        print(f">>> Lỗi: Không tìm thấy Skill '{skill_folder_name}' trong {SKILLS_FOLDER_PATH}")
        sys.exit(1)

    # Resolve dest path
    dest_folder_path = os.path.abspath(dest_folder_path)
    
    if not os.path.exists(dest_folder_path):
        print(f">>> Cảnh báo: Thư mục đích không tồn tại: {dest_folder_path}")
        ans = input("Bạn có muốn tạo thư mục này không? [y/n]: ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)
        try:
            os.makedirs(dest_folder_path, exist_ok=True)
            print(f">>> Đã tạo thành công thư mục: {dest_folder_path}")
        except Exception as e:
            print(f">>> Lỗi khi tạo thư mục đích: {e}")
            sys.exit(1)

    # Thư mục mới sẽ được tạo trong dest_folder_path với tên của skill folder
    dest_path = os.path.join(dest_folder_path, os.path.basename(os.path.normpath(src_path)))

    if os.path.exists(dest_path):
        print(f">>> Cảnh báo: Thư mục đích đã tồn tại: {dest_path}")
        ans = input("Bạn có muốn ghi đè không? [y/n]: ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)
        try:
            shutil.rmtree(dest_path)
        except Exception as e:
            print(f">>> Lỗi khi xóa thư mục cũ: {e}")
            sys.exit(1)

    print(f">>> Đang copy từ {src_path}")
    print(f">>> Sang {dest_path} ...")
    
    try:
        shutil.copytree(src_path, dest_path)
        print(">>> Copy thành công!")
    except Exception as e:
        print(f">>> Lỗi trong quá trình copy: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
