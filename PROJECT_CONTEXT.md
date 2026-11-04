# MOD CLI - TÀI LIỆU BỐI CẢNH & KIẾN TRÚC HỆ THỐNG (PROJECT CONTEXT)

> **Mục đích tài liệu:** Tài liệu này đóng vai trò là **Architecture & Technical Context** dành riêng cho **AI Coding Agent** khi làm việc trên project **Mod CLI**. 
> - **Đối tượng đọc:** AI Agent (nhằm nắm bắt kiến trúc, luồng điều phối, quy chuẩn kỹ thuật, cấu hình runtime và quy trình phát triển).
> - **Người dùng cuối (Human Developer):** Tra cứu hướng dẫn sử dụng tại [`README.md`](file:///d:/D-Documents/TOOLs/mod/README.md) hoặc gõ `mod --help`.
> - **Chi tiết tính năng & tra cứu lệnh:** Danh mục lệnh đầy đủ, cú pháp chi tiết, tham số và điều kiện được lưu tập trung tại [`src/contents/app_features.yml`](file:///d:/D-Documents/TOOLs/mod/src/contents/app_features.yml) và [`src/contents/help.txt`](file:///d:/D-Documents/TOOLs/mod/src/contents/help.txt). File này **không liệt kê chi tiết từng lệnh** để tránh phình to và luôn giữ tính ổn định (evergreen).

---

## 1. Tổng Quan Dự Án (Project Overview)

- **Tên dự án:** Mod CLI (`mod`)
- **Nền tảng mục tiêu:** Windows (Windows 10/11, PowerShell, Windows Terminal, CMD).
- **Yêu cầu môi trường:** Python >= 3.12, Git, rclone (tùy chọn cho Google Drive), module PowerShell BurntToast (tùy chọn cho Windows Toast).
- **Mục tiêu cốt lõi:** Gom toàn bộ các tác vụ tự động hóa cá nhân, thao tác file, quản lý workspace lập trình, đồng bộ Google Drive, quản lý GitHub Gist, kiểm tra proxy, keep-alive server, quản lý AI Skills / MCP Servers... vào một câu lệnh duy nhất: `mod <type> <action> [args...]`.

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
    ├── Tự parse sys.argv (Tuyệt đối KHÔNG dùng argparse ở dispatcher)
    ├── Tách Dispatcher Flags (--version / -v, --info / --des, -a / --antigravity-IDE)
    ├── Nếu không có tham số: Khởi chạy Interactive REPL (src/utils/interactive_cli.py)
    ├── Xác định type & action hợp lệ
    ├── Forward nguyên vẹn toàn bộ tham số còn lại (remaining_args)
    └── Gọi Handler tương ứng
            │
            ├── Gọi module nội bộ / subprocess.run
            ▼
    src/features/<script>.py hoặc src/features/<domain>/<script>.py
    (Tự chịu trách nhiệm parse remaining_args, validate logic nghiệp vụ & thực thi)
```

### 4 Nguyên Tắc Thiết Kế Cốt Lõi (Core Design Principles):
1. **Dispatcher mỏng (Thin Dispatcher):** `src/main.py` chỉ làm nhiệm vụ định tuyến (routing) và kiểm tra tính hợp lệ của `type`/`action`. Toàn bộ logic nghiệp vụ thuộc về các feature script độc lập.
2. **Feature Script độc lập (Self-Contained Features):** Mỗi file trong `src/features/` là một đơn vị độc lập, có thể chạy trực tiếp bằng `python src/features/<script>.py [args]` nếu truyền đủ tham số.
3. **Arg Forwarding nguyên vẹn:** Toàn bộ tham số và cờ sau `<action>` được chuyển tiếp nguyên vẹn cho feature script tự xử lý (cho phép các cờ phức tạp như regex, commit message có khoảng trắng, cờ boolean tùy ý).
4. **Quản lý đường dẫn tập trung:** Mọi đường dẫn thư mục, tài nguyên, kho lưu trữ đều được định nghĩa tại [`src/configs/paths.py`](file:///d:/D-Documents/TOOLs/mod/src/configs/paths.py). Tuyệt đối không hardcode đường dẫn tương đối trong các feature script.

---

## 3. Cấu Trúc Thư Mục & Vai Trò Các Tầng (Directory Structure)

```text
d:\D-Documents\TOOLs\mod\
├── mod.cmd                             # Wrapper Windows CLI (gọi Python vào src/main.py)
├── compress.cmd                        # Shortcut thực thi nhanh lệnh nén dự án
├── .compressignore                     # Cấu hình danh sách tệp/thư mục bỏ qua khi nén
├── requirements.txt                    # Thư viện Python phụ thuộc (PyYAML, requests, python-dotenv, qrcode...)
├── ARCHITECTURE.md                     # Tài liệu thiết kế kiến trúc chuẩn
├── README.md                           # Hướng dẫn sử dụng tổng quan cho người dùng
├── PROJECT_CONTEXT.md                  # File này - Bối cảnh & kiến trúc hệ thống cho AI Agent
├── .agent/skills/                      # Kỹ năng chuẩn cho AI Coding Agent (Open Agent Skills standard)
│   ├── mod-cli-developer/              # SOP chuẩn phát triển, thêm, sửa, xóa tính năng Mod CLI
│   └── mod-git-commit/                 # SOP review thay đổi, dọn dẹp file tạm, commit & push
├── data/                               # Dữ liệu runtime nội bộ của công cụ
│   ├── credentials/.mod_history        # Lịch sử câu lệnh nhập trong interactive REPL
│   └── media/audio/                    # Âm thanh thông báo mặc định (burnttoast sound MP3)
├── doc/ / docs/                        # Tài liệu kỹ thuật chi tiết theo chuyên đề và sơ đồ hệ thống
└── src/
    ├── main.py                         # Central Dispatcher (Bộ điều phối trung tâm)
    ├── cmd/                            # Batch script tiện ích hệ điều hành (init.cmd...)
    ├── configs/                        # Cấu hình hệ thống
    │   ├── paths.py                    # Quản lý tập trung toàn bộ đường dẫn nội bộ và ngoài máy
    │   └── version.py                  # Metadata phiên bản chuẩn hóa của Mod CLI
    ├── utils/                          # Bộ công cụ dùng chung
    │   ├── errors.py                   # Hệ thống Exception & xử lý lỗi tập trung ANSI color
    │   ├── interactive_cli.py          # REPL Interactive CLI & Tab Autocomplete Engine
    │   └── notifications/              # Kiến trúc gửi thông báo đa kênh (ntfy, telegram, toast...)
    ├── contents/                       # Dữ liệu tĩnh và Catalogs tính năng
    │   ├── app_features.yml            # Single Source of Truth chứa catalog mô tả chi tiết (--info)
    │   ├── help.txt                    # Nội dung tóm tắt cú pháp nhanh (mod --help)
    │   ├── statuses.txt                # Bảng giải thích các mã trạng thái Mod CLI
    │   └── note.txt                    # Sổ tay ghi chép các lệnh hệ điều hành / server hay dùng
    └── features/                       # Toàn bộ script nghiệp vụ (chia theo domain chuyên trách)
        ├── system/                     # Script nội bộ framework (_git.py, _statuses.py, _print_*.py)
        ├── notify/                     # Module CLI gửi thông báo đa kênh
        ├── gist/                       # Quản lý CRUD và kiểm toán dung lượng GitHub Gist
        ├── sync-to-gdrive/             # Tương tác với Google Drive qua rclone & gdown
        ├── cloudflare/                 # Cloudflare quick tunnel wrapper
        └── <feature_scripts>.py        # Các script tính năng đơn lẻ (file, folder, git, mcp, skill, run...)
```

---

## 4. Cơ Chế Tra Cứu Tính Năng & Danh Mục Lệnh (Feature Discovery for AI)

> [!IMPORTANT]
> **Hướng dẫn dành cho AI Agent:** Để tránh file bị phình to và lỗi thời theo thời gian, **file này KHÔNG lưu bảng tra cứu toàn bộ lệnh chi tiết**. Khi cần tìm hiểu hoặc kiểm tra tính năng của Mod CLI, AI Agent hãy tra cứu theo các nguồn chuẩn hóa sau:

1. **Tra cứu tóm tắt cú pháp và danh mục lệnh:**
   - Đọc file [`src/contents/help.txt`](file:///d:/D-Documents/TOOLs/mod/src/contents/help.txt) hoặc chạy `python src/main.py --help`.
2. **Tra cứu chi tiết cờ, tham số, logic và điều kiện của một lệnh:**
   - Đọc file [`src/contents/app_features.yml`](file:///d:/D-Documents/TOOLs/mod/src/contents/app_features.yml) hoặc chạy `python src/main.py <type> <action> --info`.
3. **Tra cứu danh sách Type & Action hợp lệ của hệ thống:**
   - Đọc biến `TYPE_ACTION_MAP` trong [`src/utils/interactive_cli.py`](file:///d:/D-Documents/TOOLs/mod/src/utils/interactive_cli.py).

---

## 5. Cài Đặt, Thiết Lập & Cấu Hình Runtime (Setup & Environment)

### 5.1. Thiết lập ban đầu (Initial Setup)
1. Cài đặt Python 3.12+ trên Windows.
2. Cài đặt dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Đăng ký biến môi trường `PATH`:
   - Thêm đường dẫn thư mục gốc `d:\D-Documents\TOOLs\mod` vào biến `PATH` của người dùng để có thể gọi lệnh `mod` từ bất kỳ thư mục/terminal nào trong hệ điều hành Windows.

### 5.2. Quản lý đường dẫn tập trung ([`src/configs/paths.py`](file:///d:/D-Documents/TOOLs/mod/src/configs/paths.py))
Hệ thống phân định rõ ràng 3 nhóm đường dẫn:
1. **Đường dẫn nội bộ (Tự động suy ra từ codebase, không bao giờ cần sửa):**
   - `PROJECT_ROOT`, `SRC_FOLDER`, `FEATURES_FOLDER`, `CONTENTS_FOLDER`, `TOAST_SOUND_AUDIO_FILE_PATH`, `MOD_HISTORY_FILE_PATH`.
2. **Đường dẫn ngoài máy cục bộ (Cần kiểm tra/cập nhật khi chuyển sang máy khác):**
   - `APPDATA_FOLDER`: `D:/D-AppData/me-mod` (lưu QR code, alias mở nhanh thư mục).
   - `OPEN_ALIASES_FILE_PATH`: `<APPDATA_FOLDER>/open_aliases.json`.
   - `LOCAL_ABSOLUTE_FOLDER_PATH` / `MCP_FOLDER_PATH`: Kho chứa MCP Server templates.
   - `SKILLS_FOLDER_PATH`: Kho chứa các AI Skills tập trung.
   - `VSCODE_WORKSPACES_FOLDER`: Thư mục lưu các file `.code-workspace`.
   - `SOURCE_FILES_FOLDER`: Kho chứa các tệp mã nguồn mẫu/template tái sử dụng.
   - `TEMPLATE_REPLACER_FOLDER`: Thư mục extension Template Replacer.
3. **Đường dẫn AI Agent & Cấu hình người dùng (Tự động theo User Home `~`):**
   - Antigravity: `~/.gemini/config/mcp_config.json`, `~/.gemini/config/skills`.
   - OpenAI Codex: `~/.codex/config.toml`, `~/.codex/skills`.
   - Claude Code: `~/.claude.json`, `~/.claude/skills`.
   - SSH Config: `~/.ssh/config`.

### 5.3. Cấu hình biến môi trường (`.env`)
Dùng cho các thông tin xác thực runtime và tích hợp bên ngoài (nằm tại thư mục gốc, không commit lên Git):
```env
# Telegram Notification Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# GitHub Gist API (Personal Access Token có quyền gists)
GITHUB_GIST_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

---

## 6. Các Cơ Chế Kỹ Thuật Nền Tảng (Core Technical Mechanisms)

### 6.1. Xử lý UTF-8 trên Windows Console
Để tránh lỗi vỡ font tiếng Việt hoặc crash khi in bảng ASCII / QR code trên Windows PowerShell và CMD, mọi entrypoint và script đều thiết lập:
```python
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

### 6.2. Cơ chế Không Dùng `argparse` ở Dispatcher
- `src/main.py` cố tình **không dùng `argparse`** mà parse thủ công danh sách `sys.argv`.
- **Lý do:** Cho phép chuyển tiếp nguyên vẹn (`forward verbatim`) toàn bộ đối số còn lại (`remaining_args`) sang các script con. Các script con tự quyết định cách parse riêng (dùng `sys.argv`, regex, hoặc thư viện chuyên biệt) mà không bị xung đột cú pháp ở tầng Dispatcher.

### 6.3. Interactive REPL & Tab Autocomplete Engine ([`src/utils/interactive_cli.py`](file:///d:/D-Documents/TOOLs/mod/src/utils/interactive_cli.py))
- Khi người dùng gõ `mod` không có tham số: Hệ thống chuyển sang chế độ Interactive REPL.
- Sử dụng API `msvcrt.getwch()` trên Windows để bắt từng phím bấm thời gian thực:
  - **Tab xoay vòng Type:** Quét toàn bộ `type` khớp với tiền tố đang gõ theo thứ tự A-Z.
  - **Tab xoay vòng Action:** Sau khi có type hợp lệ, tiếp tục Tab để hoàn thành `action` tương ứng.
  - **Lịch sử lệnh:** Điều hướng mũi tên lên/xuống đọc và ghi vào file `.mod_history`.

### 6.4. Kiến trúc Thông báo Đa Kênh (Multi-Channel Notifications)
- Nằm tại `src/utils/notifications/` áp dụng Factory Pattern:
  - `BaseNotifier`: Abstract Base Class định nghĩa phương thức `send(...)`.
  - `ToastNotifier`: Gửi Windows Toast qua PowerShell BurntToast ở chế độ câm (`-Silent`), đồng thời dùng trực tiếp Windows Multimedia API (`ctypes.windll.winmm.mciSendStringW`) để phát file âm thanh `.mp3`/`.wav` nhằm tránh sandbox UWP chặn file từ ổ đĩa ngoài.
  - `TelegramNotifier`: Gửi tin nhắn và cảnh báo qua Telegram Bot REST API.
  - `NtfyNotifier`: Gửi thông báo đẩy tức thì tới ứng dụng di động ntfy (Android/iOS/Web).

### 6.5. Hệ thống Xử lý Lỗi Tập Trung ([`src/utils/errors.py`](file:///d:/D-Documents/TOOLs/mod/src/utils/errors.py))
- Định nghĩa các Exception chuẩn hóa kế thừa từ `ModCLIError`:
  - `MissingActionError`: Báo lỗi khi người dùng chỉ gõ `mod <type>` mà thiếu action, tự động in danh sách các action hợp lệ.
  - `InvalidActionError`: Báo lỗi khi action không nằm trong danh mục hỗ trợ, hiển thị gợi ý cú pháp.
  - `InvalidTypeError`: Báo lỗi khi gõ sai nhóm lệnh `type`.

---

## 7. Quy Chuẩn Dành Cho AI Agent (AI Agent Standard Operating Procedures)

Khi AI Agent thực hiện thêm, sửa hoặc tối ưu tính năng trên Mod CLI, bắt buộc tuân thủ SOP trong [`.agent/skills/mod-cli-developer/SKILL.md`](file:///d:/D-Documents/TOOLs/mod/.agent/skills/mod-cli-developer/SKILL.md):

1. **Nguyên tắc an toàn mã nguồn:** Nếu có thay đổi chưa commit, luôn chạy `git stash push -u -m "<mô_tả>"` trước khi sửa file.
2. **Quy trình 5 bước phát triển tính năng:**
   - **Bước 1:** Tạo hoặc chỉnh sửa feature script tại `src/features/`.
   - **Bước 2:** Khai báo hằng số và định tuyến trong `src/main.py`.
   - **Bước 3:** Đăng ký autocomplete trong `TYPE_ACTION_MAP` tại `src/utils/interactive_cli.py`.
   - **Bước 4:** Cập nhật tài liệu 2 lớp:
     - `src/contents/help.txt` (tóm tắt lệnh).
     - `src/contents/app_features.yml` (catalog chi tiết cho `--info`).
     - *(Chỉ cập nhật `PROJECT_CONTEXT.md` khi có thay đổi về kiến trúc hệ thống, cấu hình runtime hoặc cơ chế nền tảng).*
   - **Bước 5:** Kiểm thử thực thi (`mod <type> <action> --info` và chạy thử lệnh thực tế).
3. **Quy trình commit & push:** Tuân thủ [`.agent/skills/mod-git-commit/SKILL.md`](file:///d:/D-Documents/TOOLs/mod/.agent/skills/mod-git-commit/SKILL.md) và chạy `mod git commit -m "<conventional_commit_msg>"`.

---

## 8. Các Lưu Ý Kỹ Thuật Quan Trọng (Crucial Caveats)

1. **Tuyệt đối không chuyển Dispatcher sang `argparse`:** Phải giữ nguyên cơ chế manual parsing để bảo toàn tính linh hoạt của argument forwarding.
2. **Bảo mật:** Không bao giờ commit file `.env`, API key, token cá nhân hoặc thông tin nhạy cảm lên Git repository công khai.
3. **Thao tác dữ liệu nhạy cảm:** Các lệnh có tác vụ xóa file hàng loạt (`file delete`, `file keep`, `gdrive del-fd`, `gdrive reset`, `gist delete`) luôn phải có kiểm tra an toàn hoặc bước xác nhận trước khi thực thi.
