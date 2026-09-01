# MOD CLI - TÀI LIỆU BỐI CẢNH & TOÀN BỘ KIẾN TRÚC DỰ ÁN (PROJECT CONTEXT)

> **Mục đích tài liệu:** Tài liệu này đóng vai trò là "Single Source of Truth" cung cấp toàn bộ bối cảnh hệ thống, kiến trúc luồng dữ liệu, danh mục source code, bảng tra cứu lệnh và các lưu ý kỹ thuật quan trọng của project **Mod CLI**. AI Agent hoặc Developer có thể đọc file này để nắm trọn vẹn dự án mà không cần phải duyệt qua từng file mã nguồn.

---

## 1. Tổng Quan Dự Án (Overview)

- **Tên dự án:** Mod CLI (`mod`)
- **Nền tảng mục tiêu:** Windows (Windows 10/11, PowerShell, Windows Terminal, CMD).
- **Yêu cầu môi trường:** Python >= 3.12, Git, rclone, cloudflared (tùy chọn), module PowerShell BurntToast (tùy chọn).
- **Mục tiêu cốt lõi:** Gom toàn bộ các tác vụ tự động hóa, thao tác file, quản lý workspace IDE, đồng bộ Google Drive, kiểm tra proxy, keep-alive server, phát thông báo... vào một lệnh duy nhất: `mod <type> <action> [args...]`.

---

## 2. Kiến Trúc Hệ Thống (Architecture & Design Pattern)

Dự án áp dụng mô hình **Dispatcher - Feature Script Pattern**:

```text
User Input: mod <type> <action> [args...] [-a] [--info]
    │
    ▼
mod.cmd  (Wrapper cực mỏng: @py "%~dp0src\main.py" %*)
    │
    ▼
src/main.py (Central Dispatcher)
    ├── Manual parsing sys.argv (Không dùng argparse ở dispatcher)
    ├── Tách Dispatcher Flags (--info, -a / --antigravity-IDE)
    ├── Xác định type & action
    ├── Gom toàn bộ tham số còn lại (remaining_args)
    └── Gọi Handler tương ứng
            │
            ├── Gọi nội bộ / subprocess.run
            ▼
    src/features/<script>.py hoặc src/features/system/<_script>.py
    (Tự chịu trách nhiệm parse remaining_args, validate logic nghiệp vụ & thực thi)
```

### Nguyên tắc thiết kế (Design Principles):
1. **Dispatcher mỏng:** `src/main.py` chỉ làm nhiệm vụ định tuyến (routing), không ôm logic nghiệp vụ nặng.
2. **Feature độc lập:** Mỗi script trong `src/features/` là một đơn vị độc lập, có thể chạy trực tiếp bằng `python <script>.py [args]` nếu truyền đủ tham số.
3. **Arg forwarding:** Toàn bộ tham số và cờ sau `<action>` được chuyển tiếp nguyên vẹn cho feature script tự xử lý.
4. **Quản lý đường dẫn động & tập trung:** Dùng `src/configs/paths.py` để tính toán root path tự động, hạn chế tối đa việc hardcode đường dẫn tương đối.
5. **Đồng bộ tài liệu 3 lớp:** Khi thêm/sửa lệnh, luôn đồng bộ: `src/main.py` (code) + `src/contents/help.txt` (tóm tắt nhanh) + `src/contents/app_features.yml` (catalog chi tiết).

---

## 3. Cấu Trúc Thư Mục & Danh Mục File (Source Code Catalog)

```text
d:\D-Documents\TOOLs\mod\
├── mod.cmd                             # File thực thi CLI cho Windows (gọi Python vào src/main.py)
├── compress.cmd                        # Shortcut thực thi nhanh lệnh mod compress
├── .compressignore                     # Cấu hình danh sách tệp/thư mục bỏ qua khi nén dự án
├── requirements.txt                    # Danh sách thư viện Python (PyYAML, requests, python-dotenv, qrcode)
├── ARCHITECTURE.md                     # Tài liệu thiết kế kiến trúc chuẩn
├── README.md                           # Hướng dẫn sử dụng tổng quan cho người dùng
├── PROJECT_CONTEXT.md                  # File này - Tài liệu bối cảnh toàn diện cho AI Agent
├── note.md                             # Ghi chú cá nhân
├── print_project_tree.py               # Tiện ích in cây thư mục ra file project_tree.txt
├── project_tree.txt                    # Output cây thư mục
├── .agent/                             # Cấu hình & Kỹ năng chuẩn cho AI Agent (Antigravity/Agentic Framework)
│   └── skills/
│       └── mod-cli-developer/          # Skill hướng dẫn AI Agent phát triển và bảo trì Mod CLI
│           ├── SKILL.md                # Tài liệu kỹ năng chính kèm YAML frontmatter
│           ├── examples/               # Mã nguồn mẫu (feature script template)
│           ├── references/             # Checklist và tài liệu tham khảo kiến trúc
│           └── resources/              # Template YAML khai báo tính năng
├── data/
│   └── media/audio/
│       └── burnttoast-notification-sound.mp3 # File âm thanh thông báo mặc định cho Toast Notifier
├── doc/
│   ├── add-sound-notifier.md          # Tài liệu hướng dẫn cấu hình âm thanh BurntToast
│   ├── autocomplete.md                # Tài liệu mô tả chi tiết tính năng Auto-complete & REPL
│   └── info-flag-guide.md             # Hướng dẫn toàn diện kiến trúc và triển khai cờ --info

└── src/
    ├── main.py                         # Central Dispatcher (Định tuyến lệnh trung tâm)
    ├── cmd/
    │   └── init.cmd                    # Batch script dọn dẹp task thừa trên Windows & bật Unikey
    ├── configs/
    │   ├── __init__.py
    │   └── paths.py                    # Cấu hình đường dẫn nội bộ (dynamic) & bên ngoài (appdata, template...)
    ├── utils/
    │   ├── errors.py                   # Hệ thống Exception & xử lý lỗi tập trung ANSI color
    │   ├── interactive_cli.py          # Giao diện tổng quan Types và xử lý Tab Autocomplete cho Type/Action
    │   └── notifications/              # Module gửi thông báo đa nền tảng
    │       ├── __init__.py             # Factory function `get_notifier(platform)`
    │       ├── base.py                 # Abstract Base Class: `BaseNotifier`
    │       ├── ntfy_notifier.py        # Gửi thông báo tới app ntfy (Android/iOS/Web) qua REST API
    │       ├── toast_notifier.py       # Gửi Windows Toast qua BurntToast & phát âm thanh qua winmm API
    │       └── telegram_notifier.py    # Gửi tin nhắn qua Telegram Bot API (đọc token từ .env)
    ├── contents/                       # Dữ liệu tĩnh và tài liệu định dạng
    │   ├── app_features.yml            # Catalog chi tiết cho lệnh `mod <type> <action> --info`
    │   ├── help.txt                    # Nội dung help khi chạy `mod` hoặc `mod -h`
    │   ├── list_useful_commands.txt    # Danh sách các câu lệnh hệ điều hành / server hay dùng
    │   ├── statuses.txt                # Bảng giải thích các mã trạng thái mod-status
    │   ├── files_source.txt            # Template nguồn dùng cho tính năng `mod file create`
    │   └── cURL.txt                    # Snippet mẫu các thao tác cURL CRUD
    └── features/                       # Toàn bộ script tính năng
        ├── system/                     # Script nội bộ phục vụ CLI framework
        │   ├── _git.py                 # Tự động add, commit và push lên remote repo
        │   ├── _print_content.py       # Đọc và in file trong src/contents/
        │   ├── _print_feature_description.py # Parse app_features.yml khi có cờ --info
        │   ├── _print_root_folder.py   # In danh sách file/folder cấp 1 của một đường dẫn
        │   └── _statuses.py            # In nội dung statuses.txt
        ├── notify/                     # Module gửi thông báo đa kênh (ntfy, telegram, toast...)
        │   ├── __init__.py
        │   └── notify_cli.py           # CLI wrapper xử lý mod notify send/test/channels/config
        ├── cloudflare/

        │   └── cloudflared_wrapper.py  # Mở quick tunnel Cloudflare, hiển thị public URL & mã QR ASCII
        ├── gist/                       # Module quản lý CRUD & kiểm toán dung lượng GitHub Gist
        │   ├── __init__.py             # Export GistManager, GistStorageAuditor
        │   ├── README.md               # Tài liệu hướng dẫn sử dụng chi tiết (in qua mod gist --info)
        │   ├── gist_manager.py         # Thực thi CRUD Gist qua GitHub REST API v3
        │   ├── gist_auditor.py         # Kiểm toán dung lượng, phát hiện file lớn & rate limit
        │   └── gist_cli.py             # CLI wrapper cho toàn bộ thao tác mod gist

        ├── sync-to-gdrive/             # Module tương tác với Google Drive qua rclone & gdown

        │   ├── configs.json            # Lưu tên remote rclone đang active
        │   ├── AUTH_GUIDE.txt          # Hướng dẫn chi tiết cách tạo Google Cloud OAuth credentials
        │   └── sync_to_gdrive.py       # Script thực thi sync, list, remote info, del-fd, link, dl (download)
        ├── compress_project.py         # Nén toàn bộ mã nguồn dự án thành file zip (lọc qua .compressignore)
        ├── create_files_in_folder.py   # Tạo file/thư mục từ template trong files_source.txt (interactive)
        ├── create_folders_in_path.py   # Tạo folder tự động theo pattern và tự tăng index
        ├── delete_files.py             # Xóa file cấp 1 theo danh sách extension (vd: "tmp,log")
        ├── edit_to_command.py          # Mở PowerShell Profile ($PROFILE) trong Notepad
        ├── gen_qr_image.py             # Sinh file ảnh QR Code từ text nhập vào và lưu vào APPDATA_FOLDER
        ├── keep_files_with_ext.py      # Xóa toàn bộ file khác đuôi chỉ định (chỉ giữ 1 extension)
        ├── keep_screen.py              # Giữ màn hình Windows luôn bật qua SetThreadExecutionState Win32 API
        ├── keep_server_awake.py        # Ping HTTP GET định kỳ để giữ sống server miễn phí (Render/Kaggle)
        ├── mcp_set.py                  # Copy thư mục MCP từ kho LOCAL_ABSOLUTE_FOLDER_PATH vào project đích
        ├── merge_folders.py            # Merge thư mục có kiểm tra độ tương đồng/giao nhau của cây thư mục
        ├── open_main_ws.py             # Mở workspace lập trình trong Windows Terminal + VSCode/Anti + Browser
        ├── print_cURL.py               # In snippet cURL
        ├── print_folder_tree.py        # In cây thư mục có tính năng auto-collapse khi vượt quá số lượng max
        ├── print_os_info.py            # In cấu hình phần cứng, OS, CPU, RAM, Network (systeminfo, wmic, ipconfig)
        ├── rename_files.py             # Đổi tên file hàng loạt có auto-detect prefix hoặc đặt prefix tùy ý
        ├── send_toast.py               # CLI wrapper gửi Toast notification qua `ToastNotifier`
        ├── set_download_path_in_chrome.py # Sửa file Preferences của tất cả Google Chrome profiles
        ├── setup_venv_in_project.py    # Setup toàn diện venv Python: tạo venv, nâng cấp pip, ins.cmd, venv.cmd
        ├── skill_set.py                # Copy thư mục Skill AI từ kho SKILLS_FOLDER_PATH vào project đích
        ├── srt_count_line.py           # Phân tích file phụ đề SRT và thống kê theo số lượng dòng thoại
        └── test_proxy.py               # Kiểm tra kết nối proxy (Python requests, cURL header, ipify IP check)
```

---

## 4. Bảng Tra Cứu Toàn Bộ Lệnh (CLI Reference Table)

Cú pháp tổng quát: `mod <type> <action> [args...] [-a] [--info]`

### 4.1. Dispatcher Flags
- `--info`: In mô tả chi tiết của lệnh lấy từ `src/contents/app_features.yml`.
- `-a` hoặc `--antigravity-IDE`: Dùng IDE command `anti` thay vì `code` (VSCode).

### 4.2. Danh Sách Lệnh Chi Tiết Theo `type`

| Type | Action | Tham số / Flag đi kèm | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `open` | *(không có)* | `[-f]` | Mở thư mục gốc project trong IDE. Thêm `-f` để mở trong Windows Explorer. |
| `open` | `ws` | | Mở thư mục chứa các workspace (`D:/D-Documents/VSCode-Workspaces`). |
| `open` | `env` | | Mở bảng quản lý biến môi trường Windows (`rundll32 sysdm.cpl`). |
| `open` | `proms` | | Mở thư mục Prompts của Template Replacer Extension. |
| `code` | *(không có)* | | Mở project trong IDE (`code` hoặc `anti`). |
| `code` | `ws` | `<value> [-p]` | Mở workspace thiết lập sẵn (`ptb` hoặc `tool`). `-p` chỉ mở Windows Terminal. |
| `code` | `test` / `js` / `ts` / `py` / `nestjs` / `ext` / `ts-template` | | Mở nhanh các thư mục template hoặc thư mục testing tương ứng trong IDE. |
| `file` | `create` | | Menu tương tác tạo file từ template `files_source.txt`. |
| `file` | `rename` | `<folder_path> [prefix]` | Đổi tên file hàng loạt thành `<prefix>-1.ext`, `<prefix>-2.ext`... |
| `file` | `delete` | `<folder_path> <ext1,ext2,...>` | Xóa toàn bộ file có extension nằm trong danh sách chỉ định. |
| `file` | `keep` | `<folder_path> <ext>` | Chỉ giữ lại file có extension chỉ định, xóa tất cả các file khác. |
| `folder` | `create` | `<folder_path> [pattern] [start_idx] [count]` | Tạo hàng loạt folder con tự tăng index. |
| `folder` | `dld-path` | `[folder_name]` | Đặt lại đường dẫn download cho toàn bộ Chrome profiles. |
| `folder` | `merge` | `<from_folder> <to_folder> [-y] [--dry-run]` | Kiểm tra giao nhau của cây thư mục nguồn/đích và merge nội dung (ghi đè/tạo mới). |
| `folder` | `tree` | `[folder_path] [--max N]` | In cây thư mục có tự động thu gọn thư mục quá lớn (> max). |
| `run` | `unikey` | | Khởi động UniKey. |
| `run` | `gen-qr` | | Nhập text tương tác và tạo ảnh mã QR lưu vào thư mục AppData. |
| `run` | `keep-awake` | `[url] [-i interval]` | Gửi HTTP GET định kỳ giữ server không bị sleep (khoảng random hoặc fixed). |
| `run` | `keep-screen` | | Giữ màn hình Windows luôn sáng (bấm `q` hoặc `Ctrl+C` để dừng). |
| `run` | `srt-count-line` | `<file_path>` | Đếm số dòng thoại trong file SRT và sắp xếp giảm dần. |
| `git` | `commit` | `-m "<commit_message>"` | Tự động thực hiện: `git add .` -> `git commit -m` -> `git push origin main`. |
| `git` | `remote` | | In danh sách remote URL (`git remote -v`). |
| `gdrive` | `sync` | `"<source>" "<dest>" [--noti [platform]]` | Đồng bộ thư mục lên Google Drive bằng rclone. |
| `gdrive` | `list` | `[target_path] [-d] [--file]` | Liệt kê folder/file trên GDrive (`-d`: đệ quy sâu, `--file`: chỉ liệt kê file). |
| `gdrive` | `dl` | `<url> [--dest <path>] [--folder <name>]` | Tải file/folder từ URL về máy qua rclone hoặc fallback sang `gdown`. |
| `gdrive` | `remote` | | Xem cấu hình và dung lượng còn trống của remote GDrive đang chọn. |
| `gdrive` | `del-fd` | `<remote_folder>` | Xóa một thư mục trên remote GDrive (có bước hỏi xác nhận). |
| `gdrive` | `url` / `link` | `<remote_path>` | Lấy link truy cập web trực tiếp cho thư mục trên Google Drive. |
| `gdrive` | `reset` | | Xóa cấu hình remote rclone hiện tại hoặc xóa toàn bộ file config. |
| `gdrive` | `guide` | | Mở file tài liệu hướng dẫn cấu hình OAuth Client ID cho Google Drive. |
| `gist` | `create` | `[files...] [--desc <text>] [--public]` | Tạo Gist mới từ file cục bộ hoặc nhập tương tác trực tiếp. |
| `gist` | `list` | `[--page N] [--limit N] [--all] [--public-only] [--secret-only]` | Liệt kê danh sách Gist của tài khoản dạng bảng trực quan. |
| `gist` | `get` | `<gist_id> [--raw <file>] [--save <dir>]` | Xem metadata Gist, in raw file hoặc lưu toàn bộ file về máy. |
| `gist` | `update` | `<gist_id> [--add <name> <path>] [--delete <name>] [--desc <desc>]` | Cập nhật file và mô tả trong Gist đã có. |
| `gist` | `delete` | `<gist_id> [-y]` | Xóa vĩnh viễn Gist (có bước hỏi xác nhận an toàn). |
| `gist` | `reset` | `[gist_id] [--placeholder <name>] [--file <path>] [-y]` | Reset Gist: Xóa sạch toàn bộ Gist của tài khoản (nếu không truyền gist_id) hoặc reset 1 Gist cụ thể. |

| `gist` | `audit` | | Quét toàn bộ Gist, tính tổng dung lượng, phân loại đuôi file, cảnh báo file $\ge 8\text{MB}$ và kiểm tra Rate Limit. |

| `gist` | `rate` | | Kiểm tra hạn mức và số lượt request GitHub API còn lại. |
| `tunnel` | *(không có)* | `[port]` | Mở Cloudflare Quick Tunnel trỏ tới localhost (mặc định port 3000) + QR code. |

| `proxy` | `test` | `<ip>:<port>[:<user>:<pass>] [--protocol ...]` | Test proxy qua requests, cURL và lấy IP thật qua API ipify. |
| `mcp` | `set` | `[mcp_folder_name] [dest_folder_path]` | Copy thư mục MCP từ kho chung sang thư mục dự án đích. |
| `toast` | *(không có)* | `<title> [msg...] [--audio <path>]` | Bắn Windows Toast Notification kèm âm thanh MP3/WAV tùy chỉnh. |
| `toast` | `--syntax` | | In cú pháp 1 dòng của lệnh toast để tiện copy. |
| `print` | `os` | | In cấu hình OS, CPU, RAM, Network adapter. |
| `print` | `stts` | | In giải thích các mã trạng thái Mod CLI. |
| `print` | `ws` | | In danh sách các file trong thư mục VSCode-Workspaces. |
| `print` | `curl` | | In snippet mẫu cURL CRUD. |
| `print` | `dir` | | In đường dẫn thư mục `src` của mod. |
| `print` | `cmds` | | In danh sách các lệnh hữu ích thường dùng. |
| `skill` | `set` | `[skill_name] [dest_path]` | Sao chép thư mục Skill AI từ kho `SKILLS_FOLDER_PATH` vào thư mục đích. |
| `compress` | *(không có)* | `[output_path]` | Nén toàn bộ dự án thành file `mod-{dd}-{mm}-{yyyy}-{hh}-{mm}-{ss}.zip` tại thư mục gốc dự án (hoặc output_path), áp dụng bộ lọc `.compressignore`. |
| `compress` | `folder` | `<path> [--config-file C] [--ignore-file I]` | Nén thư mục cục bộ tự động đọc `.compressignore` hoặc theo JSON config. |
| `compress` | `init-ignore` | `<path> ["rules..."]` | Khởi tạo file `.compressignore` mẫu tại đường dẫn chỉ định với các rule tùy chỉnh. |
| `notify` | `send` | `"<msg>" [--title T] [--channel C] [--topic TP] [--priority P] [--tags TG] [--url U]` | Gửi thông báo đa kênh (mặc định ntfy app, topic: `any-mod-automation-N3RT8P2L`). |
| `notify` | `test` | `[--channel C] [--topic TP]` | Gửi thông báo test ping để xác nhận kết nối kênh. |
| `notify` | `channels` | | Liệt kê các kênh thông báo hỗ trợ và trạng thái cấu hình. |
| `notify` | `config` | | Xem hướng dẫn cấu hình thiết bị / app ntfy và file `.env`. |



| `edit` | `proms` | | Mở thư mục prompts của extension trong Notepad. |
| `edit` | `to` | | Mở PowerShell Profile trong Notepad. |
| `edit` | `cmds` | | Mở file `list_useful_commands.txt` trong Notepad để chỉnh sửa. |
| `py` | `env` | `[--path P] [--name N] [--skip-dotenv]` | Khởi tạo venv chuẩn cho project Python hiện tại. |
| `init` | *(không có)* | | Chạy script `init.cmd` để dọn dẹp các tiến trình Windows chạy ngầm thừa thãi. |

---

## 5. Cấu Hình & Quản Lý Môi Trường (Config & Environment)

### 5.1. Quản lý đường dẫn (`src/configs/paths.py`)
File này tập trung toàn bộ cấu hình đường dẫn của hệ thống:
- **Tự động suy ra từ codebase:**
  - `PROJECT_ROOT`: Thư mục gốc dự án (`get_project_root()`).
  - `SRC_FOLDER`: `<PROJECT_ROOT>/src`.
  - `FEATURES_FOLDER`: `<PROJECT_ROOT>/src/features`.
  - `CONTENTS_FOLDER`: `<PROJECT_ROOT>/src/contents`.
  - `TOAST_SOUND_AUDIO_FILE_PATH`: `<PROJECT_ROOT>/data/media/audio/burnttoast-notification-sound.mp3`.
- **Cấu hình môi trường máy cục bộ (Sửa khi chuyển máy):**
  - `APPDATA_FOLDER`: `D:/D-AppData/me-mod` (Nơi lưu QR Code sinh ra).
  - `TEMPLATE_REPLACER_FOLDER`: Đường dẫn đến extension Template Replacer.
  - `LOCAL_ABSOLUTE_FOLDER_PATH`: `D:/D-Documents/MCP` (Kho chứa MCP templates).
  - `SKILLS_FOLDER_PATH`: `D:/D-Documents/SKILLs` (Kho chứa các thư mục AI Skill).

### 5.2. File `.env` tại thư mục gốc
Dùng cho các thông tin bảo mật và cấu hình runtime:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

---

## 6. Các Cơ Chế Kỹ Thuật Đáng Chú Ý (Important Technical Mechanisms)

### 6.1. Xử lý Toast Audio trên Windows
- **Vấn đề:** Windows Action Center chạy trong môi trường sandbox UWP nên lệnh `New-BurntToastNotification -Audio (New-BTAudio -Path "file:///...")` thường bị chặn không cho load file âm thanh từ ổ cứng ngoài.
- **Giải pháp:** Trong [`toast_notifier.py`](file:///d:/D-Documents/TOOLs/mod/src/utils/notifications/toast_notifier.py):
  1. Gửi Toast ở chế độ câm (`-Silent`).
  2. Đồng thời gọi trực tiếp Windows Multimedia API (`ctypes.windll.winmm.mciSendStringW`) để phát file `.mp3` / `.wav` cá nhân một cách mượt mà và không bị sandbox chặn.

### 6.2. Cơ chế Keep-Screen (Giữ sáng màn hình)
- Trong [`keep_screen.py`](file:///d:/D-Documents/TOOLs/mod/src/features/keep_screen.py), sử dụng API `SetThreadExecutionState` với cờ `ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED` để thông báo cho Windows không tắt màn hình và không vào trạng thái Sleep. Khi người dùng bấm `q` hoặc `Ctrl+C`, reset lại về `ES_CONTINUOUS`.

### 6.3. Tự động đồng bộ Google Drive & Lấy Link Web
- Trong [`sync_to_gdrive.py`](file:///d:/D-Documents/TOOLs/mod/src/features/sync-to-gdrive/sync_to_gdrive.py), sau khi lệnh `rclone sync` hoàn tất, script sẽ tự động gọi `rclone link` để sinh ngay URL truy cập web của folder đích và gửi thông báo kèm link qua Telegram/Toast.

### 6.4. Xử lý UTF-8 Encoding trên Windows Console
- Ngay đầu `src/main.py` và `src/utils/interactive_cli.py`, hệ thống tự thiết lập:
  ```python
  os.environ.setdefault("PYTHONIOENCODING", "utf-8")
  sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  sys.stderr.reconfigure(encoding="utf-8", errors="replace")
  ```
  Điều này đảm bảo output tiếng Việt và mã ASCII QR code không bị vỡ font/crash trên CMD/PowerShell Windows.

### 6.5. Chế độ Tương tác & Tab Autocomplete
- Khi người dùng chạy lệnh `mod` không có tham số:
  1. [`interactive_cli.py`](file:///d:/D-Documents/TOOLs/mod/src/utils/interactive_cli.py) sẽ in danh sách toàn bộ các nhóm lệnh (`type`) hiện có kèm theo danh sách action tương ứng và dòng gợi ý ở cuối.
  2. Mở dấu nhắc `mod > ` sử dụng `msvcrt.getwch()` trên Windows để bắt từng phím bấm mà không cần nhấn Enter.
  3. **Tab Autocomplete cho Type:** Quét toàn bộ type khớp với tiền tố đang gõ theo thứ tự A-Z. Bấm Tab liên tiếp để xoay vòng các candidate.
  4. **Tab Autocomplete cho Action:** Sau khi có type hợp lệ, gõ tiếp tiền tố action và bấm Tab để hoàn thành action của type đó (xoay vòng A-Z). Nếu type không có action, bỏ qua.
  5. Bấm `Enter` để thực thi trực tiếp lệnh vừa nhập mà không cần thoát CLI; gõ `h` hoặc `help` để xem help chi tiết; gõ `q` hoặc `exit` để thoát.

---

## 7. Hướng Dẫn Mở Rộng & Thêm Tính Năng Mới (How to Add a Feature)

Khi cần bổ sung một lệnh mới vào `mod CLI`, làm theo đúng 5 bước:

1. **Tạo script tính năng trong `src/features/<tên_tính_năng>.py`:**
   - Script tự nhận `sys.argv` để lấy tham số, validate input và in thông báo rõ ràng.
2. **Khai báo hằng số trong `src/main.py`:**
   - Khai báo hằng số `MOD_TYPE_<NAME>` và `MOD_<TYPE>_<ACTION>`.
3. **Thêm Handler & Route trong `src/main.py`:**
   - Tạo hàm `def run_my_feature(remaining_args): ...` sử dụng `subprocess.run`.
   - Bổ sung nhánh `elif type_included == ...` và `elif action_included == ...`.
4. **Cập nhật tài liệu tóm tắt trong `src/contents/help.txt`:**
   - Thêm action vào nhóm tương ứng kèm ví dụ lệnh.
5. **Cập nhật catalog chi tiết trong `src/contents/app_features.yml`:**
   - Thêm block `id`, `title`, `command`, `summary`, `details`, `conditions` để hỗ trợ cờ `--info`.

---

## 8. Các Lưu Ý Quan Trọng Cho AI Agent & Developer (Crucial Notes & Caveats)

1. **Không can thiệp vào cách parse của Dispatcher:** Dispatcher cố tình parse thủ công bằng mảng `sys.argv` để đảm bảo mọi argument phức tạp (như commit message có dấu cách, regex, danh sách extension) được forward nguyên vẹn cho script con. Không tự ý chuyển `main.py` sang dùng `argparse`.
2. **Kiểm tra đường dẫn khi chạy trên máy mới:** Nếu clone project sang máy tính khác, hãy kiểm tra lại 3 biến đường dẫn ngoài project trong [`src/configs/paths.py`](file:///d:/D-Documents/TOOLs/mod/src/configs/paths.py) (`APPDATA_FOLDER`, `TEMPLATE_REPLACER_FOLDER`, `LOCAL_ABSOLUTE_FOLDER_PATH`).
3. **Các thao tác file nhạy cảm:** Các lệnh `file delete`, `file keep`, `gdrive del-fd`, `gdrive reset` có tính chất xóa dữ liệu vĩnh viễn. Đảm bảo script luôn có validate hoặc xác nhận trước khi thực thi.
4. **Bảo mật:** Không bao giờ commit file `.env`, file cấu hình chứa token/OAuth secret thật lên git repository công khai.
