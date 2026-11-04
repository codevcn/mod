import os
import re
import sys
import yaml
import shutil
from pathlib import Path
from colorama import init, Fore, Style

# Set UTF-8 encoding for console output on Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

init(autoreset=True)

# Add project root to sys.path to import configs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import (
    SKILLS_FOLDER_PATH,
    ANTIGRAVITY_SKILLS_PATH,
    CODEX_SKILLS_PATH,
    CLAUDE_SKILLS_PATH,
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


def has_direct_skill_file(folder_path: str) -> bool:
    """Kiểm tra một thư mục có chứa file con trực tiếp là SKILL.md không."""
    if not os.path.isdir(folder_path):
        return False
    try:
        return any(
            f.lower() == "skill.md" and os.path.isfile(os.path.join(folder_path, f))
            for f in os.listdir(folder_path)
        )
    except Exception:
        return False


def get_skill_invocation_state(skill_dir: str) -> str:
    """
    Trả về 'off-invocation' nếu có disable-model-invocation: true trong YAML frontmatter,
    ngược lại trả về 'on-invocation'.
    """
    if not os.path.isdir(skill_dir):
        return "on-invocation"
    try:
        for fname in os.listdir(skill_dir):
            if fname.lower() == "skill.md":
                cand = os.path.join(skill_dir, fname)
                if os.path.isfile(cand):
                    with open(cand, "r", encoding="utf-8") as f:
                        raw = f.read().lstrip("\ufeff")
                    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", raw, re.DOTALL)
                    if m:
                        data = yaml.safe_load(m.group(1))
                        if isinstance(data, dict) and data.get("disable-model-invocation") is True:
                            return "off-invocation"
                    break
    except Exception:
        pass
    return "on-invocation"


def parse_filter_arg(val: str) -> str | None:
    """Chuẩn hóa giá trị filter thành 'on-invocation' hoặc 'off-invocation'."""
    clean = val.strip().lower()
    if clean in ("on-invocation", "on"):
        return "on-invocation"
    if clean in ("off-invocation", "off"):
        return "off-invocation"
    return None


def list_skill_folders(base_path: str) -> list[str]:
    """
    Chỉ liệt kê các folder nào có file con trực tiếp là SKILL.md.
    Các folder cha phân loại hoặc folder con bên trong skill sẽ không được liệt kê.
    """
    skill_folders = []
    ignore_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".vscode", "dist", "build"}
    base_path = os.path.abspath(base_path)
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        if root == base_path:
            continue
        # Chỉ nhận folder có file con trực tiếp là SKILL.md
        if any(f.lower() == "skill.md" and os.path.isfile(os.path.join(root, f)) for f in files):
            rel_path = os.path.relpath(root, base_path)
            skill_folders.append(rel_path.replace("\\", "/"))
            # Khi đã xác định là 1 skill, không duyệt sâu vào các thư mục con bên trong nó
            dirs[:] = []
    return sorted(skill_folders)


def find_skill_folder(base_path: str, target_name: str) -> str | None:
    """
    Tìm đường dẫn tuyệt đối của thư mục skill hợp lệ (có file con trực tiếp là SKILL.md).
    Hỗ trợ tìm theo:
    1. Đường dẫn tương đối chính xác (vd: my-skill/chatgpt-web-interaction)
    2. Tên thư mục skill (basename, vd: chatgpt-web-interaction)
    """
    target_clean = target_name.strip().replace("\\", "/").strip("/")
    base_path = os.path.abspath(base_path)

    # 1. Thử tìm trực tiếp nếu target_name là đường dẫn tương đối
    direct_path = os.path.normpath(os.path.join(base_path, target_clean))
    if has_direct_skill_file(direct_path):
        return direct_path

    # 2. Quét toàn bộ danh sách skill hợp lệ trong base_path
    skills = list_skill_folders(base_path)

    # 2.1 Khớp tương đối (case-insensitive)
    for s in skills:
        if s.lower() == target_clean.lower():
            return os.path.normpath(os.path.join(base_path, s))

    # 2.2 Khớp theo tên folder cuối (basename) (case-insensitive)
    for s in skills:
        if os.path.basename(s).lower() == target_clean.lower():
            return os.path.normpath(os.path.join(base_path, s))

    return None


def deploy_skill(src_path: str, dest_folder_path: str, agent_label: str = None, overwrite_all: bool = False) -> tuple[bool, bool]:
    """
    Sao chép thư mục skill vào thư mục đích, xử lý việc tạo folder và xác nhận ghi đè.
    Trả về: (thành công: bool, overwrite_all: bool)
    """
    dest_folder_path = os.path.abspath(dest_folder_path)

    if not os.path.exists(dest_folder_path):
        target_name = agent_label if agent_label else dest_folder_path
        print(f"\n{Fore.YELLOW}⚠️ Thư mục đích ({target_name}) chưa tồn tại:{Style.RESET_ALL} {dest_folder_path}")
        ans = input("Bạn có muốn tạo thư mục này không? [y/n]: ").strip().lower()
        if ans != "y":
            print(f">>> Bỏ qua đích: {dest_folder_path}")
            return False, overwrite_all
        try:
            os.makedirs(dest_folder_path, exist_ok=True)
            print(f"{Fore.GREEN}✅ Đã tạo thành công thư mục:{Style.RESET_ALL} {dest_folder_path}")
        except Exception as e:
            print(f"{Fore.RED}❌ Lỗi khi tạo thư mục đích:{Style.RESET_ALL} {e}")
            return False, overwrite_all

    skill_dirname = os.path.basename(os.path.normpath(src_path))
    dest_path = os.path.join(dest_folder_path, skill_dirname)

    if os.path.exists(dest_path):
        if not overwrite_all:
            target_info = f" cho {agent_label}" if agent_label else ""
            print(f"\n{Fore.YELLOW}⚠️ Skill '{skill_dirname}'{target_info} đã tồn tại tại:{Style.RESET_ALL} {dest_path}")
            ans = input("Bạn có muốn ghi đè không? [y/n/a (tất cả)]: ").strip().lower()
            if ans == "a":
                overwrite_all = True
            elif ans != "y":
                print(f">>> Bỏ qua {dest_path}.")
                return False, overwrite_all
        try:
            shutil.rmtree(dest_path)
        except Exception as e:
            print(f"{Fore.RED}❌ Lỗi khi xóa thư mục cũ:{Style.RESET_ALL} {e}")
            return False, overwrite_all

    header = f" vào {agent_label}" if agent_label else ""
    print(f"\n>>> Đang sao chép Skill '{skill_dirname}'{header}...")
    print(f"    Nguồn: {src_path}")
    print(f"    Đích : {dest_path}")

    try:
        shutil.copytree(src_path, dest_path)
        print(f"{Fore.GREEN}✅ Cài đặt thành công Skill '{skill_dirname}'{header}!{Style.RESET_ALL}")
        return True, overwrite_all
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi trong quá trình sao chép:{Style.RESET_ALL} {e}")
        return False, overwrite_all


def resolve_project_agents_skills_dir(project_path: str) -> tuple[str, str]:
    """
    Xác định thư mục đặt skill theo chuẩn AI coding agent trong project:
    - Nếu đã tồn tại thư mục `<project>/.agent/skills`: dùng `<project>/.agent/skills` (label: "Project (.agent/skills)")
    - Ngược lại: dùng `<project>/.agents/skills` (label: "Project (.agents/skills)")
    """
    abs_project = os.path.abspath(project_path)
    if not os.path.isdir(abs_project):
        print(f"{Fore.RED}❌ Lỗi: Thư mục dự án không tồn tại: {abs_project}{Style.RESET_ALL}")
        sys.exit(1)

    agent_singular = os.path.join(abs_project, ".agent", "skills")
    agents_plural = os.path.join(abs_project, ".agents", "skills")

    if os.path.isdir(agent_singular) and not os.path.isdir(agents_plural):
        return agent_singular, "Project (.agent/skills)"
    return agents_plural, "Project (.agents/skills)"


def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() not in ("set", "project", "prj", "p"):
        print(f"{Fore.RED}>>> Lỗi: Lệnh không hợp lệ.{Style.RESET_ALL}")
        sys.exit(1)

    action_raw = sys.argv[1].lower()
    is_project_mode = action_raw in ("project", "prj", "p")
    project_root = None
    ai_choice = None
    filter_choice = None
    positional_args = []

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("--ai", "--llm", "--agent"):
            if i + 1 < len(sys.argv):
                ai_choice = sys.argv[i + 1].strip().lower()
                i += 2
            else:
                print(f"{Fore.RED}❌ Lỗi: Thiếu tên AI/Agent sau cờ {arg}. (Ví dụ: --agent agy, --ai claude, --llm codex){Style.RESET_ALL}")
                sys.exit(1)
        elif arg.startswith(("--ai=", "--llm=", "--agent=")):
            ai_choice = arg.split("=", 1)[1].strip().lower()
            i += 1
        elif arg in ("--project", "--prj", "-p"):
            is_project_mode = True
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
                project_root = sys.argv[i + 1]
                i += 2
            else:
                project_root = "."
                i += 1
        elif arg.startswith(("--project=", "--prj=")):
            is_project_mode = True
            project_root = arg.split("=", 1)[1]
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
        else:
            positional_args.append(arg)
            i += 1

    # Kiểm tra kho SKILLS_FOLDER_PATH
    if not os.path.exists(SKILLS_FOLDER_PATH):
        print(f"{Fore.YELLOW}>>> Cảnh báo: Thư mục kho lưu trữ SKILLs `{SKILLS_FOLDER_PATH}` chưa tồn tại.{Style.RESET_ALL}")
        ans = input("Bạn có muốn tạo thư mục này không? [y/n]: ").strip().lower()
        if ans == "y":
            os.makedirs(SKILLS_FOLDER_PATH, exist_ok=True)
            print(f"{Fore.GREEN}>>> Đã tạo thư mục kho lưu trữ: {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
            print(f">>> Vui lòng thêm các thư mục SKILL vào `{SKILLS_FOLDER_PATH}` và thử lại.")
        sys.exit(0)

    # Xác định danh sách target directories
    targets = []
    if is_project_mode:
        if ai_choice is not None:
            print(f"{Fore.RED}❌ Lỗi: Không thể dùng đồng thời cờ --agent (Global AI Agent) và --project (Project Local). Vui lòng chọn 1 trong 2.{Style.RESET_ALL}")
            sys.exit(1)

        if project_root is None:
            if len(positional_args) >= 2:
                skill_folder_name = positional_args[0]
                project_root = positional_args[1]
            elif len(positional_args) == 1:
                cand = positional_args[0]
                if cand.startswith((".", "/", "\\")) or ":" in cand:
                    project_root = cand
                    skill_folder_name = None
                else:
                    skill_folder_name = cand
                    project_root = "."
            else:
                skill_folder_name = None
                project_root = "."
        else:
            skill_folder_name = positional_args[0] if len(positional_args) > 0 else None

        dest_dir, agent_label = resolve_project_agents_skills_dir(project_root)
        targets = [(agent_label, dest_dir)]

    elif ai_choice is not None:
        if ai_choice == "all":
            targets = [
                ("Google Antigravity", ANTIGRAVITY_SKILLS_PATH),
                ("OpenAI Codex", CODEX_SKILLS_PATH),
                ("Claude Code", CLAUDE_SKILLS_PATH),
            ]
        elif ai_choice in LLM_TARGETS:
            targets = [LLM_TARGETS[ai_choice]]
        else:
            print(f"{Fore.RED}❌ Lỗi: Tên AI/LLM '{ai_choice}' không hợp lệ.{Style.RESET_ALL}")
            print("Các lựa chọn hợp lệ:")
            print("  - agy (antigravity, gemini, anti) : Google Antigravity (~/.gemini/config/skills)")
            print("  - codex (openai)                  : OpenAI Codex (~/.codex/skills)")
            print("  - claude (clau, anthropic)        : Claude Code (~/.claude/skills)")
            print("  - all                             : Cài đặt vào tất cả các AI Agent trên")
            sys.exit(1)

        skill_folder_name = positional_args[0] if len(positional_args) > 0 else None
    else:
        skill_folder_name = positional_args[0] if len(positional_args) > 0 else None
        dest_folder_path = positional_args[1] if len(positional_args) > 1 else "."

        # UX Improvement: Nếu user chỉ truyền 1 arg dạng path (vd: ./path, D:/path), coi như đó là dest_folder_path
        if skill_folder_name and len(positional_args) == 1:
            if skill_folder_name.startswith((".", "/", "\\")) or ":" in skill_folder_name:
                dest_folder_path = skill_folder_name
                skill_folder_name = None

        targets = [(None, dest_folder_path)]

    # Quét danh sách skills có sẵn trong kho
    folders = list_skill_folders(SKILLS_FOLDER_PATH)
    if not folders:
        print(f"{Fore.YELLOW}>>> Không tìm thấy thư mục SKILL nào có chứa file SKILL.md trong {SKILLS_FOLDER_PATH}.{Style.RESET_ALL}")
        sys.exit(0)

    # Áp dụng bộ lọc --filter nếu có
    if filter_choice:
        filtered_folders = [f for f in folders if get_skill_invocation_state(os.path.join(SKILLS_FOLDER_PATH, f)) == filter_choice]
        if not filtered_folders:
            lbl = "BẬT" if filter_choice == "on-invocation" else "TẮT"
            print(f"\n{Fore.YELLOW}ℹ️ Không tìm thấy Skill nào trong kho khớp với bộ lọc '--filter {filter_choice}' (không có skill nào đang {lbl}).{Style.RESET_ALL}")
            sys.exit(0)
        folders = filtered_folders

    selected_src_paths = []

    # Xác định danh sách skill cần cài đặt
    if skill_folder_name:
        if skill_folder_name.lower() in ("all", "*"):
            selected_src_paths = [os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, f)) for f in folders]
        else:
            src_path = find_skill_folder(SKILLS_FOLDER_PATH, skill_folder_name)
            if not src_path:
                print(f"{Fore.RED}>>> Lỗi: Không tìm thấy Skill '{skill_folder_name}' hợp lệ (chứa SKILL.md) trong {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
                sys.exit(1)
            # Kiểm tra xem skill này có thỏa mãn filter không
            if filter_choice:
                state = get_skill_invocation_state(src_path)
                if state != filter_choice:
                    lbl_cur = "TẮT" if state == "off-invocation" else "BẬT"
                    lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                    print(f"\n{Fore.YELLOW}⚠️ Bỏ qua Skill '{skill_folder_name}' vì trạng thái hiện tại ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                    sys.exit(0)
            selected_src_paths = [src_path]
    else:
        # Chế độ tương tác: Hiển thị danh sách đánh số trực quan
        filter_tag = f" {Fore.CYAN}[Đã lọc: --filter {filter_choice}]{Style.RESET_ALL}" if filter_choice else ""
        print(f">>> Đang quét thư mục SKILLs...{filter_tag}")
        print("\nDanh sách các thư mục SKILL có sẵn:")
        for idx, f in enumerate(folders, 1):
            st = get_skill_invocation_state(os.path.join(SKILLS_FOLDER_PATH, f))
            st_lbl = f"{Fore.GREEN}[BẬT]{Style.RESET_ALL}" if st == "on-invocation" else f"{Fore.YELLOW}[TẮT]{Style.RESET_ALL}"
            print(f"  [{idx:2d}] {f:<42} {st_lbl}")
        print(f"  [ a] Cài đặt TẤT CẢ các Skill trên ({len(folders)} skills)")
        print()

        prompt_msg = (
            f"Nhập số thứ tự (vd: 1 hoặc 1 2 3), tên Skill, hoặc 'a' để cài tất cả ('q' để hủy): "
        )
        user_choice = input(prompt_msg).strip()

        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Hủy thao tác.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            selected_src_paths = [os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, f)) for f in folders]
        else:
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens and not re.sub(r"[\d\s,]", "", user_choice):
                chosen_indices = [int(n) for n in num_tokens]
                for idx in chosen_indices:
                    if 1 <= idx <= len(folders):
                        p = os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, folders[idx - 1]))
                        if p not in selected_src_paths:
                            selected_src_paths.append(p)
                    else:
                        print(f"{Fore.YELLOW}⚠️ Bỏ qua số thứ tự ngoài phạm vi: {idx}{Style.RESET_ALL}")
                if not selected_src_paths:
                    print(f"{Fore.RED}❌ Lỗi: Không có số thứ tự nào hợp lệ.{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                # Tìm theo tên do người dùng gõ
                src_path = find_skill_folder(SKILLS_FOLDER_PATH, user_choice)
                if not src_path:
                    print(f"{Fore.RED}>>> Lỗi: Không tìm thấy Skill '{user_choice}' hợp lệ trong {SKILLS_FOLDER_PATH}{Style.RESET_ALL}")
                    sys.exit(1)
                if filter_choice:
                    state = get_skill_invocation_state(src_path)
                    if state != filter_choice:
                        lbl_cur = "TẮT" if state == "off-invocation" else "BẬT"
                        lbl_req = "BẬT" if filter_choice == "on-invocation" else "TẮT"
                        print(f"\n{Fore.YELLOW}⚠️ Bỏ qua Skill '{user_choice}' vì trạng thái hiện tại ({lbl_cur}) không khớp với bộ lọc (--filter {filter_choice} - yêu cầu {lbl_req}).{Style.RESET_ALL}")
                        sys.exit(0)
                selected_src_paths = [src_path]

    # Thực hiện cài đặt
    overwrite_all = False
    total_deploys = len(selected_src_paths) * len(targets)
    success_count = 0

    target_names = ", ".join([label if label else "thư mục chỉ định" for label, _ in targets])
    print(f"\n🚀 Bắt đầu cài đặt {len(selected_src_paths)} Skill vào {target_names}...")

    for src_path in selected_src_paths:
        for agent_label, dest_path in targets:
            ok, overwrite_all = deploy_skill(src_path, dest_path, agent_label, overwrite_all)
            if ok:
                success_count += 1

    if success_count > 0:
        print(f"\n{Fore.GREEN}🎉 Hoàn tất! Đã cài đặt thành công {success_count}/{total_deploys} lượt Skill.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}>>> Không có Skill nào được cài đặt.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
