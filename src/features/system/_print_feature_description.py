import sys
import os
import argparse
from pathlib import Path

# Enable ANSI escape sequences on Windows terminals
if sys.platform.startswith("win"):
    os.system("")

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from configs.paths import CONTENTS_FOLDER, SRC_FOLDER, PROJECT_ROOT

import yaml

# ANSI color codes
CYAN_BOLD = "\033[96;1m"
GREEN_BOLD = "\033[92;1m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
DIM = "\033[90m"
GRAY = "\033[90m"
RESET = "\033[0m"


def warn_user_error(warning_message: str):
    print(">>> Warn: " + warning_message)
    sys.exit(0)


def render_raw_if_any(action: dict) -> bool:
    """Nếu action có raw_file hoặc raw_text, đọc và in trực tiếp."""
    if "raw_file" in action and action.get("raw_file"):
        raw_rel = action.get("raw_file")
        candidate_paths = [
            Path(SRC_FOLDER) / raw_rel,
            Path(PROJECT_ROOT) / raw_rel,
            Path(raw_rel),
        ]
        for cp in candidate_paths:
            if cp.is_file():
                with open(cp, "r", encoding="utf-8", errors="replace") as f:
                    print(f"\n{f.read().strip()}\n")
                return True
        warn_user_error(f"Không tìm thấy file tài liệu: {raw_rel}")

    if "raw_text" in action and action.get("raw_text"):
        print(f"\n{action.get('raw_text').strip()}\n")
        return True

    return False


def render_action_block(action: dict):
    """Cấp 3: In chi tiết 1 action theo định dạng bảng ANSI."""
    title = action.get("title", "Không có tiêu đề")
    act_id = action.get("id", "")
    id_badge = f" [{act_id}]" if act_id else ""

    print()
    print(f"{CYAN_BOLD}--- Tính năng: {title}{id_badge} ---{RESET}")
    print(f"{GREEN_BOLD}+) Lệnh:{RESET}\t{YELLOW}{action.get('command', 'Không có')}{RESET}")
    print(f"{GREEN_BOLD}+) Tóm tắt:{RESET}\t{WHITE}{action.get('summary', 'Không có')}{RESET}")
    print(f"{GREEN_BOLD}+) Chi tiết:{RESET}\t{DIM}{action.get('details', 'Không có')}{RESET}")

    if action.get("parameters"):
        print(f"{GREEN_BOLD}+) Tham số:{RESET}\t{WHITE}{action.get('parameters')}{RESET}")
    if action.get("flags"):
        print(f"{GREEN_BOLD}+) Flags:{RESET}\t{WHITE}{action.get('flags')}{RESET}")
    if action.get("conditions"):
        print(f"{GREEN_BOLD}+) Điều kiện:{RESET}\t{DIM}{action.get('conditions')}{RESET}")
    print()


def render_type_overview(type_data: dict):
    """Cấp 2: In danh sách toàn bộ các action trong nhóm lệnh."""
    type_name = type_data.get("name", "").upper()
    desc = type_data.get("description", "")
    actions = type_data.get("actions", [])

    print()
    print(f"{CYAN_BOLD}=== NHÓM LỆNH: {type_name} ({desc}) ==={RESET}")
    print(f"{GRAY}{'─' * 70}{RESET}")

    for a in actions:
        title = a.get("title", "")
        act_id = a.get("id", "")
        badge = f" [{act_id}]" if act_id else ""
        cmd = a.get("command", "")
        summary = a.get("summary", "")

        print(f"  {GREEN_BOLD}• {title}{badge}{RESET}")
        print(f"    {DIM}Lệnh:   {RESET} {YELLOW}{cmd}{RESET}")
        print(f"    {DIM}Tóm tắt:{RESET} {WHITE}{summary}{RESET}")
        print()

    print(f"{CYAN_BOLD}💡 Xem chi tiết từng lệnh:{RESET} Gõ {WHITE}mod {type_data.get('name')} <action> --info{RESET}")
    print(f"{GRAY}{'─' * 70}{RESET}")
    print()


def render_global_overview(data: dict):
    """Cấp 1: In thông tin toàn cục của Mod CLI."""
    mod_tool = data.get("mod_tool", {})
    dispatcher_flags = mod_tool.get("dispatcher_flags", [])
    types = mod_tool.get("types", [])

    print()
    print(f"{CYAN_BOLD}{'=' * 68}{RESET}")
    print(f"{CYAN_BOLD}🚀 Mod CLI (mod) — Bộ Công Cụ Tự Động Hóa & Tiện Ích Đa Năng{RESET}")
    print(f"{CYAN_BOLD}{'=' * 68}{RESET}")
    print(f"{GREEN_BOLD}+) Cú pháp chung:{RESET} {YELLOW}mod <type> <action> [tham_số...] [flags]{RESET}")
    print(f"{GREEN_BOLD}+) Chế độ tương tác:{RESET} {WHITE}Chạy 'mod' không tham số để vào REPL + Tab Autocomplete.{RESET}")
    print()
    print(f"{YELLOW}Các cờ điều phối toàn cục (Dispatcher Flags):{RESET}")
    for df in dispatcher_flags:
        flag_str = df.get("flag", "")
        desc = df.get("description", "")
        print(f"  {GREEN_BOLD}{flag_str:<22}{RESET} : {WHITE}{desc}{RESET}")
    print()
    print(f"{YELLOW}Danh sách nhóm lệnh (Types):{RESET}")
    for t in types:
        t_name = t.get("name", "")
        t_desc = t.get("description", "")
        print(f"  {GREEN_BOLD}{t_name:<10}{RESET} : {WHITE}{t_desc}{RESET}")
    print()
    print(f"{CYAN_BOLD}💡 Tra cứu chi tiết:{RESET} Gõ {WHITE}mod <type> --info{RESET} hoặc {WHITE}mod <type> <action> --info{RESET}")
    print(f"{CYAN_BOLD}{'=' * 68}{RESET}")
    print()


def is_command_match(command_str: str, cmd_type: str, cmd_action: str | None) -> bool:
    """
    Kiểm tra xem command_str (có thể chứa alias '|') có khớp với cmd_type và cmd_action không.
    """
    if not command_str:
        return False

    sub_cmds = [c.strip() for c in command_str.split("|")]

    for sub_cmd in sub_cmds:
        tokens = sub_cmd.split()
        if tokens and tokens[0] == "mod":
            tokens = tokens[1:]

        yaml_type = tokens[0] if len(tokens) > 0 else None
        yaml_action = (
            tokens[1]
            if len(tokens) > 1
            and not tokens[1].startswith("<")
            and not tokens[1].startswith("[")
            and not tokens[1].startswith("-")
            else None
        )

        if cmd_action:
            if yaml_type == cmd_type and yaml_action == cmd_action:
                return True
            # Khớp chuỗi alias chính xác
            if f"mod {cmd_type} {cmd_action}" in sub_cmd:
                return True
        else:
            if yaml_type == cmd_type and yaml_action is None:
                return True

    return False


def print_feature_description(cmd_type: str | None, action: str | None):
    yaml_path = os.path.join(CONTENTS_FOLDER, "app_features.yml")
    if not os.path.exists(yaml_path):
        warn_user_error(f"Cannot find feature definitions: {yaml_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        types = data.get("mod_tool", {}).get("types", [])

        # CẤP 1: Tra cứu toàn cục (mod --info)
        if not cmd_type and not action:
            render_global_overview(data)
            sys.exit(0)

        # Tìm type trong danh sách
        target_type = None
        for t in types:
            if t.get("name") == cmd_type:
                target_type = t
                break

        if not target_type:
            warn_user_error(f"Không tìm thấy nhóm lệnh '{cmd_type}' trong tài liệu.")

        actions = target_type.get("actions", [])

        # CẤP 2: Tra cứu cấp nhóm lệnh (mod <type> --info)
        if cmd_type and not action:
            # Nếu có action chứa raw_file cho cả type (như Gist)
            for a in actions:
                if is_command_match(a.get("command", ""), cmd_type, None):
                    if render_raw_if_any(a):
                        sys.exit(0)
                    if len(actions) == 1:
                        render_action_block(a)
                        sys.exit(0)

            # Mặc định in tổng quan nhóm lệnh
            render_type_overview(target_type)
            sys.exit(0)

        # CẤP 3: Tra cứu cấp action cụ thể (mod <type> <action> --info)
        target_action = None
        for a in actions:
            if is_command_match(a.get("command", ""), cmd_type, action):
                target_action = a
                break

        if target_action:
            if render_raw_if_any(target_action):
                sys.exit(0)
            render_action_block(target_action)
            sys.exit(0)

        warn_user_error(
            f"Mặc dù loại lệnh '{cmd_type}' tồn tại nhưng không tìm thấy mô tả cho action '{action}'."
        )

    except ImportError:
        warn_user_error(
            "Chưa cài đặt thư viện 'pyyaml'. Vui lòng chạy `pip install pyyaml` hoặc `pip install -r requirements.txt`"
        )
    except Exception as e:
        warn_user_error(f"Lỗi khi đọc file mô tả YAML: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print feature description.")
    parser.add_argument("--type", type=str, default=None, help="Command type")
    parser.add_argument("--action", type=str, default=None, help="Command action")
    args = parser.parse_args()

    print_feature_description(args.type, args.action)
