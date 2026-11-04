# Mod CLI - Bộ Công Cụ Dòng Lệnh Tự Động Hóa Đa Năng Cho Windows

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com/windows)
[![Architecture](https://img.shields.io/badge/architecture-Dispatcher--Feature--Pattern-orange.svg)](#kiến-trúc-hệ-thống)

**Mod CLI (`mod`)** là công cụ dòng lệnh trung tâm (Unified Command-Line Toolkit) được xây dựng riêng cho môi trường **Windows** (PowerShell, Windows Terminal, CMD), giúp gom toàn bộ các tác vụ tự động hóa hàng ngày, quản lý dự án, cấu hình AI Agent, thao tác file, đồng bộ đám mây và tiện ích hệ điều hành vào một câu lệnh duy nhất: `mod <type> <action> [args...]`.

---

## Mục Lục

- [Tính Năng Nổi Bật](#tính-năng-nổi-bật)
- [Công Nghệ Sử Dụng (Tech Stack)](#công-nghệ-sử-dụng-tech-stack)
- [Yêu Cầu Hệ Thống (Prerequisites)](#yêu-cầu-hệ-thống-prerequisites)
- [Cài Đặt & Thiết Lập (Getting Started)](#cài-đặt--thiết-lập-getting-started)
- [Cấu Hình Biến Môi Trường & Đường Dẫn](#cấu-hình-biến-môi-trường--đường-dẫn)
- [Kiến Trúc Hệ Thống (Architecture)](#kiến-trúc-hệ-thống-architecture)
- [Cú Pháp & Quy Tắc Dòng Lệnh](#cú-pháp--quy-tắc-dòng-lệnh)
- [Bảng Tra Cứu Toàn Bộ Nhóm Lệnh (Command Reference)](#bảng-tra-cứu-toàn-bộ-nhóm-lệnh-command-reference)
- [Chế Độ Tương Tác REPL & Tab Autocomplete](#chế-độ-tương-tác-repl--tab-autocomplete)
- [Bảo Trì & Mở Rộng Tính Năng](#bảo-trì--mở-rộng-tính-năng)

---

## Tính Năng Nổi Bật

- 🚀 **Quản lý AI Skills & MCP Servers:** Quản lý kho AI Skills tập trung (`mod skill`), cài đặt trực tiếp vào project theo chuẩn Open Agent Skills (`.agents/skills`), cài đặt vào Global AI Agent (`Antigravity`, `OpenAI Codex`, `Claude Code`), tìm kiếm skill theo từ khóa (`mod skill find`), bật/tắt tự động gọi (`on-invo`/`off-invo`) và mở nhanh cấu hình MCP (`mod mcp open-config`).
- 📂 **Kiểm Tra & Quản Lý Đường Dẫn Tập Trung:** Lệnh `mod paths` (alias `mod path`) in toàn bộ danh sách đường dẫn cấu hình trong `paths.py`, lọc nhanh theo từ khóa (`-k`, `--key`), kiểm tra trạng thái tồn tại trên máy (`[TỒN TẠI]` / `[CHƯA TẠO]`).
- 📁 **Mở Tài Nguyên & Workspace Siêu Tốc:** Mở nhanh các workspace lập trình, thư mục dự án, biến môi trường Windows, kho template, hoặc tự đăng ký và quản lý alias đường dẫn cá nhân (`mod open add/list/rm/<alias>`) với hỗ trợ mở trực tiếp trong VSCode hoặc Antigravity IDE (`-c` / `-a`).
- 🔄 **Tự Động Hóa Git Nâng Cao:** `mod git commit` (tự động add, commit và push), tải thư mục hoặc file đơn lẻ từ bất kỳ GitHub repo nào mà không cần clone cả repo (`mod git dl-folder`, `mod git dl-file`), và quản lý danh sách Git Stash kèm menu drop tương tác an toàn (`mod git stash list`, `mod git drop`).
- ☁️ **Tích Hợp Google Drive & GitHub Gist:** Đồng bộ tự động và lấy link web chia sẻ qua rclone (`mod gdrive sync/list/dl`), quản lý toàn diện GitHub Gists cá nhân kèm tính năng kiểm toán dung lượng, cảnh báo file lớn và kiểm tra rate limit API (`mod gist`).
- 🗜️ **Nén Mã Nguồn Dự Án Thông Minh:** Nén dự án theo timestamp (`mod compress`), nén thư mục bất kỳ hỗ trợ bộ lọc `.compressignore` hoặc cấu hình JSON (`include-items`, `exclude-items`).
- 🔍 **Tìm Kiếm File & Folder DFS Tối Ưu:** Thuật toán DFS không đệ quy cắt tỉa thông minh hơn 15 loại thư mục rác (`node_modules`, `.git`, `.venv`...), hỗ trợ tìm kiếm substring hoặc wildcard (`mod find file/folder`).
- 🔔 **Hệ Thống Thông Báo Đa Kênh:** Gửi thông báo tới app điện thoại Ntfy, Telegram Bot hoặc Windows Toast Notification kèm âm thanh cá nhân (`.mp3`/`.wav`) vượt qua sandbox UWP của Windows (`mod notify`, `mod toast`).
- 💻 **Chế Độ Tương Tác REPL:** Giao diện dòng lệnh thời gian thực (`mod`) với tính năng Tab Autocomplete xoay vòng Type/Action và duyệt lịch sử lệnh bàn phím.
- 📖 **Hệ Thống Tra Cứu Tự Tài Liệu Hóa:** Tra cứu chi tiết từng lệnh ngay tại CLI với cờ `--info` (lấy dữ liệu từ `src/contents/app_features.yml`) hoặc xem tóm tắt với `mod --help`.

---

## Công Nghệ Sử Dụng (Tech Stack)

- **Ngôn ngữ cốt lõi:** Python 3.12+ (hỗ trợ Windows Console UTF-8 toàn diện).
- **CLI Wrapper & Shell:** Batch Script (`mod.cmd`), Windows PowerShell, Windows Terminal (`wt.exe`).
- **Thư viện Python:**
  - `PyYAML`: Phân tích và quản lý catalog tài liệu tính năng chi tiết `app_features.yml`.
  - `requests`: Tương tác REST API (GitHub Gist, Telegram Bot, Ntfy, proxy tester).
  - `python-dotenv`: Quản lý biến môi trường bảo mật runtime.
  - `qrcode`: Sinh mã QR Code ảnh từ terminal.
  - `colorama` / `rich`: Xuất dữ liệu có màu ANSI và định dạng bảng trực quan.
- **Tích Hợp Hệ Điều Hành & Win32 API:**
  - `msvcrt`: Bắt phím thời gian thực cho REPL Tab Autocomplete.
  - `ctypes` (`winmm.dll`, `kernel32.dll`): Phát âm thanh thông báo và giữ sáng màn hình Windows (`SetThreadExecutionState`).
  - `BurntToast` PowerShell module: Gửi Windows Action Center Toast Notifications.
  - `rclone`: Đồng bộ và quản lý file đám mây Google Drive.

---

## Yêu Cầu Hệ Thống (Prerequisites)

- **Hệ điều hành:** Windows 10 hoặc Windows 11 (64-bit).
- **Python:** Phiên bản 3.12 trở lên (đã tích hợp vào `PATH`).
- **Git:** Đã cài đặt và có trong `PATH` (phục vụ nhóm lệnh `mod git`).
- **VSCode hoặc Antigravity IDE:** Đã cấu hình lệnh CLI `code` hoặc `anti` trong `PATH`.
- **rclone (Tùy chọn):** Cần thiết nếu sử dụng các tính năng Google Drive (`mod gdrive`).
- **BurntToast (Tùy chọn):** Module PowerShell hỗ trợ Toast Notification (`Install-Module -Name BurntToast -Scope CurrentUser`).

---

## Cài Đặt & Thiết Lập (Getting Started)

### Bước 1: Tải hoặc Clone dự án về máy
```powershell
git clone https://github.com/codevcn/mod.git "D:/D-Documents/TOOLs/mod"
cd "D:/D-Documents/TOOLs/mod"
```

### Bước 2: Cài đặt các thư viện Python
```powershell
pip install -r requirements.txt
```

### Bước 3: Đăng ký lệnh `mod` vào biến môi trường PATH
Để có thể gõ `mod` từ bất kỳ thư mục hay cửa sổ terminal nào:
1. Mở PowerShell với quyền Administrator (hoặc chỉnh sửa User Environment Variables).
2. Thêm đường dẫn thư mục gốc dự án (ví dụ `D:\D-Documents\TOOLs\mod`) vào biến `PATH`:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";D:\D-Documents\TOOLs\mod", [EnvironmentVariableTarget]::User)
   ```
3. Khởi động lại Terminal. Kiểm tra cài đặt thành công:
   ```powershell
   mod --version
   ```

---

## Cấu Hình Biến Môi Trường & Đường Dẫn

Toàn bộ hệ thống được thiết kế theo nguyên tắc **Zero Hardcoded Paths** với sự phân định rõ ràng giữa file cấu hình đường dẫn và file biến môi trường bảo mật:

### 1. Quản lý đường dẫn tập trung ([`src/configs/paths.py`](file:///d:/D-Documents/TOOLs/mod/src/configs/paths.py))
Khi chuyển máy tính hoặc đổi cấu trúc ổ đĩa, bạn **chỉ cần mở duy nhất file này** để điều chỉnh các thư mục ngoài máy:
- `APPDATA_FOLDER`: Thư mục lưu dữ liệu app (QR code, open_aliases.json) - mặc định `D:/D-AppData/me-mod`.
- `SKILLS_FOLDER_PATH`: Kho lưu trữ AI Skills tập trung - mặc định `D:/D-Documents/SKILLs`.
- `LOCAL_ABSOLUTE_FOLDER_PATH`: Kho lưu trữ MCP Servers - mặc định `D:/D-Documents/MCP`.
- `VSCODE_WORKSPACES_FOLDER`: Thư mục chứa các file workspace IDE.
- `SOURCE_FILES_FOLDER`: Kho chứa mã nguồn template mẫu.
- Các đường dẫn cấu hình AI Agent tự động suy ra theo `Path.home()` (`~/.gemini/config/skills`, `~/.codex/skills`, `~/.claude/skills`...).

> [!TIP]
> Bạn có thể kiểm tra nhanh toàn bộ đường dẫn đang cấu hình bằng lệnh:
> ```bash
> mod paths
> mod paths -k skill
> ```

### 2. File bảo mật runtime (`.env` tại thư mục gốc)
Tạo file `.env` tại thư mục gốc nếu bạn sử dụng các tính năng thông báo Telegram hoặc GitHub Gist (file này được Git bỏ qua để bảo mật):
```env
# Telegram Notification Bot (Tùy chọn)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# GitHub Gist API (Tùy chọn - Yêu cầu PAT có quyền gist)
GITHUB_GIST_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Kiến Trúc Hệ Thống (Architecture)

Mod CLI áp dụng mô hình kiến trúc **Dispatcher - Feature Script Pattern**:

```text
User Input: mod <type> <action> [args...] [-a] [--info]
    │
    ▼
mod.cmd  (Wrapper cực mỏng: @py "%~dp0src\main.py" %*)
    │
    ▼
src/main.py (Central Dispatcher)
    ├── Tự động thiết lập UTF-8 Console
    ├── Tách các Dispatcher Flags (--version / -v, --info / --des, -a / --antigravity-IDE)
    ├── Nếu không có tham số: Khởi chạy Interactive REPL (src/utils/interactive_cli.py)
    ├── Xác định type & action hợp lệ
    ├── Forward nguyên vẹn toàn bộ remaining_args
    └── Điều hướng tới Handler tương ứng
            │
            ├── subprocess.run / Gọi Module nội bộ
            ▼
    src/features/<domain>/<script>.py
    (Tự parse remaining_args, validate logic nghiệp vụ & thực thi độc lập)
```

### Nguyên Tắc Thiết Kế:
1. **Dispatcher mỏng (Thin Dispatcher):** `src/main.py` không dùng `argparse` mà parse thủ công để bảo toàn tham số cho các script con; không chứa logic nghiệp vụ nặng.
2. **Feature độc lập:** Mỗi script trong `src/features/` có thể chạy độc lập qua `python src/features/<script>.py [args]`.
3. **Tài liệu tự sinh (Self-Documenting):** Lệnh `mod <type> <action> --info` tự động trích xuất catalog chi tiết từ `src/contents/app_features.yml`.

---

## Cú Pháp & Quy Tắc Dòng Lệnh

```bash
mod <type> [action] [arguments...] [-a] [--info]
```

### Cờ Điều Phối Toàn Cục (Dispatcher Flags):
| Cờ | Ý Nghĩa |
| :--- | :--- |
| `-v`, `--version` | In thông tin phiên bản chính thức và mô tả công cụ. |
| `--info`, `--des` | In mô tả chi tiết, cú pháp, tóm tắt và điều kiện thực thi của lệnh lấy từ catalog YAML. |
| `-a`, `--antigravity-IDE` | Sử dụng IDE `anti` (Google Antigravity) thay vì `code` (VSCode mặc định). |
| `-h`, `--help` | In bảng trợ giúp tóm tắt toàn bộ câu lệnh của hệ thống. |

---

## Bảng Tra Cứu Toàn Bộ Nhóm Lệnh (Command Reference)

### 1. Nhóm `paths` - Quản Lý & Kiểm Tra Đường Dẫn Tập Trung
```bash
mod paths                      # In toàn bộ 35+ đường dẫn cấu hình và trạng thái tồn tại thực tế
mod paths -k skill             # Lọc các đường dẫn có chứa từ khóa 'skill'
mod paths --key "Program Files" # Tìm kiếm đường dẫn có khoảng trắng (case-insensitive)
mod path -k "me-mod"           # Hỗ trợ alias 'mod path'
```

### 2. Nhóm `skill` - Quản Lý AI Skills Chuẩn Open Agent Skills
```bash
mod skill set [skill_name] [dest]   # Copy skill từ kho trung tâm vào thư mục đích
mod skill set [name] --project      # Cài đặt trực tiếp vào thư mục chuẩn .agents/skills của project
mod skill prj [name]                # Alias cài đặt nhanh vào .agents/skills của project hiện tại (CWD)
mod skill set [name] --agent agy    # Cài đặt vào thư mục Global của AI Agent (agy, codex, claude, all)
mod skill set --key ssr             # Lọc skill theo từ khóa trước khi cài đặt
mod skill find <keyword>            # Tìm kiếm skill trong kho theo tên hoặc đường dẫn (alias: mod skill search)
mod skill list                      # Liệt kê skill trong kho trung tâm (alias: mod skill ls)
mod skill list-project              # Liệt kê skill đang có trong project hiện tại (alias: mod skill ls-prj)
mod skill open [-c]                 # Mở thư mục kho AI Skills trong Explorer (hoặc IDE với -c)
mod skill on-invo [skill_name]      # Bật tự động gọi skill bằng AI (xóa disable-model-invocation)
mod skill off-invo [skill_name]     # Tắt tự động gọi skill bằng AI (thêm disable-model-invocation: true)
mod skill remove [skill_name]       # Xóa skill khỏi kho hoặc khỏi AI Agent (alias: mod skill rm)
```

### 3. Nhóm `open` - Mở Nhanh Thư Mục & Quản Lý Alias
```bash
mod open                            # Mở thư mục gốc của project Mod trong Explorer
mod open -c                         # Mở thư mục gốc trong IDE
mod open ws                         # Mở thư mục VSCode Workspaces
mod open env                        # Mở cửa sổ cấu hình biến môi trường Windows
mod open mcp                        # Mở thư mục kho template MCP Servers
mod open skills                     # Mở thư mục kho AI Skills (alias: mod skill open)
mod open src-files [-c]             # Mở kho template mã nguồn Source-Files (hỗ trợ cờ -c mở IDE)
mod open agy-mcp-conf               # Mở file cấu hình MCP của Google Antigravity bằng Notepad
mod open codex-mcp-conf             # Mở file cấu hình MCP của OpenAI Codex bằng Notepad
mod open clau-mcp-conf              # Mở file cấu hình MCP của Claude Code bằng Notepad
mod open ssh-conf                   # Mở file cấu hình SSH (~/.ssh/config) bằng Notepad
mod open agy-skills                 # Mở thư mục Global Skills của Antigravity
mod open codex-skills               # Mở thư mục Global Skills của OpenAI Codex
mod open clau-skills                # Mở thư mục Global Skills của Claude Code
mod open add <alias> <path>         # Đăng ký alias mở nhanh thư mục tùy chỉnh
mod open list                       # Xem danh sách alias đã đăng ký và trạng thái tồn tại (alias: mod open ls)
mod open rm <alias>                 # Xóa một alias đã đăng ký
mod open <alias> [-c]               # Mở thư mục theo alias trong Explorer hoặc IDE với -c
```

### 4. Nhóm `git` - Tự Động Hóa Git & Thao Tác GitHub
```bash
mod git commit -m "feat: my commit" # Tự động: git add . -> git commit -m -> git push origin main
mod git dl-folder <github_url> [d]  # Tải đệ quy 1 thư mục từ GitHub repo về máy (không kèm .git)
mod git dl-file <github_url> [d]    # Tải 1 file đơn lẻ từ GitHub repo về máy
mod git stash list                  # Liệt kê các stash trong kho lưu trữ mod (alias: mod git stash ls)
mod git drop [stash_index] [-y]     # Xóa stash theo menu tương tác hoặc chỉ định trực tiếp (alias: mod git stash drop)
mod git remote                      # In danh sách Git Remote URL hiện tại (git remote -v)
```

### 5. Nhóm `gist` - Quản Lý & Kiểm Toán GitHub Gist
```bash
mod gist list [--all]               # Liệt kê danh sách Gist của tài khoản dạng bảng trực quan
mod gist create [files...] [--desc] # Tạo Gist mới từ file cục bộ hoặc nhập tương tác
mod gist get <gist_id> [--raw file] # Xem metadata Gist, in nội dung raw hoặc lưu về máy (--save <dir>)
mod gist update <gist_id> [--add]   # Cập nhật, thêm hoặc xóa file trong Gist
mod gist delete <gist_id> [-y]      # Xóa vĩnh viễn 1 Gist (có bước xác nhận an toàn)
mod gist audit                      # Quét toàn bộ Gist, kiểm toán dung lượng, cảnh báo file >8MB và rate limit
mod gist rate                       # Kiểm tra hạn mức request GitHub API còn lại và thời gian reset
mod gist reset [gist_id]            # Reset toàn bộ Gist của tài khoản hoặc đưa 1 Gist về placeholder
```

### 6. Nhóm `file` - Thao Tác Tệp Tin Hàng Loạt
```bash
mod file create                     # Menu tương tác chọn và copy template file từ kho SOURCE_FILES_FOLDER
mod file add-src <file> [--folder]  # Thêm tệp vào kho template (hỗ trợ tạo đệ quy subfolder nhiều cấp)
mod file rename <folder> [prefix]   # Đổi tên file hàng loạt thành <prefix>-1.ext, <prefix>-2.ext...
mod file delete <folder> <exts>     # Xóa file cấp 1 theo danh sách đuôi (ví dụ: "tmp,log")
mod file keep <folder> <ext>        # Chỉ giữ lại file có đuôi chỉ định, xóa tất cả các file còn lại
```

### 7. Nhóm `folder` - Thao Tác Thư Mục Chuyên Nghiệp
```bash
mod folder cr-linear <path> [-c ""] # Tạo chuỗi thư mục cha/con linear, tạo file không ghi đè nội dung
mod folder create <dir> [pat] 1 5   # Tạo hàng loạt thư mục tự động tăng chỉ số
mod folder merge <from> <to> [-y]   # Phân tích độ giao thoa cây thư mục và merge nội dung nguồn sang đích
mod folder tree [path] [-l 2]       # In cây thư mục có giới hạn độ sâu và tự động thu gọn thư mục quá lớn
mod folder dld-path [name]          # Cấu hình lại thư mục download mặc định cho tất cả Chrome profiles
```

### 8. Nhóm `find` - Tìm Kiếm File & Folder Tối Ưu (DFS Pruning)
```bash
mod find file [path] --name "*.ts"  # Tìm file theo tên/wildcard (tự động cắt tỉa thư mục rác node_modules...)
mod find file [path] --name "app" -e # Tìm kiếm file khớp chính xác 100%
mod find folder [path] --name "src" # Tìm thư mục theo tên/wildcard trong dự án
```

### 9. Nhóm `compress` - Nén Dự Án Thông Minh
```bash
mod compress [output_path]          # Nén toàn bộ dự án hiện tại thành mod-{timestamp}.zip (lọc theo .compressignore)
mod compress folder <path> [-i .ci] # Nén thư mục cục bộ chỉ định theo file ignore hoặc cấu hình JSON
mod compress init-ignore <path>     # Khởi tạo file .compressignore mẫu với các rule tùy chọn
```

### 10. Nhóm `notify` & `toast` - Thông Báo Đa Kênh
```bash
mod notify send "Build OK" --channel ntfy    # Gửi thông báo tới app điện thoại Ntfy (mặc định)
mod notify send "Lỗi server" --channel telegram # Gửi thông báo tới nhóm Telegram
mod notify send "Cảnh báo" --channel toast   # Gửi Windows Desktop Toast Notification
mod notify test                     # Gửi thông báo test ping kiểm tra cấu hình kênh
mod notify channels                 # Liệt kê trạng thái các kênh thông báo hỗ trợ
mod toast "Hoàn tất" "Backup xong" --audio "D:/sound.mp3" # Bắn Toast notification kèm âm thanh tùy chỉnh
mod toast --syntax                  # In cú pháp 1 dòng của mod toast để dễ dàng nhúng vào các batch script khác
```

### 11. Nhóm `code` & `edit` - Workspace & IDE
```bash
mod code                            # Mở thư mục mod trong IDE
mod code ws <ptb|tool> [-p]         # Mở workspace lập trình thiết lập sẵn (-p chỉ mở terminal)
mod code test / ts / js / py / ext  # Mở nhanh các thư mục testing/template tương ứng trong IDE
mod edit to                         # Mở file PowerShell Profile ($PROFILE) trong Notepad
mod edit note                       # Mở sổ tay ghi chú câu lệnh note.txt trong Notepad
mod edit proms                      # Mở thư mục prompts của Template Replacer Extension
```

### 12. Nhóm Tiện Ích Khác (`run`, `print`, `tunnel`, `proxy`, `py`, `init`, `keep`)
```bash
mod keep                            # Giữ màn hình Windows luôn sáng (bấm 'q' hoặc Ctrl+C để dừng)
mod run unikey                      # Khởi động bộ gõ tiếng Việt UniKey
mod run gen-qr                      # Nhập văn bản tương tác và sinh file ảnh QR Code
mod run keep-awake [url] -i 5m      # Gửi HTTP GET định kỳ giữ server không bị sleep (Render, Kaggle...)
mod run srt-count-line <file.srt>   # Thống kê và đếm số lượng dòng thoại trong file phụ đề SRT
mod print pc-power [-n]             # In chi tiết thông số phần cứng CPU, RAM, Disk, GPU chuẩn Task Manager (hỗ trợ Notepad)
mod print os                        # In thông tin hệ điều hành, CPU, RAM, Network adapter
mod print note [--find <text>] [-n] # In hoặc tìm kiếm các lệnh hữu ích trong note.txt kèm tô màu cú pháp
mod print stts / ws / curl / dir    # In mã trạng thái, danh sách workspace, cURL CRUD snippet, source dir
mod tunnel [port]                   # Mở Cloudflare Quick Tunnel trỏ tới localhost (mặc định port 3000) kèm mã QR
mod proxy test <ip:port:user:pass>  # Kiểm tra kết nối proxy qua Python, cURL và lấy IP thật qua ipify
mod py env                          # Thiết lập toàn diện venv Python, nâng cấp pip và tạo file kích hoạt nhanh
mod init                            # Chạy batch script dọn dẹp task Windows ngầm và bật Unikey
```

---

## Chế Độ Tương Tác REPL & Tab Autocomplete

Khi bạn gõ lệnh `mod` trên terminal mà không truyền bất kỳ tham số nào:
```powershell
mod
```
Hệ thống sẽ chuyển sang giao diện tương tác **REPL thông minh**:
- **Bắt phím thời gian thực:** Không cần gõ xong mới Enter, hệ thống bắt phím trực tiếp bằng `msvcrt`.
- **Tab Autocomplete cho Type:** Gõ tiền tố (ví dụ `sk`) và nhấn `Tab` để tự động hoàn thành thành `skill` (nhấn Tab liên tiếp để xoay vòng danh sách A-Z).
- **Tab Autocomplete cho Action:** Sau khi có type, nhấn `Tab` để hoàn thành action của type đó (ví dụ `mod skill <Tab>` sẽ xoay vòng `find`, `list`, `open`, `set`...).
- **Lịch sử lệnh:** Dùng phím mũi tên `↑` và `↓` để duyệt lại các lệnh đã từng thực thi trong quá khứ (lưu tại `data/credentials/.mod_history`).
- **Thoát nhanh:** Gõ `q` hoặc `exit` để thoát; gõ `h` hoặc `help` để xem bảng trợ giúp.

---

## Bảo Trì & Mở Rộng Tính Năng

Dự án có tài liệu quy chuẩn tác nghiệp chuẩn (SOP) dành cho cả Developer và AI Agent:

- **Bối cảnh kiến trúc & cấu hình cho AI Agent:** Xem tại [`PROJECT_CONTEXT.md`](file:///d:/D-Documents/TOOLs/mod/PROJECT_CONTEXT.md).
- **Quy trình thêm/sửa/xóa tính năng chuẩn mực:** Xem tại [`.agent/skills/mod-cli-developer/SKILL.md`](file:///d:/D-Documents/TOOLs/mod/.agent/skills/mod-cli-developer/SKILL.md).
- **Quy trình kiểm tra, review và Git commit:** Xem tại [`.agent/skills/mod-git-commit/SKILL.md`](file:///d:/D-Documents/TOOLs/mod/.agent/skills/mod-git-commit/SKILL.md).

### Quy Tắc Đồng Bộ Khi Thêm Lệnh Mới:
Khi bổ sung một tính năng mới vào Mod CLI:
1. Tạo script nghiệp vụ độc lập trong `src/features/<tên_tính_năng>.py`.
2. Khai báo hằng số và định tuyến trong `src/main.py`.
3. Đăng ký autocomplete trong `TYPE_ACTION_MAP` tại `src/utils/interactive_cli.py`.
4. Cập nhật tài liệu tóm tắt trong `src/contents/help.txt` (phục vụ `mod --help`).
5. Cập nhật catalog mô tả chi tiết trong `src/contents/app_features.yml` (phục vụ cờ `--info`).
6. Kiểm tra tính năng: `mod <type> <action> --info` và chạy thử nghiệm thực tế.

---

## Giấy Phép & Tác Quyền

Dự án phát triển bởi **codevcn** phục vụ mục đích tự động hóa quy trình làm việc cá nhân trên hệ điều hành Windows.
Mã nguồn mở phục vụ học tập, tùy biến và tham khảo kiến trúc CLI Dispatcher.
