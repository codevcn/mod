#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
seek_features.py - Tìm kiếm và liệt kê tất cả các type và action chứa từ khóa (case-insensitive) kèm ý nghĩa:
  mod seek <keyword>
"""

import os
import sys
from pathlib import Path
import yaml

# Cấu hình UTF-8 cho Windows Console
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

# Thêm project root vào sys.path để import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import CONTENTS_FOLDER

# Mã màu ANSI
CYAN_BOLD = "\033[96;1m"
GREEN_BOLD = "\033[92;1m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
DIM = "\033[90m"
GRAY = "\033[90m"
RED = "\033[91m"
RESET = "\033[0m"


def seek_features(keyword: str) -> None:
    keyword = keyword.strip()
    if not keyword:
        print(f"{RED}❌ Lỗi: Thiếu từ khóa tìm kiếm. Cú pháp: mod seek <keyword>{RESET}")
        print(f"{YELLOW}💡 Ví dụ: mod seek git hoặc mod seek ssh{RESET}")
        sys.exit(1)

    yaml_path = Path(CONTENTS_FOLDER) / "app_features.yml"
    if not yaml_path.exists():
        print(f"{RED}❌ Lỗi: Không tìm thấy file dữ liệu: {yaml_path}{RESET}")
        sys.exit(1)

    with open(yaml_path, "r", encoding="utf-8", errors="replace") as f:
        data = yaml.safe_load(f)

    mod_tool = data.get("mod_tool", {})
    types = mod_tool.get("types", [])

    kw_lower = keyword.lower()
    matched_results = []
    total_actions_found = 0

    for t in types:
        t_name = t.get("name", "")
        t_desc = t.get("description", "")
        actions = t.get("actions", [])

        # Kiểm tra xem Type có khớp từ khóa không
        type_matched = (kw_lower in t_name.lower()) or (kw_lower in t_desc.lower())

        matched_actions = []
        for a in actions:
            a_title = a.get("title", "")
            a_cmd = a.get("command", "")
            a_summary = a.get("summary", "")
            a_details = a.get("details", "")
            a_id = a.get("id", "")

            action_matched = (
                type_matched
                or (kw_lower in a_title.lower())
                or (kw_lower in a_cmd.lower())
                or (kw_lower in a_summary.lower())
                or (kw_lower in a_details.lower())
                or (kw_lower in a_id.lower())
            )

            if action_matched:
                matched_actions.append(a)

        if matched_actions:
            matched_results.append({
                "name": t_name,
                "description": t_desc,
                "type_matched": type_matched,
                "actions": matched_actions,
            })
            total_actions_found += len(matched_actions)

    if not matched_results:
        print()
        print(f"{YELLOW}⚠️  Không tìm thấy Type hoặc Action nào chứa từ khóa '{WHITE}{keyword}{YELLOW}'.{RESET}")
        print(f"{DIM}💡 Gợi ý: Dùng lệnh 'mod ls' để xem toàn bộ danh mục Type & Action hiện có.{RESET}")
        print()
        sys.exit(0)

    print()
    print(f"{CYAN_BOLD}🔍 KẾT QUẢ TÌM KIẾM CHO TỪ KHÓA: '{keyword}' (không phân biệt hoa thường){RESET}")
    print(f"{GRAY}{'─' * 70}{RESET}")

    for item in matched_results:
        t_name = item["name"].upper()
        t_desc = item["description"]
        print(f"  {GREEN_BOLD}[TYPE] {t_name}{RESET} {GRAY}—{RESET} {WHITE}{t_desc}{RESET}")

        for a in item["actions"]:
            title = a.get("title", "")
            act_id = a.get("id", "")
            badge = f" [{act_id}]" if act_id else ""
            cmd = a.get("command", "")
            summary = a.get("summary", "")

            print(f"    {CYAN_BOLD}• {title}{badge}{RESET}")
            print(f"      {DIM}Lệnh:   {RESET}{YELLOW}{cmd}{RESET}")
            print(f"      {DIM}Ý nghĩa:{RESET} {WHITE}{summary}{RESET}")
        print()

    print(f"{GRAY}{'─' * 70}{RESET}")
    print(f"{GREEN_BOLD}📊 Tìm thấy: {len(matched_results)} nhóm lệnh (type), {total_actions_found} hành động (action) khớp với từ khóa '{keyword}'.{RESET}")
    print(f"{DIM}💡 Gõ 'mod <type> <action> --info' để tra cứu chi tiết đầy đủ tham số & điều kiện.{RESET}\n")
    sys.exit(0)


if __name__ == "__main__":
    raw_args = sys.argv[1:]
    # Nếu user gõ `mod seek` thì sys.argv[1:] có thể chứa keyword
    keyword_input = " ".join(raw_args)
    seek_features(keyword_input)
