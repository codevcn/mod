#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
skill_import.py - Import (copy) AI Skill từ thư mục Global của AI Agent về kho chung SKILLS_FOLDER_PATH:
  mod skill import <skill_name> [--from-ai agy|claude|codex] [--to-folder <folder>]
  mod skill import --from-ai <agy|claude|codex> [--to-folder <folder>] [--key, -k <kw>] [--filter, -f <on|off>]

Quy tắc đầu vào (optional có điều kiện):
  - Nếu KHÔNG truyền <skill_name>: BẮT BUỘC phải truyền --from-ai để quét Agent đó và liệt kê danh sách chọn (hỗ trợ chọn nhiều: 1 2 4, hoặc 'a').
  - Nếu CÓ truyền <skill_name>: --from-ai là tùy chọn (nếu bỏ trống sẽ tự tìm trên Antigravity, Claude Code, Codex).
"""

import os
import re
import shutil
import sys
from pathlib import Path
from colorama import init, Fore, Style

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

init(autoreset=True)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import (
    ANTIGRAVITY_SKILLS_PATH,
    CLAUDE_SKILLS_PATH,
    CODEX_SKILLS_PATH,
    SKILLS_FOLDER_PATH,
)
from features.skill_invocation import get_invocation_status
from features.skill_remove import get_agent_skills
from features.skill_set import (
    LLM_TARGETS,
    get_skill_invocation_state,
    has_direct_skill_file,
    list_skill_folders,
    parse_filter_arg,
)

AGENTS_ORDER = [
    ("agy", "Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
    ("claude", "Claude Code", CLAUDE_SKILLS_PATH),
    ("codex", "OpenAI Codex", CODEX_SKILLS_PATH),
]

COPY_IGNORE_PATTERNS = shutil.ignore_patterns(
    ".git", ".github", ".vscode", ".idea", "node_modules", ".venv", "venv", "__pycache__", "*.pyc", "dist", "build"
)


def get_category_folders(base_path: str) -> list[str]:
    """
    Lọc các thư mục con trực tiếp cấp 1 trong kho skills có hậu tố '-skill'.
    Loại trừ thư mục ẩn và thư mục bản thân nó đã là 1 skill (chứa SKILL.md trực tiếp).
    """
    root = Path(base_path)
    if not root.is_dir():
        return []

    categories = [
        item.name
        for item in root.iterdir()
        if item.is_dir()
        and not item.name.startswith(".")
        and item.name.lower().endswith("-skill")
        and not has_direct_skill_file(str(item))
    ]
    return sorted(categories, key=str.lower)


def resolve_to_folder(raw_val: str, categories: list[str]) -> str | None:
    """
    Khớp giá trị --to-folder theo tên đầy đủ (vd: 'outside-skill') hoặc gõ tắt bỏ hậu tố (vd: 'outside').
    """
    clean = raw_val.strip().strip("/\\").lower()
    if not clean:
        return None

    for cat in categories:
        if cat.lower() == clean:
            return cat

    if not clean.endswith("-skill"):
        with_suffix = f"{clean}-skill"
        for cat in categories:
            if cat.lower() == with_suffix:
                return cat

    return None


def get_valid_agent_skills(agent_path: str) -> list[str]:
    """Trả về danh sách tên skill hợp lệ (có SKILL.md trực tiếp) trong thư mục Agent."""
    return [
        name
        for name in get_agent_skills(agent_path)
        if has_direct_skill_file(os.path.join(agent_path, name))
    ]


def find_skill_in_agent(agent_path: str, target_name: str) -> str | None:
    """Tìm tên thư mục skill khớp (case-insensitive) trong thư mục của một Agent."""
    clean = target_name.strip().lower()
    for s in get_valid_agent_skills(agent_path):
        if s.lower() == clean:
            return s
    return None


def prompt_select_single(title: str, options: list[str]) -> int:
    """Hiển thị menu đánh số đơn và trả về chỉ số 0-based người dùng chọn."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{title}{Style.RESET_ALL}")
    for idx, label in enumerate(options, 1):
        print(f"  {Fore.GREEN}[{idx}]{Style.RESET_ALL} {label}")

    while True:
        raw = input(f"\nChọn số thứ tự (1-{len(options)}, hoặc Enter để hủy): ").strip()
        if not raw:
            print(">>> Đã hủy thao tác.")
            sys.exit(0)
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"{Fore.RED}⚠️ Lựa chọn không hợp lệ. Vui lòng nhập số từ 1 đến {len(options)}.{Style.RESET_ALL}")


def build_repo_skill_index(base_path: str) -> dict[str, list[str]]:
    """Lập chỉ mục tên skill (lowercase) -> danh sách đường dẫn tương đối đang có trong kho chung."""
    index: dict[str, list[str]] = {}
    for rel in list_skill_folders(base_path):
        index.setdefault(os.path.basename(rel).lower(), []).append(rel)
    return index


def prompt_select_skills_like_on_invo(
    agent_label: str,
    agent_dir: str,
    skills: list[str],
    repo_index: dict[str, list[str]],
    keyword_choice: str | None,
    filter_choice: str | None,
) -> list[str]:
    """
    Liệt kê danh sách skill theo giao diện giống 'mod skill on-invo' và cho phép chọn 1, nhiều (1 2 4) hoặc tất cả ('a').
    """
    tags = []
    if keyword_choice:
        tags.append(f"--key '{keyword_choice}'")
    if filter_choice:
        tags.append(f"--filter {filter_choice}")
    filter_tag = f" {Fore.CYAN}[Đã lọc: {', '.join(tags)}]{Style.RESET_ALL}" if tags else ""

    print(f"\n{Fore.MAGENTA}=== IMPORT SKILL TỪ AI AGENT{filter_tag} ==={Style.RESET_ALL}")
    print(f">>> Đang quét danh sách Skill trong {Fore.MAGENTA}{agent_label}{Style.RESET_ALL} ({len(skills)} skills):\n")

    for idx, s in enumerate(skills, 1):
        full_p = os.path.join(agent_dir, s)
        stts = get_invocation_status(full_p)
        existing_rels = repo_index.get(s.lower(), [])
        repo_badge = ""
        if existing_rels:
            cats = ", ".join(os.path.dirname(r) or r for r in existing_rels)
            repo_badge = f" {Fore.LIGHTBLACK_EX}(Đã có: {cats}){Style.RESET_ALL}"
        print(f"  [{idx:2d}] {s:<42} {stts}{repo_badge}")
    print(f"  [ a] Áp dụng cho TẤT CẢ các Skill trên ({len(skills)} skills)\n")

    user_choice = input("Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' ('q' để hủy): ").strip()
    if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
        print(">>> Đã hủy thao tác an toàn.")
        sys.exit(0)

    if user_choice.lower() in ("a", "all", "*"):
        if len(skills) > 1:
            confirm_all = input(f"{Fore.YELLOW}⚠️ Bạn chuẩn bị chọn toàn bộ {len(skills)} skills từ {agent_label}. Tiếp tục? [y/n]: {Style.RESET_ALL}").strip().lower()
            if confirm_all != "y":
                print(">>> Đã hủy thao tác an toàn.")
                sys.exit(0)
        return skills

    num_tokens = re.findall(r"\d+", user_choice)
    if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
        chosen = [skills[int(n) - 1] for n in num_tokens if 1 <= int(n) <= len(skills)]
        # Giữ nguyên thứ tự chọn và loại bỏ số lặp lại
        chosen = list(dict.fromkeys(chosen))
    else:
        matched = [s for s in skills if s.lower() == user_choice.lower()]
        chosen = matched if matched else []

    if not chosen:
        print(f"{Fore.RED}❌ Lỗi: Không có Skill nào hợp lệ được chọn.{Style.RESET_ALL}")
        sys.exit(1)

    return chosen


def resolve_source_agent_and_skills(
    from_ai: str | None,
    skill_arg: str | None,
    keyword_choice: str | None,
    filter_choice: str | None,
    repo_index: dict[str, list[str]],
) -> tuple[str, str, list[str]]:
    """
    Xác định (agent_label, agent_skills_dir, [danh sách skill_name]).
    Ràng buộc điều kiện: nếu thiếu skill_arg thì BẮT BUỘC phải có from_ai.
    """
    if not skill_arg and not from_ai:
        print(f"{Fore.RED}❌ Lỗi: Phải truyền <skill_name> hoặc chỉ định cờ '--from-ai <agy|claude|codex>'.{Style.RESET_ALL}")
        print("💡 Khi bỏ trống <skill_name>, cần truyền --from-ai để quét và liệt kê skill trong AI Agent đó.")
        print("   Ví dụ: mod skill import diagram-design --to-folder outside")
        print("          mod skill import --from-ai agy --to-folder outside")
        sys.exit(1)

    if from_ai:
        if from_ai == "all" or from_ai not in LLM_TARGETS:
            print(f"{Fore.RED}❌ Lỗi: Giá trị --from-ai '{from_ai}' không hợp lệ.{Style.RESET_ALL}")
            print("Các giá trị hợp lệ (chọn 1 nguồn): agy (antigravity), claude, codex")
            sys.exit(1)
        agent_label, agent_dir = LLM_TARGETS[from_ai]
        if not os.path.isdir(agent_dir):
            print(f"{Fore.RED}❌ Lỗi: Thư mục skill của {agent_label} không tồn tại: {agent_dir}{Style.RESET_ALL}")
            sys.exit(1)

        if skill_arg:
            matched = find_skill_in_agent(agent_dir, skill_arg)
            if not matched:
                print(f"{Fore.RED}❌ Không tìm thấy skill '{skill_arg}' hợp lệ trong {agent_label} ({agent_dir}).{Style.RESET_ALL}")
                sys.exit(1)
            if keyword_choice and keyword_choice.lower() not in matched.lower():
                print(f"{Fore.YELLOW}⚠️ Bỏ qua Skill '{matched}' vì không khớp với từ khóa (--key {keyword_choice}).{Style.RESET_ALL}")
                sys.exit(0)
            if filter_choice and get_skill_invocation_state(os.path.join(agent_dir, matched)) != filter_choice:
                print(f"{Fore.YELLOW}⚠️ Bỏ qua Skill '{matched}' vì trạng thái invocation không khớp bộ lọc (--filter {filter_choice}).{Style.RESET_ALL}")
                sys.exit(0)
            return agent_label, agent_dir, [matched]

        skills = get_valid_agent_skills(agent_dir)
        if not skills:
            print(f"{Fore.YELLOW}⚠️ Chưa có Skill nào hợp lệ được cài đặt trong {agent_label} ({agent_dir}).{Style.RESET_ALL}")
            sys.exit(0)

        if keyword_choice:
            skills = [s for s in skills if keyword_choice.lower() in s.lower()]
        if filter_choice:
            skills = [s for s in skills if get_skill_invocation_state(os.path.join(agent_dir, s)) == filter_choice]
        if not skills:
            print(f"{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong {agent_label} khớp với bộ lọc.{Style.RESET_ALL}")
            sys.exit(0)

        chosen = prompt_select_skills_like_on_invo(
            agent_label, agent_dir, skills, repo_index, keyword_choice, filter_choice
        )
        return agent_label, agent_dir, chosen

    # Có skill_arg nhưng không có --from-ai: tự quét cả 3 Agent
    matches: list[tuple[str, str, str]] = []
    for _, label, agent_dir in AGENTS_ORDER:
        matched = find_skill_in_agent(agent_dir, skill_arg)
        if matched:
            matches.append((label, agent_dir, matched))

    if not matches:
        print(f"{Fore.RED}❌ Không tìm thấy skill '{skill_arg}' trong Antigravity, Claude Code hay Codex.{Style.RESET_ALL}")
        sys.exit(1)

    if len(matches) == 1:
        agent_label, agent_dir, matched = matches[0]
    else:
        options = [f"{lbl} ({p})" for lbl, p, _ in matches]
        idx = prompt_select_single(
            f"🔍 Skill '{skill_arg}' có mặt ở nhiều AI Agent. Chọn nguồn import:",
            options,
        )
        agent_label, agent_dir, matched = matches[idx]

    if keyword_choice and keyword_choice.lower() not in matched.lower():
        print(f"{Fore.YELLOW}⚠️ Bỏ qua Skill '{matched}' vì không khớp với từ khóa (--key {keyword_choice}).{Style.RESET_ALL}")
        sys.exit(0)
    if filter_choice and get_skill_invocation_state(os.path.join(agent_dir, matched)) != filter_choice:
        print(f"{Fore.YELLOW}⚠️ Bỏ qua Skill '{matched}' vì trạng thái invocation không khớp bộ lọc (--filter {filter_choice}).{Style.RESET_ALL}")
        sys.exit(0)

    return agent_label, agent_dir, [matched]


def parse_args(argv: list[str]) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """Parse [skill_name], [--from-ai <agent>], [--to-folder <folder>], [--key, -k <kw>], [--filter, -f <on|off>]."""
    from_ai = None
    to_folder = None
    keyword_choice = None
    filter_choice = None
    positional: list[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--from-ai", "--from", "--ai", "--llm", "--agent"):
            if i + 1 < len(argv):
                from_ai = argv[i + 1].strip().lower()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên AI Agent sau cờ {arg}. (Ví dụ: {arg} agy){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--from-ai=", "--from=", "--ai=", "--llm=", "--agent=")):
            from_ai = arg.split("=", 1)[1].strip().lower()
            i += 1
        elif arg in ("--to-folder", "--to", "--folder"):
            if i + 1 < len(argv):
                to_folder = argv[i + 1].strip()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên thư mục đích sau cờ {arg}. (Ví dụ: {arg} outside-skill hoặc {arg} outside){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--to-folder=", "--to=", "--folder=")):
            to_folder = arg.split("=", 1)[1].strip()
            i += 1
        elif arg in ("--keyword", "--key", "-k"):
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                keyword_choice = argv[i + 1].strip()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu từ khóa sau cờ {arg}. (Ví dụ: --key diagram){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--keyword=", "--key=", "-k=")):
            keyword_choice = arg.split("=", 1)[1].strip()
            if not keyword_choice:
                print(f"{Fore.RED}❌ Lỗi: Từ khóa không được để trống.{Style.RESET_ALL}")
                sys.exit(1)
            i += 1
        elif arg in ("--filter", "-f"):
            if i + 1 < len(argv):
                raw_filter = argv[i + 1]
                filter_choice = parse_filter_arg(raw_filter)
                if not filter_choice:
                    print(f"{Fore.RED}❌ Lỗi: Giá trị filter '{raw_filter}' không hợp lệ. Chỉ chấp nhận 'on-invocation' (hoặc 'on') và 'off-invocation' (hoặc 'off').{Style.RESET_ALL}")
                    sys.exit(1)
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu giá trị sau cờ {arg}. (Ví dụ: --filter on-invocation hoặc --filter off-invocation){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--filter=", "-f=")):
            raw_filter = arg.split("=", 1)[1]
            filter_choice = parse_filter_arg(raw_filter)
            if not filter_choice:
                print(f"{Fore.RED}❌ Lỗi: Giá trị filter '{raw_filter}' không hợp lệ. Chỉ chấp nhận 'on-invocation' (hoặc 'on') và 'off-invocation' (hoặc 'off').{Style.RESET_ALL}")
                sys.exit(1)
            i += 1
        elif arg.startswith("-"):
            print(f"{Fore.RED}❌ Lỗi: Cờ không hợp lệ '{arg}'.{Style.RESET_ALL}")
            print("💡 Cú pháp: mod skill import [skill_name] [--from-ai agy|claude|codex] [--to-folder <folder>] [-k <key>] [-f <on|off>]")
            sys.exit(1)
        else:
            positional.append(arg)
            i += 1

    skill_arg = positional[0] if positional else None
    return skill_arg, from_ai, to_folder, keyword_choice, filter_choice


def import_single_skill(
    agent_label: str,
    src_path: str,
    dest_path: str,
    target_category: str,
    skill_dirname: str,
    existing_in_repo: list[str],
    overwrite_all: bool,
) -> tuple[str, bool]:
    """Thực hiện copy 1 skill vào kho chung kèm xử lý trùng lặp. Trả về ('ok'|'skipped'|'error', overwrite_all)."""
    target_rel = f"{target_category}/{skill_dirname}"

    if os.path.exists(dest_path):
        if not overwrite_all:
            print(f"\n{Fore.YELLOW}⚠️ Skill '{skill_dirname}' đã tồn tại tại đích:{Style.RESET_ALL} {dest_path}")
            ans = input("Bạn có muốn ghi đè không? [y/n/a (tất cả)]: ").strip().lower()
            if ans == "a":
                overwrite_all = True
            elif ans != "y":
                print(f">>> Bỏ qua '{skill_dirname}'.")
                return "skipped", overwrite_all
        try:
            shutil.rmtree(dest_path)
        except Exception as e:
            print(f"{Fore.RED}❌ Lỗi khi xóa thư mục cũ của '{skill_dirname}':{Style.RESET_ALL} {e}")
            return "error", overwrite_all
    elif existing_in_repo:
        others = [r for r in existing_in_repo if r.lower() != target_rel.lower()]
        if others:
            print(f"\n{Fore.YELLOW}⚠️ Cảnh báo trùng lặp: Skill '{skill_dirname}' đã có trong kho tại:{Style.RESET_ALL} {', '.join(others)}")
            ans = input(f"Bạn vẫn muốn copy thêm vào '{target_category}/' không? [y/n]: ").strip().lower()
            if ans != "y":
                print(f">>> Bỏ qua '{skill_dirname}' để tránh trùng lặp trong kho.")
                return "skipped", overwrite_all

    print(f"\n>>> Đang import Skill '{skill_dirname}' từ {agent_label}...")
    print(f"    Nguồn: {src_path}")
    print(f"    Đích : {dest_path}")

    try:
        shutil.copytree(src_path, dest_path, ignore=COPY_IGNORE_PATTERNS)
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi khi copy '{skill_dirname}' vào kho chung:{Style.RESET_ALL} {e}")
        return "error", overwrite_all

    invo_state = get_skill_invocation_state(dest_path)
    invo_lbl = "TẮT (off-invocation)" if invo_state == "off-invocation" else "BẬT (on-invocation)"
    print(f"{Fore.GREEN}✅ Import thành công '{skill_dirname}' vào '{target_category}/'!{Style.RESET_ALL} ({invo_lbl})")
    return "ok", overwrite_all


def main() -> None:
    if not sys.argv[1:] or sys.argv[1].lower() != "import":
        print(f"{Fore.RED}❌ Lỗi: Action không hợp lệ cho skill_import.py.{Style.RESET_ALL}")
        sys.exit(1)

    if not os.path.isdir(SKILLS_FOLDER_PATH):
        print(f"{Fore.RED}❌ Lỗi: Kho lưu trữ AI Skills không tồn tại: {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
        sys.exit(1)

    categories = get_category_folders(SKILLS_FOLDER_PATH)
    if not categories:
        print(f"{Fore.RED}❌ Lỗi: Không tìm thấy thư mục con nào có hậu tố '-skill' trong {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
        sys.exit(1)

    skill_arg, from_ai, raw_to_folder, keyword_choice, filter_choice = parse_args(sys.argv[2:])

    # Fail-fast nếu --to-folder truyền sai
    target_category = None
    if raw_to_folder is not None:
        target_category = resolve_to_folder(raw_to_folder, categories)
        if not target_category:
            valid_hint = ", ".join(f"{c} (hoặc '{c[:-6]}')" for c in categories)
            print(f"{Fore.RED}❌ Lỗi: Thư mục đích '{raw_to_folder}' không hợp lệ.{Style.RESET_ALL}")
            print(f"💡 Các thư mục đích hợp lệ trong {SKILLS_FOLDER_PATH}: {valid_hint}")
            sys.exit(1)

    repo_index = build_repo_skill_index(SKILLS_FOLDER_PATH)

    # 1. Xác định Agent nguồn & danh sách Skill cần import
    agent_label, agent_dir, selected_skills = resolve_source_agent_and_skills(
        from_ai, skill_arg, keyword_choice, filter_choice, repo_index
    )

    # 2. Nếu chưa truyền --to-folder, hỏi chọn 1 lần cho toàn bộ đợt import
    if target_category is None:
        options = [f"{c} {Fore.LIGHTBLACK_EX}(gõ tắt: {c[:-6]}){Style.RESET_ALL}" for c in categories]
        idx = prompt_select_single("📁 Chọn thư mục phân loại đích trong kho SKILLs:", options)
        target_category = categories[idx]

    # 3. Thực hiện copy từng skill
    imported_names: list[str] = []
    skipped_count = 0
    error_count = 0
    overwrite_all = False

    for skill_dirname in selected_skills:
        src_path = os.path.join(agent_dir, skill_dirname)
        dest_path = os.path.join(SKILLS_FOLDER_PATH, target_category, skill_dirname)
        existing_in_repo = repo_index.get(skill_dirname.lower(), [])

        status, overwrite_all = import_single_skill(
            agent_label,
            src_path,
            dest_path,
            target_category,
            skill_dirname,
            existing_in_repo,
            overwrite_all,
        )
        if status == "ok":
            imported_names.append(skill_dirname)
        elif status == "skipped":
            skipped_count += 1
        else:
            error_count += 1

    print()
    if len(selected_skills) > 1 or skipped_count > 0 or error_count > 0:
        print(
            f"{Fore.CYAN}📊 Tổng kết import: {Fore.GREEN}{len(imported_names)} thành công{Style.RESET_ALL} │ "
            f"{Fore.YELLOW}{skipped_count} bỏ qua{Style.RESET_ALL} │ {Fore.RED}{error_count} lỗi{Style.RESET_ALL}"
        )

    if imported_names:
        sample_msg = f"feat: add {imported_names[0]} skill" if len(imported_names) == 1 else f"feat: import {len(imported_names)} skills into {target_category}"
        print(f"{Fore.LIGHTBLACK_EX}💡 Gợi ý tiếp theo: Chạy `mod skill git-commit -m \"{sample_msg}\"` để đẩy lên kho Git SKILLs.{Style.RESET_ALL}\n")

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
