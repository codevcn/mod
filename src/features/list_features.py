#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
list_features.py - Liệt kê tất cả các type và action hiện có (chỉ tên, không giải thích ý nghĩa):
  mod ls
  mod list
  mod ls -k "<keyword>"
  mod list --key "<keyword>"
"""

import os
import sys
from pathlib import Path

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

# Thêm project root vào sys.path để import configs và utils
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.interactive_cli import TYPE_ACTION_MAP

# Mã màu ANSI
CYAN_BOLD = "\033[96;1m"
GREEN_BOLD = "\033[92;1m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
DIM = "\033[90m"
GRAY = "\033[90m"
RED = "\033[91m"
RESET = "\033[0m"


def parse_arguments(args: list[str]) -> str | None:
    """Parse cờ --key, -k, --keyword từ danh sách đối số."""
    keyword = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--key", "-k", "--keyword"):
            if i + 1 < len(args):
                keyword = args[i + 1].strip()
                i += 2
            else:
                print(f"{RED}❌ Lỗi: Thiếu từ khóa sau cờ {arg}.{RESET}")
                print(f"{YELLOW}💡 Ví dụ: mod ls {arg} \"git\"{RESET}")
                sys.exit(1)
        elif arg.startswith(("--key=", "-k=", "--keyword=")):
            keyword = arg.split("=", 1)[1].strip()
            i += 1
        elif not arg.startswith("-") and keyword is None:
            # Hỗ trợ truyền thẳng keyword không cần cờ
            keyword = arg.strip()
            i += 1
        else:
            i += 1
    return keyword


def list_features(args: list[str]) -> None:
    keyword = parse_arguments(args)

    sorted_types = sorted(TYPE_ACTION_MAP.keys())

    if keyword:
        kw_lower = keyword.lower()
        matched_items = []
        total_actions_found = 0

        for t in sorted_types:
            acts = sorted(TYPE_ACTION_MAP.get(t, []))
            type_matched = kw_lower in t.lower()

            if type_matched:
                matched_items.append((t, acts))
                total_actions_found += len(acts)
            else:
                matched_acts = [a for a in acts if kw_lower in a.lower()]
                if matched_acts:
                    matched_items.append((t, matched_acts))
                    total_actions_found += len(matched_acts)

        if not matched_items:
            print()
            print(f"{YELLOW}⚠️  Không tìm thấy Type hoặc Action nào chứa từ khóa '{WHITE}{keyword}{YELLOW}'.{RESET}")
            print(f"{DIM}💡 Gõ 'mod ls' để xem toàn bộ danh sách Type & Action hiện có.{RESET}")
            print()
            sys.exit(0)

        print()
        print(f"{CYAN_BOLD}🔍 KẾT QUẢ LỌC DANH SÁCH THEO TỪ KHÓA: '{keyword}'{RESET}")
        print(f"{GRAY}{'─' * 70}{RESET}")
        for t, acts in matched_items:
            acts_str = f"{CYAN_BOLD}{', '.join(acts)}{RESET}" if acts else f"{DIM}(không có action){RESET}"
            print(f"  {GREEN_BOLD}• {t:<10}{RESET} {GRAY}│{RESET} {acts_str}")
        print(f"{GRAY}{'─' * 70}{RESET}")
        print(f"{GREEN_BOLD}📊 Tìm thấy: {len(matched_items)} nhóm lệnh (type), {total_actions_found} hành động (action) khớp với từ khóa '{keyword}'.{RESET}")
        print(f"{DIM}💡 Gõ 'mod seek {keyword}' để xem giải thích ý nghĩa chi tiết.{RESET}\n")
        sys.exit(0)

    # Trường hợp không có keyword: Liệt kê toàn bộ
    print()
    print(f"{CYAN_BOLD}📋 DANH SÁCH TOÀN BỘ NHÓM LỆNH (TYPES) & HÀNH ĐỘNG (ACTIONS):{RESET}")
    print(f"{GRAY}{'─' * 70}{RESET}")
    total_actions = 0
    for t in sorted_types:
        acts = sorted(TYPE_ACTION_MAP.get(t, []))
        total_actions += len(acts)
        acts_str = f"{CYAN_BOLD}{', '.join(acts)}{RESET}" if acts else f"{DIM}(không có action){RESET}"
        print(f"  {GREEN_BOLD}• {t:<10}{RESET} {GRAY}│{RESET} {acts_str}")
    print(f"{GRAY}{'─' * 70}{RESET}")
    print(f"{GREEN_BOLD}📊 Tổng cộng: {len(sorted_types)} nhóm lệnh (type), {total_actions} hành động (action).{RESET}")
    print(f"{DIM}💡 Gõ 'mod seek <keyword>' để tìm kiếm kèm giải thích ý nghĩa.{RESET}")
    print(f"{DIM}💡 Gõ 'mod ls -k <keyword>' để lọc danh sách theo từ khóa.{RESET}\n")
    sys.exit(0)


if __name__ == "__main__":
    list_features(sys.argv[1:])
