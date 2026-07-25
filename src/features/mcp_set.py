import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path to import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import LOCAL_ABSOLUTE_FOLDER_PATH

def list_folders_recursive(base_path: str) -> list[str]:
    folders = []
    ignore_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".vscode", "dist", "build"}
    base_path = os.path.abspath(base_path)
    for root, dirs, files in os.walk(base_path):
        # Remove ignored directories to not traverse them
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for d in dirs:
            if os.path.abspath(root) == base_path:
                continue # Bỏ qua folder con cấp 1
            rel_path = os.path.relpath(os.path.join(root, d), base_path)
            # Standardize to forward slashes for output
            folders.append(rel_path.replace("\\", "/"))
    return folders

def find_mcp_folder(base_path: str, target_name: str) -> str | None:
    # 1. Thử tìm trực tiếp nếu target_name là đường dẫn tương đối (vd: my-mcp/iconify)
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

    mcp_folder_name = sys.argv[2] if len(sys.argv) > 2 else None
    dest_folder_path = sys.argv[3] if len(sys.argv) > 3 else "."

    # UX Improvement: Nếu user chỉ truyền 1 arg dạng path (vd: ./path, D:/path), coi như đó là dest_folder_path và bật chế độ chọn MCP (mcp_folder_name = None)
    if mcp_folder_name and len(sys.argv) == 3:
        if mcp_folder_name.startswith((".", "/", "\\")) or ":" in mcp_folder_name:
            dest_folder_path = mcp_folder_name
            mcp_folder_name = None

    if not os.path.exists(LOCAL_ABSOLUTE_FOLDER_PATH):
        print(f">>> Lỗi: Thư mục gốc {LOCAL_ABSOLUTE_FOLDER_PATH} không tồn tại.")
        sys.exit(1)

    if not mcp_folder_name:
        print(">>> Đang quét thư mục...")
        folders = list_folders_recursive(LOCAL_ABSOLUTE_FOLDER_PATH)
        if not folders:
            print(f">>> Không tìm thấy thư mục con nào trong {LOCAL_ABSOLUTE_FOLDER_PATH}.")
            sys.exit(0)

        print("\nDanh sách các thư mục MCP có sẵn:")
        for f in folders:
            print(f"  - {f}")
        print()
        
        mcp_folder_name = input("Nhập folder name và nhấn enter để chọn: ").strip()
        if not mcp_folder_name:
            print(">>> Hủy thao tác.")
            sys.exit(0)

    # Resolve src path
    src_path = find_mcp_folder(LOCAL_ABSOLUTE_FOLDER_PATH, mcp_folder_name)
    if not src_path:
        print(f">>> Lỗi: Không tìm thấy MCP '{mcp_folder_name}' trong {LOCAL_ABSOLUTE_FOLDER_PATH}")
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
            os.makedirs(dest_folder_path)
            print(f">>> Đã tạo thành công thư mục: {dest_folder_path}")
        except Exception as e:
            print(f">>> Lỗi khi tạo thư mục đích: {e}")
            sys.exit(1)

    # The new folder will be created inside dest_folder_path with the name (basename) of src_path
    dest_path = os.path.join(dest_folder_path, os.path.basename(os.path.normpath(src_path)))

    if os.path.exists(dest_path):
        print(f">>> Cảnh báo: Thư mục đích đã tồn tại: {dest_path}")
        ans = input("Bạn có muốn ghi đè không? [y/n]: ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)
        # Remove existing if user wants to overwrite
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
