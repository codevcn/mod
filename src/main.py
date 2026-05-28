import os
import subprocess
import sys
from pathlib import Path
from configs.paths import PROJECT_ROOT, FEATURES_FOLDER, TEMPLATE_REPLACER_FOLDER

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- Status ---
MOD_STATUS = "OK"

# --- Types ---
MOD_TYPE_OPEN = "open"
MOD_TYPE_CODE = "code"
MOD_TYPE_RUN = "run"
MOD_TYPE_PRINT = "print"
MOD_TYPE_GIT = "git"
MOD_TYPE_GDRIVE = "gdrive"
MOD_TYPE_INIT = "init"
MOD_TYPE_PY = "py"
MOD_TYPE_EDIT = "edit"
MOD_TYPE_FILE = "file"
MOD_TYPE_FOLDER = "folder"

# --- Actions ---
# open
MOD_OPEN_ENV = "env"
MOD_OPEN_PROMPTS_FOLDER = "proms"
# code
MOD_CODE_VSCODE_WORKSPACE = "ws"
MOD_CODE_TEST = "test"
MOD_CODE_TYPESCRIPT_TEMPLATE = "ts-template"
MOD_CODE_JS = "js"
MOD_CODE_TS = "ts"
MOD_CODE_NESTJS = "nestjs"
MOD_CODE_PY = "py"
MOD_CODE_EXTENSIONS = "ext"
# run
MOD_RUN_UNIKEY_APP = "unikey"
MOD_GEN_QR_IMAGE = "gen-qr"
MOD_KEEP_AWAKE = "keep-awake"
MOD_SRT_COUNT_LINE = "srt-count-line"
# file
MOD_FILE_CREATE = "create"
MOD_FILE_RENAME = "rename"
MOD_FILE_DELETE = "delete"
MOD_FILE_KEEP = "keep"
# folder
MOD_FOLDER_CREATE = "create"
MOD_FOLDER_DLD_PATH = "dld-path"
# edit
MOD_EDIT_PROMPTS = "proms"
MOD_EDIT_TO_COMMAND = "to"
# git
MOD_GIT_COMMIT_AND_PUSH = "commit"
# print
MOD_PRINT_OS_INFO = "os"
MOD_PRINT_STATUSES_INFO = "stts"
MOD_PRINT_VSCODE_WORKSPACES = "ws"
MOD_PRINT_CURL = "curl"
MOD_PRINT_DIRECTORY = "dir"
MOD_PRINT_USEFUL_COMMANDS = "cmds"
# py
MOD_PY_ENV = "env"

MOD_WARNING_TYPE_WRONG = "WRONG-TYPE"
MOD_WARNING_TYPE_MISSING = "MISSING-TYPE"
MOD_WARNING_ACTION_WRONG = "WRONG-ACTION"
MOD_WARNING_ACTION_MISSING = "MISSING-ACTION"

MOD_SRC_FOLDER = Path(__file__).resolve().parent
MOD_ROOT_FOLDER = PROJECT_ROOT
MOD_FEATURES_FOLDER_PATH = FEATURES_FOLDER
MOD_SYSTEM_FEATURES_FOLDER_PATH = str(Path(MOD_FEATURES_FOLDER_PATH) / "system")

TEMPLATE_REPLACER_FOLDER_PATH = TEMPLATE_REPLACER_FOLDER

# --- Functions ---


def get_feature_path(*parts: str) -> str:
    return str(Path(MOD_FEATURES_FOLDER_PATH, *parts))


def get_system_feature_path(filename: str) -> str:
    return str(Path(MOD_SYSTEM_FEATURES_FOLDER_PATH, filename))


def gdrive_execute(action, remaining_args):
    cmd_args = [
        "python",
        get_feature_path("sync-to-gdrive", "sync_to_gdrive.py"),
    ]
    if action is not None:
        cmd_args.append(action)
    cmd_args.extend(remaining_args)

    subprocess.run(
        cmd_args,
        check=True,
        shell=True,
    )
    sys.exit(0)


def print_content(content_filename):
    subprocess.run(
        [
            "python",
            get_system_feature_path("_print_content.py"),
            content_filename,
        ],
        check=True,
        shell=True,
    )
    sys.exit(0)


def open_vscode_extensions_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Browser-Extensions"], shell=True)
    sys.exit(0)


def warn_user_error(warning_message: str):
    messages = {
        MOD_WARNING_TYPE_WRONG: {
            "title": "Sai nhóm lệnh",
            "reason": "Type bạn nhập không tồn tại trong danh sách lệnh hỗ trợ.",
            "suggestion": "Chạy `mod --help` để xem danh sách type hợp lệ.",
        },
        MOD_WARNING_TYPE_MISSING: {
            "title": "Thiếu nhóm lệnh",
            "reason": "Bạn chưa nhập type của command.",
            "suggestion": "Ví dụ: `mod run keep-awake <healthcheck_url>`",
        },
        MOD_WARNING_ACTION_WRONG: {
            "title": "Sai action",
            "reason": "Action bạn nhập không hợp lệ với type hiện tại.",
            "suggestion": "Chạy `mod --help` hoặc `mod <type> <action> --des` để xem mô tả.",
        },
        MOD_WARNING_ACTION_MISSING: {
            "title": "Thiếu action",
            "reason": "Type này cần thêm action phía sau.",
            "suggestion": "Ví dụ: `mod run keep-awake <healthcheck_url>`",
        },
    }

    info = messages.get(warning_message)

    print()
    print("=" * 70)

    if info:
        print(f"❌ {info['title']}")
        print("-" * 70)
        print(f"Nguyên nhân : {info['reason']}")
        print(f"Gợi ý      : {info['suggestion']}")
    else:
        print("❌ Lỗi không xác định")
        print("-" * 70)
        print(f"Chi tiết   : {warning_message}")

    print("=" * 70)
    print()

    sys.exit(1)


def open_testing_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Testing"], shell=True)
    sys.exit(0)


def print_mod_files_root_dir():
    print(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(0)


def print_useful_commands():
    print_content("list_useful_commands.txt")


def run_git_command(git_type, remaining_args):
    cmd_args = [
        "python",
        get_system_feature_path("_git.py"),
        git_type,
    ]
    cmd_args.extend(remaining_args)
    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


def open_mod_file_in_system_folder():
    # Lấy đường dẫn, nếu MOD_ROOT_FOLDER không tồn tại thì lấy thư mục chứa file main.py hiện tại
    folder_path = (
        MOD_ROOT_FOLDER
        if MOD_ROOT_FOLDER
        else os.path.dirname(os.path.abspath(__file__))
    )

    # Sử dụng os.startfile (cách chuẩn nhất trên Windows để mở thư mục/file bằng app mặc định)
    if hasattr(os, "startfile"):
        os.startfile(folder_path)
    else:
        # Dự phòng gọi thẳng explorer
        subprocess.run(["explorer", os.path.normpath(folder_path)])

    sys.exit(0)


def print_statuses_info():
    subprocess.run(
        ["python", get_system_feature_path("_statuses.py")],
        check=True,
        shell=True,
    )
    sys.exit(0)


def print_help():
    print_content("help.txt")


def print_cURL():
    subprocess.run(
        ["python", get_feature_path("print_cURL.py")],
        check=True,
        shell=True,
    )
    sys.exit(0)


def open_environment_variables_panel():
    subprocess.run(["rundll32.exe", "sysdm.cpl,EditEnvironmentVariables"], shell=True)
    sys.exit(0)


def open_prompts_folder():
    subprocess.run(["start", f"{TEMPLATE_REPLACER_FOLDER_PATH}/Prompts"], shell=True)
    sys.exit(0)


def open_vscode_workspaces_in_system_folder():
    subprocess.run(["start", "D:/D-Documents/VSCode-Workspaces"], shell=True)
    sys.exit(0)


def open_working_vscode(ide_prefix: str, remaining_args: list[str]):
    if not ide_prefix:
        raise Exception("IDE prefix is missing.")
    cmd_args = [
        "python",
        get_feature_path("open_main_ws.py"),
        ide_prefix,
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(
        cmd_args,
        check=True,
        shell=True,
    )
    sys.exit(0)


def print_vscode_workspaces(workspace_path):
    subprocess.run(
        [
            "python",
            get_system_feature_path("_print_root_folder.py"),
            workspace_path,
        ],
        check=True,
    )
    sys.exit(0)


def open_mod_files_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, f"{MOD_ROOT_FOLDER}"], shell=True)
    sys.exit(0)


def open_template_nestjs_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Code_VCN/nestjs"], shell=True)
    sys.exit(0)


def print_os_info():
    subprocess.run(
        ["python", get_feature_path("print_os_info.py")],
        check=True,
        shell=True,
    )
    sys.exit(0)


def run_Unikey_app():
    subprocess.run(["start", "C:/Users/dell/Downloads/UniKeyNT.exe"], shell=True)
    sys.exit(0)


def open_typescript_template_in_cursor(ide_prefix):
    subprocess.run(
        [ide_prefix, "D:/D-Documents/Templates/standard-express-server-ts"], shell=True
    )
    sys.exit(0)


def open_testing_javascript_typescript_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Testing/js-ts"], shell=True)
    sys.exit(0)


def open_testing_python_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Testing/py"], shell=True)
    sys.exit(0)


def create_files_in_folder():
    subprocess.run(
        ["py", get_feature_path("create_files_in_folder.py")],
        shell=True,
    )
    sys.exit(0)


def set_download_path_in_chrome(remaining_args: list[str]):
    cmd_args = [
        "py",
        get_feature_path("set_download_path_in_chrome.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def create_folders_in_path(remaining_args: list[str]):
    cmd_args = [
        "py",
        get_feature_path("create_folders_in_path.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def edit_prompts():
    subprocess.run(
        [f"{TEMPLATE_REPLACER_FOLDER_PATH}/edit-prompts.cmd"],
        shell=True,
    )
    sys.exit(0)


def rename_files(remaining_args: list[str]):
    cmd_args = [
        "py",
        get_feature_path("rename_files.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def delete_files(remaining_args: list[str]):
    cmd_args = [
        "py",
        get_feature_path("delete_files.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def keep_files(remaining_args: list[str]):
    cmd_args = [
        "py",
        get_feature_path("keep_files_with_ext.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def print_feature_description(cmd_type: str | None, action: str | None):
    cmd_args = [
        "python",
        get_system_feature_path("_print_feature_description.py"),
    ]
    if cmd_type:
        cmd_args.extend(["--type", cmd_type])
    if action:
        cmd_args.extend(["--action", action])

    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def cmd_init():
    subprocess.run(
        [f"{MOD_ROOT_FOLDER}/src/cmd/init.cmd"],
        shell=True,
    )
    sys.exit(0)


def py_setup_venv():
    cmd_args = [
        "python",
        get_feature_path("setup_venv_in_project.py"),
    ]

    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def edit_to_command():
    cmd_args = [
        "python",
        get_feature_path("edit_to_command.py"),
    ]
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def gen_qr_image():
    cmd_args = [
        "python",
        get_feature_path("gen_qr_image.py"),
    ]
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def keep_server_awake(remaining_args):
    cmd_args = [
        "python",
        get_feature_path("keep_server_awake.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def srt_count_lines(remaining_args):
    cmd_args = [
        "python",
        get_feature_path("srt_count_line.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


# --- Main ---

if __name__ == "__main__":
    try:
        raw_args = sys.argv[1:]

        # --- Tách dispatcher flags (chỉ giữ --des và -a) ---
        des_flag = False
        antigravity_flag = False
        feature_args = []

        for arg in raw_args:
            if arg == "--des":
                des_flag = True
            elif arg in ("-a", "--antigravity-IDE"):
                antigravity_flag = True
            else:
                feature_args.append(arg)

        # --- Tách type / action / remaining ---
        type_included = feature_args[0] if len(feature_args) > 0 else None
        action_included = feature_args[1] if len(feature_args) > 1 else None
        remaining_args = feature_args[2:]

        # --- Help: mod | mod -h | mod --help ---
        if type_included is None or type_included in ("-h", "--help"):
            print_help()

        # --- Feature description: mod <type> <action> --des ---
        if des_flag:
            print_feature_description(type_included, action_included)

        # --- IDE prefix ---
        default_ide_prefix: str = "anti" if antigravity_flag else "code"

        # --- Dispatch ---
        if type_included == MOD_TYPE_EDIT:
            if action_included == MOD_EDIT_PROMPTS:
                edit_prompts()
            elif action_included == MOD_EDIT_TO_COMMAND:
                edit_to_command()
            else:
                raise Exception(MOD_WARNING_ACTION_MISSING)
        elif type_included == MOD_TYPE_PY:
            if action_included == MOD_PY_ENV:
                py_setup_venv()
            else:
                raise Exception(MOD_WARNING_ACTION_MISSING)
        elif type_included == MOD_TYPE_INIT:
            cmd_init()
        elif type_included == MOD_TYPE_GDRIVE:
            gdrive_execute(action_included, remaining_args)
        elif type_included == MOD_TYPE_CODE:
            if action_included is None:
                open_mod_files_in_vscode(default_ide_prefix)
            elif action_included == MOD_CODE_VSCODE_WORKSPACE:
                open_working_vscode(default_ide_prefix, remaining_args)
            elif action_included == MOD_CODE_TEST:
                open_testing_folder_in_vscode(default_ide_prefix)
            elif action_included == MOD_CODE_TYPESCRIPT_TEMPLATE:
                open_typescript_template_in_cursor(default_ide_prefix)
            elif action_included in (MOD_CODE_JS, MOD_CODE_TS):
                open_testing_javascript_typescript_folder_in_vscode(default_ide_prefix)
            elif action_included == MOD_CODE_NESTJS:
                open_template_nestjs_folder_in_vscode(default_ide_prefix)
            elif action_included == MOD_CODE_PY:
                open_testing_python_folder_in_vscode(default_ide_prefix)
            elif action_included == MOD_CODE_EXTENSIONS:
                open_vscode_extensions_in_vscode(default_ide_prefix)
            else:
                raise Exception(MOD_WARNING_ACTION_WRONG)
        elif type_included == MOD_TYPE_GIT:
            if not action_included:
                raise Exception(MOD_WARNING_ACTION_MISSING)
            run_git_command(action_included, remaining_args)
        elif type_included == MOD_TYPE_RUN:
            if action_included == MOD_RUN_UNIKEY_APP:
                run_Unikey_app()
            elif action_included == MOD_GEN_QR_IMAGE:
                gen_qr_image()
            elif action_included == MOD_KEEP_AWAKE:
                keep_server_awake(remaining_args)
            elif action_included == MOD_SRT_COUNT_LINE:
                srt_count_lines(remaining_args)
            elif action_included is None:
                raise Exception(MOD_WARNING_ACTION_MISSING)
            else:
                raise Exception(MOD_WARNING_ACTION_WRONG)
        elif type_included == MOD_TYPE_FILE:
            if action_included == MOD_FILE_CREATE:
                create_files_in_folder()
            elif action_included == MOD_FILE_RENAME:
                rename_files(remaining_args)
            elif action_included == MOD_FILE_DELETE:
                delete_files(remaining_args)
            elif action_included == MOD_FILE_KEEP:
                keep_files(remaining_args)
            elif action_included is None:
                raise Exception(MOD_WARNING_ACTION_MISSING)
            else:
                raise Exception(MOD_WARNING_ACTION_WRONG)
        elif type_included == MOD_TYPE_FOLDER:
            if action_included == MOD_FOLDER_CREATE:
                create_folders_in_path(remaining_args)
            elif action_included == MOD_FOLDER_DLD_PATH:
                set_download_path_in_chrome(remaining_args)
            elif action_included is None:
                raise Exception(MOD_WARNING_ACTION_MISSING)
            else:
                raise Exception(MOD_WARNING_ACTION_WRONG)
        elif type_included == MOD_TYPE_OPEN:
            # Gom action + remaining để detect flag -f/--file
            all_open_args = (
                [action_included] if action_included else []
            ) + remaining_args
            has_file_flag = "-f" in all_open_args or "--file" in all_open_args
            clean_action = (
                action_included
                if action_included not in ("-f", "--file", None)
                else None
            )

            if clean_action is None:
                if has_file_flag:
                    open_mod_file_in_system_folder()
                else:
                    open_mod_files_in_vscode(default_ide_prefix)
            elif clean_action == MOD_OPEN_ENV:
                open_environment_variables_panel()
            elif clean_action == MOD_OPEN_PROMPTS_FOLDER:
                open_prompts_folder()
            elif clean_action == MOD_CODE_VSCODE_WORKSPACE:
                open_vscode_workspaces_in_system_folder()
            else:
                raise Exception(MOD_WARNING_ACTION_WRONG)
        elif type_included == MOD_TYPE_PRINT:
            if action_included == MOD_PRINT_OS_INFO:
                print_os_info()
            elif action_included == MOD_PRINT_VSCODE_WORKSPACES:
                print_vscode_workspaces("D:/D-Documents/VSCode-Workspaces")
            elif action_included == MOD_PRINT_DIRECTORY:
                print_mod_files_root_dir()
            elif action_included == MOD_PRINT_USEFUL_COMMANDS:
                print_useful_commands()
            elif action_included == MOD_PRINT_CURL:
                print_cURL()
            elif action_included == MOD_PRINT_STATUSES_INFO:
                print_statuses_info()
            elif action_included is None:
                raise Exception(MOD_WARNING_ACTION_MISSING)
            else:
                raise Exception(MOD_WARNING_ACTION_WRONG)
        else:
            raise Exception(MOD_WARNING_TYPE_WRONG)

        # Nếu chạy đến đây (không rẽ nhánh nào) thì báo lỗi.
        MOD_STATUS = "OUT-OF-MAIN-SECTION"
        print(">>> These commands end up with mod-status: " + MOD_STATUS)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
    except Exception as e:
        warn_user_error(str(e))
        sys.exit(1)
