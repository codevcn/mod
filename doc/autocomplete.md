# ⌨️ Tài Liệu Toàn Diện Về Chế Độ Tương Tác & Tính Năng Auto-Complete (Mod CLI)

Tài liệu này cung cấp toàn bộ kiến trúc, thiết kế luồng dữ liệu, thuật toán nội bộ, cơ chế quản lý con trỏ, hệ thống lịch sử lệnh và quy chuẩn bảo trì cho **Chế Độ Tương Tác (Interactive Mode / REPL)** và **Tính Năng Auto-Complete** trong hệ thống **Mod CLI (`mod`)**.

---

## 📑 Mục Lục
1. [Tổng Quan & Cách Kích Hoạt](#1-tổng-quan--cách-kích-hoạt)
2. [Hướng Dẫn Trải Nghiệm Người Dùng (UX Guide)](#2-hướng-dẫn-trải-nghiệm-người-dùng-ux-guide)
   - [2.1. Tự động hoàn thành & Xoay vòng Nhóm lệnh (Type Completion)](#21-tự-động-hoàn-thành--xoay-vòng-nhóm-lệnh-type-completion)
   - [2.2. Tự động hoàn thành & Xoay vòng Hành động (Action Completion)](#22-tự-động-hoàn-thành--xoay-vòng-hành-động-action-completion)
   - [2.3. Bảo toàn tham số phụ khi đổi lệnh (Extra Arguments Preservation)](#23-bảo-toàn-tham-số-phụ-khi-đổi-lệnh-extra-arguments-preservation)
   - [2.4. Điều khiển con trỏ nội dòng (In-Line Cursor Navigation)](#24-điều-khiển-con-trỏ-nội-dòng-in-line-cursor-navigation)
   - [2.5. Lịch sử lệnh với Draft Preservation (Command History)](#25-lịch-sử-lệnh-với-draft-preservation-command-history)
   - [2.6. Tô màu cú pháp thời gian thực (Real-time Syntax Highlighting)](#26-tô-màu-cú-pháp-thời-gian-thực-real-time-syntax-highlighting)
3. [Sơ Đồ Kiến Trúc & Luồng Dữ Liệu (Architecture & Workflow)](#3-sơ-đồ-kiến-trúc--luồng-dữ-liệu-architecture--workflow)
4. [Chi Tiết Kỹ Thuật Từng Phân Hệ](#4-chi-tiết-kỹ-thuật-từng-phân-hệ)
   - [4.1. Hạ tầng I/O mức thấp với `msvcrt` & Fallback đa nền tảng](#41-hạ-tầng-io-mức-thấp-với-msvcrt--fallback-đa-nền-tảng)
   - [4.2. Quản lý Buffer, Con trỏ và Cơ chế Render `render_input_line`](#42-quản-lý-buffer-con-trỏ-và-cơ-chế-render-render_input_line)
   - [4.3. Thuật toán Auto-Complete `get_tab_completion` & Stateful Cycling](#43-thuật-toán-auto-complete-get_tab_completion--stateful-cycling)
   - [4.4. Động cơ tô màu cú pháp `format_buffer_colored`](#44-động-cơ-tô-màu-cú-pháp-format_buffer_colored)
   - [4.5. Phân hệ quản lý lịch sử lệnh (Persistent History File)](#45-phân-hệ-quản-lý-lịch-sử-lệnh-persistent-history-file)
   - [4.6. REPL Controller & Điều phối Subprocess an toàn](#46-repl-controller--điều-phối-subprocess-an-toàn)
5. [Bảng Tra Cứu Phím Bấm & Mã Quét (Key Map Reference)](#5-bảng-tra-cứu-phím-bấm--mã-quét-key-map-reference)
6. [Các Lệnh Tiện Ích Trong Session](#6-các-lệnh-tiện-ích-trong-session)
7. [Quy Chuẩn Đồng Bộ Khi Thêm/Sửa/Xóa Tính Năng (Developer SOP)](#7-quy-chuẩn-đồng-bộ-khi-thêmsửaxóa-tính-năng-developer-sop)

---

## 1. Tổng Quan & Cách Kích Hoạt

Trong Mod CLI, khi người dùng gõ `mod` mà **không truyền bất kỳ tham số nào**, Central Dispatcher (`src/main.py`) sẽ khởi động ngay **Chế độ Tương tác (Interactive Session / REPL)**.

```powershell
mod
```

Màn hình console sẽ in bảng tổng quan danh mục 19 nhóm lệnh (`Types`) kèm các hành động (`Actions`) tương ứng, sau đó hiển thị dấu nhắc lệnh (`prompt`):

```text
=== DANH SÁCH CÁC NHÓM LỆNH (TYPES) HIỆN CÓ ===
──────────────────────────────────────────────────────────────────────
  code     │ Mở các dự án, template, workspace trong IDE
           └── actions: ext, js, nestjs, py, test, ts, ts-template, ws
  compress │ Nén toàn bộ dự án hoặc nén thư mục theo cấu hình JSON
           └── actions: folder, init-ignore
  edit     │ Mở và chỉnh sửa nhanh cấu hình hoặc profile PowerShell
           └── actions: cmds, proms, to
  file     │ Thao tác xử lý file hàng loạt (create, rename, delete, keep)
           └── actions: create, delete, keep, rename
  folder   │ Thao tác xử lý folder (create, dld-path, merge, tree)
           └── actions: create, dld-path, merge, tree
  gdrive   │ Quản lý và đồng bộ Google Drive qua rclone
           └── actions: del-fd, dl, guide, link, list, remote, reset, sync, url
  gist     │ Quản lý CRUD và kiểm toán dung lượng GitHub Gist
           └── actions: audit, create, delete, get, list, rate, reset, update
  git      │ Tự động hóa các thao tác Git (commit & push, remote)
           └── actions: commit, remote
  init     │ Dọn dẹp các tiến trình Windows chạy ngầm và khởi động Unikey
  mcp      │ Thiết lập và copy các thư mục MCP
           └── actions: set
  notify   │ Gửi thông báo qua các kênh ntfy (mặc định), Telegram, Toast...
           └── actions: channels, config, send, test
  open     │ Mở thư mục gốc hoặc các tài nguyên trong Explorer/IDE
           └── actions: env, proms, ws
  print    │ In thông tin cấu hình hệ thống, cURL, status, lệnh hữu ích
           └── actions: cmds, curl, dir, os, stts, ws
  proxy    │ Kiểm tra kết nối và tính hợp lệ của proxy
           └── actions: test
  py       │ Thiết lập môi trường ảo Python (venv) cho dự án
           └── actions: env
  run      │ Thực thi các script tiện ích (unikey, gen-qr, keep-awake...)
           └── actions: gen-qr, keep-awake, keep-screen, srt-count-line, unikey
  skill    │ Thiết lập và copy các thư mục Skill AI từ kho lưu trữ
           └── actions: set
  toast    │ Gửi Windows Toast notification kèm âm thanh tùy chỉnh
           └── actions: --syntax
  tunnel   │ Mở Cloudflare Quick Tunnel cho cổng cục bộ
──────────────────────────────────────────────────────────────────────
💡 Gợi ý: Nhập 'help' hoặc 'h' để xem toàn bộ tài liệu chi tiết.
          Thêm '--info' vào sau bất kỳ lệnh nào (vd: gdrive sync --info) để tra cứu cú pháp & điều kiện.
          Nhấn [↑]/[↓] duyệt lịch sử, nhấn [Tab] tự động điền Type & Action, nhập 'q' để thoát.

mod > 
```

---

## 2. Hướng Dẫn Trải Nghiệm Người Dùng (UX Guide)

### 2.1. Tự động hoàn thành & Xoay vòng Nhóm lệnh (Type Completion)
- Khi ở đầu dòng lệnh, bạn nhập 1 hoặc vài ký tự tiền tố rồi nhấn phím **`[Tab]`**.
- Nếu có nhiều `Type` cùng khớp với tiền tố, nhấn tiếp **`[Tab]`** sẽ **xoay vòng tuần hoàn (cycle)** qua lần lượt các type theo thứ tự A-Z.
- Sau khi hoàn thành Type, hệ thống tự động thêm một dấu cách phía sau để bạn sẵn sàng gõ action.

**Ví dụ:**
```text
mod > g[Tab]         -->  mod > gdrive 
mod > gdrive [Tab]   -->  mod > gist 
mod > gist [Tab]     -->  mod > git 
mod > git [Tab]      -->  mod > gdrive  (quay lại đầu danh sách khớp)

mod > fi[Tab]        -->  mod > file 
mod > fo[Tab]        -->  mod > folder 
mod > no[Tab]        -->  mod > notify 
```

### 2.2. Tự động hoàn thành & Xoay vòng Hành động (Action Completion)
- Sau khi đã có `Type` và dấu cách, nhấn phím **`[Tab]`** để duyệt danh sách các `Action` của nhóm lệnh đó.
- Nếu gõ trước tiền tố của action (vd `mod > gdrive l` + `[Tab]`), hệ thống chỉ xoay vòng giữa các action bắt đầu bằng chữ `l` (`link` $\rightarrow$ `list`).

**Ví dụ:**
```text
mod > gdrive [Tab]          -->  mod > gdrive del-fd 
mod > gdrive del-fd [Tab]   -->  mod > gdrive dl 
mod > gdrive dl [Tab]       -->  mod > gdrive guide 
...
mod > gdrive url [Tab]      -->  mod > gdrive del-fd  (xoay vòng lại)

# Lọc theo tiền tố action:
mod > gdrive l[Tab]         -->  mod > gdrive link 
mod > gdrive link [Tab]     -->  mod > gdrive list 
mod > gdrive list [Tab]     -->  mod > gdrive link 
```

### 2.3. Bảo toàn tham số phụ khi đổi lệnh (Extra Arguments Preservation)
Nếu bạn đã nhập sẵn các tham số dài phía sau (đường dẫn thư mục, link URL, cờ `--tags`, commit message...) nhưng muốn đổi action, việc nhấn `[Tab]` sẽ chỉ thay thế đúng vị trí token `Action` và **giữ nguyên 100% các tham số phía sau**:

**Ví dụ:**
```text
mod > gdrive sync "D:\Projects\App" "backup/app"
# Đặt con trỏ hoặc nhấn Tab tại vị trí action -> đổi sang action khác nhưng giữ nguyên params:
mod > gdrive del-fd "D:\Projects\App" "backup/app"
```

### 2.4. Điều khiển con trỏ nội dòng (In-Line Cursor Navigation)
Chế độ tương tác hỗ trợ đầy đủ các phím điều hướng con trỏ chuẩn xác:
- **`[←]` (Left Arrow):** Di chuyển con trỏ sang trái 1 ký tự (`cursor_pos -= 1`).
- **`[→]` (Right Arrow):** Di chuyển con trỏ sang phải 1 ký tự (`cursor_pos += 1`).
- **`[Home]`:** Đưa con trỏ ngay lập tức về đầu dòng lệnh (`cursor_pos = 0`).
- **`[End]`:** Đưa con trỏ ngay lập tức về cuối dòng lệnh (`cursor_pos = len(buffer)`).
- **Chèn ký tự giữa chuỗi:** Nhập ký tự ở bất kỳ vị trí con trỏ nào, ký tự sẽ được chèn vào giữa và đẩy các ký tự phía sau sang phải mà không bị ghi đè.
- **`[Backspace]` nội dòng:** Xóa ký tự nằm ngay bên trái con trỏ.
- **`[Delete]` nội dòng:** Xóa ký tự nằm ngay tại vị trí con trỏ.

### 2.5. Lịch sử lệnh với Draft Preservation (Command History)
- **`[↑]` (Up Arrow):** Lùi về các câu lệnh đã chạy trước đó trong lịch sử (từ lệnh gần nhất $\rightarrow$ lệnh cũ hơn).
- **`[↓]` (Down Arrow):** Tiến về các câu lệnh mới hơn.
- **Bảo tồn nội dung nháp (Draft Preservation):** Nếu bạn đang gõ dở một câu lệnh (ví dụ: `notify send "Build done" `) rồi bấm `[↑]` để xem lại lệnh cũ, chuỗi đang gõ sẽ được lưu tạm vào `saved_draft`. Khi bấm `[↓]` quay trở lại đáy lịch sử, chuỗi nháp ban đầu sẽ được khôi phục nguyên vẹn.
- **Tự động lưu giữa các phiên (Persistent File):** Tự động lưu trữ tối đa 200 lệnh gần nhất vào `data/credentials/.mod_history` (không commit lên Git).

### 2.6. Tô màu cú pháp thời gian thực (Real-time Syntax Highlighting)
Mỗi khi buffer thay đổi (do gõ phím, backspace, xóa, duyệt lịch sử hay tab autocomplete), chuỗi lệnh được phân tích cú pháp và tô màu tự động theo thời gian thực:
- `mod > `: Prompt màu xanh lá cây đậm (`\033[92;1m`).
- **Type hợp lệ:** Màu xanh lá cây đậm (`\033[92;1m`).
- **Action hợp lệ:** Màu xanh ngọc đậm (`\033[96;1m`).
- **Các tham số, cờ, đường dẫn file:** Màu trắng sáng (`\033[97m`).
- **Từ khóa chưa hợp lệ / đang gõ dở:** Màu trắng thường.

---

## 3. Sơ Đồ Kiến Trúc & Luồng Dữ Liệu (Architecture & Workflow)

Toàn bộ logic tương tác, bắt phím, auto-complete và command history được đóng gói tập trung tại:
📍 **`src/utils/interactive_cli.py`**

```mermaid
flowchart TD
    Start["Khởi động: python src/main.py (Không tham số)"] --> REPLInit["run_interactive_session()\n- print_types_overview()\n- history = load_history()"]
    
    REPLInit --> InputLoop["autocomplete_input(prompt, history)"]
    
    subgraph KeyReader ["Vòng Lặp Đọc Phím Mức Thấp (msvcrt.getwch)"]
        InputLoop --> ReadChar{"Đọc ký tự ch"}
        
        ReadChar -->|"\t" - Tab| TabHandler["get_tab_completion()\n- Phân tích Token 0 / Token 1\n- Xoay vòng modulo candidates\n- cursor_pos = len(buffer)"]
        
        ReadChar -->|"\xe0 + H" - Up Arrow| HistoryUp["history_index -= 1\n- Lấy lệnh cũ từ history\n- Lưu saved_draft nếu ở đáy\n- cursor_pos = len(buffer)"]
        
        ReadChar -->|"\xe0 + P" - Down Arrow| HistoryDown["history_index += 1\n- Lấy lệnh mới hoặc trả saved_draft\n- cursor_pos = len(buffer)"]
        
        ReadChar -->|"\xe0 + K" - Left Arrow| CursorLeft["cursor_pos = max(0, cursor_pos - 1)"]
        ReadChar -->|"\xe0 + M" - Right Arrow| CursorRight["cursor_pos = min(len(buf), cursor_pos + 1)"]
        ReadChar -->|"\xe0 + G" - Home| CursorHome["cursor_pos = 0"]
        ReadChar -->|"\xe0 + O" - End| CursorEnd["cursor_pos = len(buffer)"]
        ReadChar -->|"\xe0 + S" - Delete| DeleteKey["buffer.pop(cursor_pos)"]
        
        ReadChar -->|"\x08" - Backspace| BackspaceHandler["buffer.pop(cursor_pos - 1)\ncursor_pos -= 1"]
        
        ReadChar -->|Ký tự in được| InsertHandler["buffer.insert(cursor_pos, ch)\ncursor_pos += 1"]
        
        ReadChar -->|"\x1b" - Esc| EscHandler["buffer.clear()\ncursor_pos = 0"]
        
        TabHandler --> Render["render_input_line(prompt, buffer, cursor_pos)\n1. format_buffer_colored(buffer)\n2. In: \\r\\033[K + prompt + colored_buffer\n3. Lùi con trỏ: \\033[N D"]
        HistoryUp --> Render
        HistoryDown --> Render
        CursorLeft --> Render
        CursorRight --> Render
        CursorHome --> Render
        CursorEnd --> Render
        DeleteKey --> Render
        BackspaceHandler --> Render
        InsertHandler --> Render
        EscHandler --> Render
        
        ReadChar -->|"\r" hoặc "\n" - Enter| ReturnLine["Trả về buffer chuỗi lệnh"]
    end
    
    ReturnLine --> CheckSpecial{"Kiểm tra lệnh nội bộ?"}
    CheckSpecial -->|"q" / "exit" / "quit"| ExitApp["Kết thúc phiên REPL"]
    CheckSpecial -->|"h" / "help"| PrintHelp["In help.txt ra console"] --> InputLoop
    CheckSpecial -->|"cls" / "clear"| ClearScreen["Xóa màn hình & in lại types"] --> InputLoop
    CheckSpecial -->|"type" / "list" / "ls"| PrintTypes["In lại bảng danh mục Types"] --> InputLoop
    
    CheckSpecial -->|Lệnh thực thi| ExecCmd["1. append_history(history, line)\n2. save_history(history)\n3. Loại bỏ prefix 'mod '\n4. shlex.split(line)\n5. dispatch_callback(feature_args, info_flag, antigravity_flag)"]
    
    ExecCmd --> InputLoop
```

---

## 4. Chi Tiết Kỹ Thuật Từng Phân Hệ

### 4.1. Hạ tầng I/O mức thấp với `msvcrt` & Fallback đa nền tảng
Hàm chuẩn `input()` của Python trên Windows sử dụng *Line-buffered I/O*, chỉ trả về quyền điều khiển khi nhấn Enter và nuốt mất các phím điều hướng (Tab, Arrow keys, Home, End).

Mod CLI sử dụng trực tiếp thư viện C runtime chuẩn của Windows: **`msvcrt.getwch()`**:
* `getwch()` đọc từng phím bấm Unicode tức thời mà không cần nhấn Enter.
* Khi nhấn các phím đặc biệt (mũi tên, Home, End, Delete, F-keys), `getwch()` trả về ký tự tiền tố `\x00` hoặc `\xe0`, tiếp theo là mã quét phụ (scan code).
* **Cơ chế fallback an toàn:** Kiểm tra `sys.stdin.isatty()` và `sys.platform`. Nếu đang chạy trong môi trường không phải Windows hoặc qua pipeline/script tự động, hàm tự động chuyển sang `input()` tiêu chuẩn để không gây lỗi crash.

### 4.2. Quản lý Buffer, Con trỏ và Cơ chế Render `render_input_line`
Hàm `render_input_line` đảm nhiệm việc đồng bộ giữa dữ liệu logic (`buffer`), vị trí con trỏ logic (`cursor_pos`) và vị trí con trỏ thực tế trên terminal:

* `\r`: Đưa con trỏ terminal về đầu dòng.
* `\033[K`: Xóa toàn bộ nội dung từ vị trí con trỏ đến hết dòng hiện tại (tránh hiện tượng để lại rác ký tự khi xóa ngắn dòng).
* `\033[{N}D`: Mã escape ANSI di chuyển con trỏ lùi sang trái $N$ cột (Cursor Back).

### 4.3. Thuật toán Auto-Complete `get_tab_completion` & Stateful Cycling
Thuật toán phân tích trạng thái dòng lệnh và xử lý thông minh theo 2 ngữ cảnh:

```python
def get_tab_completion(
    buffer: str,
    last_was_tab: bool,
    original_prefix: str,
    cycle_idx: int,
) -> tuple[str, str, int, bool]:
    sorted_types = SORTED_TYPES

    # NGỮ CẢNH 1: Đang ở Token 0 (Chưa có dấu cách -> Điền/Xoay vòng Type)
    if " " not in buffer:
        cleaned_buf = buffer.strip().lower()
        if not last_was_tab:
            if cleaned_buf in sorted_types:
                original_prefix = ""
                candidates = sorted_types
                cycle_idx = (sorted_types.index(cleaned_buf) + 1) % len(sorted_types)
                return f"{candidates[cycle_idx]} ", original_prefix, cycle_idx, True
            else:
                original_prefix = cleaned_buf
                cycle_idx = 0
        else:
            cycle_idx += 1

        candidates = [t for t in sorted_types if t.startswith(original_prefix)]
        if not candidates:
            return buffer, original_prefix, cycle_idx, False

        cycle_idx = cycle_idx % len(candidates)
        return f"{candidates[cycle_idx]} ", original_prefix, cycle_idx, True

    # NGỮ CẢNH 2: Đã có Type -> Đang ở Token 1 (Điền/Xoay vòng Action)
    else:
        parts = buffer.split(" ")
        cmd_type = parts[0].strip().lower()
        valid_actions = sorted(TYPE_ACTION_MAP.get(cmd_type, []))
        if not valid_actions:
            return buffer, original_prefix, cycle_idx, False

        action_part = parts[1].strip().lower() if len(parts) > 1 else ""
        rest_of_args = (" " + " ".join(parts[2:])) if len(parts) > 2 else ""

        if not last_was_tab:
            if action_part in valid_actions:
                original_prefix = ""
                candidates = valid_actions
                cycle_idx = (valid_actions.index(action_part) + 1) % len(valid_actions)
                return f"{cmd_type} {candidates[cycle_idx]}{rest_of_args} ", original_prefix, cycle_idx, True
            else:
                original_prefix = action_part
                cycle_idx = 0
        else:
            cycle_idx += 1

        candidates = [a for a in valid_actions if a.startswith(original_prefix)]
        if not candidates:
            return buffer, original_prefix, cycle_idx, False

        cycle_idx = cycle_idx % len(candidates)
        selected_action = candidates[cycle_idx]
        return f"{cmd_type} {selected_action}{rest_of_args} ", original_prefix, cycle_idx, True
```

* **Stateful Cycling:** Lưu vết `original_prefix` ban đầu khi người dùng gõ. Nhờ vậy, khi nhấn Tab liên tục (ví dụ gõ `g` rồi ấn Tab 3 lần), prefix tìm kiếm vẫn là `g` chứ không bị biến thành từ khóa hoàn chỉnh của lần nhấn trước.
* **Modulo Wrap-around:** Khi duyệt đến ứng viên cuối cùng trong danh sách candidates, lần nhấn Tab tiếp theo sẽ quay trở lại ứng viên đầu tiên (`(cycle_idx + 1) % len(candidates)`).

---

### 4.4. Động cơ tô màu cú pháp `format_buffer_colored`
Hàm bóc tách tối đa 2 khoảng trắng đầu tiên để xác định `Type` và `Action`:

```python
def format_buffer_colored(buffer: str) -> str:
    if not buffer:
        return ""

    parts = buffer.split(" ", 2)
    if len(parts) == 1:
        cmd_type = parts[0]
        type_color = f"\033[92;1m{cmd_type}\033[0m" if cmd_type.lower() in TYPE_ACTION_MAP else f"\033[97m{cmd_type}\033[0m"
        return type_color
    elif len(parts) == 2:
        cmd_type, cmd_action = parts[0], parts[1]
        type_color = f"\033[92;1m{cmd_type}\033[0m" if cmd_type.lower() in TYPE_ACTION_MAP else f"\033[97m{cmd_type}\033[0m"
        valid_actions = TYPE_ACTION_MAP.get(cmd_type.lower(), [])
        action_color = f"\033[96;1m{cmd_action}\033[0m" if cmd_action.lower() in valid_actions else f"\033[97m{cmd_action}\033[0m"
        return f"{type_color} {action_color}"
    else:
        cmd_type, cmd_action, rest = parts[0], parts[1], parts[2]
        type_color = f"\033[92;1m{cmd_type}\033[0m" if cmd_type.lower() in TYPE_ACTION_MAP else f"\033[97m{cmd_type}\033[0m"
        valid_actions = TYPE_ACTION_MAP.get(cmd_type.lower(), [])
        action_color = f"\033[96;1m{cmd_action}\033[0m" if cmd_action.lower() in valid_actions else f"\033[97m{cmd_action}\033[0m"
        return f"{type_color} {action_color} \033[97m{rest}\033[0m"
```

---

### 4.5. Phân hệ quản lý lịch sử lệnh (Persistent History File)
- **Vị trí lưu trữ:** `data/credentials/.mod_history` (tự động tạo thư mục nếu chưa có).
- **Quy tắc lọc thông minh (`append_history`):**
  1. Loại bỏ khoảng trắng thừa đầu cuối (`strip()`).
  2. Bỏ qua nếu dòng rỗng.
  3. Bỏ qua các lệnh điều khiển session: `q`, `quit`, `exit`, `cls`, `clear`, `h`, `help`.
  4. Bỏ qua nếu trùng lặp hoàn toàn với câu lệnh ngay liền trước (`history[-1] == line`).
- **Giới hạn số lượng:** Tự động cắt và giữ lại tối đa `MAX_HISTORY_ITEMS = 200` câu lệnh gần nhất.

---

### 4.6. REPL Controller & Điều phối Subprocess an toàn
Khi người dùng xác nhận một câu lệnh bằng phím `Enter`:
1. Ghi nhận vào `history` và lưu vào file `.mod_history`.
2. Kiểm tra nếu người dùng vô tình gõ thừa từ khóa `mod ` ở đầu (ví dụ: `mod gdrive sync ...`), hàm tự động cắt bỏ thành `gdrive sync ...`.
3. Phân tách tham số an toàn bằng `shlex.split(line, posix=False)` (giữ nguyên cặp dấu nháy kép trên Windows).
4. Tách dispatcher flags (`--info`, `-a` / `--antigravity-IDE`).
5. Gọi `dispatch_callback(feature_args, info_flag, antigravity_flag)`:
   - Bọc trong khối `try...except SystemExit` để khi subprocess hoặc lệnh con gọi `sys.exit(0)`, session vẫn tiếp tục vòng lặp mới mà không bị thoát ra ngoài terminal.
   - Bắt `KeyboardInterrupt` để hủy lệnh hiện tại an toàn.

---

## 5. Bảng Tra Cứu Phím Bấm & Mã Quét (Key Map Reference)

| Phím bấm | Mã Byte / Scan Code | Chức năng chi tiết trong Mod CLI |
| :--- | :--- | :--- |
| **`[Tab]`** | `\t` / `0x09` | Kích hoạt Auto-complete / Xoay vòng ứng viên (candidates cycle). |
| **`[←]` (Left Arrow)** | `\xe0` + `'K'` (`0x4B`) | Di chuyển con trỏ sang trái 1 ký tự (`cursor_pos -= 1`). |
| **`[→]` (Right Arrow)** | `\xe0` + `'M'` (`0x4D`) | Di chuyển con trỏ sang phải 1 ký tự (`cursor_pos += 1`). |
| **`[↑]` (Up Arrow)** | `\xe0` + `'H'` (`0x48`) | Lùi về lệnh cũ hơn trong lịch sử, tự lưu bản nháp hiện tại. |
| **`[↓]` (Down Arrow)** | `\xe0` + `'P'` (`0x50`) | Tiến về lệnh mới hơn trong lịch sử, phục hồi bản nháp khi chạm đáy. |
| **`[Home]`** | `\xe0` + `'G'` (`0x47`) | Đưa con trỏ về ngay đầu dòng lệnh (`cursor_pos = 0`). |
| **`[End]`** | `\xe0` + `'O'` (`0x4F`) | Đưa con trỏ về ngay cuối dòng lệnh (`cursor_pos = len(buffer)`). |
| **`[Delete]`** | `\xe0` + `'S'` (`0x53`) | Xóa ký tự nằm ngay tại vị trí con trỏ. |
| **`[Backspace]`** | `\x08` / `0x7F` | Xóa ký tự bên trái con trỏ, vẽ lại dòng và định vị lại con trỏ. |
| **`[Enter]`** | `\r` / `\n` | Kết thúc nhập liệu, trả về buffer cho controller thực thi. |
| **`[Esc]`** | `\x1b` | Xóa sạch buffer dòng hiện tại (hoặc thoát session nếu dòng đang rỗng). |
| **`[Ctrl+C]` / `[Ctrl+D]`** | `\x03` / `0x04` | Thoát phiên làm việc tương tác an toàn. |

---

## 6. Các Lệnh Tiện Ích Trong Session

Khi đang ở trong phiên làm việc tương tác `mod > `, bạn có thể sử dụng các lệnh tắt sau:

| Lệnh | Ý nghĩa |
| :--- | :--- |
| `h` hoặc `help` | Hiển thị toàn bộ tài liệu trợ giúp chi tiết (`help.txt`). |
| `type`, `types`, `list`, `ls` | In lại bảng tổng quan danh mục Type và Action. |
| `cls`, `clear` | Xóa màn hình terminal và in lại bảng gợi ý. |
| `q`, `quit`, `exit` | Thoát khỏi phiên làm việc tương tác. |
| `<cmd> --info` | Xem mô tả chi tiết, cú pháp và điều kiện thực thi của lệnh đó. |
| Gõ `mod <cmd>` | Hệ thống tự động nhận diện và loại bỏ từ khóa `mod` thừa nếu bạn lỡ tay gõ đầy đủ (vd: `mod gdrive sync` -> tự chạy `gdrive sync`). |

---

## 7. Quy Chuẩn Đồng Bộ Khi Phát Triển Tính Năng Mới

Mỗi khi bạn thêm, sửa hoặc xóa tính năng trong Mod CLI:
1. **Thêm một nhóm lệnh mới (`Type`)**: Phải khai báo vào `TYPE_ACTION_MAP` và `TYPE_DESCRIPTIONS` trong `src/utils/interactive_cli.py`.
2. **Thêm/Sửa/Xóa một hành động (`Action`)**: Phải cập nhật danh sách mảng của Type đó trong `TYPE_ACTION_MAP` (luôn giữ thứ tự **sắp xếp A-Z**).

### Ví dụ khi thêm action `backup` vào type `gdrive`:
```python
# Trong src/utils/interactive_cli.py
TYPE_ACTION_MAP = {
    # ...
    "gdrive": [
        "backup",
        "del-fd",
        "dl",
        "guide",
        "link",
        "list",
        "remote",
        "reset",
        "sync",
        "url",
    ],
    # ...
}
```

Việc này đảm bảo tính năng **Tab Auto-complete** luôn hoạt động chính xác và đồng bộ 100% với các tài liệu `help.txt`, `app_features.yml`, `PROJECT_CONTEXT.md` và bộ định tuyến `src/main.py`.
