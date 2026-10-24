import os
import re
import sys
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


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "set":
        print(f"{Fore.RED}>>> Lỗi: Lệnh không hợp lệ.{Style.RESET_ALL}")
        sys.exit(1)

    ai_choice = None
    positional_args = []

    # Parse arguments: hỗ trợ --ai <name>, --llm <name>, --agent <name> (hoặc --ai=..., --llm=..., --agent=...)
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
    if ai_choice is not None:
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
            selected_src_paths = [src_path]
    else:
        # Chế độ tương tác: Hiển thị danh sách đánh số trực quan
        print(">>> Đang quét thư mục SKILLs...")
        print("\nDanh sách các thư mục SKILL có sẵn:")
        for idx, f in enumerate(folders, 1):
            print(f"  [{idx}] {f}")
        print(f"  [a] Cài đặt TẤT CẢ các Skill trên ({len(folders)} skills)")
        print()

        prompt_msg = (
            f"Nhập số thứ tự (vd: 1 hoặc 1 2 3), tên Skill, hoặc 'a' để cài tất cả ('q' để hủy): "
        )
        user_choice = input(prompt_msg).strip()

        # Mặc định: Nếu người dùng không nhập gì (Enter) hoặc nhập 'q'/'quit'/'exit' -> Không cài cho agent nào hết và hủy an toàn
        if not user_choice or user_choice.lower() in ("q", "quit", "exit"):
            print(">>> Hủy thao tác.")
            sys.exit(0)
        elif user_choice.lower() in ("a", "all", "*"):
            selected_src_paths = [os.path.normpath(os.path.join(SKILLS_FOLDER_PATH, f)) for f in folders]
        else:
            # Kiểm tra xem người dùng có nhập số thứ tự không (vd: '1', '1 2 4')
            num_tokens = re.findall(r"\d+", user_choice)
            if num_tokens:
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
