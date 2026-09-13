import os
import sys
import shutil
from pathlib import Path

# Set UTF-8 encoding for console output on Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path to import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import LOCAL_ABSOLUTE_FOLDER_PATH

def has_direct_mcp_file(folder_path: str) -> bool:
    """Kiểm tra một thư mục có chứa file con trực tiếp là README.md không."""
    if not os.path.isdir(folder_path):
        return False
    try:
        return any(
            f.lower() == "readme.md" and os.path.isfile(os.path.join(folder_path, f))
            for f in os.listdir(folder_path)
        )
    except Exception:
        return False

def list_mcp_folders(base_path: str) -> list[str]:
    """
    Chỉ liệt kê các folder nào có file con trực tiếp là README.md.
    Các folder cha phân loại hoặc folder con bên trong MCP sẽ không được liệt kê.
    """
    mcp_folders = []
    ignore_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".vscode", "dist", "build"}
    base_path = os.path.abspath(base_path)
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        if root == base_path:
            continue
        # Chỉ nhận folder có file con trực tiếp là README.md
        if any(f.lower() == "readme.md" and os.path.isfile(os.path.join(root, f)) for f in files):
            rel_path = os.path.relpath(root, base_path)
            mcp_folders.append(rel_path.replace("\\", "/"))
            # Khi đã xác định là 1 MCP, không duyệt sâu vào các thư mục con bên trong nó
            dirs[:] = []
    return sorted(mcp_folders)

def find_mcp_folder(base_path: str, target_name: str) -> str | None:
    """
    Tìm đường dẫn tuyệt đối của thư mục MCP hợp lệ (có file con trực tiếp là README.md).
    Hỗ trợ tìm theo:
    1. Đường dẫn tương đối chính xác (vd: my-mcp/iconify)
    2. Tên thư mục MCP (basename, vd: iconify)
    """
    target_clean = target_name.strip().replace("\\", "/").strip("/")
    base_path = os.path.abspath(base_path)

    # 1. Thử tìm trực tiếp nếu target_name là đường dẫn tương đối
    direct_path = os.path.normpath(os.path.join(base_path, target_clean))
    if has_direct_mcp_file(direct_path):
        return direct_path

    # 2. Quét toàn bộ danh sách MCP hợp lệ trong base_path
    mcps = list_mcp_folders(base_path)

    # 2.1 Khớp tương đối (case-insensitive)
    for m in mcps:
        if m.lower() == target_clean.lower():
            return os.path.normpath(os.path.join(base_path, m))

    # 2.2 Khớp theo tên folder cuối (basename) (case-insensitive)
    for m in mcps:
        if os.path.basename(m).lower() == target_clean.lower():
            return os.path.normpath(os.path.join(base_path, m))

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
        folders = list_mcp_folders(LOCAL_ABSOLUTE_FOLDER_PATH)
        if not folders:
            print(f">>> Không tìm thấy thư mục MCP nào có chứa file README.md trong {LOCAL_ABSOLUTE_FOLDER_PATH}.")
            sys.exit(0)

        print("\nDanh sách các thư mục MCP có sẵn:")
        for f in folders:
            print(f"  - {f}")
        print()
        
        mcp_folder_name = input("Nhập tên MCP và nhấn enter để chọn (hoặc 'q' để hủy): ").strip()
        if not mcp_folder_name or mcp_folder_name.lower() in ("q", "quit", "exit"):
            print(">>> Hủy thao tác.")
            sys.exit(0)

    # Resolve src path
    src_path = find_mcp_folder(LOCAL_ABSOLUTE_FOLDER_PATH, mcp_folder_name)
    if not src_path:
        print(f">>> Lỗi: Không tìm thấy MCP '{mcp_folder_name}' hợp lệ (chứa README.md) trong {LOCAL_ABSOLUTE_FOLDER_PATH}")
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
