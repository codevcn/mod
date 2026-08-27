import os
import sys
import shutil
import time
import argparse
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

# ANSI Colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GRAY = "\033[90m"

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
}
DEFAULT_IGNORE_FILES = {".DS_Store", "Thumbs.db"}


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def scan_folder_tree(
    root_path: Path, ignore_dirs=None, ignore_files=None
) -> tuple[set[str], set[str]]:
    """
    Quét đệ quy toàn bộ thư mục và tệp tin, trả về tập hợp các đường dẫn tương đối (posix format).
    """
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS
    if ignore_files is None:
        ignore_files = DEFAULT_IGNORE_FILES

    rel_dirs = set()
    rel_files = set()

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Bỏ qua các thư mục trong ignore list (lọc in-place)
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

        curr_path = Path(dirpath)
        try:
            rel_dir = curr_path.relative_to(root_path)
        except ValueError:
            continue

        if rel_dir != Path("."):
            rel_dirs.add(rel_dir.as_posix())

        for f in filenames:
            if f not in ignore_files:
                if rel_dir == Path("."):
                    rel_files.add(f)
                else:
                    rel_files.add((rel_dir / f).as_posix())

    return rel_dirs, rel_files


def analyze_tree_similarity(from_path: Path, to_path: Path) -> dict:
    """
    Phân tích cây thư mục nội bộ giữa nguồn và đích để tìm điểm giao và tính độ tương đồng.
    """
    from_dirs, from_files = scan_folder_tree(from_path)
    to_dirs, to_files = scan_folder_tree(to_path)

    from_all = from_dirs | from_files
    to_all = to_dirs | to_files

    common_dirs = from_dirs & to_dirs
    common_files = from_files & to_files
    common_all = from_all & to_all

    new_dirs = from_dirs - to_dirs
    new_files = from_files - to_files
    untouched_files = to_files - from_files

    total_from = len(from_all)
    total_to = len(to_all)
    overlap_count = len(common_all)

    # Tỷ lệ bao phủ so với source (%)
    overlap_from_ratio = (
        (overlap_count / total_from * 100) if total_from > 0 else 0.0
    )
    # Độ tương đồng Jaccard (%)
    union_count = len(from_all | to_all)
    jaccard_similarity = (
        (overlap_count / union_count * 100) if union_count > 0 else 0.0
    )

    return {
        "from_dirs": from_dirs,
        "from_files": from_files,
        "to_dirs": to_dirs,
        "to_files": to_files,
        "common_dirs": sorted(common_dirs),
        "common_files": sorted(common_files),
        "common_all": common_all,
        "new_dirs": sorted(new_dirs),
        "new_files": sorted(new_files),
        "untouched_files": sorted(untouched_files),
        "total_from": total_from,
        "total_to": total_to,
        "overlap_count": overlap_count,
        "overlap_from_ratio": overlap_from_ratio,
        "jaccard_similarity": jaccard_similarity,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Merge nội dung từ folder nguồn vào folder đích với bước kiểm tra độ tương đồng cây thư mục."
    )
    parser.add_argument("from_path", help="Đường dẫn thư mục nguồn (source)")
    parser.add_argument("to_path", help="Đường dẫn thư mục đích (destination)")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Tự động đồng ý xác nhận merge, không hỏi lại",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Chế độ chạy thử, hiển thị thông tin kiểm tra mà không ghi đè/tạo file thật",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Hiển thị chi tiết danh sách các file sẽ bị ghi đè và tạo mới",
    )

    args = parser.parse_args()

    from_folder = Path(args.from_path).resolve()
    to_folder = Path(args.to_path).resolve()

    print(f"\n{BOLD}{CYAN}=== MOD FOLDER MERGE ==={RESET}")
    print(f"  {BOLD}Nguồn (From):{RESET} {from_folder}")
    print(f"  {BOLD}Đích (To):{RESET}   {to_folder}")

    # 1. Validate paths
    if not from_folder.exists():
        print(
            f"\n{RED}[LỖI]{RESET} Thư mục nguồn không tồn tại: '{from_folder}'"
        )
        sys.exit(1)

    if not from_folder.is_dir():
        print(
            f"\n{RED}[LỖI]{RESET} Đường dẫn nguồn không phải là thư mục: '{from_folder}'"
        )
        sys.exit(1)

    if not to_folder.exists():
        print(f"\n{RED}[LỖI]{RESET} Thư mục đích không tồn tại: '{to_folder}'")
        sys.exit(1)

    if not to_folder.is_dir():
        print(
            f"\n{RED}[LỖI]{RESET} Đường dẫn đích không phải là thư mục: '{to_folder}'"
        )
        sys.exit(1)

    if from_folder == to_folder:
        print(
            f"\n{RED}[LỖI]{RESET} Thư mục nguồn và thư mục đích không được trùng nhau."
        )
        sys.exit(1)

    # Kiểm tra tránh trường hợp lồng nhau
    try:
        to_folder.relative_to(from_folder)
        print(
            f"\n{RED}[LỖI]{RESET} Thư mục đích là thư mục con của thư mục nguồn. Không thể merge."
        )
        sys.exit(1)
    except ValueError:
        pass

    try:
        from_folder.relative_to(to_folder)
        print(
            f"\n{RED}[LỖI]{RESET} Thư mục nguồn là thư mục con của thư mục đích. Không thể merge."
        )
        sys.exit(1)
    except ValueError:
        pass

    # 2. Quét và phân tích cây thư mục nội bộ
    print(f"\n{GRAY}Đang quét và kiểm tra độ tương đồng cây thư mục...{RESET}")
    analysis = analyze_tree_similarity(from_folder, to_folder)

    total_from_files = len(analysis["from_files"])
    total_from_dirs = len(analysis["from_dirs"])
    total_to_files = len(analysis["to_files"])
    total_to_dirs = len(analysis["to_dirs"])

    common_files_count = len(analysis["common_files"])
    common_dirs_count = len(analysis["common_dirs"])
    new_files_count = len(analysis["new_files"])
    new_dirs_count = len(analysis["new_dirs"])
    overlap_count = analysis["overlap_count"]

    print(
        f"  - Thư mục nguồn: {BOLD}{total_from_files}{RESET} file, {BOLD}{total_from_dirs}{RESET} folder"
    )
    print(
        f"  - Thư mục đích:   {BOLD}{total_to_files}{RESET} file, {BOLD}{total_to_dirs}{RESET} folder"
    )
    print(
        f"  - Điểm giao nhau: {BOLD}{overlap_count}{RESET} nodes ({common_files_count} file trùng, {common_dirs_count} folder chung)"
    )
    print(
        f"  - Độ tương đồng cấu trúc (Jaccard): {BOLD}{analysis['jaccard_similarity']:.1f}%{RESET}"
    )
    print(
        f"  - Tỷ lệ trùng với nguồn:           {BOLD}{analysis['overlap_from_ratio']:.1f}%{RESET}"
    )

    # 3. Kiểm tra điều kiện GIAO NHAU (Intersection Check)
    if overlap_count == 0:
        print(f"\n{RED}{BOLD}[KIỂM TRA THẤT BẠI - INTERSECTION FAILED]{RESET}")
        print(
            f"{RED}Cây thư mục bên trong giữa 2 folder hoàn toàn KHÔNG CÓ ĐIỂM GIAO NHAU (0% tương đồng).{RESET}"
        )
        print(
            f"{YELLOW}Thư mục nguồn và đích có cấu trúc hoàn toàn tách biệt. Hủy bỏ thao tác merge để tránh nhầm lẫn.{RESET}\n"
        )
        sys.exit(1)

    print(f"\n{GREEN}{BOLD}[KIỂM TRA ĐẠT - TREE INTERSECTION PASSED]{RESET}")
    print(
        f"  {CYAN}●{RESET} File sẽ bị {BOLD}{YELLOW}GHI ĐÈ (Overwrite){RESET}: {BOLD}{common_files_count}{RESET}"
    )
    print(
        f"  {CYAN}●{RESET} File sẽ được {BOLD}{GREEN}TẠO MỚI (Create){RESET}:   {BOLD}{new_files_count}{RESET}"
    )
    print(
        f"  {CYAN}●{RESET} Folder sẽ được {BOLD}{GREEN}TẠO MỚI{RESET}:          {BOLD}{new_dirs_count}{RESET}"
    )
    print(
        f"  {CYAN}●{RESET} File ở đích được {BOLD}{GRAY}GIỮ NGUYÊN{RESET}:       {BOLD}{len(analysis['untouched_files'])}{RESET}"
    )

    # Preview nếu được yêu cầu hoặc khi chạy dry-run
    if args.preview or args.dry_run:
        print(f"\n{BOLD}Chi tiết thao tác dự kiến:{RESET}")
        if analysis["common_files"]:
            print(f"  {YELLOW}--- File sẽ bị ghi đè ({min(5, common_files_count)}/{common_files_count}): ---{RESET}")
            for cf in analysis["common_files"][:5]:
                print(f"    [OVERWRITE] {cf}")
            if common_files_count > 5:
                print(f"    {GRAY}... và {common_files_count - 5} file khác{RESET}")

        if analysis["new_files"]:
            print(f"  {GREEN}--- File sẽ tạo mới ({min(5, new_files_count)}/{new_files_count}): ---{RESET}")
            for nf in analysis["new_files"][:5]:
                print(f"    [CREATE]    {nf}")
            if new_files_count > 5:
                print(f"    {GRAY}... và {new_files_count - 5} file khác{RESET}")

    if args.dry_run:
        print(
            f"\n{YELLOW}[DRY-RUN]{RESET} Đã hoàn tất kiểm tra thử nghiệm. Không có tệp nào bị thay đổi."
        )
        sys.exit(0)

    # 4. Xác nhận người dùng
    if not args.yes:
        try:
            confirm = (
                input(
                    f"\n{BOLD}Bạn có chắc chắn muốn merge từ '{from_folder.name}' vào '{to_folder.name}'? [y/N]: {RESET}"
                )
                .strip()
                .lower()
            )
        except (KeyboardInterrupt, EOFError):
            print(f"\n{YELLOW}Đã hủy thao tác.{RESET}")
            sys.exit(0)

        if confirm not in ("y", "yes"):
            print(f"{YELLOW}Đã hủy thao tác merge theo yêu cầu người dùng.{RESET}")
            sys.exit(0)

    # 5. Thực thi Merge
    print(f"\n{BLUE}Đang tiến hành merge dữ liệu...{RESET}")
    start_time = time.time()
    files_overwritten = 0
    files_created = 0
    dirs_created = 0
    total_bytes = 0

    # Tạo các thư mục con mới nếu chưa có
    for rel_d in analysis["from_dirs"]:
        dest_d = to_folder / rel_d
        if not dest_d.exists():
            dest_d.mkdir(parents=True, exist_ok=True)
            dirs_created += 1

    # Copy files
    for rel_f in analysis["from_files"]:
        src_f = from_folder / rel_f
        dst_f = to_folder / rel_f

        # Đảm bảo thư mục cha của file tồn tại
        dst_f.parent.mkdir(parents=True, exist_ok=True)

        is_overwrite = dst_f.exists()
        file_size = src_f.stat().st_size if src_f.exists() else 0

        shutil.copy2(src_f, dst_f)
        total_bytes += file_size

        if is_overwrite:
            files_overwritten += 1
        else:
            files_created += 1

    elapsed = time.time() - start_time

    # 6. Tổng kết
    print(f"\n{GREEN}{BOLD}=== MERGE THÀNH CÔNG ==={RESET}")
    print(f"  {CYAN}✓{RESET} File đã ghi đè:   {BOLD}{files_overwritten}{RESET}")
    print(f"  {CYAN}✓{RESET} File đã tạo mới:  {BOLD}{files_created}{RESET}")
    print(f"  {CYAN}✓{RESET} Folder đã tạo:    {BOLD}{dirs_created}{RESET}")
    print(f"  {CYAN}✓{RESET} Tổng dung lượng:  {BOLD}{format_size(total_bytes)}{RESET}")
    print(f"  {CYAN}✓{RESET} Thời gian xử lý:  {BOLD}{elapsed:.2f}s{RESET}\n")


if __name__ == "__main__":
    main()
