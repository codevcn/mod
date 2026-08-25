"""
Module GistStorageAuditor: Quét, kiểm toán dung lượng và đánh giá hạn mức GitHub Gist.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Cấu hình UTF-8 console Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Đảm bảo đường dẫn gốc dự án được thêm vào sys.path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from .gist_manager import GistManager

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class GistStorageAuditor:
    """Kiểm toán dung lượng lưu trữ, phân loại tệp và giám sát GitHub Gist."""

    # Ngưỡng cảnh báo kích thước file đơn lẻ (GitHub Gist giới hạn tối đa 10 MB/file)
    MAX_FILE_LIMIT_BYTES = 10 * 1024 * 1024  # 10 MB
    WARN_FILE_LIMIT_BYTES = 8 * 1024 * 1024   # 8 MB

    def __init__(self, manager: Optional[GistManager] = None):
        self.manager = manager or GistManager()

    def audit(self) -> Dict[str, Any]:
        """
        Thực hiện toàn bộ quy trình kiểm toán Gist và API Rate Limit.
        """
        gists = self.manager.get_all_gists()

        total_bytes = 0
        total_files = 0
        public_count = sum(1 for g in gists if g.get("public"))
        secret_count = len(gists) - public_count

        # Phân tích theo đuôi mở rộng: {ext: {"size": bytes, "count": int}}
        file_types: Dict[str, Dict[str, Any]] = {}
        all_files_detail: List[Dict[str, Any]] = []
        large_files_warnings: List[Dict[str, Any]] = []

        for gist in gists:
            gist_id = gist.get("id", "")
            is_public = gist.get("public", False)
            description = gist.get("description", "") or "(Không có mô tả)"

            for fname, finfo in gist.get("files", {}).items():
                fsize = finfo.get("size", 0)
                total_bytes += fsize
                total_files += 1

                ext = os.path.splitext(fname)[1].lower() or "[no_ext]"
                if ext not in file_types:
                    file_types[ext] = {"size": 0, "count": 0}
                file_types[ext]["size"] += fsize
                file_types[ext]["count"] += 1

                file_record = {
                    "filename": fname,
                    "size_bytes": fsize,
                    "size_kb": round(fsize / 1024, 2),
                    "size_mb": round(fsize / (1024 * 1024), 4),
                    "gist_id": gist_id,
                    "gist_desc": description,
                    "public": is_public,
                    "raw_url": finfo.get("raw_url", ""),
                }
                all_files_detail.append(file_record)

                if fsize >= self.WARN_FILE_LIMIT_BYTES:
                    large_files_warnings.append(file_record)

        # Sắp xếp top file lớn nhất giảm dần
        all_files_detail.sort(key=lambda x: x["size_bytes"], reverse=True)
        top_files = all_files_detail[:10]

        # Sắp xếp file types theo dung lượng giảm dần
        sorted_file_types = dict(
            sorted(file_types.items(), key=lambda item: item[1]["size"], reverse=True)
        )

        # Lấy thông tin Rate Limit
        rate_info = {}
        try:
            rate_data = self.manager.get_rate_limit()
            core_rate = rate_data.get("resources", {}).get("core", {})
            reset_ts = core_rate.get("reset", 0)
            reset_dt = (
                datetime.fromtimestamp(reset_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                if reset_ts
                else "N/A"
            )
            rate_info = {
                "limit": core_rate.get("limit", 0),
                "remaining": core_rate.get("remaining", 0),
                "used": core_rate.get("used", 0),
                "reset_timestamp": reset_ts,
                "reset_time_utc": reset_dt,
            }
        except Exception as e:
            rate_info = {
                "error": str(e),
                "limit": "N/A",
                "remaining": "N/A",
                "used": "N/A",
                "reset_time_utc": "N/A",
            }

        return {
            "total_gists": len(gists),
            "public_gists": public_count,
            "secret_gists": secret_count,
            "total_files": total_files,
            "total_size_bytes": total_bytes,
            "total_size_kb": round(total_bytes / 1024, 2),
            "total_size_mb": round(total_bytes / (1024 * 1024), 4),
            "file_type_breakdown": sorted_file_types,
            "top_files": top_files,
            "large_files_warnings": large_files_warnings,
            "rate_limit": rate_info,
        }

    def print_audit_report(self, data: Optional[Dict[str, Any]] = None):
        """In báo cáo kiểm toán trực quan ra console bằng Rich hoặc ANSI."""
        if data is None:
            data = self.audit()

        if HAS_RICH:
            try:
                self._print_rich_report(data)
            except Exception:
                self._print_ansi_report(data)
        else:
            self._print_ansi_report(data)

    def _print_rich_report(self, data: Dict[str, Any]):
        console = Console(legacy_windows=False)


        # Panel Tổng quan
        rate = data.get("rate_limit", {})
        summary_text = Text()
        summary_text.append(f"📦 Tổng số Gist       : ", style="bold cyan")
        summary_text.append(f"{data['total_gists']:,} ", style="bold white")
        summary_text.append(f"({data['secret_gists']} Secret 🔒, {data['public_gists']} Public 🌐)\n", style="dim")

        summary_text.append(f"📄 Tổng số File       : ", style="bold cyan")
        summary_text.append(f"{data['total_files']:,} files\n", style="bold white")

        summary_text.append(f"💾 Tổng dung lượng    : ", style="bold cyan")
        summary_text.append(f"{data['total_size_mb']:.4f} MB ", style="bold green")
        summary_text.append(f"({data['total_size_kb']:,} KB / {data['total_size_bytes']:,} Bytes)\n", style="dim")

        summary_text.append(f"⚡ GitHub Rate Limit  : ", style="bold cyan")
        rem = rate.get("remaining", "N/A")
        lim = rate.get("limit", "N/A")
        rate_style = "bold green" if isinstance(rem, int) and rem > 1000 else "bold yellow"
        summary_text.append(f"{rem}/{lim} requests ", style=rate_style)
        summary_text.append(f"(Reset lúc: {rate.get('reset_time_utc', 'N/A')})", style="dim")

        console.print()
        console.print(
            Panel(
                summary_text,
                title="[bold yellow]📊 BÁO CÁO KIỂM TOÁN DUNG LƯỢNG GITHUB GIST[/bold yellow]",
                border_style="bright_blue",
                box=box.ROUNDED,
            )
        )

        # Cảnh báo file lớn
        warnings = data.get("large_files_warnings", [])
        if warnings:
            warn_table = Table(
                title="⚠️ CẢNH BÁO FILE GẦN NGƯỠNG GIỚI HẠN (>= 8 MB / 10 MB MAX)",
                box=box.ROUNDED,
                header_style="bold red",
                border_style="red",
            )
            warn_table.add_column("Tên File", style="white")
            warn_table.add_column("Dung lượng (MB)", justify="right", style="bold red")
            warn_table.add_column("Gist ID", style="cyan")
            warn_table.add_column("Loại", justify="center")

            for w in warnings:
                warn_table.add_row(
                    w["filename"],
                    f"{w['size_mb']:.2f} MB",
                    w["gist_id"],
                    "Public" if w["public"] else "Secret",
                )
            console.print(warn_table)
            console.print()

        # Bảng phân loại theo đuôi file (Extension breakdown)
        breakdown = data.get("file_type_breakdown", {})
        if breakdown:
            type_table = Table(
                title="📑 PHÂN BỐ DUNG LƯỢNG THEO ĐUÔI TỆP (FILE TYPE BREAKDOWN)",
                box=box.SIMPLE_HEAVY,
                header_style="bold magenta",
                border_style="bright_black",
            )
            type_table.add_column("Định dạng (Ext)", style="bold cyan")
            type_table.add_column("Số lượng file", justify="right", style="white")
            type_table.add_column("Dung lượng (KB)", justify="right", style="white")
            type_table.add_column("Dung lượng (MB)", justify="right", style="bold green")
            type_table.add_column("Tỷ lệ %", justify="right", style="yellow")

            total_b = data["total_size_bytes"] or 1
            for ext, info in breakdown.items():
                sz = info["size"]
                cnt = info["count"]
                pct = (sz / total_b) * 100
                type_table.add_row(
                    ext,
                    f"{cnt:,}",
                    f"{sz / 1024:,.2f}",
                    f"{sz / (1024 * 1024):,.4f}",
                    f"{pct:.1f}%",
                )
            console.print(type_table)
            console.print()

        # Bảng Top 10 file lớn nhất
        top_files = data.get("top_files", [])
        if top_files:
            top_table = Table(
                title="🏆 TOP FILE CÓ KÍCH THƯỚC LỚN NHẤT",
                box=box.SIMPLE_HEAVY,
                header_style="bold green",
                border_style="bright_black",
            )
            top_table.add_column("#", justify="center", style="dim")
            top_table.add_column("Tên File", style="white")
            top_table.add_column("Kích thước", justify="right", style="bold cyan")
            top_table.add_column("Gist ID", style="yellow")
            top_table.add_column("Mô tả Gist", style="dim")

            for idx, f in enumerate(top_files, start=1):
                size_str = (
                    f"{f['size_mb']:.3f} MB"
                    if f["size_mb"] >= 1.0
                    else f"{f['size_kb']:.1f} KB"
                )
                desc = (
                    (f["gist_desc"][:30] + "...")
                    if len(f["gist_desc"]) > 30
                    else f["gist_desc"]
                )
                top_table.add_row(str(idx), f["filename"], size_str, f["gist_id"], desc)
            console.print(top_table)
            console.print()

    def _print_ansi_report(self, data: Dict[str, Any]):
        rate = data.get("rate_limit", {})
        print("\n" + "=" * 65)
        print("  📊 BÁO CÁO KIỂM TOÁN DUNG LƯỢNG GITHUB GIST")
        print("=" * 65)
        print(f"📦 Tổng số Gist    : {data['total_gists']} ({data['secret_gists']} Secret, {data['public_gists']} Public)")
        print(f"📄 Tổng số File    : {data['total_files']} files")
        print(f"💾 Tổng dung lượng : {data['total_size_mb']:.4f} MB ({data['total_size_kb']} KB)")
        print(f"⚡ API Rate Limit  : {rate.get('remaining', 'N/A')}/{rate.get('limit', 'N/A')} reqs (Reset: {rate.get('reset_time_utc', 'N/A')})")
        print("-" * 65)

        warnings = data.get("large_files_warnings", [])
        if warnings:
            print("\n⚠️  CẢNH BÁO FILE LỚN (>= 8 MB):")
            for w in warnings:
                print(f"  - {w['filename']} ({w['size_mb']:.2f} MB) [Gist ID: {w['gist_id']}]")

        breakdown = data.get("file_type_breakdown", {})
        if breakdown:
            print("\n📑 PHÂN BỐ THEO ĐUÔI TỆP:")
            for ext, info in breakdown.items():
                print(f"  {ext:<10} : {info['count']:>4} files | {info['size'] / (1024 * 1024):>8.4f} MB")

        top_files = data.get("top_files", [])
        if top_files:
            print("\n🏆 TOP 10 FILE LỚN NHẤT:")
            for idx, f in enumerate(top_files, 1):
                print(f"  {idx:>2}. {f['filename']} ({f['size_kb']} KB) [ID: {f['gist_id']}]")
        print("=" * 65 + "\n")
