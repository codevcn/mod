import os
import subprocess
import sys
from pathlib import Path
from configs.paths import PROJECT_ROOT, FEATURES_FOLDER, TEMPLATE_REPLACER_FOLDER
from utils.errors import (
    handle_cli_error,
    InvalidTypeError,
    MissingTypeError,
    InvalidActionError,
    MissingActionError,
)
from utils.interactive_cli import run_interactive_session

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
MOD_TYPE_TUNNEL = "tunnel"
MOD_TYPE_PROXY = "proxy"
MOD_TYPE_MCP = "mcp"
MOD_TYPE_SKILL = "skill"
MOD_TYPE_TOAST = "toast"
MOD_TYPE_COMPRESS = "compress"
MOD_TYPE_GIST = "gist"


# --- Actions ---
# gist
MOD_GIST_CREATE = "create"
MOD_GIST_LIST = "list"
MOD_GIST_GET = "get"
MOD_GIST_UPDATE = "update"
MOD_GIST_DELETE = "delete"
MOD_GIST_RESET = "reset"
MOD_GIST_AUDIT = "audit"
MOD_GIST_RATE = "rate"


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
MOD_RUN_KEEP_SCREEN = "keep-screen"
MOD_SRT_COUNT_LINE = "srt-count-line"
# file
MOD_FILE_CREATE = "create"
MOD_FILE_RENAME = "rename"
MOD_FILE_DELETE = "delete"
MOD_FILE_KEEP = "keep"
# folder
MOD_FOLDER_CREATE = "create"
MOD_FOLDER_DLD_PATH = "dld-path"
MOD_FOLDER_MERGE = "merge"
MOD_FOLDER_TREE = "tree"
# edit
MOD_EDIT_PROMPTS = "proms"
MOD_EDIT_TO_COMMAND = "to"
MOD_EDIT_USEFUL_COMMANDS = "cmds"
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
# proxy
MOD_PROXY_TEST = "test"
# mcp
MOD_MCP_SET = "set"
# skill
MOD_SKILL_SET = "set"
# compress
MOD_COMPRESS_FOLDER = "folder"
MOD_COMPRESS_INIT_IGNORE = "init-ignore"



# --- Warnings (deprecated, replaced by utils.errors) ---

MOD_SRC_FOLDER = Path(__file__).resolve().parent
MOD_ROOT_FOLDER = PROJECT_ROOT
MOD_FEATURES_FOLDER_PATH = FEATURES_FOLDER
MOD_SYSTEM_FEATURES_FOLDER_PATH = str(Path(MOD_FEATURES_FOLDER_PATH) / "system")
MOD_CONTENT_FOLDER_PATH = str(Path(MOD_SRC_FOLDER) / "contents")

TEMPLATE_REPLACER_FOLDER_PATH = TEMPLATE_REPLACER_FOLDER

# --- Functions ---


def get_feature_path(*parts: str) -> str:
    return str(Path(MOD_FEATURES_FOLDER_PATH, *parts))


def get_system_feature_path(filename: str) -> str:
    return str(Path(MOD_SYSTEM_FEATURES_FOLDER_PATH, filename))


def get_content_path(filename: str) -> str:
    return str(Path(MOD_CONTENT_FOLDER_PATH, filename))


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


def merge_folders(remaining_args: list[str]):
    cmd_args = [
        "py",
        get_feature_path("merge_folders.py"),
    ]
    cmd_args.extend(remaining_args)
    result = subprocess.run(cmd_args, shell=True)
    sys.exit(result.returncode)


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


def cmd_tunnel(action, remaining_args):
    cmd_args = [
        "python",
        get_feature_path("cloudflare", "cloudflared_wrapper.py"),
    ]
    if action is not None:
        cmd_args.append(action)
    cmd_args.extend(remaining_args)

    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


def cmd_proxy(action, remaining_args):
    cmd_args = [
        "python",
        get_feature_path("test_proxy.py"),
    ]
    if action is not None:
        if action != MOD_PROXY_TEST:
            raise InvalidActionError(MOD_TYPE_PROXY, action, [MOD_PROXY_TEST])
    cmd_args.extend(remaining_args)

    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


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


def edit_useful_commands():
    cmd_args = [
        "notepad",
        get_content_path("list_useful_commands.txt"),
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


def keep_screen():
    cmd_args = [
        "python",
        get_feature_path("keep_screen.py"),
    ]
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


def print_folder_tree(remaining_args):
    cmd_args = [
        "python",
        get_feature_path("print_folder_tree.py"),
    ]
    cmd_args.extend(remaining_args)
    subprocess.run(cmd_args, shell=True)
    sys.exit(0)


def cmd_mcp(action, remaining_args):
    cmd_args = [
        "python",
        get_feature_path("mcp_set.py"),
    ]
    if action is not None:
        cmd_args.append(action)
    cmd_args.extend(remaining_args)

    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


def cmd_skill(action, remaining_args):
    cmd_args = [
        "python",
        get_feature_path("skill_set.py"),
    ]
    if action is not None:
        cmd_args.append(action)
    cmd_args.extend(remaining_args)

    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


def cmd_toast(title, remaining_args):
    cmd_args = [
        "python",
        get_feature_path("send_toast.py"),
    ]
    if title is not None:
        cmd_args.append(title)
    cmd_args.extend(remaining_args)

    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


def cmd_compress(remaining_args):
    cmd_args = [
        "python",
        get_feature_path("compress_project.py"),
    ]
    cmd_args.extend(remaining_args)

    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


def cmd_gist(action, remaining_args):
    cmd_args = [
        "python",
        get_feature_path("gist", "gist_cli.py"),
    ]
    if action is not None:
        cmd_args.append(action)
    cmd_args.extend(remaining_args)

    result = subprocess.run(
        cmd_args,
        check=False,
    )
    sys.exit(result.returncode)


def dispatch_command(
    feature_args: list[str],
    des_flag: bool = False,
    antigravity_flag: bool = False,
):
    type_included = feature_args[0] if len(feature_args) > 0 else None
    action_included = feature_args[1] if len(feature_args) > 1 else None
    remaining_args = feature_args[2:]

    # --- Feature description: mod <type> <action> --des ---
    if des_flag:
        print_feature_description(type_included, action_included)

    # --- IDE prefix ---
    default_ide_prefix: str = "anti" if antigravity_flag else "code"

    # --- Dispatch ---
    if type_included == MOD_TYPE_GIST:
        valid_actions = [
            MOD_GIST_AUDIT,
            MOD_GIST_CREATE,
            MOD_GIST_DELETE,
            MOD_GIST_GET,
            MOD_GIST_LIST,
            MOD_GIST_RATE,
            MOD_GIST_RESET,
            MOD_GIST_UPDATE,
        ]

        if action_included is None:
            raise MissingActionError(type_included, valid_actions)
        elif action_included not in valid_actions:
            raise InvalidActionError(type_included, action_included, valid_actions)
        cmd_gist(action_included, remaining_args)
    elif type_included == MOD_TYPE_COMPRESS:
        valid_actions = [MOD_COMPRESS_FOLDER, MOD_COMPRESS_INIT_IGNORE]
        if action_included is not None and action_included not in valid_actions:
            raise InvalidActionError(type_included, action_included, valid_actions)
        cmd_compress(feature_args[1:])


    elif type_included == MOD_TYPE_EDIT:
        valid_actions = [MOD_EDIT_PROMPTS, MOD_EDIT_TO_COMMAND, MOD_EDIT_USEFUL_COMMANDS]
        if action_included == MOD_EDIT_PROMPTS:
            edit_prompts()
        elif action_included == MOD_EDIT_TO_COMMAND:
            edit_to_command()
        elif action_included == MOD_EDIT_USEFUL_COMMANDS:
            edit_useful_commands()
        elif action_included is None:
            raise MissingActionError(type_included, valid_actions)
        else:
            raise InvalidActionError(type_included, action_included, valid_actions)
    elif type_included == MOD_TYPE_PY:
        valid_actions = [MOD_PY_ENV]
        if action_included == MOD_PY_ENV:
            py_setup_venv()
        elif action_included is None:
            raise MissingActionError(type_included, valid_actions)
        else:
            raise InvalidActionError(type_included, action_included, valid_actions)
    elif type_included == MOD_TYPE_INIT:
        cmd_init()
    elif type_included == MOD_TYPE_GDRIVE:
        gdrive_execute(action_included, remaining_args)
    elif type_included == MOD_TYPE_TUNNEL:
        cmd_tunnel(action_included, remaining_args)
    elif type_included == MOD_TYPE_PROXY:
        valid_actions = [MOD_PROXY_TEST]
        if action_included is None:
            raise MissingActionError(type_included, valid_actions)
        if action_included != MOD_PROXY_TEST:
            raise InvalidActionError(type_included, action_included, valid_actions)
        cmd_proxy(action_included, remaining_args)
    elif type_included == MOD_TYPE_MCP:
        valid_actions = [MOD_MCP_SET]
        if action_included is None:
            raise MissingActionError(type_included, valid_actions)
        if action_included != MOD_MCP_SET:
            raise InvalidActionError(type_included, action_included, valid_actions)
        cmd_mcp(action_included, remaining_args)
    elif type_included == MOD_TYPE_SKILL:
        valid_actions = [MOD_SKILL_SET]
        if action_included is None:
            raise MissingActionError(type_included, valid_actions)
        if action_included != MOD_SKILL_SET:
            raise InvalidActionError(type_included, action_included, valid_actions)
        cmd_skill(action_included, remaining_args)
    elif type_included == MOD_TYPE_TOAST:
        cmd_toast(action_included, remaining_args)
    elif type_included == MOD_TYPE_CODE:
        valid_actions = [
            MOD_CODE_VSCODE_WORKSPACE, MOD_CODE_TEST, MOD_CODE_TYPESCRIPT_TEMPLATE,
            MOD_CODE_JS, MOD_CODE_TS, MOD_CODE_NESTJS, MOD_CODE_PY, MOD_CODE_EXTENSIONS
        ]
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
            raise InvalidActionError(type_included, action_included, valid_actions)
    elif type_included == MOD_TYPE_GIT:
        valid_actions = ["commit", "remote"]
        if not action_included:
            raise MissingActionError(type_included, valid_actions)
        run_git_command(action_included, remaining_args)
    elif type_included == MOD_TYPE_RUN:
        valid_actions = [
            MOD_RUN_UNIKEY_APP, MOD_GEN_QR_IMAGE, MOD_KEEP_AWAKE,
            MOD_RUN_KEEP_SCREEN, MOD_SRT_COUNT_LINE
        ]
        if action_included == MOD_RUN_UNIKEY_APP:
            run_Unikey_app()
        elif action_included == MOD_GEN_QR_IMAGE:
            gen_qr_image()
        elif action_included == MOD_KEEP_AWAKE:
            keep_server_awake(remaining_args)
        elif action_included == MOD_RUN_KEEP_SCREEN:
            keep_screen()
        elif action_included == MOD_SRT_COUNT_LINE:
            srt_count_lines(remaining_args)
        elif action_included is None:
            raise MissingActionError(type_included, valid_actions)
        else:
            raise InvalidActionError(type_included, action_included, valid_actions)
    elif type_included == MOD_TYPE_FILE:
        valid_actions = [MOD_FILE_CREATE, MOD_FILE_RENAME, MOD_FILE_DELETE, MOD_FILE_KEEP]
        if action_included == MOD_FILE_CREATE:
            create_files_in_folder()
        elif action_included == MOD_FILE_RENAME:
            rename_files(remaining_args)
        elif action_included == MOD_FILE_DELETE:
            delete_files(remaining_args)
        elif action_included == MOD_FILE_KEEP:
            keep_files(remaining_args)
        elif action_included is None:
            raise MissingActionError(type_included, valid_actions)
        else:
            raise InvalidActionError(type_included, action_included, valid_actions)
    elif type_included == MOD_TYPE_FOLDER:
        valid_actions = [
            MOD_FOLDER_CREATE,
            MOD_FOLDER_DLD_PATH,
            MOD_FOLDER_MERGE,
            MOD_FOLDER_TREE,
        ]
        if action_included == MOD_FOLDER_CREATE:
            create_folders_in_path(remaining_args)
        elif action_included == MOD_FOLDER_DLD_PATH:
            set_download_path_in_chrome(remaining_args)
        elif action_included == MOD_FOLDER_MERGE:
            merge_folders(remaining_args)
        elif action_included == MOD_FOLDER_TREE:
            print_folder_tree(remaining_args)
        elif action_included is None:
            raise MissingActionError(type_included, valid_actions)
        else:
            raise InvalidActionError(type_included, action_included, valid_actions)
    elif type_included == MOD_TYPE_OPEN:
        valid_actions = [MOD_OPEN_ENV, MOD_OPEN_PROMPTS_FOLDER, MOD_CODE_VSCODE_WORKSPACE]
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
            raise InvalidActionError(type_included, clean_action, valid_actions)
    elif type_included == MOD_TYPE_PRINT:
        valid_actions = [
            MOD_PRINT_OS_INFO, MOD_PRINT_VSCODE_WORKSPACES, MOD_PRINT_DIRECTORY,
            MOD_PRINT_USEFUL_COMMANDS, MOD_PRINT_CURL, MOD_PRINT_STATUSES_INFO
        ]
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
            raise MissingActionError(type_included, valid_actions)
        else:
            raise InvalidActionError(type_included, action_included, valid_actions)
    else:
        raise InvalidTypeError(type_included)

    # Nếu chạy đến đây (không rẽ nhánh nào) thì báo lỗi.
    global MOD_STATUS
    MOD_STATUS = "OUT-OF-MAIN-SECTION"
    print(">>> These commands end up with mod-status: " + MOD_STATUS)
    sys.exit(1)


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

        # --- Khi user gõ `mod` không có tham số: chạy phiên tương tác ---
        if not feature_args:
            if des_flag:
                print_feature_description(None, None)
            else:
                run_interactive_session(dispatch_command, print_help)
            sys.exit(0)

        type_included = feature_args[0]
        # --- Help: mod -h | mod --help ---
        if type_included in ("-h", "--help"):
            print_help()

        # --- Thực thi lệnh trực tiếp ---
        dispatch_command(feature_args, des_flag, antigravity_flag)

    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
    except Exception as e:
        handle_cli_error(e)
