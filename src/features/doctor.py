#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
doctor.py - Chẩn đoán tổng thể sức khỏe môi trường & đồng bộ nội bộ cho Mod CLI:
  mod doctor [--strict] [--verbose]
"""

import argparse
import importlib.metadata as importlib_metadata
import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

# Bật ANSI escape trên Windows console (không phụ thuộc colorama để chạy được cả khi thiếu package)
if sys.platform.startswith("win"):
    os.system("")

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import paths
from configs.paths import CONTENTS_FOLDER, PROJECT_ROOT
from configs.version import get_version_tag

# Mã màu ANSI
CYAN_BOLD = "\033[96;1m"
GREEN = "\033[92m"
GREEN_BOLD = "\033[92;1m"
YELLOW = "\033[93m"
RED = "\033[91m"
RED_BOLD = "\033[91;1m"
BLUE = "\033[94m"
WHITE = "\033[97m"
GRAY = "\033[90m"
RESET = "\033[0m"

# Map tên gói PyPI trong requirements.txt sang module Python để kiểm tra import
PACKAGE_IMPORT_MAP = {
    "pyyaml": "yaml",
    "python-dotenv": "dotenv",
    "pillow": "PIL",
    "qrcode": "qrcode",
    "requests": "requests",
    "rich": "rich",
    "colorama": "colorama",
    "gdown": "gdown",
}

# Các alias type hợp lệ có chủ đích giữa VALID_TYPES, TYPE_ACTION_MAP và app_features.yml
KNOWN_VALID_TYPE_ALIASES = {"path"}
KNOWN_MAP_ONLY_ALIASES = {"ls"}

STATUS_BADGE = {
    "OK": f"{GREEN_BOLD}[OK  ]{RESET}",
    "WARN": f"{YELLOW}[WARN]{RESET}",
    "FAIL": f"{RED_BOLD}[FAIL]{RESET}",
    "INFO": f"{BLUE}[INFO]{RESET}",
}


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Đọc key-value từ file .env mà không phụ thuộc python-dotenv."""
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values

    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            values[key] = val
    return values


def parse_requirements(req_path: Path) -> list[tuple[str, str]]:
    """Trích xuất (tên gói chuẩn, dòng yêu cầu gốc) từ requirements.txt."""
    if not req_path.is_file():
        return []

    packages: list[tuple[str, str]] = []
    for raw_line in req_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        pkg_match = re.match(r"^([A-Za-z0-9_.-]+)", line)
        if pkg_match:
            packages.append((pkg_match.group(1), line))
    return packages


def check_environment() -> list[tuple[str, str, str]]:
    """Kiểm tra runtime Python, encoding, công cụ gọi mod trong PATH và file cốt lõi."""
    results: list[tuple[str, str, str]] = []

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 12):
        results.append(("OK", "Python Runtime", f"v{py_ver} ({sys.executable})"))
    else:
        results.append(("FAIL", "Python Runtime", f"v{py_ver} — yêu cầu Python >= 3.12"))

    stdout_enc = getattr(sys.stdout, "encoding", "") or "unknown"
    if "utf" in stdout_enc.lower():
        results.append(("OK", "Console Encoding", f"{stdout_enc}"))
    else:
        results.append(("WARN", "Console Encoding", f"Đang là '{stdout_enc}' (nên dùng UTF-8)"))

    mod_bin = shutil.which("mod") or shutil.which("mod.cmd")
    if mod_bin:
        results.append(("OK", "Lệnh 'mod' trong PATH", mod_bin))
    else:
        results.append(("WARN", "Lệnh 'mod' trong PATH", "Chưa thấy trong PATH (thêm thư mục gốc vào PATH)"))

    py_launcher = shutil.which("py")
    python_bin = shutil.which("python")
    if py_launcher and python_bin:
        results.append(("OK", "Python Launchers", f"py & python sẵn sàng"))
    elif python_bin or py_launcher:
        missing_name = "py" if not py_launcher else "python"
        results.append(("WARN", "Python Launchers", f"Thiếu '{missing_name}' trong PATH"))
    else:
        results.append(("FAIL", "Python Launchers", "Không tìm thấy 'py' hoặc 'python' trong PATH"))

    core_files = [
        "src/main.py",
        "src/configs/paths.py",
        "src/configs/version.py",
        "src/contents/help.txt",
        "src/contents/app_features.yml",
        "requirements.txt",
    ]
    missing_core = [rel for rel in core_files if not (Path(PROJECT_ROOT) / rel).is_file()]
    if not missing_core:
        results.append(("OK", "Tệp cốt lõi hệ thống", f"{len(core_files)}/{len(core_files)} tệp hợp lệ"))
    else:
        results.append(("FAIL", "Tệp cốt lõi hệ thống", f"Thiếu: {', '.join(missing_core)}"))

    return results


def check_python_dependencies() -> list[tuple[str, str, str]]:
    """Kiểm tra toàn bộ dependencies được khai báo trong requirements.txt."""
    req_path = Path(PROJECT_ROOT) / "requirements.txt"
    if not req_path.is_file():
        return [("FAIL", "requirements.txt", "Không tìm thấy file requirements.txt")]

    results: list[tuple[str, str, str]] = []
    for pkg_name, raw_spec in parse_requirements(req_path):
        mod_name = PACKAGE_IMPORT_MAP.get(pkg_name.lower(), pkg_name.replace("-", "_"))
        try:
            installed_ver = importlib_metadata.version(pkg_name)
        except importlib_metadata.PackageNotFoundError:
            installed_ver = None

        can_import = importlib.util.find_spec(mod_name) is not None
        if installed_ver and can_import:
            results.append(("OK", pkg_name, f"v{installed_ver} (khớp '{raw_spec}')"))
        elif can_import:
            results.append(("OK", pkg_name, f"import '{mod_name}' sẵn sàng"))
        else:
            results.append(("FAIL", pkg_name, f"Chưa cài đặt — chạy: pip install -r requirements.txt"))

    return results


def check_external_tools() -> list[tuple[str, str, str]]:
    """Kiểm tra các công cụ CLI bên ngoài được các lệnh của Mod sử dụng."""
    tools = [
        ("git", True, "Bắt buộc cho 'mod git' và 'mod skill git-commit'"),
        ("powershell", False, "Dùng cho Windows Toast / Keep-screen / Power info"),
        ("code", False, "VS Code CLI — dùng cho 'mod code' và 'mod open ... -c'"),
        ("cloudflared", False, "Tùy chọn — dùng cho 'mod tunnel'"),
        ("rclone", False, "Tùy chọn — dùng cho 'mod gdrive'"),
    ]
    results: list[tuple[str, str, str]] = []
    for cmd_name, is_required, purpose in tools:
        found = shutil.which(cmd_name)
        if found:
            results.append(("OK", cmd_name, found))
        elif is_required:
            results.append(("FAIL", cmd_name, f"Không tìm thấy trong PATH ({purpose})"))
        else:
            results.append(("WARN", cmd_name, f"Chưa cài hoặc chưa có trong PATH ({purpose})"))
    return results


def check_env_and_secrets() -> list[tuple[str, str, str]]:
    """Kiểm tra file .env và các khóa tích hợp (không hiển thị giá trị secret)."""
    results: list[tuple[str, str, str]] = []
    env_path = Path(PROJECT_ROOT) / ".env"
    file_env = parse_env_file(env_path)

    if env_path.is_file():
        results.append(("OK", "File .env", str(env_path)))
    else:
        results.append(("INFO", "File .env", "Chưa tạo (chỉ cần nếu dùng 'mod gist' hoặc Telegram)"))

    def has_key(name: str) -> bool:
        return bool(os.environ.get(name) or file_env.get(name))

    if has_key("GITHUB_GIST_TOKEN"):
        results.append(("OK", "GITHUB_GIST_TOKEN", "Đã cấu hình (sẵn sàng cho 'mod gist')"))
    else:
        results.append(("INFO", "GITHUB_GIST_TOKEN", "Chưa cấu hình (chỉ cần nếu dùng 'mod gist')"))

    has_tg_token = has_key("TELEGRAM_BOT_TOKEN")
    has_tg_chat = has_key("TELEGRAM_CHAT_ID")
    if has_tg_token and has_tg_chat:
        results.append(("OK", "Telegram Bot (.env)", "Đã đủ Token & Chat ID ('mod notify --channel telegram')"))
    elif has_tg_token or has_tg_chat:
        missing_part = "TELEGRAM_CHAT_ID" if has_tg_token else "TELEGRAM_BOT_TOKEN"
        results.append(("WARN", "Telegram Bot (.env)", f"Cấu hình dở dang — thiếu {missing_part}"))
    else:
        results.append(("INFO", "Telegram Bot (.env)", "Chưa cấu hình (kênh mặc định hiện tại là 'ntfy')"))

    return results


def check_paths_and_registry(verbose: bool = False) -> list[tuple[str, str, str]]:
    """Kiểm tra đường dẫn trong paths.py và tính đồng bộ giữa các registry nội bộ."""
    results: list[tuple[str, str, str]] = []

    configured = [
        (key, str(val))
        for key, val in paths.__dict__.items()
        if key.isupper() and isinstance(val, (str, Path))
    ]
    missing_paths = [(k, v) for k, v in configured if not os.path.exists(v)]
    ok_count = len(configured) - len(missing_paths)

    if not missing_paths:
        results.append(("OK", "Đường dẫn paths.py", f"{ok_count}/{len(configured)} đường dẫn đều tồn tại"))
    else:
        preview_names = ", ".join(k for k, _ in missing_paths[:4])
        suffix = f" (+{len(missing_paths) - 4} mục khác)" if len(missing_paths) > 4 else ""
        msg = f"{ok_count}/{len(configured)} tồn tại, {len(missing_paths)} chưa tạo: {preview_names}{suffix} — chạy 'mod paths' để xem chi tiết"
        results.append(("WARN", "Đường dẫn paths.py", msg))
        if verbose:
            for k, v in missing_paths:
                results.append(("INFO", f"  └─ {k}", f"Chưa tồn tại: {v}"))

    try:
        from utils.errors import VALID_TYPES
        from utils.interactive_cli import TYPE_ACTION_MAP, TYPE_DESCRIPTIONS

        valid_set = set(VALID_TYPES)
        map_set = set(TYPE_ACTION_MAP.keys())
        desc_set = set(TYPE_DESCRIPTIONS.keys())

        missing_in_map = sorted((valid_set - map_set) - KNOWN_VALID_TYPE_ALIASES)
        missing_in_valid = sorted(map_set - valid_set)
        missing_in_desc = sorted(map_set - desc_set)

        if not missing_in_map and not missing_in_valid and not missing_in_desc:
            results.append(("OK", "Đồng bộ Type Registry", f"VALID_TYPES ({len(valid_set)}) ↔ interactive_cli ({len(map_set)}) khớp"))
        else:
            diffs = []
            if missing_in_map:
                diffs.append(f"VALID_TYPES thừa: {missing_in_map}")
            if missing_in_valid:
                diffs.append(f"Thiếu trong VALID_TYPES: {missing_in_valid}")
            if missing_in_desc:
                diffs.append(f"Thiếu mô tả TYPE_DESCRIPTIONS: {missing_in_desc}")
            results.append(("FAIL", "Đồng bộ Type Registry", "; ".join(diffs)))
    except Exception as exc:
        results.append(("FAIL", "Đồng bộ Type Registry", f"Không thể import registry: {exc}"))
        return results

    yaml_path = Path(CONTENTS_FOLDER) / "app_features.yml"
    if importlib.util.find_spec("yaml") is None:
        results.append(("WARN", "Đồng bộ app_features.yml", "Bỏ qua do thiếu thư viện PyYAML"))
    elif not yaml_path.is_file():
        results.append(("FAIL", "Đồng bộ app_features.yml", f"Không tìm thấy {yaml_path}"))
    else:
        try:
            import yaml

            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8", errors="replace")) or {}
            types_list = data.get("mod_tool", {}).get("types", [])
            yml_set = {t.get("name") for t in types_list if t.get("name") and t.get("name") != "dispatcher"}
            empty_action_types = [t.get("name") for t in types_list if t.get("name") != "dispatcher" and not t.get("actions")]

            missing_in_yml = sorted((map_set - yml_set) - KNOWN_MAP_ONLY_ALIASES)
            missing_from_map = sorted(yml_set - map_set)

            if not missing_in_yml and not missing_from_map and not empty_action_types:
                results.append(("OK", "Catalog app_features.yml", f"{len(yml_set)} types đều khớp & sẵn sàng cho '--info' / 'mod seek'"))
            else:
                issues = []
                if missing_in_yml:
                    issues.append(f"Thiếu trong YAML: {missing_in_yml}")
                if missing_from_map:
                    issues.append(f"YAML chưa đăng ký ở interactive_cli: {missing_from_map}")
                if empty_action_types:
                    issues.append(f"Thiếu actions (mod seek bỏ qua): {empty_action_types}")
                results.append(("FAIL", "Catalog app_features.yml", "; ".join(issues)))
        except Exception as exc:
            results.append(("FAIL", "Catalog app_features.yml", f"Lỗi đọc YAML: {exc}"))

    return results


def render_section(title: str, items: list[tuple[str, str, str]], counts: dict[str, int]) -> None:
    """In một nhóm kiểm tra và cộng dồn bộ đếm trạng thái."""
    print(f"\n{CYAN_BOLD}▸ {title}{RESET}")
    for status, label, detail in items:
        counts[status] = counts.get(status, 0) + 1
        badge = STATUS_BADGE.get(status, status)
        print(f"  {badge} {WHITE}{label:<24}{RESET} {GRAY}│{RESET} {detail}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mod doctor",
        description="Kiểm tra sức khỏe môi trường, dependencies và đồng bộ nội bộ của Mod CLI.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Trả về mã lỗi (exit 1) nếu phát hiện bất kỳ cảnh báo [WARN] hoặc lỗi [FAIL] nào.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Hiển thị chi tiết các đường dẫn chưa tồn tại trong paths.py.",
    )
    args = parser.parse_args()

    print()
    print(f"{CYAN_BOLD}🩺 MOD CLI DOCTOR ({get_version_tag()}) — CHẨN ĐOÁN HỆ THỐNG{RESET}")
    print(f"{GRAY}{'─' * 78}{RESET}")

    counts = {"OK": 0, "WARN": 0, "FAIL": 0, "INFO": 0}
    render_section("1. Môi trường Python & Tệp cốt lõi", check_environment(), counts)
    render_section("2. Thư viện Python (requirements.txt)", check_python_dependencies(), counts)
    render_section("3. Công cụ CLI bên ngoài", check_external_tools(), counts)
    render_section("4. Cấu hình .env & Tích hợp", check_env_and_secrets(), counts)
    render_section("5. Đường dẫn & Đồng bộ Registry", check_paths_and_registry(verbose=args.verbose), counts)

    print(f"\n{GRAY}{'─' * 78}{RESET}")
    summary = (
        f"{GREEN_BOLD}{counts['OK']} OK{RESET} │ "
        f"{YELLOW}{counts['WARN']} WARN{RESET} │ "
        f"{RED_BOLD}{counts['FAIL']} FAIL{RESET} │ "
        f"{BLUE}{counts['INFO']} INFO{RESET}"
    )
    print(f"📊 Tổng kết: {summary}")

    if counts["FAIL"] > 0:
        print(f"{RED_BOLD}❌ Phát hiện {counts['FAIL']} vấn đề nghiêm trọng cần khắc phục.{RESET}\n")
        sys.exit(1)
    if args.strict and counts["WARN"] > 0:
        print(f"{YELLOW}⚠️  Chế độ --strict: Phát hiện {counts['WARN']} cảnh báo cần lưu ý.{RESET}\n")
        sys.exit(1)

    if counts["WARN"] > 0:
        print(f"{GREEN_BOLD}✅ Hệ thống cốt lõi khỏe mạnh{RESET} {GRAY}(có {counts['WARN']} cảnh báo tùy chọn — gõ 'mod doctor --verbose' để xem chi tiết).{RESET}\n")
    else:
        print(f"{GREEN_BOLD}✅ Mọi thành phần đều khỏe mạnh và đồng bộ hoàn toàn!{RESET}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
