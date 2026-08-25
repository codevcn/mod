"""
CLI Handler cho tính năng mod gist:
Cú pháp: mod gist <action> [args...]
Actions hỗ trợ:
  - create <file1> [file2...] [--desc "mô tả"] [--public]
  - list [--page N] [--limit N] [--all] [--public-only] [--secret-only]
  - get <gist_id> [--raw <filename>] [--save <output_dir>]
  - update <gist_id> [--add <name> <path>] [--delete <name>] [--desc "mô tả mới"]
  - delete <gist_id> [-y]
  - audit
  - rate
"""
import os
import sys
from pathlib import Path
from typing import List

# Đảm bảo UTF-8 và nạp đường dẫn gốc
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from configs.paths import PROJECT_ROOT
from features.gist.gist_manager import GistManager
from features.gist.gist_auditor import GistStorageAuditor

try:
    from rich import box
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def print_success(msg: str):
    print(f"\033[92m\033[1m✔ {msg}\033[0m")


def print_info(msg: str):
    print(f"\033[96mℹ {msg}\033[0m")


def print_warning(msg: str):
    print(f"\033[93m⚠️  {msg}\033[0m")


def print_error(msg: str):
    print(f"\033[91m\033[1m❌ {msg}\033[0m")


def handle_create(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist create <file1> [file2...] [--desc "mô tả"] [--public]"""
    desc = ""
    public = False
    file_paths: List[str] = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--desc", "-d", "--description"):
            if i + 1 < len(args):
                desc = args[i + 1]
                i += 2
                continue
            else:
                print_error("Thiếu nội dung mô tả sau cờ --desc.")
                sys.exit(1)
        elif arg in ("--public", "-p"):
            public = True
            i += 1
        else:
            file_paths.append(arg)
            i += 1

    files_dict = {}

    if file_paths:
        for fp_str in file_paths:
            fp = Path(fp_str).resolve()
            if not fp.is_file():
                print_error(f"Tập tin không tồn tại hoặc là thư mục: {fp_str}")
                sys.exit(1)
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    files_dict[fp.name] = f.read()
            except Exception as e:
                print_error(f"Không thể đọc file '{fp.name}': {e}")
                sys.exit(1)
    else:
        # Chế độ tương tác nhập trực tiếp
        print_info("Chế độ tạo Gist tương tác (Interactive Mode):")
        filename = input(" Nhập tên file (vd: note.md, data.json): ").strip()
        if not filename:
            print_error("Tên file không được để trống.")
            sys.exit(1)
        if not desc:
            desc = input(" Nhập mô tả Gist (tùy chọn): ").strip()

        print(" Nhập nội dung file (Gõ 'EOF' trên một dòng riêng để kết thúc):")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break
        content = "\n".join(lines)
        if not content.strip():
            print_error("Nội dung file rỗng, hủy tạo Gist.")
            sys.exit(1)
        files_dict[filename] = content

    print_info(f"Đang tạo Gist ({'Public' if public else 'Secret'})...")
    result = manager.create_gist(files=files_dict, description=desc, public=public)

    gist_id = result.get("id", "")
    html_url = result.get("html_url", "")
    files = result.get("files", {})
    print_success(f"Tạo Gist thành công!")
    print(f"  • Gist ID : \033[93m{gist_id}\033[0m")
    print(f"  • Web URL : \033[96m{html_url}\033[0m")

    if len(files) == 1:
        raw_url = next(iter(files.values())).get("raw_url", "")
        print(f"  • Raw URL : \033[96m{raw_url}\033[0m")
    elif len(files) > 1:
        print(f"  • Raw URLs:")
        for fname, finfo in files.items():
            print(f"    - {fname}: \033[96m{finfo.get('raw_url', '')}\033[0m")

    print(f"  • Files   : {', '.join(files.keys())}")



def handle_list(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist list [--page N] [--limit N] [--all] [--public-only] [--secret-only]"""
    page = 1
    limit = 30
    fetch_all = False
    public_only = False
    secret_only = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--page" and i + 1 < len(args):
            try:
                page = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif arg in ("--limit", "-n") and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif arg in ("--all", "-a"):
            fetch_all = True
            i += 1
        elif arg == "--public-only":
            public_only = True
            i += 1
        elif arg == "--secret-only":
            secret_only = True
            i += 1
        else:
            i += 1

    print_info(f"Đang tải danh sách Gist (trang {page})...")
    if fetch_all:
        gists = manager.get_all_gists()
    else:
        gists = manager.list_gists(per_page=limit, page=page)

    if public_only:
        gists = [g for g in gists if g.get("public")]
    elif secret_only:
        gists = [g for g in gists if not g.get("public")]

    if not gists:
        print_info("Không có Gist nào phù hợp.")
        return

    if HAS_RICH:
        try:
            console = Console(legacy_windows=False)
            table = Table(
                title=f"📋 DANH SÁCH GITHUB GISTS (Tổng: {len(gists)})",
                box=box.SIMPLE_HEAVY,
                header_style="bold cyan",
                border_style="bright_black",
            )
            table.add_column("Gist ID", style="yellow", no_wrap=True)
            table.add_column("Quyền", justify="center")
            table.add_column("Số File", justify="right", style="cyan")
            table.add_column("Dung lượng", justify="right", style="green")
            table.add_column("Tệp đính kèm", style="white")
            table.add_column("Mô tả", style="dim")

            for g in gists:
                gid = g.get("id", "")
                is_pub = g.get("public", False)
                files = g.get("files", {})
                fnames = ", ".join(list(files.keys())[:3])
                if len(files) > 3:
                    fnames += f" (+{len(files) - 3})"

                total_size_bytes = sum(f.get("size", 0) for f in files.values())
                size_str = (
                    f"{total_size_bytes / 1024:.1f} KB"
                    if total_size_bytes < 1024 * 1024
                    else f"{total_size_bytes / (1024 * 1024):.2f} MB"
                )

                desc = g.get("description") or "(Không mô tả)"
                if len(desc) > 35:
                    desc = desc[:32] + "..."

                table.add_row(
                    gid,
                    "🌐 Public" if is_pub else "🔒 Secret",
                    str(len(files)),
                    size_str,
                    fnames,
                    desc,
                )
            console.print(table)
            return
        except Exception:
            pass

    print(f"\n{'ID':<34} | {'Loại':<7} | {'Files':<5} | {'Dung lượng':<10} | Mô tả")
    print("-" * 80)
    for g in gists:
        gid = g.get("id", "")
        is_pub = "Public" if g.get("public") else "Secret"
        files = g.get("files", {})
        total_size_bytes = sum(f.get("size", 0) for f in files.values())
        size_str = f"{total_size_bytes / 1024:.1f} KB"
        desc = (g.get("description") or "(Không mô tả)")[:30]
        print(f"{gid:<34} | {is_pub:<7} | {len(files):<5} | {size_str:<10} | {desc}")
    print()



def handle_get(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist get <gist_id> [--raw <filename>] [--save <output_dir>]"""
    if not args:
        print_error("Thiếu tham số <gist_id>. Cú pháp: mod gist get <gist_id> [--raw <filename>] [--save <dir>]")
        sys.exit(1)

    gist_id = args[0]
    raw_filename = None
    save_dir = None

    i = 1
    while i < len(args):
        if args[i] == "--raw" and i + 1 < len(args):
            raw_filename = args[i + 1]
            i += 2
        elif args[i] in ("--save", "-s") and i + 1 < len(args):
            save_dir = args[i + 1]
            i += 2
        else:
            i += 1

    print_info(f"Đang tải thông tin Gist: {gist_id}...")
    gist = manager.get_gist(gist_id)

    files = gist.get("files", {})
    if not files:
        print_warning("Gist không chứa file nào.")
        return

    # Trường hợp 1: In trực tiếp nội dung raw của một file
    if raw_filename:
        if raw_filename not in files:
            print_error(f"Không tìm thấy file '{raw_filename}' trong Gist {gist_id}.")
            print(f"Các file có sẵn: {', '.join(files.keys())}")
            sys.exit(1)

        finfo = files[raw_filename]
        content = finfo.get("content")
        if content is None:
            raw_url = finfo.get("raw_url", "")
            content = manager.get_raw_file(raw_url)

        print(content)
        return

    # Trường hợp 2: Lưu tất cả file vào thư mục
    if save_dir:
        out_path = Path(save_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)
        print_info(f"Đang lưu các file vào thư mục: {out_path}...")
        for fname, finfo in files.items():
            content = finfo.get("content")
            if content is None:
                content = manager.get_raw_file(finfo.get("raw_url", ""))
            target_file = out_path / fname
            with open(target_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
            print(f"  ✔ Đã lưu: {fname} ({len(content.encode('utf-8')):,} bytes)")
        print_success(f"Tất cả file đã được lưu vào: {out_path}")
        return

    # Trường hợp 3: Hiển thị metadata tóm tắt
    print()
    print(f"\033[1m📌 GIST METADATA:\033[0m")
    print(f"  • ID          : \033[93m{gist.get('id')}\033[0m")
    print(f"  • Mô tả       : {gist.get('description') or '(Không có)'}")
    print(f"  • Quyền       : {'🌐 Public' if gist.get('public') else '🔒 Secret'}")
    print(f"  • Web URL     : \033[96m{gist.get('html_url')}\033[0m")
    print(f"  • Tạo lúc     : {gist.get('created_at')}")
    print(f"  • Cập nhật    : {gist.get('updated_at')}")
    print(f"\n\033[1m📄 DANH SÁCH FILE TRONG GIST ({len(files)}):\033[0m")
    for fname, finfo in files.items():
        sz = finfo.get("size", 0)
        size_str = f"{sz / 1024:.1f} KB" if sz >= 1024 else f"{sz} Bytes"
        print(f"  - \033[92m{fname}\033[0m ({size_str}) -> Raw: \033[90m{finfo.get('raw_url')}\033[0m")
    print()


def handle_update(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist update <gist_id> [--add <name> <filepath>] [--delete <name>] [--desc <mô tả>]"""
    if not args:
        print_error("Thiếu tham số <gist_id>. Cú pháp: mod gist update <gist_id> [--add <name> <filepath>] [--delete <name>] [--desc <desc>]")
        sys.exit(1)

    gist_id = args[0]
    desc = None
    files_to_add = {}
    files_to_delete = []

    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ("--desc", "-d") and i + 1 < len(args):
            desc = args[i + 1]
            i += 2
        elif arg == "--add" and i + 2 < len(args):
            fname = args[i + 1]
            fpath_str = args[i + 2]
            fp = Path(fpath_str).resolve()
            if not fp.is_file():
                print_error(f"File local không tồn tại: {fpath_str}")
                sys.exit(1)
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                files_to_add[fname] = f.read()
            i += 3
        elif arg in ("--delete", "--del") and i + 1 < len(args):
            files_to_delete.append(args[i + 1])
            i += 2
        else:
            i += 1

    if not files_to_add and not files_to_delete and desc is None:
        print_error("Không có thay đổi nào được chỉ định (--add, --delete, hoặc --desc).")
        sys.exit(1)

    print_info(f"Đang cập nhật Gist {gist_id}...")
    result = manager.update_gist(
        gist_id=gist_id,
        files=files_to_add if files_to_add else None,
        files_to_delete=files_to_delete if files_to_delete else None,
        description=desc,
    )
    print_success("Cập nhật Gist thành công!")
    if files_to_add:
        print(f"  • Đã thêm/sửa file : {', '.join(files_to_add.keys())}")
    if files_to_delete:
        print(f"  • Đã xóa file      : {', '.join(files_to_delete)}")
    if desc is not None:
        print(f"  • Mô tả mới        : {desc}")


def handle_delete(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist delete <gist_id> [-y]"""
    if not args:
        print_error("Thiếu tham số <gist_id>. Cú pháp: mod gist delete <gist_id> [-y]")
        sys.exit(1)

    gist_id = args[0]
    skip_confirm = "-y" in args or "--yes" in args

    if not skip_confirm:
        confirm = input(f"\033[93mBạn có chắc chắn muốn XÓA VĨNH VIỄN Gist '{gist_id}'? (y/N): \033[0m").strip().lower()
        if confirm not in ("y", "yes"):
            print_info("Đã hủy thao tác xóa.")
            return

    print_info(f"Đang xóa Gist {gist_id}...")
    success = manager.delete_gist(gist_id)
    if success:
        print_success(f"Đã xóa thành công Gist {gist_id}.")
    else:
        print_error(f"Xóa Gist {gist_id} thất bại.")
        sys.exit(1)


def handle_audit(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist audit"""
    print_info("Đang tiến hành quét và kiểm toán toàn bộ GitHub Gists...")
    auditor = GistStorageAuditor(manager=manager)
    auditor.print_audit_report()


def handle_rate(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist rate"""
    rate_data = manager.get_rate_limit()
    core = rate_data.get("resources", {}).get("core", {})
    from datetime import datetime, timezone

    reset_ts = core.get("reset", 0)
    reset_dt = datetime.fromtimestamp(reset_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print()
    print(f"\033[1m⚡ GITHUB API RATE LIMIT STATUS:\033[0m")
    print(f"  • Tổng hạn mức : \033[96m{core.get('limit', 'N/A')}\033[0m requests/giờ")
    print(f"  • Còn lại      : \033[92m{core.get('remaining', 'N/A')}\033[0m requests")
    print(f"  • Đã dùng      : \033[93m{core.get('used', 'N/A')}\033[0m requests")
    print(f"  • Reset vào lúc: \033[90m{reset_dt}\033[0m")
    print()


def handle_reset(manager: GistManager, args: List[str]):
    """Xử lý lệnh: mod gist reset <gist_id> [--placeholder <name>] [--file <path>] [--desc <desc>] [-y]"""
    if not args:
        print_error("Thiếu tham số <gist_id>. Cú pháp: mod gist reset <gist_id> [--placeholder <name>] [--file <path>] [-y]")
        sys.exit(1)

    gist_id = args[0]
    placeholder_name = "README.md"
    placeholder_content = None
    desc = None
    skip_confirm = False

    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ("--placeholder", "-p") and i + 1 < len(args):
            placeholder_name = args[i + 1]
            i += 2
        elif arg in ("--file", "-f") and i + 1 < len(args):
            fp = Path(args[i + 1]).resolve()
            if not fp.is_file():
                print_error(f"File local không tồn tại: {args[i + 1]}")
                sys.exit(1)
            placeholder_name = fp.name
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                placeholder_content = f.read()
            i += 2
        elif arg in ("--desc", "-d") and i + 1 < len(args):
            desc = args[i + 1]
            i += 2
        elif arg in ("-y", "--yes"):
            skip_confirm = True
            i += 1
        else:
            i += 1

    # Lấy thông tin Gist để hiển thị xác nhận
    print_info(f"Đang kiểm tra Gist '{gist_id}'...")
    gist = manager.get_gist(gist_id)
    files = gist.get("files", {})
    file_count = len(files)

    if not skip_confirm:
        print_warning(
            f"Bạn chuẩn bị RESET Gist '{gist_id}'.\n"
            f"  • Thao tác này sẽ XÓA VĨNH VIỄN {file_count} file hiện có: {', '.join(files.keys())}\n"
            f"  • Và khởi tạo lại với 1 file duy nhất: '{placeholder_name}'"
        )
        confirm = input("\033[93mXác nhận thực hiện reset? (y/N): \033[0m").strip().lower()
        if confirm not in ("y", "yes"):
            print_info("Đã hủy thao tác reset.")
            return

    print_info(f"Đang tiến hành reset Gist {gist_id}...")
    result = manager.reset_gist(
        gist_id=gist_id,
        placeholder_name=placeholder_name,
        placeholder_content=placeholder_content,
        description=desc,
    )

    new_files = result.get("files", {})
    raw_url = next(iter(new_files.values())).get("raw_url", "") if new_files else ""

    print_success(f"Đã reset thành công Gist {gist_id}!")
    print(f"  • Đã xóa bỏ : {file_count} file cũ")
    print(f"  • File mới  : {placeholder_name}")
    print(f"  • Web URL   : \033[96m{result.get('html_url', '')}\033[0m")
    if raw_url:
        print(f"  • Raw URL   : \033[96m{raw_url}\033[0m")


def main():
    raw_args = sys.argv[1:]

    if not raw_args:
        print_error("Thiếu action cho lệnh mod gist.")
        print("Các action hợp lệ: `create`, `list`, `get`, `update`, `delete`, `reset`, `audit`, `rate`.")
        print("Ví dụ: `mod gist list` hoặc `mod gist audit`.")
        sys.exit(1)

    action = raw_args[0].lower()
    remaining = raw_args[1:]

    try:
        manager = GistManager()
    except Exception as e:
        print_error(f"Lỗi khởi tạo GistManager: {e}")
        sys.exit(1)

    try:
        if action == "create":
            handle_create(manager, remaining)
        elif action == "list":
            handle_list(manager, remaining)
        elif action in ("get", "read"):
            handle_get(manager, remaining)
        elif action == "update":
            handle_update(manager, remaining)
        elif action == "delete":
            handle_delete(manager, remaining)
        elif action == "reset":
            handle_reset(manager, remaining)
        elif action in ("audit", "stats"):
            handle_audit(manager, remaining)
        elif action == "rate":
            handle_rate(manager, remaining)
        else:
            print_error(f"Action '{action}' không được hỗ trợ trong nhóm lệnh `mod gist`.")
            print("Các action hợp lệ: `create`, `list`, `get`, `update`, `delete`, `reset`, `audit`, `rate`.")
            sys.exit(1)
    except Exception as e:
        print_error(f"{e}")
        sys.exit(1)



if __name__ == "__main__":
    main()
