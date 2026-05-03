import argparse
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/mod/.env")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- Static parameters (constants) ---
MOD_STATUS = "OK"
MOD_TYPE_OPEN = "open"
MOD_TYPE_CODE = "code"
MOD_TYPE_RUN = "run"
MOD_TYPE_PRINT = "print"
MOD_TYPE_GIT = "git"
MOD_TYPE_GDRIVE = "gdrive"
MOD_TYPE_INIT = "init"
MOD_TYPE_PY = "py"
MOD_TYPE_EDIT = "edit"

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
MOD_RUN_CREATE_FILES_IN_FOLDER = "cr-files"
MOD_RUN_SET_DOWNLOAD_PATH_IN_CHROME = "dld-path"
MOD_RENAME_FILES = "rn-files"
MOD_DELETE_FILES = "del-files"
MOD_KEEP_FILES = "keep-files"
MOD_GEN_QR_IMAGE = "gen-qr"
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
MOD_ROOT_FOLDER = os.getenv("ROOT_FOLDER_PATH") or str(MOD_SRC_FOLDER.parent)
MOD_FEATURES_FOLDER_PATH = os.getenv("FEATURES_FOLDER_PATH") or str(
    MOD_SRC_FOLDER / "features"
)
MOD_SYSTEM_FEATURES_FOLDER_PATH = str(Path(MOD_FEATURES_FOLDER_PATH) / "system")

TEMPLATE_REPLACER_FOLDER_PATH = os.getenv("TEMPLATE_REPLACER_FOLDER_PATH") or ""

# --- Functions ---


def get_feature_path(*parts: str) -> str:
    return str(Path(MOD_FEATURES_FOLDER_PATH, *parts))


def get_system_feature_path(filename: str) -> str:
    return str(Path(MOD_SYSTEM_FEATURES_FOLDER_PATH, filename))


def gdrive_execute(gdrive_command, *args):
    cmd_args = [
        "python",
        get_feature_path("sync-to-gdrive", "sync_to_gdrive.py"),
    ]
    if gdrive_command is not None:
        cmd_args.append(gdrive_command)
    cmd_args.extend([arg for arg in args if arg is not None])

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
    global MOD_STATUS
    print(">>> Warn: " + warning_message)
    sys.exit(0)


def open_testing_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Testing"], shell=True)
    sys.exit(0)


def print_mod_files_root_dir():
    print(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(0)


def print_useful_commands():
    print_content("list_useful_commands.txt")


def run_git_command(git_type, user_message=None):
    args = [
        "python",
        get_system_feature_path("_git.py"),
        git_type,
    ]
    if user_message:
        args.append(user_message)
    result = subprocess.run(
        args,
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


def open_working_vscode(ide_prefix: str, value: str, powershell_only=False):
    if not ide_prefix:
        raise Exception("IDE prefix is missing.")
    cmd_args = [
        "python",
        get_feature_path("open_main_ws.py"),
        ide_prefix,
    ]
    if value:
        cmd_args.append(value)
    if powershell_only:
        cmd_args.append("-p")
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


def set_download_path_in_chrome(folder_name: str | None = None):
    cmd_args = [
        "py",
        get_feature_path("set_download_path_in_chrome.py"),
    ]
    if folder_name:
        cmd_args.append(folder_name)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def edit_prompts():
    subprocess.run(
        [f"{TEMPLATE_REPLACER_FOLDER_PATH}/edit-prompts.cmd"],
        shell=True,
    )
    sys.exit(0)


def rename_files(folder_path: str | None = None, prefix: str | None = None):
    cmd_args = [
        "py",
        get_feature_path("rename_files.py"),
    ]
    if folder_path:
        cmd_args.append(folder_path)
    if prefix is not None:
        cmd_args.append(prefix)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def delete_files(folder_path: str | None = None, ext_list: str | None = None):
    cmd_args = [
        "py",
        get_feature_path("delete_files.py"),
    ]
    if folder_path:
        cmd_args.append(folder_path)
    if ext_list:
        cmd_args.append(ext_list)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def keep_files(folder_path: str | None = None, ext: str | None = None):
    cmd_args = [
        "py",
        get_feature_path("keep_files_with_ext.py"),
    ]
    if folder_path:
        cmd_args.append(folder_path)
    if ext:
        cmd_args.append(ext)
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


# --- Main ---

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="mod (Python version) - Command line tool for automating tasks."
        )
        parser.add_argument(
            "type", nargs="?", default=None, help="Type (open, code, run, print, git)"
        )
        parser.add_argument(
            "action",
            nargs="?",
            default=None,
            help="Action (e.g. env, ws, test, commit, os, stts, curl, dir, unikey)",
        )
        parser.add_argument(
            "value",
            nargs="?",
            default=None,
            help="Value (e.g. <remote-name> for gdrive set-remote)",
        )
        parser.add_argument(
            "extra",
            nargs="?",
            default=None,
            help="Extra value (e.g. prefix for rn-files)",
        )
        parser.add_argument(
            "-m",
            "--message",
            default=None,
            dest="user_message",
            help="User message (for git commit)",
        )
        parser.add_argument(
            "-a",
            "--antigravity-IDE",
            default=None,
            dest="antigravity_IDE",
            action="store_true",
            help="Open codes in Antigravity IDE",
        )
        parser.add_argument(
            "-p",
            "--powershell-only",
            default=None,
            dest="powershell_only",
            action="store_true",
            help="Only open folders in Windows Terminal (skip IDE)",
        )
        parser.add_argument(
            "--des",
            action="store_true",
            help="Show feature description from app_features.yml",
        )
        parser.add_argument(
            "-d",
            "--deep",
            default=False,
            action="store_true",
            help="Deep recursive action (e.g. for gdrive list)",
        )
        parser.add_argument(
            "-f",
            "--file",
            default=False,
            action="store_true",
            help="List files instead of folders (for gdrive list) or open app folder in File Explorer (for open)",
        )
        args = parser.parse_args()

        type_included = args.type
        action_included = args.action
        value_included = args.value
        extra_included = args.extra
        user_message_included = args.user_message
        deep_included = args.deep
        file_included = args.file

        if args.des:
            print_feature_description(type_included, action_included)

        # for coding
        antigravity_included = args.antigravity_IDE
        powershell_only_included = args.powershell_only
        default_ide_prefix: str = "anti" if antigravity_included else "code"

        if type_included == None:
            if action_included == None:
                print_help()
            else:
                raise Exception(MOD_WARNING_TYPE_MISSING)
        elif type_included == MOD_TYPE_EDIT:
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
            gdrive_args = [value_included, extra_included]
            if deep_included:
                gdrive_args.append("-d")
            if file_included:
                gdrive_args.append("--file")
            gdrive_execute(action_included, *gdrive_args)
        elif type_included == MOD_TYPE_CODE:
            if action_included == None:
                open_mod_files_in_vscode(default_ide_prefix)
            elif action_included == MOD_CODE_VSCODE_WORKSPACE:
                open_working_vscode(
                    default_ide_prefix,
                    value_included,
                    powershell_only_included,
                )
            elif action_included == MOD_CODE_TEST:
                open_testing_folder_in_vscode(default_ide_prefix)
            elif action_included == MOD_CODE_TYPESCRIPT_TEMPLATE:
                open_typescript_template_in_cursor(default_ide_prefix)
            elif action_included == MOD_CODE_JS or action_included == MOD_CODE_TS:
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
            if action_included == MOD_GIT_COMMIT_AND_PUSH:
                if not user_message_included:
                    raise Exception("Missing commit message (use -m or --message)")
            if not action_included:
                raise Exception(MOD_WARNING_ACTION_MISSING)
            run_git_command(action_included, user_message_included)
        elif type_included == MOD_TYPE_RUN:
            if action_included == MOD_RUN_UNIKEY_APP:
                run_Unikey_app()
            elif action_included == MOD_RUN_CREATE_FILES_IN_FOLDER:
                create_files_in_folder()
            elif action_included == MOD_RUN_SET_DOWNLOAD_PATH_IN_CHROME:
                set_download_path_in_chrome(value_included)
            elif action_included == MOD_RENAME_FILES:
                rename_files(value_included, extra_included)
            elif action_included == MOD_DELETE_FILES:
                delete_files(value_included, extra_included)
            elif action_included == MOD_KEEP_FILES:
                keep_files(value_included, extra_included)
            elif action_included == MOD_GEN_QR_IMAGE:
                gen_qr_image()
            elif action_included == None:
                raise Exception(MOD_WARNING_ACTION_MISSING)
            else:
                raise Exception(MOD_WARNING_ACTION_WRONG)
        elif type_included == MOD_TYPE_OPEN:
            if action_included == None:
                if file_included:
                    open_mod_file_in_system_folder()
                else:
                    open_mod_files_in_vscode(default_ide_prefix)
            elif action_included == MOD_OPEN_ENV:
                open_environment_variables_panel()
            elif action_included == MOD_OPEN_PROMPTS_FOLDER:
                open_prompts_folder()
            elif action_included == MOD_CODE_VSCODE_WORKSPACE:
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
            elif action_included == None:
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
