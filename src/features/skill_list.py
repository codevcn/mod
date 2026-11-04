#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
skill_list.py - Liệt kê các AI Skill trong kho lưu trữ, trong AI Agent Global, hoặc trong dự án (Project):
- mod skill list                             : Chỉ liệt kê các skill trong kho lưu trữ trung tâm.
- mod skill list --agent <name|all>          : CHỈ liệt kê các skill global của AI Agent chỉ định (không in kho gốc).
- mod skill list --include-agent <name|all>  : Liệt kê CẢ HAI (kho lưu trữ trung tâm VÀ các AI Agent).
- mod skill list-project [dest_folder_path]  : Liệt kê các skill trong thư mục dự án (mặc định CWD).
"""

import os
import re
import sys
import yaml
from pathlib import Path
from colorama import init, Fore, Style

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

init(autoreset=True)

# Thêm project root vào sys.path để import configs và features
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import (
    SKILLS_FOLDER_PATH,
    ANTIGRAVITY_SKILLS_PATH,
    CODEX_SKILLS_PATH,
    CLAUDE_SKILLS_PATH,
)
from features.skill_set import (
    LLM_TARGETS,
    list_skill_folders,
    has_direct_skill_file,
)
from features.skill_remove import get_agent_skills


def get_skill_md_path(folder_path: str) -> str | None:
    """Tìm file SKILL.md (hoặc skill.md) trực tiếp bên trong thư mục skill."""
    if not os.path.isdir(folder_path):
        return None
    try:
        for fname in os.listdir(folder_path):
            if fname.lower() == "skill.md":
                p = os.path.join(folder_path, fname)
                if os.path.isfile(p):
                    return p
    except Exception:
        pass
    return None


def get_skill_info(folder_path: str) -> dict:
    """Đọc thông tin name, description, và invocation status từ file SKILL.md."""
    md_path = get_skill_md_path(folder_path)
    if not md_path:
        return {
            "name": os.path.basename(folder_path),
            "description": "",
            "invocation_label": f"{Fore.RED}[Thiếu SKILL.md]{Style.RESET_ALL}",
            "is_valid": False,
        }

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            raw = f.read().lstrip("\ufeff")
    except Exception as e:
        return {
            "name": os.path.basename(folder_path),
            "description": "",
            "invocation_label": f"{Fore.RED}[Lỗi đọc: {e}]{Style.RESET_ALL}",
            "is_valid": False,
        }

    pattern = r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$"
    match = re.match(pattern, raw, re.DOTALL)
    if not match:
        return {
            "name": os.path.basename(folder_path),
            "description": "",
            "invocation_label": f"{Fore.RED}[Frontmatter LỖI]{Style.RESET_ALL}",
            "is_valid": False,
        }

    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    name = data.get("name") or os.path.basename(folder_path)
    desc = data.get("description", "").strip()
    desc_clean = re.sub(r"\s+", " ", desc)

    if data.get("disable-model-invocation") is True:
        invoc_label = f"{Fore.YELLOW}[Tự động gọi: TẮT]{Style.RESET_ALL}"
    else:
        invoc_label = f"{Fore.GREEN}[Tự động gọi: BẬT]{Style.RESET_ALL}"

    return {
        "name": name,
        "description": desc_clean,
        "invocation_label": invoc_label,
        "is_valid": True,
    }


def find_project_skills(base_path: str) -> list[str]:
    """
    Quét danh sách tất cả các skill có trong thư mục dự án base_path.
    Nếu chính base_path chứa trực tiếp SKILL.md, trả về ['.'].
    Ngược lại quét các thư mục con bằng list_skill_folders.
    """
    base_path = os.path.abspath(base_path)
    if has_direct_skill_file(base_path):
        return ["."]
    return list_skill_folders(base_path)


def render_central_skills(skills: list[str], base_path: str):
    """In danh sách skill trong kho trung tâm."""
    norm_base = os.path.normpath(base_path)
    print(f"\n{Fore.CYAN}📦 KHO LƯU TRỮ SKILLS ({len(skills)} skills):{Style.RESET_ALL}")
    print(f"   Đường dẫn: {norm_base}")
    print("─" * 76)

    for idx, s in enumerate(skills, 1):
        full_dir = os.path.normpath(os.path.join(norm_base, s))
        info = get_skill_info(full_dir)
        print(f"  [{idx:2d}] {Fore.WHITE}{Style.BRIGHT}{s:<44}{Style.RESET_ALL} {info['invocation_label']}")
        if info["description"]:
            max_len = 85
            desc = info["description"]
            if len(desc) > max_len:
                desc = desc[:max_len] + "..."
            print(f"       {Fore.LIGHTBLACK_EX}└─ {desc}{Style.RESET_ALL}")


def render_agent_skills(agent_label: str, agent_path: str):
    """In danh sách skill global của một AI Agent cụ thể."""
    norm_path = os.path.normpath(agent_path)
    skills = get_agent_skills(agent_path)

    print(f"\n{Fore.MAGENTA}🤖 SKILL GLOBAL CỦA {agent_label.upper()} ({len(skills)} skills):{Style.RESET_ALL}")
    print(f"   Đường dẫn: {norm_path}")
    print("─" * 76)

    if not os.path.isdir(agent_path):
        print(f"   {Fore.YELLOW}⚠️ Thư mục chưa tồn tại trên máy tính.{Style.RESET_ALL}")
        return

    if not skills:
        print(f"   {Fore.YELLOW}ℹ️ Chưa có Skill nào được cài đặt trong Agent này.{Style.RESET_ALL}")
        return

    for idx, s in enumerate(skills, 1):
        full_dir = os.path.join(norm_path, s)
        info = get_skill_info(full_dir)
        print(f"  [{idx:2d}] {Fore.WHITE}{Style.BRIGHT}{s:<44}{Style.RESET_ALL} {info['invocation_label']}")
        if info["description"]:
            max_len = 85
            desc = info["description"]
            if len(desc) > max_len:
                desc = desc[:max_len] + "..."
            print(f"       {Fore.LIGHTBLACK_EX}└─ {desc}{Style.RESET_ALL}")


def print_agent_target_skills(target_choice: str):
    """In danh sách skill của agent theo lựa chọn (tên agent hoặc 'all')."""
    if target_choice == "all":
        all_agents = [
            ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
            ("OpenAI Codex", CODEX_SKILLS_PATH),
            ("Claude Code", CLAUDE_SKILLS_PATH),
        ]
        for agent_label, agent_path in all_agents:
            render_agent_skills(agent_label, agent_path)
    elif target_choice in LLM_TARGETS:
        agent_label, agent_path = LLM_TARGETS[target_choice]
        render_agent_skills(agent_label, agent_path)
    else:
        print(f"\n{Fore.RED}❌ Lỗi: Tên AI/LLM '{target_choice}' không hợp lệ.{Style.RESET_ALL}")
        print("Các lựa chọn hợp lệ:")
        print("  - agy (antigravity, gemini, anti) : Google Antigravity (~/.gemini/config/skills)")
        print("  - codex (openai)                  : OpenAI Codex (~/.codex/skills)")
        print("  - claude (clau, anthropic)        : Claude Code (~/.claude/skills)")
        print("  - all                             : Liệt kê tất cả các AI Agent trên")
        sys.exit(1)


def handle_list_action(ai_choice: str | None, include_choice: str | None):
    """
    Xử lý lệnh 'mod skill list' / 'mod skill ls':
    1. ai_choice != None      : CHỈ liệt kê AI Agent chỉ định (KHÔNG in kho lưu trữ).
    2. include_choice != None : Liệt kê CẢ HAI (Kho lưu trữ trung tâm VÀ AI Agent).
    3. Không cờ               : CHỈ liệt kê Kho lưu trữ trung tâm.
    """
    # Case 1: Agent-Only mode
    if ai_choice is not None:
        print_agent_target_skills(ai_choice)
        print()
        return

    # Case 2 & 3: Có duyệt qua kho trung tâm
    if not os.path.exists(SKILLS_FOLDER_PATH):
        print(f"{Fore.RED}❌ Lỗi: Thư mục kho lưu trữ SKILLs không tồn tại: {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
        sys.exit(1)

    central_skills = list_skill_folders(SKILLS_FOLDER_PATH)
    if not central_skills:
        print(f"\n{Fore.YELLOW}⚠️ Kho lưu trữ rỗng: Chưa có skill nào trong {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
    else:
        render_central_skills(central_skills, SKILLS_FOLDER_PATH)

    # Nếu truyền --include-agent: Liệt kê thêm Agent
    if include_choice is not None:
        print_agent_target_skills(include_choice)

    print()


def handle_list_project_action(target_dir_input: str | None):
    """Xử lý lệnh 'mod skill list-project' / 'mod skill list-prj'."""
    if target_dir_input:
        target_dir = os.path.abspath(target_dir_input)
        if not os.path.isdir(target_dir):
            print(f"{Fore.RED}❌ Lỗi: Thư mục chỉ định không tồn tại: {target_dir}{Style.RESET_ALL}")
            sys.exit(1)
    else:
        target_dir = os.getcwd()

    norm_target = os.path.normpath(target_dir)
    skills = find_project_skills(target_dir)

    if not skills:
        print(f"\n{Fore.YELLOW}⚠️ Không tìm thấy Skill nào trong thư mục:{Style.RESET_ALL}")
        print(f"   {norm_target}")
        print(f"\n{Fore.LIGHTBLACK_EX}💡 Gợi ý:")
        print(f"   - Thư mục skill hợp lệ phải chứa trực tiếp file 'SKILL.md' (hoặc 'skill.md').")
        print(f"   - Dùng lệnh 'mod skill set <tên_skill> {norm_target}' để cài đặt skill vào thư mục này.{Style.RESET_ALL}\n")
        sys.exit(0)

    print(f"\n{Fore.BLUE}📁 CÁC SKILL TRONG DỰ ÁN ({len(skills)} skills):{Style.RESET_ALL}")
    print(f"   Thư mục: {norm_target}")
    print("─" * 76)

    for idx, s in enumerate(skills, 1):
        if s == ".":
            display_name = os.path.basename(norm_target)
            full_dir = norm_target
        else:
            display_name = s
            full_dir = os.path.normpath(os.path.join(norm_target, s))

        info = get_skill_info(full_dir)
        print(f"  [{idx:2d}] {Fore.WHITE}{Style.BRIGHT}{display_name:<44}{Style.RESET_ALL} {info['invocation_label']}")
        if info["description"]:
            max_len = 85
            desc = info["description"]
            if len(desc) > max_len:
                desc = desc[:max_len] + "..."
            print(f"       {Fore.LIGHTBLACK_EX}└─ {desc}{Style.RESET_ALL}")

    print()


def main():
    if len(sys.argv) < 2:
        print(f"{Fore.RED}❌ Lỗi: Thiếu action (list hoặc list-project).{Style.RESET_ALL}")
        sys.exit(1)

    action = sys.argv[1].lower()
    ai_choice = None
    include_choice = None
    positional_args = []

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("--ai", "--llm", "--agent"):
            if i + 1 < len(sys.argv):
                ai_choice = sys.argv[i + 1].strip().lower()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên AI/Agent sau cờ {arg}. (Ví dụ: --agent agy, --ai claude, --agent all){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--ai=", "--llm=", "--agent=")):
            ai_choice = arg.split("=", 1)[1].strip().lower()
            i += 1
        elif arg in ("--include-agent", "--include-ai", "--include-llm"):
            if i + 1 < len(sys.argv):
                include_choice = sys.argv[i + 1].strip().lower()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên AI/Agent sau cờ {arg}. (Ví dụ: --include-agent agy, --include-agent all){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--include-agent=", "--include-ai=", "--include-llm=")):
            include_choice = arg.split("=", 1)[1].strip().lower()
            i += 1
        else:
            positional_args.append(arg)
            i += 1

    # Kiểm tra xung đột cờ
    if ai_choice is not None and include_choice is not None:
        print(f"{Fore.RED}❌ Lỗi: Không thể dùng đồng thời cờ độc lập (--agent/--ai/--llm) và cờ đồng bộ (--include-agent/--include-ai/--include-llm). Vui lòng chỉ chọn 1 trong 2.{Style.RESET_ALL}")
        sys.exit(1)

    if action in ("list", "ls"):
        handle_list_action(ai_choice, include_choice)
    elif action in ("list-project", "list-prj"):
        target_dir_input = positional_args[0] if positional_args else None
        handle_list_project_action(target_dir_input)
    else:
        print(f"{Fore.RED}❌ Lỗi: Action '{action}' không hợp lệ.{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
