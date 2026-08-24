import os
import sys
import json
import fnmatch
import glob
import zipfile
from datetime import datetime
from pathlib import Path

# Cấu hình UTF-8 cho console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import PROJECT_ROOT


def load_ignore_patterns(ignore_file_path: str) -> list[str]:
    """
    Đọc và phân tích các pattern từ file .compressignore.
    """
    patterns = []
    if not os.path.exists(ignore_file_path):
        return patterns

    with open(ignore_file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            clean_pattern = line.replace("\\", "/")
            patterns.append(clean_pattern)
    return patterns


def is_ignored_by_patterns(rel_path: str, is_dir: bool, patterns: list[str]) -> bool:
    """
    Kiểm tra xem một đường dẫn tương đối có khớp với bất kỳ rule nào trong .compressignore hay không.
    """
    rel_path_norm = rel_path.replace("\\", "/")
    path_parts = rel_path_norm.split("/")

    for pattern in patterns:
        pat = pattern.rstrip("/")
        if pattern.endswith("/"):
            if any(fnmatch.fnmatch(part, pat) for part in path_parts if is_dir or part != path_parts[-1]):
                return True
            if fnmatch.fnmatch(rel_path_norm, pat) or fnmatch.fnmatch(rel_path_norm, f"{pat}/*"):
                return True
        else:
            if fnmatch.fnmatch(rel_path_norm, pat) or fnmatch.fnmatch(os.path.basename(rel_path_norm), pat):
                return True
            if any(fnmatch.fnmatch(part, pat) for part in path_parts):
                return True

    return False


def load_json_config(config_path: str) -> tuple[list[str], list[str]]:
    """
    Đọc file JSON config để lấy include-items và exclude-items.
    """
    include_items = []
    exclude_items = []

    if not os.path.exists(config_path):
        return include_items, exclude_items

    try:
        with open(config_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
            
        raw_includes = data.get("include-items") or data.get("include_items") or []
        raw_excludes = data.get("exclude-items") or data.get("exclude_items") or []

        include_items = [str(x).strip().replace("\\", "/") for x in raw_includes if str(x).strip()]
        exclude_items = [str(x).strip().replace("\\", "/") for x in raw_excludes if str(x).strip()]
    except Exception as e:
        print(f"⚠️ Cảnh báo: Lỗi khi đọc file cấu hình JSON `{config_path}`: {e}")

    return include_items, exclude_items


def match_item_rule(rel_path: str, is_dir: bool, item: str) -> bool:
    """
    Kiểm tra xem rel_path có khớp với một item quy tắc trong include/exclude hay không.
    """
    item_clean = item.rstrip("/")
    rel_norm = rel_path.replace("\\", "/").rstrip("/")
    parts = rel_norm.split("/")

    # 1. Khớp chính xác hoặc là thư mục con bên trong item
    if rel_norm == item_clean or rel_norm.startswith(item_clean + "/"):
        return True

    # 2. Khớp glob với tên file/folder hoặc toàn bộ rel_path
    if fnmatch.fnmatch(rel_norm, item_clean) or fnmatch.fnmatch(os.path.basename(rel_norm), item_clean):
        return True

    # 3. Khớp từng component trong đường dẫn
    if any(fnmatch.fnmatch(part, item_clean) for part in parts if is_dir or part != parts[-1]):
        return True

    return False


def should_traverse_dir(rel_dir: str, include_items: list[str], exclude_items: list[str]) -> bool:
    """
    Quyết định xem có tiếp tục duyệt vào thư mục rel_dir hay không.
    """
    rel_dir_norm = rel_dir.replace("\\", "/").rstrip("/")

    # Nếu nằm trong exclude-items -> Không duyệt
    if any(match_item_rule(rel_dir_norm, True, exc) for exc in exclude_items):
        return False

    # Nếu không có include-items -> Luôn duyệt
    if not include_items:
        return True

    # Nếu có include-items: Duyệt nếu rel_dir là con của include item HOẶC include item nằm bên trong rel_dir
    for inc in include_items:
        inc_clean = inc.rstrip("/")
        # Thư mục hiện tại nằm trong include (vd: include='src', rel_dir='src/utils')
        if rel_dir_norm == inc_clean or rel_dir_norm.startswith(inc_clean + "/"):
            return True
        # Include item nằm sâu bên trong thư mục hiện tại (vd: include='src/utils/tool.py', rel_dir='src')
        if inc_clean.startswith(rel_dir_norm + "/"):
            return True
        # Khớp glob pattern
        if fnmatch.fnmatch(rel_dir_norm, inc_clean) or fnmatch.fnmatch(os.path.basename(rel_dir_norm), inc_clean):
            return True

    return False


def should_include_file(rel_file: str, include_items: list[str], exclude_items: list[str]) -> bool:
    """
    Quyết định xem file rel_file có được đóng gói vào zip hay không.
    """
    rel_file_norm = rel_file.replace("\\", "/")

    # Nếu khớp exclude-items -> Loại bỏ
    if any(match_item_rule(rel_file_norm, False, exc) for exc in exclude_items):
        return False

    # Nếu không khai báo include-items -> Đóng gói tất cả (ngoại trừ exclude)
    if not include_items:
        return True

    # Nếu có include-items -> Chỉ đóng gói file khớp
    for inc in include_items:
        inc_clean = inc.rstrip("/")
        if rel_file_norm == inc_clean or rel_file_norm.startswith(inc_clean + "/"):
            return True
        if fnmatch.fnmatch(rel_file_norm, inc_clean) or fnmatch.fnmatch(os.path.basename(rel_file_norm), inc_clean):
            return True

    return False


def format_size(size_bytes: int) -> str:
    """Định dạng byte thành KB / MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def cleanup_old_zips(target_dir: str, prefix_name: str, current_dest_zip: str):
    """
    Xóa toàn bộ các file zip cũ mang tiền tố tương ứng trong target_dir.
    """
    old_zip_patterns = [
        os.path.join(target_dir, f"{prefix_name}.zip"),
        os.path.join(target_dir, f"{prefix_name}-*.zip"),
    ]
    for pattern in old_zip_patterns:
        for old_file in glob.glob(pattern):
            if os.path.abspath(old_file) != os.path.abspath(current_dest_zip):
                try:
                    os.remove(old_file)
                    print(f"🗑️  Đã dọn dẹp file zip cũ: `{os.path.basename(old_file)}`")
                except Exception as e:
                    print(f"⚠️ Cảnh báo: Không thể xóa file `{os.path.basename(old_file)}`: {e}")


def compress_project(output_path: str | None = None):
    """
    Nén toàn bộ dự án Mod CLI dựa trên file .compressignore.
    """
    project_root = os.path.abspath(PROJECT_ROOT)
    project_name = os.path.basename(project_root)
    
    timestamp_str = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    default_zip_name = f"mod-{timestamp_str}.zip"

    # Mặc định lưu file zip ngay tại root folder của dự án
    if output_path:
        dest_zip = os.path.abspath(output_path)
        if os.path.isdir(dest_zip):
            dest_zip = os.path.join(dest_zip, default_zip_name)
    else:
        dest_zip = os.path.join(project_root, default_zip_name)

    dest_folder = os.path.dirname(dest_zip)
    os.makedirs(dest_folder, exist_ok=True)

    # Đọc .compressignore
    ignore_file = os.path.join(project_root, ".compressignore")
    patterns = load_ignore_patterns(ignore_file)

    print(f"\n======================================================================")
    print(f"📦 BẮT ĐẦU NÉN DỰ ÁN: {project_name}")
    print(f"📍 Thư mục nguồn : {project_root}")
    print(f"📄 File cấu hình : {'.compressignore' if os.path.exists(ignore_file) else 'Không có (nén tất cả)'}")

    # Xóa toàn bộ file zip cũ của dự án
    cleanup_old_zips(dest_folder, "mod", dest_zip)
    print(f"──────────────────────────────────────────────────────────────────────")

    file_count = 0
    try:
        with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(project_root):
                rel_root = os.path.relpath(root, project_root).replace("\\", "/")
                
                # Lọc bỏ các thư mục con khớp với pattern ignore
                dirs_to_keep = []
                for d in dirs:
                    rel_dir_path = f"{rel_root}/{d}" if rel_root != "." else d
                    if not is_ignored_by_patterns(rel_dir_path, is_dir=True, patterns=patterns):
                        dirs_to_keep.append(d)
                dirs[:] = dirs_to_keep

                # Xử lý các file
                for f in files:
                    full_file_path = os.path.join(root, f)
                    rel_file_path = os.path.relpath(full_file_path, project_root).replace("\\", "/")

                    if os.path.abspath(full_file_path) == os.path.abspath(dest_zip):
                        continue
                    if is_ignored_by_patterns(rel_file_path, is_dir=False, patterns=patterns):
                        continue

                    zipf.write(full_file_path, arcname=rel_file_path)
                    file_count += 1

        file_size = os.path.getsize(dest_zip)
        formatted_size = format_size(file_size)

        print(f"✅ ĐÃ NÉN THÀNH CÔNG DỰ ÁN!")
        print(f"──────────────────────────────────────────────────────────────────────")
        print(f"📁 Thư mục lưu trữ : {dest_folder}")
        print(f"📦 Tên file zip     : {os.path.basename(dest_zip)}")
        print(f"📍 Đường dẫn đầy đủ: {dest_zip}")
        print(f"📊 Dung lượng       : {formatted_size} ({file_count} files đã nén)")
        print(f"======================================================================\n")

    except Exception as e:
        print(f"❌ Lỗi trong quá trình nén: {e}")
        sys.exit(1)


def compress_folder(target_folder_path: str, custom_config_path: str | None = None):
    """
    Nén một thư mục cục bộ tùy chỉnh dựa trên file JSON config (include-items & exclude-items).
    """
    target_folder = os.path.abspath(target_folder_path)
    if not os.path.exists(target_folder):
        print(f"❌ Lỗi: Thư mục cần nén không tồn tại: `{target_folder}`")
        sys.exit(1)
    if not os.path.isdir(target_folder):
        print(f"❌ Lỗi: Đường dẫn chỉ định không phải là thư mục: `{target_folder}`")
        sys.exit(1)

    folder_name = os.path.basename(target_folder)
    
    # 1. Tìm file config JSON
    config_file = None
    if custom_config_path:
        resolved_custom = os.path.abspath(custom_config_path)
        if os.path.exists(resolved_custom):
            config_file = resolved_custom
        else:
            print(f"❌ Lỗi: Không tìm thấy file cấu hình được chỉ định: `{resolved_custom}`")
            sys.exit(1)
    else:
        # Mặc định tìm compress-config.json ngay tại root folder của thư mục được chỉ định
        target_internal_config = os.path.join(target_folder, "compress-config.json")
        if os.path.exists(target_internal_config):
            config_file = target_internal_config

    include_items, exclude_items = ([], [])
    if config_file:
        include_items, exclude_items = load_json_config(config_file)

    # 2. Tạo tên file zip đích: <folder_name>-{dd}-{mm}-{yyyy}-{hh}-{mm}-{ss}.zip
    timestamp_str = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    zip_filename = f"{folder_name}-{timestamp_str}.zip"
    dest_zip = os.path.join(target_folder, zip_filename)

    print(f"\n======================================================================")
    print(f"📦 BẮT ĐẦU NÉN THƯ MỤC: {folder_name}")
    print(f"📍 Thư mục nguồn : {target_folder}")
    if config_file:
        print(f"📄 File cấu hình : {config_file}")
        if include_items:
            print(f"   └── Include ({len(include_items)}): {', '.join(include_items)}")
        if exclude_items:
            print(f"   └── Exclude ({len(exclude_items)}): {', '.join(exclude_items)}")
    else:
        print(f"📄 File cấu hình : Không có (nén toàn bộ nội dung thư mục)")

    # 3. Dọn dẹp các file zip cũ của folder này
    cleanup_old_zips(target_folder, folder_name, dest_zip)
    print(f"──────────────────────────────────────────────────────────────────────")

    file_count = 0
    try:
        with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(target_folder):
                rel_root = os.path.relpath(root, target_folder).replace("\\", "/")
                
                # Lọc bỏ các thư mục không cần duyệt
                dirs_to_keep = []
                for d in dirs:
                    rel_dir_path = f"{rel_root}/{d}" if rel_root != "." else d
                    if should_traverse_dir(rel_dir_path, include_items, exclude_items):
                        dirs_to_keep.append(d)
                dirs[:] = dirs_to_keep

                # Xử lý các files
                for f in files:
                    full_file_path = os.path.join(root, f)
                    rel_file_path = os.path.relpath(full_file_path, target_folder).replace("\\", "/")

                    # Không nén chính file output zip
                    if os.path.abspath(full_file_path) == os.path.abspath(dest_zip):
                        continue

                    # Không nén file config json nếu người dùng không muốn
                    if config_file and os.path.abspath(full_file_path) == os.path.abspath(config_file) and not include_items:
                        # Tùy chọn bỏ qua config file nếu mặc định
                        pass

                    if should_include_file(rel_file_path, include_items, exclude_items):
                        zipf.write(full_file_path, arcname=rel_file_path)
                        file_count += 1

        file_size = os.path.getsize(dest_zip)
        formatted_size = format_size(file_size)

        print(f"✅ ĐÃ NÉN THÀNH CÔNG THƯ MỤC!")
        print(f"──────────────────────────────────────────────────────────────────────")
        print(f"📁 Thư mục lưu trữ : {target_folder}")
        print(f"📦 Tên file zip     : {zip_filename}")
        print(f"📍 Đường dẫn đầy đủ: {dest_zip}")
        print(f"📊 Dung lượng       : {formatted_size} ({file_count} files đã nén)")
        print(f"======================================================================\n")

    except Exception as e:
        print(f"❌ Lỗi trong quá trình nén thư mục: {e}")
        sys.exit(1)


def main():
    args = sys.argv[1:]
    
    if not args:
        compress_project(None)
        return

    first_arg = args[0].lower()

    if first_arg == "folder":
        # Cú pháp: mod compress folder <local_folder_path> [--config-file <path>]
        folder_args = args[1:]
        if not folder_args:
            print("❌ Lỗi: Thiếu đường dẫn thư mục cần nén.")
            print("👉 Cú pháp: mod compress folder <local folder path> [--config-file <config_path>]")
            sys.exit(1)

        custom_config = None
        target_path = None
        
        i = 0
        while i < len(folder_args):
            arg = folder_args[i]
            if arg in ("--config-file", "-c"):
                if i + 1 < len(folder_args):
                    custom_config = folder_args[i + 1]
                    i += 2
                    continue
                else:
                    print("❌ Lỗi: Thiếu đường dẫn file cấu hình sau cờ `--config-file`.")
                    sys.exit(1)
            else:
                if target_path is None:
                    target_path = arg
                i += 1

        if not target_path:
            print("❌ Lỗi: Thiếu đường dẫn thư mục cần nén.")
            sys.exit(1)

        compress_folder(target_path, custom_config)
    else:
        # Cú pháp: mod compress [output_path]
        compress_project(args[0])


if __name__ == "__main__":
    main()
