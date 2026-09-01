# 📘 Hướng Dẫn Triển Khai Logic Cờ `--info` Trong Mod CLI

Tài liệu này cung cấp toàn bộ kiến trúc, luồng dữ liệu, quy chuẩn cấu trúc và hướng dẫn từng bước để triển khai, bảo trì và tích hợp cơ chế tra cứu tính năng qua cờ **`--info`** trong hệ thống **Mod CLI (`mod`)**.

---

## 📑 Mục Lục
1. [Tổng Quan & Mục Đích](#1-tổng-quan--mục-đích)
2. [Sơ Đồ Kiến Trúc & Luồng Dữ Liệu](#2-sơ-đồ-kiến-trúc--luồng-dữ-liệu)
3. [Cấu Trúc Catalog Dữ Liệu (`app_features.yml`)](#3-cấu-trúc-catalog-dữ-liệu-app_featuresyml)
4. [Logic Bóc Tách Cờ Tại Central Dispatcher](#4-logic-bóc-tách-cờ-tại-central-dispatcher)
5. [Logic Xử Lý & Hiển Thị (`_print_feature_description.py`)](#5-logic-xử-lý--hiển-thị-_print_feature_descriptionpy)
6. [Cơ Chế Nạp Tài Liệu Nâng Cao (`raw_file` & `raw_text`)](#6-cơ-chế-nạp-tài-liệu-nâng-cao-raw_file--raw_text)
7. [Hướng Dẫn Từng Bước Khi Thêm/Sửa Lệnh Mới](#7-hướng-dẫn-từng-bước-khi-thêmsửa-lệnh-mới)
8. [Bộ Test Case Nghiệm Thu (Verification)](#8-bộ-test-case-nghiệm-thu-verification)

---

## 1. Tổng Quan & Mục Đích

Cờ **`--info`** là một trong hai **Dispatcher Flags** toàn cục cốt lõi của Mod CLI (cùng với cờ `-a` / `--antigravity-IDE`).

### Mục đích cốt lõi:
- **Tra cứu không thực thi:** Cho phép người dùng hoặc AI Agent xem cú pháp, tóm tắt nghiệp vụ, giải thích chi tiết và điều kiện tiên quyết của bất kỳ câu lệnh nào mà **không kích hoạt logic thực thi nghiệp vụ**.
- **Tra cứu linh hoạt 3 cấp độ:**
  1. **Cấp hệ thống (Toàn bộ tool):** `mod --info`
  2. **Cấp nhóm lệnh (Type level):** `mod <type> --info` (ví dụ: `mod gist --info`, `mod open --info`)
  3. **Cấp hành động cụ thể (Action level):** `mod <type> <action> --info` (ví dụ: `mod gdrive sync --info`, `mod file delete --info`)
- **Vị trí tự do:** Người dùng có thể đặt cờ `--info` ở bất kỳ vị trí nào trong câu lệnh (cuối dòng, giữa các tham số), Dispatcher sẽ tự động tách lọc.

---

## 2. Sơ Đồ Kiến Trúc & Luồng Dữ Liệu

```text
User Input: mod <type> <action> [args...] [--info]
   │
   ▼
mod.cmd (@py src\main.py %*)
   │
   ▼
src/main.py (Central Dispatcher)
   ├── 1. Duyệt sys.argv[1:]: Nếu thấy '--info' -> bật info_flag = True, loại bỏ khỏi feature_args
   ├── 2. Tách: type_included = feature_args[0], action_included = feature_args[1]
   │
   ├── [Nếu info_flag == True]
   │       └── Gọi: print_feature_description(type_included, action_included)
   │               └── Subprocess gọi: src/features/system/_print_feature_description.py
   │                       │
   │                       ├── Đọc catalog: src/contents/app_features.yml
   │                       ├── So khớp block Type và Action
   │                       ├── [Nếu có raw_file / raw_text] ──► Đọc & in trực tiếp nội dung Markdown
   │                       └── [Mặc định] ──► In bảng màu ANSI (Title, Lệnh, Tóm tắt, Chi tiết, Điều kiện)
   │                       └── sys.exit(0)
   │
   └── [Nếu info_flag == False] ──► Dispatch bình thường tới Feature Script
```

---

## 3. Cấu Trúc Catalog Dữ Liệu (`app_features.yml`)

File `src/contents/app_features.yml` là **Single Source of Truth** cung cấp dữ liệu mô tả cho cờ `--info`.

### 3.1. Schema Chuẩn Cho Mỗi Action (Standard Format)

```yaml
mod_tool:
  dispatcher_flags:
    - flag: "--info"
      description: "In mô tả chi tiết command từ app_features.yml."
    - flag: "-a / --antigravity-IDE"
      description: "Dùng Antigravity IDE thay vì VSCode."

  types:
    - name: "<tên_type>"
      description: "<Mô tả ngắn về nhóm lệnh>"
      actions:
        - id: "ACTION <XX>"
          title: "<Tên tính năng ngắn gọn, rõ ràng>"
          command: "mod <type> <action> [args...]"
          summary: "<Tóm tắt 1-2 câu về tác vụ chính>"
          details: "<Giải thích sâu về các cờ con, cách thức xử lý bên dưới>"
          conditions: "<Các điều kiện tiên quyết: PATH, API token, OS, file .env...>"
```

### 3.2. Quy Tắc Khai Báo Trường `command`
- Nếu lệnh có nhiều alias/cú pháp tương đương, dùng dấu gạch đứng `|`:
  ```yaml
  command: "mod gdrive url <remote_path> | mod gdrive link <remote_path>"
  ```
- Dùng dấu `<...>` cho tham số bắt buộc và `[...]` cho tham số tùy chọn:
  ```yaml
  command: "mod file rename <folder_path> [prefix]"
  ```

---

## 4. Logic Bóc Tách Cờ Tại Central Dispatcher

### 4.1. Trong `src/main.py` (CLI Entrypoint)

```python
# 1. Bóc tách flag trước khi xác định type và action
raw_args = sys.argv[1:]
info_flag = False
antigravity_flag = False
feature_args = []

for arg in raw_args:
    if arg == "--info":
        info_flag = True
    elif arg in ("-a", "--antigravity-IDE"):
        antigravity_flag = True
    else:
        feature_args.append(arg)

# 2. Xử lý khi không truyền type (gõ `mod --info` hoặc `mod`)
if not feature_args:
    if info_flag:
        print_feature_description(None, None)
    else:
        run_interactive_session(dispatch_command, print_help)
    sys.exit(0)

# 3. Chuyển tiếp vào dispatch_command
dispatch_command(feature_args, info_flag, antigravity_flag)
```

### 4.2. Trong `dispatch_command()`

```python
def dispatch_command(
    feature_args: list[str],
    info_flag: bool = False,
    antigravity_flag: bool = False,
):
    type_included = feature_args[0] if len(feature_args) > 0 else None
    action_included = feature_args[1] if len(feature_args) > 1 else None
    remaining_args = feature_args[2:]

    # Bắt cờ --info: In mô tả và dừng ngay lập tức
    if info_flag:
        print_feature_description(type_included, action_included)
        sys.exit(0)

    # Nếu không có --info, tiếp tục routing nghiệp vụ...
```

### 4.3. Trong `src/utils/interactive_cli.py` (Interactive Session / REPL)

Trong vòng lặp REPL, các lệnh nhập vào cũng được bóc tách cờ `--info` tương tự:
```python
# Tách dispatcher flags
info_flag = False
antigravity_flag = False
feature_args = []

for arg in args:
    if arg == "--info":
        info_flag = True
    elif arg in ("-a", "--antigravity-IDE"):
        antigravity_flag = True
    else:
        feature_args.append(arg)

dispatch_callback(feature_args, info_flag, antigravity_flag)
```

---

## 5. Logic Xử Lý & Hiển Thị (`_print_feature_description.py`)

File `src/features/system/_print_feature_description.py` chịu trách nhiệm đọc và render dữ liệu từ YAML.

### Thuật Toán Khớp Lệnh (Matching Algorithm):
```python
for t in types:
    if cmd_type and t.get("name") != cmd_type:
        continue

    for a in t.get("actions", []):
        cmd_raw = a.get("command", "")
        cmds = [c.strip() for c in cmd_raw.split("|")]

        for cmd in cmds:
            cmd_parts = cmd.split()
            if cmd_parts and cmd_parts[0] == "mod":
                cmd_parts = cmd_parts[1:]

            yaml_type = cmd_parts[0] if len(cmd_parts) > 0 else None
            yaml_action = (
                cmd_parts[1]
                if len(cmd_parts) > 1
                and not cmd_parts[1].startswith("<")
                and not cmd_parts[1].startswith("[")
                and not cmd_parts[1].startswith("-")
                else None
            )

            target_found = False
            # 1. Tra cứu toàn cục: `mod --info`
            if cmd_type is None and action is None:
                if yaml_type is None or yaml_type.startswith("-"):
                    target_found = True
            # 2. Tra cứu cấp type: `mod <type> --info`
            elif cmd_type is not None and action is None:
                if yaml_type == cmd_type and yaml_action is None:
                    target_found = True
            # 3. Tra cứu cấp action: `mod <type> <action> --info`
            elif cmd_type is not None and action is not None:
                if yaml_type == cmd_type and yaml_action == action:
                    target_found = True
```

### Định Dạng Hiển Thị Chuẩn (ANSI Colors Output):
Khi tìm thấy action, hệ thống format output với mã màu ANSI trực quan:
```python
C = "\033[36m"  # Cyan
G = "\033[32m"  # Green
Y = "\033[33m"  # Yellow
W = "\033[97m"  # White bright
D = "\033[2m"   # Dim
R = "\033[0m"   # Reset

print(f"\n{C}--- Tính năng: {a.get('title')} ---{R}")
print(f"{G}+) Lệnh:{R}\t{Y}{a.get('command')}{R}")
print(f"{G}+) Tóm tắt:{R}\t{W}{a.get('summary')}{R}")
print(f"{G}+) Chi tiết:{R}\t{D}{a.get('details')}{R}")
print(f"{G}+) Điều kiện:{R}\t{D}{a.get('conditions')}{R}\n")
```

---

## 6. Cơ Chế Nạp Tài Liệu Nâng Cao (`raw_file` & `raw_text`)

Đối với các module lớn, phức tạp có tài liệu hướng dẫn riêng (như GitHub Gist Manager), YAML cho phép khai báo trường **`raw_file`** hoặc **`raw_text`** để in trực tiếp file Markdown/Text thay vì format bảng ANSI ngắn gọn.

### Ví Dụ Khai Báo Trong `app_features.yml`:
```yaml
    - name: "gist"
      description: "Quản lý CRUD & Kiểm toán dung lượng GitHub Gist"
      actions:
        - id: "ACTION 50b"
          title: "Tài liệu hướng dẫn sử dụng GitHub Gist"
          command: "mod gist"
          raw_file: "features/gist/README.md"
```

### Logic Xử Lý Bên Dưới:
```python
if "raw_file" in a and a.get("raw_file"):
    raw_rel = a.get("raw_file")
    candidate_paths = [
        Path(SRC_FOLDER) / raw_rel,
        Path(PROJECT_ROOT) / raw_rel,
        Path(raw_rel),
    ]
    for cp in candidate_paths:
        if cp.is_file():
            with open(cp, "r", encoding="utf-8", errors="replace") as f:
                print(f"\n{f.read().strip()}\n")
            sys.exit(0)
    warn_user_error(f"Không tìm thấy file tài liệu: {raw_rel}")
```

---

## 7. Hướng Dẫn Từng Bước Khi Thêm/Sửa Lệnh Mới

Khi phát triển một tính năng mới (ví dụ: `mod backup create <target>`), làm theo 4 bước sau để đảm bảo cờ `--info` hoạt động chuẩn xác:

### Bước 1: Khai báo Catalog trong `src/contents/app_features.yml`
Tìm block `types` tương ứng (hoặc tạo type mới) và thêm action:
```yaml
    - name: "backup"
      description: "Quản lý sao lưu dữ liệu tự động"
      actions:
        - id: "ACTION 62"
          title: "Tạo bản sao lưu mới"
          command: "mod backup create <target_folder> [--dest <path>]"
          summary: "Tạo file nén backup từ thư mục chỉ định."
          details: "Tự động đánh timestamp vào tên file và lưu vào thư mục đích."
          conditions: "Yêu cầu quyền đọc thư mục nguồn."
```

### Bước 2: Khai báo Route trong `src/main.py`
```python
MOD_TYPE_BACKUP = "backup"
MOD_BACKUP_CREATE = "create"

# Trong dispatch_command():
elif type_included == MOD_TYPE_BACKUP:
    valid_actions = [MOD_BACKUP_CREATE]
    if action_included is None:
        raise MissingActionError(type_included, valid_actions)
    elif action_included not in valid_actions:
        raise InvalidActionError(type_included, action_included, valid_actions)
    cmd_backup(action_included, remaining_args)
```

### Bước 3: Đồng bộ `src/contents/help.txt` và `PROJECT_CONTEXT.md`
Thêm dòng tóm tắt vào `help.txt` và bảng tra cứu lệnh trong `PROJECT_CONTEXT.md`.

### Bước 4: Kiểm thử cờ `--info`
Chạy lệnh kiểm tra:
```bash
python src/main.py backup create --info
```

---

## 8. Bộ Test Case Nghiệm Thu (Verification)

| STT | Câu lệnh kiểm thử | Kết quả mong đợi |
| :---: | :--- | :--- |
| **1** | `mod --info` | In thông tin tính năng trợ giúp chung (`mod | mod -h`). |
| **2** | `mod <type> <action> --info` | In đúng block Title, Lệnh, Tóm tắt, Chi tiết, Điều kiện của action đó. |
| **3** | `mod <type> --info` (Type có `raw_file`) | Đọc và in toàn bộ nội dung file Markdown chỉ định (vd: `mod gist --info`). |
| **4** | `mod <type> <action> arg1 arg2 --info` | Cờ `--info` đặt ở cuối vẫn được lọc ra và in mô tả thành công. |
| **5** | `mod invalid_type invalid_act --info` | In thông báo `>>> Warn: Không tìm thấy mô tả cho lệnh...` với exit code 0. |
| **6** | Chạy trong chế độ tương tác `mod >` | Nhập `<cmd> --info` hiển thị mô tả mà không thoát khỏi session REPL. |
