import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from configs.paths import CONTENTS_FOLDER

import yaml


def warn_user_error(warning_message: str):
    print(">>> Warn: " + warning_message)
    sys.exit(0)


def print_feature_description(cmd_type: str | None, action: str | None):
    yaml_path = os.path.join(CONTENTS_FOLDER, "app_features.yml")
    if not os.path.exists(yaml_path):
        warn_user_error(f"Cannot find feature definitions: {yaml_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        types = data.get("mod_tool", {}).get("types", [])

        for t in types:
            if cmd_type and t.get("name") != cmd_type:
                continue

            for a in t.get("actions", []):
                cmd_raw = a.get("command", "")
                cmds = [c.strip() for c in cmd_raw.split("|")]

                for cmd in cmds:
                    cmd_parts = cmd.split()

                    if cmd_parts and cmd_parts[0] == "mod":
                        cmd_parts = cmd_parts[1:]

                    yaml_type = cmd_parts[0] if len(cmd_parts) > 0 else None
                    yaml_action = (
                        cmd_parts[1]
                        if len(cmd_parts) > 1
                        and not cmd_parts[1].startswith("<")
                        and not cmd_parts[1].startswith("[")
                        and not cmd_parts[1].startswith("-")
                        else None
                    )

                    target_found = False
                    if cmd_type is None and action is None:
                        if yaml_type is None or yaml_type.startswith("-"):
                            target_found = True
                    elif cmd_type is not None and action is None:
                        if yaml_type == cmd_type and yaml_action is None:
                            target_found = True
                    elif cmd_type is not None and action is not None:
                        if yaml_type == cmd_type and yaml_action == action:
                            target_found = True

                    if target_found:
                        # ANSI color codes
                        C = "\033[36m"  # Cyan
                        G = "\033[32m"  # Green
                        Y = "\033[33m"  # Yellow
                        W = "\033[97m"  # White bright
                        D = "\033[2m"   # Dim
                        R = "\033[0m"   # Reset

                        print(f"\n{C}--- Tính năng: {a.get('title')} ---{R}")
                        print(f"{G}+) Lệnh:{R}\t{Y}{a.get('command')}{R}")
                        print(f"{G}+) Tóm tắt:{R}\t{W}{a.get('summary')}{R}")
                        print(f"{G}+) Chi tiết:{R}\t{D}{a.get('details')}{R}")
                        print(f"{G}+) Điều kiện:{R}\t{D}{a.get('conditions')}{R}\n")
                        sys.exit(0)

        cmd_str = f"mod {cmd_type or ''} {action or ''}".strip()
        warn_user_error(f"Không tìm thấy mô tả cho lệnh: `{cmd_str}`")

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
