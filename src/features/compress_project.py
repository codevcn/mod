import os
import sys
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
            # Chuẩn hóa dấu phân cách đường dẫn
            clean_pattern = line.replace("\\", "/")
            patterns.append(clean_pattern)
    return patterns


def is_ignored(rel_path: str, is_dir: bool, patterns: list[str]) -> bool:
    """
    Kiểm tra xem một đường dẫn tương đối có khớp với bất kỳ rule nào trong .compressignore hay không.
    """
    rel_path_norm = rel_path.replace("\\", "/")
    path_parts = rel_path_norm.split("/")

    for pattern in patterns:
        pat = pattern.rstrip("/")
        
        # Nếu pattern chỉ định thư mục (có đuôi /)
        if pattern.endswith("/"):
            # Khớp tên bất kỳ folder nào trong chuỗi đường dẫn
            if any(fnmatch.fnmatch(part, pat) for part in path_parts if is_dir or part != path_parts[-1]):
                return True
            if fnmatch.fnmatch(rel_path_norm, pat) or fnmatch.fnmatch(rel_path_norm, f"{pat}/*"):
                return True
        else:
            # Khớp với toàn bộ rel_path hoặc từng component (file name / folder name)
            if fnmatch.fnmatch(rel_path_norm, pat) or fnmatch.fnmatch(os.path.basename(rel_path_norm), pat):
                return True
            if any(fnmatch.fnmatch(part, pat) for part in path_parts):
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


def compress_project(output_path: str | None = None):
    project_root = os.path.abspath(PROJECT_ROOT)
    project_name = os.path.basename(project_root)
    
    # Tạo tên file zip kèm timestamp: mod-{dd}-{mm}-{yyyy}-{hh}-{mm}-{ss}.zip
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

    # Xóa toàn bộ file zip cũ của dự án (mod-*.zip và mod.zip) trong thư mục đích trước khi tạo mới
    old_zip_patterns = [
        os.path.join(dest_folder, "mod.zip"),
        os.path.join(dest_folder, "mod-*.zip"),
    ]
    for pattern in old_zip_patterns:
        for old_file in glob.glob(pattern):
            if os.path.abspath(old_file) != os.path.abspath(dest_zip):
                try:
                    os.remove(old_file)
                    print(f"🗑️  Đã dọn dẹp file zip cũ: `{os.path.basename(old_file)}`")
                except Exception as e:
                    print(f"⚠️ Cảnh báo: Không thể xóa file `{os.path.basename(old_file)}`: {e}")

    print(f"──────────────────────────────────────────────────────────────────────")

    file_count = 0
    skipped_dir_count = 0

    try:
        with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(project_root):
                # Tính relative path của root hiện tại
                rel_root = os.path.relpath(root, project_root).replace("\\", "/")
                
                # Lọc bỏ các thư mục con khớp với pattern ignore
                dirs_to_keep = []
                for d in dirs:
                    rel_dir_path = f"{rel_root}/{d}" if rel_root != "." else d
                    if is_ignored(rel_dir_path, is_dir=True, patterns=patterns):
                        skipped_dir_count += 1
                    else:
                        dirs_to_keep.append(d)
                dirs[:] = dirs_to_keep

                # Xử lý các file
                for f in files:
                    full_file_path = os.path.join(root, f)
                    rel_file_path = os.path.relpath(full_file_path, project_root).replace("\\", "/")

                    # Không nén chính file output zip nếu nằm trong project root
                    if os.path.abspath(full_file_path) == os.path.abspath(dest_zip):
                        continue

                    # Kiểm tra ignore
                    if is_ignored(rel_file_path, is_dir=False, patterns=patterns):
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


def main():
    # Nhận output path tùy chọn từ CLI nếu người dùng truyền vào
    custom_output = sys.argv[1] if len(sys.argv) > 1 else None
    compress_project(custom_output)


if __name__ == "__main__":
    main()
