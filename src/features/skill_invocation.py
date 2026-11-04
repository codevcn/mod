#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
skill_invocation.py - Quản lý trạng thái tự động gọi (Auto-Invocation) của AI Skill:
- mod skill off-invocation [skill]                            : CHỈ tác động lên kho lưu trữ trung tâm.
- mod skill off-invocation [skill] --agent <name|all>         : CHỈ tác động lên AI Agent chỉ định (không chạm kho gốc).
- mod skill off-invocation [skill] --include-agent <name|all> : Tác động CẢ HAI (kho lưu trữ VÀ đồng bộ sang AI Agent).
- mod skill off-invocation [skill] --project [dest_path]      : Tác động lên Skill bên trong dự án cục bộ (mặc định CWD).
  Alias: '--prj', '-p'
- mod skill on-invocation [...]                               : Tương tự, bật tự động gọi (xóa field).
- Alias: 'off-invo' tương đương 'off-invocation', 'on-invo' tương đương 'on-invocation'.
- Cờ lọc: --filter <on-invocation|off-invocation> (hoặc -f)  : Chỉ tác động & hiển thị các skill khớp với trạng thái chỉ định.
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
    find_skill_folder,
    deploy_skill,
    get_skill_invocation_state,
    parse_filter_arg,
)
from features.skill_remove import get_agent_skills
from features.skill_list import find_project_skills


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


def validate_and_parse_frontmatter(file_path: str):
    """
    Kiểm tra và trích xuất YAML frontmatter từ file SKILL.md.
    Trả về:
      is_valid: bool
      error_msg: str
      fm_text: str (nội dung giữa 2 dấu ---)
      body_text: str (nội dung sau dấu --- thứ 2)
      fm_dict: dict (dữ liệu đã parse từ YAML)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return False, f"Không thể đọc file: {e}", "", "", {}

    clean_content = content.lstrip("\ufeff")
    if not clean_content.startswith("---"):
        return False, "File không bắt đầu bằng khối '---' (thiếu YAML frontmatter mở).", "", "", {}

    pattern = r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$"
    match = re.match(pattern, clean_content, re.DOTALL)
    if not match:
        return False, "Không tìm thấy dấu đóng '---' hợp lệ cho khối YAML frontmatter.", "", "", {}

    fm_text = match.group(1)
    body_text = match.group(2)

    try:
        fm_dict = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        return False, f"Cú pháp YAML bên trong frontmatter không hợp lệ: {e}", fm_text, body_text, {}

    if not isinstance(fm_dict, dict):
        return False, "Nội dung YAML frontmatter không phải là dictionary hợp lệ.", fm_text, body_text, {}

    return True, "", fm_text, body_text, fm_dict


def get_invocation_status(skill_dir_path: str) -> str:
    """Lấy nhãn trạng thái invocation hiện tại để hiển thị trực quan trong danh sách."""
    skill_md = get_skill_md_path(skill_dir_path)
    if not skill_md:
        return f"{Fore.RED}[Thiếu SKILL.md]{Style.RESET_ALL}"

    is_valid, _, _, _, fm_dict = validate_and_parse_frontmatter(skill_md)
    if not is_valid:
        return f"{Fore.RED}[Frontmatter LỖI]{Style.RESET_ALL}"

    if fm_dict.get("disable-model-invocation") is True:
        return f"{Fore.YELLOW}[Tự động gọi: TẮT]{Style.RESET_ALL}"
    return f"{Fore.GREEN}[Tự động gọi: BẬT]{Style.RESET_ALL}"


def process_off_invocation(file_path: str, fm_text: str, body_text: str, fm_dict: dict) -> tuple[bool, str]:
    """Tắt tự động gọi: Đảm bảo có disable-model-invocation: true trong YAML frontmatter."""
    current_val = fm_dict.get("disable-model-invocation")

    if current_val is True:
        return False, "Skill đã ở trạng thái TẮT tự động gọi từ trước (disable-model-invocation: true)."

    if "disable-model-invocation" in fm_dict:
        new_fm = re.sub(
            r"(?m)^disable-model-invocation\s*:.*$",
            "disable-model-invocation: true",
            fm_text,
        )
        action_desc = "Cập nhật disable-model-invocation thành true"
    else:
        clean_fm = fm_text.rstrip("\r\n")
        new_fm = clean_fm + "\ndisable-model-invocation: true\n"
        action_desc = "Thêm field disable-model-invocation: true"

    clean_new_fm = new_fm.rstrip("\r\n") + "\n"
    new_content = f"---\n{clean_new_fm}---\n{body_text}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True, f"Đã tắt tự động gọi ({action_desc})."


def process_on_invocation(file_path: str, fm_text: str, body_text: str, fm_dict: dict) -> tuple[bool, str]:
    """Bật tự động gọi: Xóa bỏ field disable-model-invocation khỏi YAML frontmatter."""
    if "disable-model-invocation" not in fm_dict:
        return False, "Skill hiện đã được BẬT tự động gọi sẵn (không có field disable-model-invocation)."

    new_fm = re.sub(
        r"(?m)^disable-model-invocation\s*:.*(?:\r?\n)?",
        "",
        fm_text,
    )

    clean_new_fm = new_fm.rstrip("\r\n") + "\n"
    new_content = f"---\n{clean_new_fm}---\n{body_text}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True, "Đã bật tự động gọi (đã gỡ bỏ field disable-model-invocation)."


def parse_cli_args():
    """Phân tích các đối số dòng lệnh."""
    if len(sys.argv) < 2:
        print(f"{Fore.RED}❌ Lỗi: Thiếu action (off-invocation hoặc on-invocation).{Style.RESET_ALL}")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action in ("off-invocation", "off-invo"):
        action = "off-invocation"
    elif action in ("on-invocation", "on-invo"):
        action = "on-invocation"
    else:
        print(f"{Fore.RED}❌ Lỗi: Action '{action}' không hợp lệ.{Style.RESET_ALL}")
        sys.exit(1)

    ai_choice = None
    include_choice = None
    filter_choice = None
    force_overwrite = False
    is_project_mode = False
    project_root = None
    positional_args = []

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("--project", "--prj", "-p"):
            is_project_mode = True
            if i + 1 < len(sys.argv):
                next_val = sys.argv[i + 1]
                if not next_val.startswith("-"):
                    # Nếu đã có positional_args (skill_name) trước đó, hoặc next_val là path/folder rõ ràng
                    if positional_args or os.path.isdir(next_val) or any(c in next_val for c in "/\\") or next_val in (".", ".."):
                        project_root = next_val
                        i += 2
                        continue
            i += 1
        elif arg.startswith(("--project=", "--prj=")):
            is_project_mode = True
            project_root = arg.split("=", 1)[1].strip()
            i += 1
        elif arg in ("--ai", "--llm", "--agent"):
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
        elif arg in ("--filter", "-f"):
            if i + 1 < len(sys.argv):
                raw_filter = sys.argv[i + 1]
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
        elif arg in ("-y", "--yes", "--force"):
            force_overwrite = True
            i += 1
        else:
            positional_args.append(arg)
            i += 1

    if is_project_mode:
        if ai_choice is not None:
            print(f"{Fore.RED}❌ Lỗi: Không thể dùng đồng thời cờ dự án (--project/--prj) và cờ AI Agent (--agent/--ai/--llm). Vui lòng chỉ chọn 1 trong 2.{Style.RESET_ALL}")
            sys.exit(1)
        if include_choice is not None:
            print(f"{Fore.RED}❌ Lỗi: Không thể dùng đồng thời cờ dự án (--project/--prj) và cờ đồng bộ (--include-agent/--include-ai/--include-llm). Vui lòng chỉ chọn 1 trong 2.{Style.RESET_ALL}")
            sys.exit(1)
        if not project_root:
            project_root = "."

    if ai_choice is not None and include_choice is not None:
        print(f"{Fore.RED}❌ Lỗi: Không thể dùng đồng thời cờ độc lập (--agent/--ai/--llm) và cờ đồng bộ (--include-agent/--include-ai/--include-llm). Vui lòng chỉ chọn 1 trong 2.{Style.RESET_ALL}")
        sys.exit(1)

    skill_name = positional_args[0] if positional_args else None
    return action, skill_name, ai_choice, include_choice, filter_choice, force_overwrite, is_project_mode, project_root


def resolve_targets(agent_choice: str) -> list[tuple[str, str]]:
    """Xác định danh sách các thư mục AI Agent đích theo cờ."""
    if agent_choice == "all":
        return [
            ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
            ("OpenAI Codex", CODEX_SKILLS_PATH),
            ("Claude Code", CLAUDE_SKILLS_PATH),
        ]
    elif agent_choice in LLM_TARGETS:
        return [LLM_TARGETS[agent_choice]]
    else:
        print(f"{Fore.RED}❌ Lỗi: Tên AI/LLM '{agent_choice}' không hợp lệ.{Style.RESET_ALL}")
        print("Các lựa chọn hợp lệ:")
        print("  - agy (antigravity, gemini, anti) : Google Antigravity (~/.gemini/config/skills)")
        print("  - codex (openai)                  : OpenAI Codex (~/.codex/skills)")
        print("  - claude (clau, anthropic)        : Claude Code (~/.claude/skills)")
        print("  - all                             : Áp dụng cho tất cả các AI Agent trên")
        sys.exit(1)


def apply_action_to_file(action: str, file_path: str, label: str) -> bool:
    """Kiểm tra và thực hiện bật/tắt invocation cho 1 file SKILL.md."""
    is_valid, err_msg, fm_text, body_text, fm_dict = validate_and_parse_frontmatter(file_path)
    if not is_valid:
        print(f"\n{Fore.RED}❌ [LỖI FRONTMATTER] {label}: {err_msg}{Style.RESET_ALL}")
        print(f"   Đường dẫn: {file_path}")
        return False

    if action == "off-invocation":
        changed, msg = process_off_invocation(file_path, fm_text, body_text, fm_dict)
    else:
        changed, msg = process_on_invocation(file_path, fm_text, body_text, fm_dict)

    if changed:
        print(f"{Fore.GREEN}✔ [{label}] {msg}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}ℹ [{label}] {msg}{Style.RESET_ALL}")
    return True


def execute_agent_only_mode(action: str, skill_name_input: str | None, ai_choice: str, filter_choice: str | None):
    """
    Mode A: Agent-Only mode.
    CHỈ thao tác trực tiếp trên các thư mục của AI Agent.
    TUYỆT ĐỐI KHÔNG can thiệp vào kho lưu trữ trung tâm.
    """
    targets = resolve_targets(ai_choice)
    action_title = "TẮT TỰ ĐỘNG GỌI (OFF-INVOCATION) [AGENT-ONLY]" if action == "off-invocation" else "BẬT TỰ ĐỘNG GỌI (ON-INVOCATION) [AGENT-ONLY]"
    filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
    print(f"\n{Fore.MAGENTA}=== {action_title}{filter_tag} ==={Style.RESET_ALL}")

    target_items = []  # List of dict: {"name": str, "agent_label": str, "dir": str, "md": str}

    if skill_name_input:
        target_name_lower = skill_name_input.strip().lower()
        found_any = False
        for agent_label, agent_path in targets:
            if not os.path.isdir(agent_path):
                print(f"{Fore.YELLOW}⚠️ Thư mục Agent chưa tồn tại: {agent_path}{Style.RESET_ALL}")
                continue
            skills = get_agent_skills(agent_path)
            matched = [s for s in skills if s.lower() == target_name_lower]
            if matched:
                s_name = matched[0]
                s_dir = os.path.join(agent_path, s_name)
                # Kiểm tra bộ lọc filter_choice
                if filter_choice:
                    state = get_skill_invocation_state(s_dir)
                    if state != filter_choice:
                        lbl_cur = "TẮT" if state == "off-invocation" else "BẬT"
                        lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                        print(f"{Fore.YELLOW}⚠️ Bỏ qua Skill '{skill_name_input}' trên {agent_label} vì trạng thái hiện tại ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                        continue
                s_md = get_skill_md_path(s_dir)
                if s_md:
                    target_items.append({"name": s_name, "agent_label": agent_label, "dir": s_dir, "md": s_md})
                    found_any = True
            else:
                print(f"{Fore.YELLOW}⚠️ Skill '{skill_name_input}' chưa được cài đặt trong {agent_label} ({agent_path}).{Style.RESET_ALL}")

        if not found_any and not filter_choice:
            print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{skill_name_input}' trong bất kỳ Agent nào được chỉ định.{Style.RESET_ALL}")
            sys.exit(1)
        elif not target_items:
            print(f"{Fore.YELLOW}>>> Không có Skill nào được xử lý.{Style.RESET_ALL}")
            sys.exit(0)
    else:
        # Chế độ tương tác cho Agent
        if len(targets) == 1:
            agent_label, agent_path = targets[0]
            skills = get_agent_skills(agent_path)
            if not skills:
                print(f"{Fore.YELLOW}⚠️ Chưa có Skill nào được cài đặt trong {agent_label} ({agent_path}).{Style.RESET_ALL}")
                sys.exit(0)

            # Lọc theo filter_choice nếu có
            if filter_choice:
                skills = [s for s in skills if get_skill_invocation_state(os.path.join(agent_path, s)) == filter_choice]
                if not skills:
                    lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                    print(f"{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong {agent_label} khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
                    sys.exit(0)

            print(f">>> Đang quét danh sách Skill trong {Fore.MAGENTA}{agent_label}{Style.RESET_ALL} ({len(skills)} skills):")
            print()
            for idx, s in enumerate(skills, 1):
                full_p = os.path.join(agent_path, s)
                stts = get_invocation_status(full_p)
                print(f"  [{idx:2d}] {s:<42} {stts}")
            print(f"  [ a] Áp dụng cho TẤT CẢ các Skill trên ({len(skills)} skills)")
            print()

            user_choice = input("Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' ('q' để hủy): ").strip()
            if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
                print(">>> Đã hủy thao tác an toàn.")
                sys.exit(0)
            elif user_choice.lower() in ("a", "all", "*"):
                chosen_names = skills
            else:
                num_tokens = re.findall(r"\d+", user_choice)
                if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                    chosen_names = [skills[int(n) - 1] for n in num_tokens if 1 <= int(n) <= len(skills)]
                else:
                    matched = [s for s in skills if s.lower() == user_choice.lower()]
                    chosen_names = matched if matched else []

            if not chosen_names:
                print(f"{Fore.RED}❌ Lỗi: Không có Skill nào hợp lệ được chọn.{Style.RESET_ALL}")
                sys.exit(1)

            for s in chosen_names:
                s_dir = os.path.join(agent_path, s)
                s_md = get_skill_md_path(s_dir)
                if s_md:
                    target_items.append({"name": s, "agent_label": agent_label, "dir": s_dir, "md": s_md})

        else:
            # Targets là 'all' 3 agents
            aggregated = {}
            for agent_label, agent_path in targets:
                for s in get_agent_skills(agent_path):
                    s_dir = os.path.join(agent_path, s)
                    if filter_choice and get_skill_invocation_state(s_dir) != filter_choice:
                        continue
                    s_md = get_skill_md_path(s_dir)
                    if s_md:
                        aggregated.setdefault(s, []).append((agent_label, s_dir, s_md))

            if not aggregated:
                lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                filter_info = f" khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl})" if filter_choice else ""
                print(f"{Fore.YELLOW}⚠️ Không tìm thấy Skill nào trên cả 3 AI Agent{filter_info}.{Style.RESET_ALL}")
                sys.exit(0)

            sorted_names = sorted(aggregated.keys(), key=lambda s: s.lower())
            print(f">>> Danh sách các Skill hiện diện trên các AI Agent ({len(sorted_names)} skills):")
            print()
            for idx, s in enumerate(sorted_names, 1):
                agent_names = ", ".join([lbl for lbl, _, _ in aggregated[s]])
                sample_md = aggregated[s][0][2]
                sample_status = get_invocation_status(os.path.dirname(sample_md))
                print(f"  [{idx:2d}] {s:<36} {sample_status} ({agent_names})")
            print(f"  [ a] Áp dụng cho TẤT CẢ các Skill trên ({len(sorted_names)} skills)")
            print()

            user_choice = input("Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' ('q' để hủy): ").strip()
            if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
                print(">>> Đã hủy thao tác an toàn.")
                sys.exit(0)
            elif user_choice.lower() in ("a", "all", "*"):
                chosen_names = sorted_names
            else:
                num_tokens = re.findall(r"\d+", user_choice)
                if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                    chosen_names = [sorted_names[int(n) - 1] for n in num_tokens if 1 <= int(n) <= len(sorted_names)]
                else:
                    matched = [s for s in sorted_names if s.lower() == user_choice.lower()]
                    chosen_names = matched if matched else []

            if not chosen_names:
                print(f"{Fore.RED}❌ Lỗi: Không có Skill nào hợp lệ được chọn.{Style.RESET_ALL}")
                sys.exit(1)

            for s in chosen_names:
                for agent_label, s_dir, s_md in aggregated[s]:
                    target_items.append({"name": s, "agent_label": agent_label, "dir": s_dir, "md": s_md})

    # Thực thi trên target_items
    print(f"\n🔄 Bắt đầu cập nhật {len(target_items)} lượt Skill trên các AI Agent...")
    success_count = 0
    for item in target_items:
        label = f"{item['agent_label']} / {item['name']}"
        ok = apply_action_to_file(action, item["md"], label)
        if ok:
            success_count += 1

    print(f"\n{Fore.GREEN}🎉 Hoàn tất: Đã cập nhật thành công {success_count}/{len(target_items)} lượt Skill trên AI Agent.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}ℹ️ Kho lưu trữ trung tâm ({SKILLS_FOLDER_PATH}) không bị thay đổi.{Style.RESET_ALL}\n")


def execute_project_mode(action: str, skill_name_input: str | None, project_root: str, filter_choice: str | None):
    """
    Mode D: Project mode (--project, --prj, -p).
    Tác động trực tiếp lên Skill bên trong thư mục dự án cục bộ (.agents/skills, .agent/skills, hoặc chính dự án).
    TUYỆT ĐỐI KHÔNG can thiệp vào kho lưu trữ trung tâm và Global AI Agents.
    """
    target_project = os.path.abspath(project_root)
    if not os.path.exists(target_project):
        print(f"{Fore.RED}❌ Lỗi: Thư mục dự án không tồn tại: {target_project}{Style.RESET_ALL}")
        sys.exit(1)
    if not os.path.isdir(target_project):
        print(f"{Fore.RED}❌ Lỗi: Đường dẫn dự án không phải là thư mục: {target_project}{Style.RESET_ALL}")
        sys.exit(1)

    available_skills = find_project_skills(target_project)
    if not available_skills:
        print(f"\n{Fore.YELLOW}⚠️ Không tìm thấy Skill nào trong thư mục dự án:{Style.RESET_ALL}")
        print(f"   {target_project}")
        print(f"\n{Fore.LIGHTBLACK_EX}💡 Gợi ý:{Style.RESET_ALL}")
        print(f"   - Thư mục skill hợp lệ phải chứa trực tiếp file 'SKILL.md' (hoặc 'skill.md').")
        print(f"   - Dùng lệnh 'mod skill set <tên_skill> {target_project}' để cài đặt skill vào dự án.")
        sys.exit(0)

    # Áp dụng bộ lọc filter_choice nếu có
    if filter_choice:
        filtered_available = []
        for s in available_skills:
            full_dir = target_project if s == "." else os.path.normpath(os.path.join(target_project, s))
            if get_skill_invocation_state(full_dir) == filter_choice:
                filtered_available.append(s)
        available_skills = filtered_available
        if not available_skills:
            lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
            print(f"\n{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong dự án khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
            sys.exit(0)

    selected_skills = []

    if skill_name_input:
        if skill_name_input.lower() in ("all", "*"):
            selected_skills = available_skills
        else:
            target_name_lower = skill_name_input.strip().lower()
            matched = []
            for s in available_skills:
                full_dir = target_project if s == "." else os.path.normpath(os.path.join(target_project, s))
                base_name = os.path.basename(full_dir).lower()
                rel_path = s.replace("\\", "/").lower()
                if target_name_lower in (base_name, rel_path, s.lower()):
                    matched.append(s)

            if not matched:
                print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{skill_name_input}' trong dự án {target_project}.{Style.RESET_ALL}")
                sys.exit(1)

            selected_skills = matched
    else:
        action_title = "TẮT TỰ ĐỘNG GỌI (OFF-INVOCATION) [DỰ ÁN]" if action == "off-invocation" else "BẬT TỰ ĐỘNG GỌI (ON-INVOCATION) [DỰ ÁN]"
        filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
        print(f"\n{Fore.GREEN}=== {action_title}{filter_tag} ==={Style.RESET_ALL}")
        print(f"📂 Thư mục dự án: {Fore.WHITE}{target_project}{Style.RESET_ALL}")
        print(f">>> Đang quét danh sách Skill trong dự án ({len(available_skills)} skills):")
        print()

        for idx, s in enumerate(available_skills, 1):
            full_p = target_project if s == "." else os.path.normpath(os.path.join(target_project, s))
            stts = get_invocation_status(full_p)
            display_name = s if s != "." else os.path.basename(target_project)
            print(f"  [{idx:2d}] {display_name:<44} {stts}")

        print(f"  [ a] Áp dụng cho TẤT CẢ các Skill trên ({len(available_skills)} skills)")
        print()

        user_choice = input("Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' ('q' để hủy): ").strip()
        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Đã hủy thao tác an toàn.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            selected_skills = available_skills
        else:
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                for n in num_tokens:
                    idx = int(n)
                    if 1 <= idx <= len(available_skills):
                        s = available_skills[idx - 1]
                        if s not in selected_skills:
                            selected_skills.append(s)
                    else:
                        print(f"{Fore.YELLOW}⚠️ Bỏ qua số thứ tự ngoài phạm vi: {idx}{Style.RESET_ALL}")
                if not selected_skills:
                    print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                target_lower = user_choice.lower()
                matched = []
                for s in available_skills:
                    full_dir = target_project if s == "." else os.path.normpath(os.path.join(target_project, s))
                    if target_lower in (os.path.basename(full_dir).lower(), s.lower(), s.replace("\\", "/").lower()):
                        matched.append(s)
                if not matched:
                    print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{user_choice}' trong danh sách.{Style.RESET_ALL}")
                    sys.exit(1)
                selected_skills = matched

    print(f"\n🔄 Bắt đầu xử lý {len(selected_skills)} Skill trong dự án...")
    success_count = 0
    error_count = 0

    for s in selected_skills:
        full_dir = target_project if s == "." else os.path.normpath(os.path.join(target_project, s))
        skill_md = get_skill_md_path(full_dir)
        display_name = s if s != "." else os.path.basename(target_project)
        if not skill_md:
            print(f"\n{Fore.RED}❌ [THIẾU FILE] Không tìm thấy file SKILL.md trong: {full_dir}{Style.RESET_ALL}")
            error_count += 1
            continue

        ok = apply_action_to_file(action, skill_md, f"Dự án / {display_name}")
        if ok:
            success_count += 1
        else:
            error_count += 1

    print(f"\n{Fore.GREEN}🎉 Hoàn tất: Đã cập nhật thành công {success_count}/{len(selected_skills)} Skill trong dự án.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}ℹ️ Kho lưu trữ trung tâm ({SKILLS_FOLDER_PATH}) và Global AI Agents không bị thay đổi.{Style.RESET_ALL}\n")


def execute_repo_mode(action: str, skill_name_input: str | None, include_choice: str | None, force_overwrite: bool, filter_choice: str | None):
    """
    Mode B & C: Tác động lên kho lưu trữ trung tâm.
    Nếu include_choice != None: Đồng bộ sang AI Agent sau khi sửa kho.
    """
    if not os.path.exists(SKILLS_FOLDER_PATH):
        print(f"{Fore.RED}❌ Lỗi: Thư mục kho lưu trữ SKILLs không tồn tại: {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
        sys.exit(1)

    available_skills = list_skill_folders(SKILLS_FOLDER_PATH)
    if not available_skills:
        print(f"{Fore.YELLOW}⚠️ Không tìm thấy Skill hợp lệ nào trong kho {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
        sys.exit(0)

    # Áp dụng bộ lọc filter_choice nếu có
    if filter_choice:
        available_skills = [s for s in available_skills if get_skill_invocation_state(os.path.join(SKILLS_FOLDER_PATH, s)) == filter_choice]
        if not available_skills:
            lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
            print(f"\n{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong kho khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
            sys.exit(0)

    selected_skill_dirs = []

    if skill_name_input:
        if skill_name_input.lower() in ("all", "*"):
            selected_skill_dirs = [os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, s)) for s in available_skills]
        else:
            found_dir = find_skill_folder(SKILLS_FOLDER_PATH, skill_name_input)
            if not found_dir and (os.path.isdir(skill_name_input) or os.path.isfile(skill_name_input)):
                cand = os.path.abspath(skill_name_input)
                if os.path.isfile(cand) and os.path.basename(cand).lower() == "skill.md":
                    found_dir = os.path.dirname(cand)
                elif os.path.isdir(cand) and get_skill_md_path(cand):
                    found_dir = cand

            if not found_dir:
                print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{skill_name_input}' hợp lệ trong {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
                sys.exit(1)

            if filter_choice:
                state = get_skill_invocation_state(found_dir)
                if state != filter_choice:
                    lbl_cur = "TẮT" if state == "off-invocation" else "BẬT"
                    lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                    print(f"\n{Fore.YELLOW}⚠️ Bỏ qua Skill '{skill_name_input}' vì trạng thái hiện tại ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                    sys.exit(0)

            selected_skill_dirs = [found_dir]
    else:
        action_title = "TẮT TỰ ĐỘNG GỌI (OFF-INVOCATION)" if action == "off-invocation" else "BẬT TỰ ĐỘNG GỌI (ON-INVOCATION)"
        if include_choice:
            action_title += f" [KHO GỐC + ĐỒNG BỘ {include_choice.upper()}]"
        else:
            action_title += " [KHO LƯU TRỮ GỐC]"

        filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
        print(f"\n{Fore.CYAN}=== {action_title}{filter_tag} ==={Style.RESET_ALL}")
        print(f">>> Đang quét danh sách Skill trong kho lưu trữ ({len(available_skills)} skills):")
        print()

        for idx, s in enumerate(available_skills, 1):
            full_p = os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, s))
            stts = get_invocation_status(full_p)
            print(f"  [{idx:2d}] {s:<42} {stts}")

        print(f"  [ a] Áp dụng cho TẤT CẢ các Skill trên ({len(available_skills)} skills)")
        print()

        user_choice = input("Nhập số thứ tự (vd: 1 hoặc 1 2 4), tên Skill, hoặc 'a' ('q' để hủy): ").strip()
        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Đã hủy thao tác an toàn.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            selected_skill_dirs = [os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, s)) for s in available_skills]
        else:
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                chosen_indices = [int(n) for n in num_tokens]
                for idx in chosen_indices:
                    if 1 <= idx <= len(available_skills):
                        p = os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, available_skills[idx - 1]))
                        if p not in selected_skill_dirs:
                            selected_skill_dirs.append(p)
                    else:
                        print(f"{Fore.YELLOW}⚠️ Bỏ qua số thứ tự ngoài phạm vi: {idx}{Style.RESET_ALL}")
                if not selected_skill_dirs:
                    print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                found_dir = find_skill_folder(SKILLS_FOLDER_PATH, user_choice)
                if not found_dir:
                    print(f"{Fore.RED}❌ Lỗi: Không tìm thấy Skill '{user_choice}' hợp lệ trong {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
                    sys.exit(1)
                selected_skill_dirs = [found_dir]

    print(f"\n🔄 Bắt đầu xử lý {len(selected_skill_dirs)} Skill trong kho lưu trữ...")
    success_skills = []
    error_count = 0

    for skill_dir in selected_skill_dirs:
        skill_base_name = os.path.basename(skill_dir)
        skill_md_file = get_skill_md_path(skill_dir)

        if not skill_md_file:
            print(f"\n{Fore.RED}❌ [THIẾU FILE] Không tìm thấy file SKILL.md trong: {skill_dir}{Style.RESET_ALL}")
            error_count += 1
            continue

        ok = apply_action_to_file(action, skill_md_file, f"Kho gốc / {skill_base_name}")
        if ok:
            success_skills.append(skill_dir)
        else:
            error_count += 1

    # Nếu truyền --include-agent: Tiến hành đồng bộ sang các AI Agent
    if include_choice and success_skills:
        targets = resolve_targets(include_choice)
        target_labels = ", ".join([label for label, _ in targets])
        print(f"\n🚀 Đang đồng bộ {len(success_skills)} Skill vào các AI Agent ({target_labels})...")
        overwrite_all = force_overwrite
        deploy_count = 0
        total_deploys = len(success_skills) * len(targets)

        for src_skill_path in success_skills:
            for agent_label, dest_folder in targets:
                ok, overwrite_all = deploy_skill(src_skill_path, dest_folder, agent_label, overwrite_all)
                if ok:
                    deploy_count += 1

        print(f"\n{Fore.GREEN}🎉 Đồng bộ hoàn tất: Đã cập nhật thành công {deploy_count}/{total_deploys} lượt vào các AI Agent.{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}✔ Hoàn tất xử lý: {len(success_skills)}/{len(selected_skill_dirs)} skill thành công trong kho.{Style.RESET_ALL}")
    if error_count > 0:
        print(f"{Fore.YELLOW}⚠️ Có {error_count} skill gặp lỗi format YAML và bị bỏ qua.{Style.RESET_ALL}\n")


def main():
    try:
        action, skill_name_input, ai_choice, include_choice, filter_choice, force_overwrite, is_project_mode, project_root = parse_cli_args()

        if is_project_mode:
            # Case 4: Project mode (--project / --prj / -p)
            execute_project_mode(action, skill_name_input, project_root, filter_choice)
        elif ai_choice is not None:
            # Case 1: Agent-Only mode
            execute_agent_only_mode(action, skill_name_input, ai_choice, filter_choice)
        else:
            # Case 2 & 3: Repo mode (Repo-only hoặc Include-agent)
            execute_repo_mode(action, skill_name_input, include_choice, force_overwrite, filter_choice)

    except KeyboardInterrupt:
        print("\n\n>>> Đã hủy thao tác (Ctrl+C).")
        sys.exit(0)


if __name__ == "__main__":
    main()
