#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
skill_remove.py - Xóa thư mục Skill:
- mod skill remove [skill_name]                            : Xóa khỏi kho lưu trữ trung tâm (với xác nhận an toàn).
- mod skill remove [skill_name] --agent <name|all>         : CHỈ xóa khỏi AI Agent chỉ định (không chạm kho gốc).
- mod skill remove [skill_name] --include-agent <name|all> : Xóa CẢ HAI (kho lưu trữ trung tâm VÀ AI Agent).
- Cờ lọc: --filter, -f <on-invocation|off-invocation>      : Chỉ xóa/hiển thị Skill đang BẬT hoặc TẮT tự động gọi.
- Alias: 'mod skill rm' tương đương 'mod skill remove'.
"""

import os
import re
import sys
import shutil
from pathlib import Path
from colorama import init, Fore, Style

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

init(autoreset=True)

# Thêm project root vào sys.path để import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import (
    SKILLS_FOLDER_PATH,
    ANTIGRAVITY_SKILLS_PATH,
    CODEX_SKILLS_PATH,
    CLAUDE_SKILLS_PATH,
)
from features.skill_set import (
    list_skill_folders,
    find_skill_folder,
    get_skill_invocation_state,
    parse_filter_arg,
)

# Mapping các alias của AI Agent / LLM sang tên hiển thị và đường dẫn Global Skills
LLM_TARGETS = {
    "agy": ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
    "anti": ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
    "antigravity": ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
    "gemini": ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
    "codex": ("OpenAI Codex", CODEX_SKILLS_PATH),
    "openai": ("OpenAI Codex", CODEX_SKILLS_PATH),
    "claude": ("Claude Code", CLAUDE_SKILLS_PATH),
    "clau": ("Claude Code", CLAUDE_SKILLS_PATH),
    "anthropic": ("Claude Code", CLAUDE_SKILLS_PATH),
}

ALL_AGENTS = [
    ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
    ("OpenAI Codex", CODEX_SKILLS_PATH),
    ("Claude Code", CLAUDE_SKILLS_PATH),
]


def get_agent_skills(agent_path: str) -> list[str]:
    """Quét danh sách các thư mục skill trong thư mục của Agent."""
    p = Path(agent_path)
    if not p.exists() or not p.is_dir():
        return []
    try:
        skills = [
            item.name
            for item in p.iterdir()
            if item.is_dir() and not item.name.startswith(".") and item.name != ".git"
        ]
        return sorted(skills, key=lambda s: s.lower())
    except Exception:
        return []


def is_safe_to_delete(path_to_delete: str, base_root: str) -> bool:
    """Đảm bảo thư mục cần xóa là thư mục con hợp lệ của base_root, không phải root hay .git."""
    try:
        abs_target = os.path.abspath(path_to_delete)
        abs_base = os.path.abspath(base_root)
        if abs_target == abs_base:
            return False
        rel = os.path.relpath(abs_target, abs_base)
        if rel.startswith(".."):
            return False
        parts = [p.lower() for p in rel.replace("\\", "/").split("/") if p]
        ignore_dirs = {".git", ".github", ".vscode", ".idea", "node_modules", ".venv", "venv", "__pycache__"}
        if any(p in ignore_dirs for p in parts):
            return False
        return True
    except Exception:
        return False


def handle_remove_for_single_agent(
    agent_label: str,
    agent_path: str,
    preselected_skill: str | None = None,
    filter_choice: str | None = None,
):
    """Xử lý xóa skill cho một AI Agent cụ thể (CHỈ tác động lên Agent đó)."""
    skills = get_agent_skills(agent_path)
    if not skills:
        print(f"\n{Fore.YELLOW}>>> Không có Skill nào được cài đặt trong {agent_label} ({agent_path}).{Style.RESET_ALL}")
        sys.exit(0)

    if filter_choice:
        skills = [s for s in skills if get_skill_invocation_state(os.path.join(agent_path, s)) == filter_choice]
        if not skills:
            lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
            print(f"\n{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong {agent_label} khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
            sys.exit(0)

    chosen_skills = []

    if preselected_skill:
        for s in skills:
            if s.lower() == preselected_skill.lower():
                chosen_skills.append(s)
                break
        if not chosen_skills:
            if filter_choice:
                all_agent_skills = get_agent_skills(agent_path)
                for s in all_agent_skills:
                    if s.lower() == preselected_skill.lower():
                        st = get_skill_invocation_state(os.path.join(agent_path, s))
                        lbl_cur = "TẮT" if st == "off-invocation" else "BẬT"
                        lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                        print(f"\n{Fore.YELLOW}⚠️ Bỏ qua Skill '{preselected_skill}' vì trạng thái hiện tại trong {agent_label} ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                        sys.exit(0)
            print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{preselected_skill}' trong {agent_label}.{Style.RESET_ALL}")
            print(f">>> Danh sách các Skill hiện có tại {agent_path}:")
            for idx, s in enumerate(skills, 1):
                print(f"  [{idx}] {s}")
            sys.exit(1)
    else:
        filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
        print(f"\n>>> Đang quét thư mục Skills của {Style.BRIGHT}{agent_label}{Style.RESET_ALL} ({agent_path}){filter_tag}...")
        print("\nDanh sách các Skill hiện có:")
        for idx, s in enumerate(skills, 1):
            print(f"  [{idx}] {s}")
        if len(skills) > 1:
            print(f"  [a] Xóa TẤT CẢ các Skill trên ({len(skills)} skills)")
        print()

        prompt_msg = "Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' để xóa tất cả ('q' để hủy): "
        user_choice = input(prompt_msg).strip()

        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Hủy thao tác an toàn.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            chosen_skills = list(skills)
        else:
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                chosen_indices = [int(n) for n in num_tokens]
                for idx in chosen_indices:
                    if 1 <= idx <= len(skills):
                        skill_candidate = skills[idx - 1]
                        if skill_candidate not in chosen_skills:
                            chosen_skills.append(skill_candidate)
                    else:
                        print(f"{Fore.YELLOW}⚠️ Bỏ qua số thứ tự ngoài phạm vi: {idx}{Style.RESET_ALL}")
                if not chosen_skills:
                    print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                matched_skill = None
                for s in skills:
                    if s.lower() == user_choice.lower():
                        matched_skill = s
                        break
                if not matched_skill:
                    print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{user_choice}' trong {agent_label}.{Style.RESET_ALL}")
                    sys.exit(1)
                chosen_skills.append(matched_skill)

    if len(chosen_skills) == 1:
        skill_name = chosen_skills[0]
        skill_dir = os.path.join(agent_path, skill_name)
        print(f"\n{Fore.YELLOW}⚠️ Bạn có chắc chắn muốn xóa Skill '{skill_name}' khỏi {agent_label}?{Style.RESET_ALL}")
        print(f"   Đường dẫn: {skill_dir}")
        ans = input("Nhập 'y' để xác nhận xóa (hoặc phím khác để hủy): ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)

        try:
            if not is_safe_to_delete(skill_dir, agent_path):
                print(f"{Fore.RED}❌ Lỗi: Đường dẫn không an toàn hoặc là thư mục cấm xóa (.git/root): {skill_dir}{Style.RESET_ALL}")
                sys.exit(1)
            if os.path.exists(skill_dir):
                shutil.rmtree(skill_dir)
                print(f"{Fore.GREEN}✅ Đã xóa thành công Skill '{skill_name}' khỏi {agent_label}!{Style.RESET_ALL}")
                print(f"{Fore.CYAN}ℹ️ Kho lưu trữ trung tâm không bị thay đổi.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ Thư mục không tồn tại: {skill_dir}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Lỗi khi xóa Skill:{Style.RESET_ALL} {e}")
            sys.exit(1)
    else:
        print(f"\n{Fore.YELLOW}⚠️ Bạn có chắc chắn muốn xóa {len(chosen_skills)} Skill sau khỏi {agent_label}?{Style.RESET_ALL}")
        for s in chosen_skills:
            print(f"   - {s}")
        ans = input(f"\nNhập 'y' để xác nhận xóa toàn bộ {len(chosen_skills)} Skill trên (hoặc phím khác để hủy): ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)

        print()
        deleted_count = 0
        for s in chosen_skills:
            skill_dir = os.path.join(agent_path, s)
            try:
                if not is_safe_to_delete(skill_dir, agent_path):
                    print(f"{Fore.RED}❌ Bỏ qua vì đường dẫn không an toàn (.git/root): {skill_dir}{Style.RESET_ALL}")
                    continue
                if os.path.exists(skill_dir):
                    shutil.rmtree(skill_dir)
                    print(f"{Fore.GREEN}✅ Đã xóa '{s}' khỏi {agent_label}!{Style.RESET_ALL}")
                    deleted_count += 1
                else:
                    print(f"{Fore.YELLOW}⚠️ Thư mục không tồn tại: {skill_dir}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi khi xóa '{s}':{Style.RESET_ALL} {e}")

        print(f"\n{Fore.GREEN}🎉 Hoàn tất! Đã xóa thành công {deleted_count}/{len(chosen_skills)} Skill khỏi {agent_label}.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}ℹ️ Kho lưu trữ trung tâm không bị thay đổi.{Style.RESET_ALL}")


def handle_remove_for_all_agents(preselected_skill: str | None = None, filter_choice: str | None = None):
    """Xử lý rà soát và xóa các skill trên cả 3 AI Agent (CHỈ tác động lên Agent)."""
    filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
    print(f"\n>>> Đang rà soát Skill trên cả 3 AI Agent (Antigravity, Codex, Claude Code){filter_tag}...")

    agent_skills_map = {}
    for label, path in ALL_AGENTS:
        agent_skills_map[label] = {
            "path": path,
            "skills": set(get_agent_skills(path)),
        }

    all_skill_names = set()
    for data in agent_skills_map.values():
        all_skill_names.update(data["skills"])

    skill_occurrences = []
    for skill_name in sorted(all_skill_names, key=lambda s: s.lower()):
        present_agents = [
            (label, data["path"])
            for label, data in agent_skills_map.items()
            if skill_name in data["skills"]
        ]
        if len(present_agents) >= 2:
            skill_occurrences.append({
                "name": skill_name,
                "agents": present_agents,
            })

    if not skill_occurrences:
        print(f"\n{Fore.GREEN}✅ Không có Skill chung nào giữa các AI Agent (không có skill nào xuất hiện từ 2 agent trở lên).{Style.RESET_ALL}")
        sys.exit(0)

    if filter_choice:
        filtered_occurrences = []
        for item in skill_occurrences:
            first_path = item["agents"][0][1]
            st = get_skill_invocation_state(os.path.join(first_path, item["name"]))
            if st == filter_choice:
                filtered_occurrences.append(item)
        skill_occurrences = filtered_occurrences

        if not skill_occurrences:
            lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
            print(f"\n{Fore.YELLOW}ℹ️ Không có Skill chung nào giữa các AI Agent khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
            sys.exit(0)

    chosen_items = []

    if preselected_skill:
        for item in skill_occurrences:
            if item["name"].lower() == preselected_skill.lower():
                chosen_items.append(item)
                break
        if not chosen_items:
            if filter_choice:
                for label, path in ALL_AGENTS:
                    cand_path = os.path.join(path, preselected_skill)
                    if os.path.exists(cand_path):
                        st = get_skill_invocation_state(cand_path)
                        if st != filter_choice:
                            lbl_cur = "TẮT" if st == "off-invocation" else "BẬT"
                            lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                            print(f"\n{Fore.YELLOW}⚠️ Bỏ qua Skill '{preselected_skill}' vì trạng thái hiện tại ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                            sys.exit(0)
            print(f"{Fore.RED}❌ Lỗi: Skill '{preselected_skill}' không nằm trong danh sách Skill chung giữa các Agent.{Style.RESET_ALL}")
            print(f">>> Danh sách các Skill chung hiện có:")
            for idx, item in enumerate(skill_occurrences, 1):
                agent_labels = ", ".join([lbl for lbl, _ in item["agents"]])
                print(f"  [{idx}] {item['name']:<35} [{agent_labels}]")
            sys.exit(1)
    else:
        print(f"\nDanh sách các Skill chung giữa các AI Agent ({len(skill_occurrences)} skills):")
        for idx, item in enumerate(skill_occurrences, 1):
            if len(item["agents"]) == 3:
                agent_info = f"{Fore.CYAN}[Cả 3 Agent: Antigravity, Codex, Claude Code]{Style.RESET_ALL}"
            else:
                agent_labels = ", ".join([lbl for lbl, _ in item["agents"]])
                agent_info = f"{Fore.YELLOW}[{len(item['agents'])} Agent: {agent_labels}]{Style.RESET_ALL}"
            print(f"  [{idx}] {item['name']:<35} {agent_info}")
        if len(skill_occurrences) > 1:
            print(f"  [a] Xóa TẤT CẢ các Skill chung trên ({len(skill_occurrences)} skills)")
        print()

        prompt_msg = "Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' để xóa tất cả ('q' để hủy): "
        user_choice = input(prompt_msg).strip()

        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Hủy thao tác an toàn.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            chosen_items = list(skill_occurrences)
        else:
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                chosen_indices = [int(n) for n in num_tokens]
                for idx in chosen_indices:
                    if 1 <= idx <= len(skill_occurrences):
                        candidate_item = skill_occurrences[idx - 1]
                        if candidate_item not in chosen_items:
                            chosen_items.append(candidate_item)
                    else:
                        print(f"{Fore.YELLOW}⚠️ Bỏ qua số thứ tự ngoài phạm vi: {idx}{Style.RESET_ALL}")
                if not chosen_items:
                    print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                matched_item = None
                for item in skill_occurrences:
                    if item["name"].lower() == user_choice.lower():
                        matched_item = item
                        break
                if not matched_item:
                    print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{user_choice}' trong danh sách Skill chung.{Style.RESET_ALL}")
                    sys.exit(1)
                chosen_items.append(matched_item)

    if len(chosen_items) == 1:
        chosen_item = chosen_items[0]
        target_agents = chosen_item["agents"]
        agent_names = ", ".join([lbl for lbl, _ in target_agents])
        print(f"\n{Fore.YELLOW}⚠️ Bạn có chắc chắn muốn xóa Skill '{chosen_item['name']}' khỏi {len(target_agents)} AI Agent ({agent_names})?{Style.RESET_ALL}")
        print("Các thư mục sẽ bị xóa:")
        for lbl, p in target_agents:
            print(f"  - [{lbl}] {os.path.join(p, chosen_item['name'])}")

        ans = input("\nNhập 'y' để xác nhận xóa (hoặc phím khác để hủy): ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)

        print()
        deleted_count = 0
        for lbl, p in target_agents:
            skill_dir = os.path.join(p, chosen_item["name"])
            try:
                if not is_safe_to_delete(skill_dir, p):
                    print(f"{Fore.RED}❌ Bỏ qua vì đường dẫn không an toàn (.git/root): {skill_dir}{Style.RESET_ALL}")
                    continue
                if os.path.exists(skill_dir):
                    shutil.rmtree(skill_dir)
                    print(f"{Fore.GREEN}✅ Đã xóa '{chosen_item['name']}' khỏi {lbl}!{Style.RESET_ALL}")
                    deleted_count += 1
                else:
                    print(f"{Fore.YELLOW}⚠️ Thư mục không tồn tại: {skill_dir}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi khi xóa khỏi {lbl}:{Style.RESET_ALL} {e}")

        print(f"\n{Fore.GREEN}🎉 Hoàn tất! Đã xóa thành công Skill '{chosen_item['name']}' khỏi {deleted_count}/{len(target_agents)} AI Agent.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}ℹ️ Kho lưu trữ trung tâm không bị thay đổi.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠️ Bạn có chắc chắn muốn xóa {len(chosen_items)} Skill sau khỏi các AI Agent tương ứng?{Style.RESET_ALL}")
        for item in chosen_items:
            agent_names = ", ".join([lbl for lbl, _ in item["agents"]])
            print(f"   - {Style.BRIGHT}{item['name']}{Style.RESET_ALL} (ở {len(item['agents'])} agent: {agent_names})")

        ans = input(f"\nNhập 'y' để xác nhận xóa toàn bộ {len(chosen_items)} Skill trên (hoặc phím khác để hủy): ").strip().lower()
        if ans != "y":
            print(">>> Hủy thao tác.")
            sys.exit(0)

        print()
        total_deletions = 0
        for item in chosen_items:
            for lbl, p in item["agents"]:
                skill_dir = os.path.join(p, item["name"])
                try:
                    if not is_safe_to_delete(skill_dir, p):
                        print(f"{Fore.RED}❌ Bỏ qua vì đường dẫn không an toàn (.git/root): {skill_dir}{Style.RESET_ALL}")
                        continue
                    if os.path.exists(skill_dir):
                        shutil.rmtree(skill_dir)
                        print(f"{Fore.GREEN}✅ Đã xóa '{item['name']}' khỏi {lbl}!{Style.RESET_ALL}")
                        total_deletions += 1
                    else:
                        print(f"{Fore.YELLOW}⚠️ Thư mục không tồn tại: {skill_dir}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}❌ Lỗi khi xóa '{item['name']}' khỏi {lbl}:{Style.RESET_ALL} {e}")

        print(f"\n{Fore.GREEN}🎉 Hoàn tất! Đã xóa thành công {len(chosen_items)} Skill ({total_deletions} lượt xóa trên các agent).{Style.RESET_ALL}")
        print(f"{Fore.CYAN}ℹ️ Kho lưu trữ trung tâm không bị thay đổi.{Style.RESET_ALL}")


def handle_remove_for_central_repo(preselected_skill: str | None = None, filter_choice: str | None = None):
    """
    Xóa Skill khỏi kho lưu trữ trung tâm SKILLS_FOLDER_PATH (Mode Repo-Only).
    Yêu cầu bước xác nhận an toàn tuyệt đối trước khi xóa vĩnh viễn.
    """
    if not os.path.exists(SKILLS_FOLDER_PATH):
        print(f"{Fore.RED}❌ Lỗi: Thư mục kho lưu trữ SKILLs không tồn tại: {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
        sys.exit(1)

    available_skills = list_skill_folders(SKILLS_FOLDER_PATH)
    if not available_skills:
        print(f"{Fore.YELLOW}⚠️ Kho lưu trữ rỗng: Chưa có skill nào trong {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
        sys.exit(0)

    if filter_choice:
        available_skills = [s for s in available_skills if get_skill_invocation_state(os.path.join(SKILLS_FOLDER_PATH, s)) == filter_choice]
        if not available_skills:
            lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
            print(f"\n{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong kho khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
            sys.exit(0)

    chosen_paths = []

    if preselected_skill:
        found = find_skill_folder(SKILLS_FOLDER_PATH, preselected_skill)
        if not found:
            print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{preselected_skill}' trong kho lưu trữ {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
            print(f">>> Danh sách các Skill hiện có trong kho:")
            for idx, s in enumerate(available_skills, 1):
                print(f"  [{idx}] {s}")
            sys.exit(1)
        if filter_choice:
            st = get_skill_invocation_state(found)
            if st != filter_choice:
                lbl_cur = "TẮT" if st == "off-invocation" else "BẬT"
                lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                print(f"\n{Fore.YELLOW}⚠️ Bỏ qua Skill '{preselected_skill}' vì trạng thái hiện tại trong kho ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                sys.exit(0)
        chosen_paths = [found]
    else:
        filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
        print(f"\n{Fore.RED}=== XÓA SKILL TRONG KHO LƯU TRỮ TRUNG TÂM (REPO-ONLY){filter_tag} ==={Style.RESET_ALL}")
        print(f">>> Kho lưu trữ: {SKILLS_FOLDER_PATH} ({len(available_skills)} skills)")
        print("\nDanh sách các Skill hiện có trong kho:")
        for idx, s in enumerate(available_skills, 1):
            print(f"  [{idx:2d}] {s}")
        if len(available_skills) > 1:
            print(f"  [ a] Xóa TẤT CẢ các Skill trên ({len(available_skills)} skills)")
        print()

        user_choice = input("Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' ('q' để hủy): ").strip()
        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Hủy thao tác an toàn.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            chosen_paths = [os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, s)) for s in available_skills]
        else:
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                chosen_indices = [int(n) for n in num_tokens]
                for idx in chosen_indices:
                    if 1 <= idx <= len(available_skills):
                        p = os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, available_skills[idx - 1]))
                        if p not in chosen_paths:
                            chosen_paths.append(p)
                    else:
                        print(f"{Fore.YELLOW}⚠️ Bỏ qua số thứ tự ngoài phạm vi: {idx}{Style.RESET_ALL}")
                if not chosen_paths:
                    print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                found = find_skill_folder(SKILLS_FOLDER_PATH, user_choice)
                if not found:
                    print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{user_choice}' trong kho {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
                    sys.exit(1)
                chosen_paths = [found]

    # Xác nhận an toàn
    print(f"\n{Fore.RED}{Style.BRIGHT}⚠️ CẢNH BÁO NGUY HIỂM:{Style.RESET_ALL} Bạn có chắc chắn muốn {Fore.RED}XÓA VĨNH VIỄN{Style.RESET_ALL} {len(chosen_paths)} Skill sau khỏi KHO LƯU TRỮ TRUNG TÂM?")
    for p in chosen_paths:
        print(f"   - {Style.BRIGHT}{os.path.relpath(p, SKILLS_FOLDER_PATH)}{Style.RESET_ALL} ({p})")
    print(f"{Fore.LIGHTBLACK_EX}Hành động này sẽ xóa hoàn toàn thư mục trên ổ đĩa và KHÔNG THỂ HOÀN TÁC.{Style.RESET_ALL}")

    ans = input(f"\nNhập 'y' để xác nhận xóa vĩnh viễn (hoặc phím khác để hủy): ").strip().lower()
    if ans != "y":
        print(">>> Hủy thao tác.")
        sys.exit(0)

    print()
    deleted_count = 0
    for p in chosen_paths:
        try:
            if not is_safe_to_delete(p, SKILLS_FOLDER_PATH):
                print(f"{Fore.RED}❌ Bỏ qua vì đường dẫn không an toàn (.git/root): {p}{Style.RESET_ALL}")
                continue
            if os.path.exists(p):
                shutil.rmtree(p)
                print(f"{Fore.GREEN}✅ Đã xóa vĩnh viễn: {p}{Style.RESET_ALL}")
                deleted_count += 1
            else:
                print(f"{Fore.YELLOW}⚠️ Thư mục không tồn tại: {p}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Lỗi khi xóa {p}: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}🎉 Hoàn tất! Đã xóa thành công {deleted_count}/{len(chosen_paths)} Skill khỏi kho lưu trữ trung tâm.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}ℹ️ Các AI Agent không bị thay đổi.{Style.RESET_ALL}\n")


def handle_remove_include_agents(include_agent_choice: str, preselected_skill: str | None = None, filter_choice: str | None = None):
    """
    Xóa Skill khỏi CẢ KHO LƯU TRỮ TRUNG TÂM lẫn các AI Agent tương ứng (Mode Include-Agent).
    """
    if include_agent_choice == "all":
        targets = ALL_AGENTS
    elif include_agent_choice in LLM_TARGETS:
        targets = [LLM_TARGETS[include_agent_choice]]
    else:
        print(f"{Fore.RED}❌ Lỗi: Tên AI/LLM '{include_agent_choice}' không hợp lệ.{Style.RESET_ALL}")
        sys.exit(1)

    if not os.path.exists(SKILLS_FOLDER_PATH):
        print(f"{Fore.RED}❌ Lỗi: Thư mục kho lưu trữ SKILLs không tồn tại: {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
        sys.exit(1)

    available_skills = list_skill_folders(SKILLS_FOLDER_PATH)
    if not available_skills:
        print(f"{Fore.YELLOW}⚠️ Kho lưu trữ rỗng: Chưa có skill nào trong {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
        sys.exit(0)

    if filter_choice:
        available_skills = [s for s in available_skills if get_skill_invocation_state(os.path.join(SKILLS_FOLDER_PATH, s)) == filter_choice]
        if not available_skills:
            lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
            print(f"\n{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong kho khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
            sys.exit(0)

    chosen_central_paths = []

    if preselected_skill:
        found = find_skill_folder(SKILLS_FOLDER_PATH, preselected_skill)
        if not found:
            print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{preselected_skill}' trong kho lưu trữ {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
            sys.exit(1)
        if filter_choice:
            st = get_skill_invocation_state(found)
            if st != filter_choice:
                lbl_cur = "TẮT" if st == "off-invocation" else "BẬT"
                lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                print(f"\n{Fore.YELLOW}⚠️ Bỏ qua Skill '{preselected_skill}' vì trạng thái hiện tại trong kho ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                sys.exit(0)
        chosen_central_paths = [found]
    else:
        filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
        print(f"\n{Fore.RED}=== XÓA SKILL TRONG KHO LƯU TRỮ VÀ CẢ CÁC AI AGENT{filter_tag} ==={Style.RESET_ALL}")
        print(f">>> Kho lưu trữ: {SKILLS_FOLDER_PATH} ({len(available_skills)} skills)")
        print("\nDanh sách các Skill hiện có trong kho:")
        for idx, s in enumerate(available_skills, 1):
            print(f"  [{idx:2d}] {s}")
        if len(available_skills) > 1:
            print(f"  [ a] Xóa TẤT CẢ các Skill trên ({len(available_skills)} skills)")
        print()

        user_choice = input("Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' ('q' để hủy): ").strip()
        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Hủy thao tác an toàn.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            chosen_central_paths = [os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, s)) for s in available_skills]
        else:
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                chosen_indices = [int(n) for n in num_tokens]
                for idx in chosen_indices:
                    if 1 <= idx <= len(available_skills):
                        p = os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, available_skills[idx - 1]))
                        if p not in chosen_central_paths:
                            chosen_central_paths.append(p)
                if not chosen_central_paths:
                    print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                found = find_skill_folder(SKILLS_FOLDER_PATH, user_choice)
                if not found:
                    print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{user_choice}' trong kho {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
                    sys.exit(1)
                chosen_central_paths = [found]

    # Xây dựng danh sách xóa tổng thể
    deletion_plan = []
    for p in chosen_central_paths:
        base_name = os.path.basename(p)
        item = {
            "name": base_name,
            "central_path": p,
            "agent_dirs": []
        }
        for lbl, agent_path in targets:
            agent_skill_dir = os.path.join(agent_path, base_name)
            if os.path.exists(agent_skill_dir):
                item["agent_dirs"].append((lbl, agent_skill_dir))
        deletion_plan.append(item)

    target_labels = ", ".join([lbl for lbl, _ in targets])
    print(f"\n{Fore.RED}{Style.BRIGHT}⚠️ CẢNH BÁO NGUY HIỂM:{Style.RESET_ALL} Bạn có chắc chắn muốn {Fore.RED}XÓA VĨNH VIỄN{Style.RESET_ALL} {len(deletion_plan)} Skill sau khỏi CẢ KHO GỐC lẫn AI AGENT ({target_labels})?")
    for item in deletion_plan:
        agent_info = f" (có trong {len(item['agent_dirs'])} agent)" if item["agent_dirs"] else " (chưa cài vào agent nào)"
        print(f"   - {Style.BRIGHT}{item['name']}{Style.RESET_ALL}{agent_info}")
        print(f"     Kho gốc: {item['central_path']}")
        for lbl, adir in item["agent_dirs"]:
            print(f"     {lbl}: {adir}")

    ans = input(f"\nNhập 'y' để xác nhận xóa vĩnh viễn (hoặc phím khác để hủy): ").strip().lower()
    if ans != "y":
        print(">>> Hủy thao tác.")
        sys.exit(0)

    print()
    total_repo_deleted = 0
    total_agent_deleted = 0

    for item in deletion_plan:
        # Xóa khỏi kho
        try:
            if not is_safe_to_delete(item["central_path"], SKILLS_FOLDER_PATH):
                print(f"{Fore.RED}❌ Bỏ qua vì đường dẫn không an toàn (.git/root): {item['central_path']}{Style.RESET_ALL}")
            elif os.path.exists(item["central_path"]):
                shutil.rmtree(item["central_path"])
                print(f"{Fore.GREEN}✅ Đã xóa khỏi kho gốc: {item['name']}{Style.RESET_ALL}")
                total_repo_deleted += 1
        except Exception as e:
            print(f"{Fore.RED}❌ Lỗi khi xóa khỏi kho gốc: {e}{Style.RESET_ALL}")

        # Xóa khỏi agent
        for lbl, adir in item["agent_dirs"]:
            try:
                if not any(is_safe_to_delete(adir, ap) for _, ap in targets):
                    print(f"{Fore.RED}❌ Bỏ qua vì đường dẫn không an toàn (.git/root): {adir}{Style.RESET_ALL}")
                elif os.path.exists(adir):
                    shutil.rmtree(adir)
                    print(f"{Fore.GREEN}✅ Đã xóa khỏi {lbl}: {item['name']}{Style.RESET_ALL}")
                    total_agent_deleted += 1
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi khi xóa khỏi {lbl}: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}🎉 Hoàn tất! Đã xóa {total_repo_deleted} skill khỏi kho lưu trữ và {total_agent_deleted} lượt skill khỏi các AI Agent.{Style.RESET_ALL}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("remove", "rm"):
        print(f"{Fore.RED}>>> Lỗi: Lệnh không hợp lệ.{Style.RESET_ALL}")
        sys.exit(1)

    ai_choice = None
    include_agent_choice = None
    filter_choice = None
    positional_args = []

    # Parse arguments:
    # --filter, -f <on-invocation|off-invocation>
    # --ai, --llm, --agent <name|all>
    # --include-agent, --include-ai, --include-llm <name|all>
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("--filter", "-f"):
            if i + 1 < len(sys.argv):
                parsed = parse_filter_arg(sys.argv[i + 1])
                if not parsed:
                    print(f"{Fore.RED}❌ Lỗi: Giá trị filter '{sys.argv[i + 1]}' không hợp lệ.{Style.RESET_ALL}")
                    print("Các giá trị hợp lệ:")
                    print("  - on-invocation (hoặc on)   : Chỉ xử lý/hiển thị Skill đang BẬT tự động gọi")
                    print("  - off-invocation (hoặc off) : Chỉ xử lý/hiển thị Skill đang TẮT tự động gọi")
                    sys.exit(1)
                filter_choice = parsed
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu giá trị sau cờ {arg}. (Ví dụ: --filter on-invocation, -f off-invocation){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--filter=", "-f=")):
            val = arg.split("=", 1)[1]
            parsed = parse_filter_arg(val)
            if not parsed:
                print(f"{Fore.RED}❌ Lỗi: Giá trị filter '{val}' không hợp lệ.{Style.RESET_ALL}")
                print("Các giá trị hợp lệ:")
                print("  - on-invocation (hoặc on)   : Chỉ xử lý/hiển thị Skill đang BẬT tự động gọi")
                print("  - off-invocation (hoặc off) : Chỉ xử lý/hiển thị Skill đang TẮT tự động gọi")
                sys.exit(1)
            filter_choice = parsed
            i += 1
        elif arg in ("--ai", "--llm", "--agent"):
            if i + 1 < len(sys.argv):
                ai_choice = sys.argv[i + 1].strip().lower()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên AI/Agent sau cờ {arg}. (Ví dụ: --agent agy, --ai claude, --llm codex, --agent all){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--ai=", "--llm=", "--agent=")):
            ai_choice = arg.split("=", 1)[1].strip().lower()
            i += 1
        elif arg in ("--include-agent", "--include-ai", "--include-llm"):
            if i + 1 < len(sys.argv):
                include_agent_choice = sys.argv[i + 1].strip().lower()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên AI/Agent sau cờ {arg}. (Ví dụ: --include-agent agy, --include-agent all){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--include-agent=", "--include-ai=", "--include-llm=")):
            include_agent_choice = arg.split("=", 1)[1].strip().lower()
            i += 1
        else:
            positional_args.append(arg)
            i += 1

    if ai_choice is not None and include_agent_choice is not None:
        print(f"{Fore.RED}❌ Lỗi: Không thể dùng đồng thời cờ độc lập (--agent/--ai/--llm) và cờ đồng bộ (--include-agent/--include-ai/--include-llm). Vui lòng chỉ chọn 1 trong 2.{Style.RESET_ALL}")
        sys.exit(1)

    preselected_skill = positional_args[0] if len(positional_args) > 0 else None

    # Case 1: Agent-Only mode
    if ai_choice is not None:
        if ai_choice == "all":
            handle_remove_for_all_agents(preselected_skill, filter_choice)
        elif ai_choice in LLM_TARGETS:
            agent_label, agent_path = LLM_TARGETS[ai_choice]
            handle_remove_for_single_agent(agent_label, agent_path, preselected_skill, filter_choice)
        else:
            print(f"{Fore.RED}❌ Lỗi: Tên AI/LLM '{ai_choice}' không hợp lệ.{Style.RESET_ALL}")
            print("Các lựa chọn hợp lệ:")
            print("  - agy (antigravity, gemini, anti) : Google Antigravity (~/.gemini/config/skills)")
            print("  - codex (openai)                  : OpenAI Codex (~/.codex/skills)")
            print("  - claude (clau, anthropic)        : Claude Code (~/.claude/skills)")
            print("  - all                             : Rà soát và xóa Skill chung giữa cả 3 AI Agent trên")
            sys.exit(1)

    # Case 2: Include-Agent mode
    elif include_agent_choice is not None:
        handle_remove_include_agents(include_agent_choice, preselected_skill, filter_choice)

    # Case 3: Repo-Only mode (không cờ)
    else:
        handle_remove_for_central_repo(preselected_skill, filter_choice)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
