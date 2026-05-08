# Kiến trúc hệ thống CLI Dispatcher

Tài liệu này mô tả cách xây dựng một hệ thống CLI dùng một file trung tâm để nhận lệnh, phân tích tham số, rồi điều phối sang các script con. Nội dung được viết theo hướng tổng quát để có thể áp dụng cho các project automation tương tự, không phụ thuộc vào đường dẫn, máy tính, tài khoản, hoặc tên riêng của một project cụ thể.

---

## 1. Mục tiêu kiến trúc

Hệ thống được thiết kế cho các bộ công cụ cá nhân hoặc nội bộ cần gom nhiều thao tác nhỏ vào một lệnh CLI thống nhất.

Các mục tiêu chính:

- Có một entry point dễ nhớ cho người dùng.
- Có một dispatcher trung tâm để định tuyến lệnh.
- Tách logic nghiệp vụ sang các script độc lập.
- Có tài liệu command-line ngắn gọn cho người dùng cuối.
- Có file mô tả tính năng có cấu trúc để tool có thể in mô tả tự động.
- Có quy ước đặt tên hằng số rõ ràng để mở rộng mà ít nhầm lẫn.
- Có cách lưu nhanh project lên remote Git repository.

---

## 2. System Design

Luồng tổng thể:

```text
User
  |
  v
CLI entry point
  |
  v
src/main.py
  |
  +-- manual parse sys.argv
  +-- tách dispatcher flags (--des, -a)
  +-- xác định type / action
  +-- gom remaining args
  +-- dispatch by type/action
  |
  v
handler function
  |
  v
subprocess (forward remaining args) / system command
```

Các thành phần chính:

| Thành phần             | Vai trò                                                                      |
| ---------------------- | ---------------------------------------------------------------------------- |
| CLI entry point        | File lệnh mỏng, chỉ forward toàn bộ tham số vào `src/main.py`.               |
| `src/main.py`          | Dispatcher trung tâm: parse CLI, kiểm tra type/action, gọi handler.          |
| Handler functions      | Hàm nhỏ trong dispatcher, chỉ build command args rồi gọi script con.         |
| `src/features/`        | Script tính năng độc lập, mỗi file xử lý một nhóm nghiệp vụ cụ thể.          |
| `src/features/system/` | Script nội bộ phục vụ chính hệ CLI, ví dụ in nội dung, thao tác Git, status. |
| `src/contents/`        | Tài liệu và dữ liệu tĩnh dùng để in help, mô tả feature, template.           |
| `.env`                 | Cấu hình local, path, token, hoặc thông tin thay đổi theo môi trường.        |
| Remote Git repo        | Nơi lưu version project để backup và đồng bộ nhanh giữa nhiều máy.           |

Nguyên tắc thiết kế:

- Dispatcher không chứa nghiệp vụ nặng.
- Mỗi feature script có thể chạy độc lập nếu truyền đủ tham số.
- Dữ liệu mô tả tính năng không hardcode trong dispatcher.
- Path hoặc config phụ thuộc máy nên đưa vào `.env` hoặc file config.
- Các thao tác nguy hiểm như delete, reset, purge nên có xác nhận hoặc kiểm tra rõ ràng.

---

## 3. Kiến trúc code

### 3.1. Entry point

Entry point nên là một wrapper mỏng:

```cmd
@echo off
python "%~dp0src\main.py" %*
```

Nhiệm vụ của file này chỉ là giúp người dùng gọi lệnh ngắn, ví dụ:

```bash
tool <type> <action> [value] [extra] [flags]
```

Không nên đặt logic nghiệp vụ trong wrapper.

### 3.2. Dispatcher

`src/main.py` là nơi định nghĩa:

- Hằng số type/action/warning.
- Manual parsing `sys.argv` (không dùng `argparse`).
- Các handler function.
- Khối dispatch chính.
- Cơ chế gọi script con bằng `subprocess`.

Dispatcher chỉ xử lý 2 flag riêng:

- `--des`: in mô tả tính năng từ `app_features.yml`.
- `-a` / `--antigravity-IDE`: chọn IDE prefix.

Mọi args sau `action` được gom vào `remaining_args` và forward nguyên vẹn cho feature script.

Mẫu command grammar:

```text
<tool> <type> <action> [args...] [--des] [-a]
```

Ví dụ generic:

```bash
tool print help
tool run rename-files "path/to/folder" "prefix"
tool git commit -m "update feature"
tool feature action --des
tool -a code ws ptb -p
```

### 3.3. Handler

Một handler tốt nên ngắn và chỉ forward remaining args:

```python
def run_feature(remaining_args: list[str]):
    cmd_args = [
        "python",
        get_feature_path("feature_script.py"),
    ]
    cmd_args.extend(remaining_args)

    result = subprocess.run(cmd_args, check=False)
    sys.exit(result.returncode)
```

Quy ước:

- Handler nhận `remaining_args` (list các args sau action) từ dispatcher.
- Handler build command list, extend với remaining_args, rồi gọi subprocess.
- Handler trả đúng exit code của script con.
- Script con chịu trách nhiệm parse args và validate nghiệp vụ chi tiết.

### 3.4. Script con

Script con trong `features` nên có cấu trúc:

```python
def parse_args():
    ...

def validate_inputs(args):
    ...

def main():
    args = parse_args()
    validate_inputs(args)
    ...

if __name__ == "__main__":
    main()
```

Script con nên tự in thông báo lỗi rõ ràng, tự kiểm tra file/folder cần dùng, và hạn chế phụ thuộc vào trạng thái global của dispatcher.

---

## 4. Cách đặt tên hằng số

Hằng số trong dispatcher nên có prefix chung theo tên ứng dụng. Dùng chữ hoa, phân tách bằng `_`.

### 4.1. Type constants

Mẫu:

```python
APP_TYPE_RUN = "run"
APP_TYPE_PRINT = "print"
APP_TYPE_GIT = "git"
```

Quy ước:

- Format: `<APP>_TYPE_<TYPE_NAME>`.
- Giá trị CLI nên là chữ thường, ưu tiên `kebab-case` nếu có nhiều từ.
- Type là nhóm lệnh cấp cao, ví dụ `run`, `print`, `open`, `git`.

### 4.2. Action constants

Mẫu:

```python
APP_RUN_RENAME_FILES = "rename-files"
APP_RUN_DELETE_FILES = "delete-files"
APP_PRINT_HELP = "help"
```

Quy ước:

- Format: `<APP>_<TYPE_NAME>_<ACTION_NAME>`.
- `TYPE_NAME` phải khớp nhóm type chứa action.
- `ACTION_NAME` mô tả hành động cụ thể.
- Giá trị CLI nên ổn định vì người dùng sẽ ghi nhớ và có thể dùng trong script ngoài.

### 4.3. Flag constants

Dispatcher chỉ giữ 2 flag riêng. Các flag khác thuộc về feature script.

Mẫu dispatcher flags:

```python
# Dispatcher flags (xử lý bởi main.py)
APP_FLAG_DESCRIPTION = "--des"
APP_FLAG_ANTIGRAVITY = "-a"
```

Feature-level flags (ví dụ, xử lý bởi script con):

```python
# Trong _git.py
"-m", "--message"   # commit message

# Trong open_main_ws.py
"-p"                # powershell only

# Trong sync_to_gdrive.py
"-d", "--deep"      # deep recursive
"--file"            # list files
```

### 4.4. Warning/status constants

Mẫu:

```python
APP_WARNING_TYPE_WRONG = "WRONG-TYPE"
APP_WARNING_ACTION_MISSING = "MISSING-ACTION"
APP_STATUS_OK = "OK"
```

Quy ước:

- Warning dùng format `<APP>_WARNING_<SCOPE>_<STATE>`.
- Status dùng format `<APP>_STATUS_<STATE>`.
- Giá trị in ra terminal nên ngắn, dễ grep, và ổn định.

### 4.5. Function naming

Python function dùng `snake_case`:

```python
def print_help():
    ...

def run_git_command():
    ...

def open_project_folder():
    ...
```

Tên function nên nói rõ hành động. Tránh tên quá chung như `process`, `handle`, `do`.

---

## 5. Cấu trúc thư mục

Cấu trúc đề xuất:

```text
project-root/
├── .env
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── requirements.txt
├── tool.cmd hoặc tool.sh
│
└── src/
    ├── main.py
    │
    ├── cmd/
    │   └── init.cmd
    │
    ├── contents/
    │   ├── help.txt
    │   ├── app_features.yml
    │   ├── statuses.txt
    │   └── other-static-content.txt
    │
    └── features/
        ├── feature_a.py
        ├── feature_b.py
        ├── system/
        │   ├── _git.py
        │   ├── _print_content.py
        │   └── _statuses.py
        └── integration-name/
            ├── configs.json
            └── integration_script.py
```

Ý nghĩa từng thư mục:

| Thư mục                       | Mục đích                                                                  |
| ----------------------------- | ------------------------------------------------------------------------- |
| `src/cmd/`                    | Batch/shell scripts phục vụ khởi tạo hoặc lệnh hệ điều hành.              |
| `src/contents/`               | File text/YAML dùng làm tài liệu và dữ liệu mô tả.                        |
| `src/features/`               | Script tính năng thực tế mà người dùng gọi qua CLI.                       |
| `src/features/system/`        | Script nội bộ phục vụ framework CLI.                                      |
| `src/features/<integration>/` | Nhóm script/config cho một tích hợp lớn như cloud, storage, browser, API. |

Quy ước:

- File nội bộ có thể bắt đầu bằng `_` để phân biệt với feature người dùng gọi trực tiếp.
- Feature script nên dùng tên mô tả hành động: `rename_files.py`, `print_os_info.py`, `sync_to_remote.py`.
- Không để dữ liệu secret trong repo. Secret đặt trong `.env` hoặc nơi lưu config an toàn.
- File config mẫu có thể commit, file config thật có token nên ignore.

---

## 6. Dùng Git để lưu nhanh project lên remote repo

### 6.1. Thiết lập lần đầu

```bash
git init
git add .
git commit -m "init project"
git branch -M main
git remote add origin <remote-repo-url>
git push -u origin main
```

Trước khi commit, nên có `.gitignore` tối thiểu:

```gitignore
.env
.venv/
venv/
__pycache__/
*.pyc
*.log
*.bak.*
```

### 6.2. Lưu nhanh các thay đổi

```bash
git status
git add .
git commit -m "update tool"
git push origin main
```

Nếu hệ thống có command riêng cho Git, command đó nên làm đúng các bước:

```text
validate repo
git add .
git commit -m "<message>"
git push origin main
return exit code
```

### 6.3. Nguyên tắc an toàn khi dùng Git helper

- Luôn bắt buộc commit message.
- Kiểm tra thư mục hiện tại có phải Git repository không.
- Không tự chạy `git reset --hard`.
- Không tự xóa remote.
- Không commit `.env`, token, file cache, file backup có dữ liệu nhạy cảm.
- Nếu helper dùng branch mặc định, nên cấu hình branch đó bằng biến config thay vì hardcode.

---

## 7. Dùng `help.txt` để mô tả CLI cho người dùng

`src/contents/help.txt` là tài liệu ngắn gọn in ra khi người dùng gọi lệnh không tham số hoặc gọi help.

Mục tiêu của `help.txt`:

- Cho người dùng biết cú pháp tổng quát.
- Liệt kê type/action đang có.
- Mô tả ngắn mỗi action làm gì.
- Nêu các flag phổ biến.
- Đưa ví dụ command thường dùng.

Cấu trúc đề xuất:

```text
# Help for <tool-name>

# Usage:
<tool> <type> <action> [args...] [-a] [--des]

Dispatcher chỉ xử lý 2 flag: --des và -a.
Mọi args sau <action> được forward cho feature script.

# Dispatcher flags:
--des
-a

# Feature-level flags (truyền sau action):
-m, --message     (git commit)
-p                (code ws)
-d, --deep        (gdrive list)
-f, --file        (gdrive list / open)

# Types:
run
print
git

# Actions:
## run:
  rename-files <folder_path> [prefix]
  delete-files <folder_path> <ext1,ext2>

## print:
  help
  statuses

# Examples:
<tool> run rename-files "path/to/folder" "prefix"
<tool> git commit -m "update"
<tool> feature action --des
```

Quy ước cập nhật:

- Khi thêm type mới trong dispatcher, thêm type đó vào `help.txt`.
- Khi thêm action mới, thêm action vào đúng nhóm.
- Args sau action ghi rõ cú pháp feature script chấp nhận.
- Mô tả trong `help.txt` chỉ nên ngắn. Chi tiết dài để trong `app_features.yml`.
- Ví dụ command trong `help.txt` nên chạy được hoặc gần với cú pháp thật.

---

## 8. Dùng `app_features.yml` để mô tả toàn bộ tính năng

`src/contents/app_features.yml` là catalog có cấu trúc cho toàn bộ tính năng. File này phục vụ lệnh kiểu `--des`, giúp in mô tả chi tiết cho một command cụ thể.

Mục tiêu của `app_features.yml`:

- Là nguồn mô tả đầy đủ hơn `help.txt`.
- Có thể parse bằng code.
- Mỗi action có title, command, summary, details, conditions.
- Giúp người dùng xem mô tả theo type/action mà không phải mở tài liệu dài.

Cấu trúc đề xuất:

```yaml
tool:
  flags:
    - flag: "-h / --help"
      description: "In help ra terminal."

  types:
    - name: "run"
      description: "Thực thi các script tiện ích."
      actions:
        - id: "RUN_001"
          title: "Rename Files"
          command: '<tool> run rename-files "<folder_path>" "<prefix>"'
          summary: "Đổi tên file trong một thư mục theo prefix."
          details: "Script đọc các file cấp 1, sắp xếp, đổi tên theo pattern ổn định."
          conditions: "Folder phải tồn tại. Prefix nên là chuỗi không rỗng."

    - name: "print"
      description: "In thông tin ra terminal."
      actions:
        - id: "PRINT_001"
          title: "Print Help"
          command: "<tool> print help"
          summary: "In hướng dẫn sử dụng."
          details: "Đọc nội dung từ src/contents/help.txt."
          conditions: "File help.txt phải tồn tại."

  config:
    ROOT_FOLDER_PATH: "Đường dẫn gốc của project."
    CONTENTS_FOLDER_PATH: "Đường dẫn đến thư mục contents."
```

Quy ước nội dung:

- `name` của type phải khớp giá trị CLI trong dispatcher.
- `command` phải chứa command thật để parser tìm được type/action.
- `summary` viết một câu ngắn.
- `details` mô tả behavior chính, input/output, side effect.
- `conditions` ghi dependency, file cần tồn tại, quyền cần có, hoặc cảnh báo.
- `id` nên ổn định để dễ tham chiếu trong tài liệu hoặc changelog.

### Quan hệ giữa `help.txt` và `app_features.yml`

| File               | Dành cho                             | Mức chi tiết | Cách dùng                               |
| ------------------ | ------------------------------------ | ------------ | --------------------------------------- |
| `help.txt`         | Người dùng cần nhớ lệnh nhanh        | Ngắn         | In khi gọi help hoặc không truyền lệnh. |
| `app_features.yml` | Người dùng cần hiểu kỹ một tính năng | Chi tiết     | Parse và in khi dùng `--des`.           |

Khi thêm tính năng mới, cập nhật theo thứ tự:

1. Thêm hằng số type/action trong dispatcher.
2. Thêm handler trong dispatcher.
3. Thêm script con nếu cần.
4. Thêm mô tả ngắn vào `help.txt`.
5. Thêm mô tả đầy đủ vào `app_features.yml`.
6. Chạy command `--des` để kiểm tra mô tả được parse đúng.

---

## 9. Quy trình thêm một tính năng mới

Ví dụ thêm command generic:

```bash
tool run compress-files <folder>
```

Các bước:

1. Tạo script `src/features/compress_files.py`. Script tự parse `sys.argv` để lấy args.
2. Đặt hằng số:

```python
APP_RUN_COMPRESS_FILES = "compress-files"
```

3. Tạo handler (nhận remaining_args):

```python
def compress_files(remaining_args: list[str]):
    cmd_args = ["python", get_feature_path("compress_files.py")]
    cmd_args.extend(remaining_args)
    result = subprocess.run(cmd_args, check=False)
    sys.exit(result.returncode)
```

4. Thêm nhánh dispatch:

```python
elif action_included == APP_RUN_COMPRESS_FILES:
    compress_files(remaining_args)
```

5. Cập nhật `help.txt`.
6. Cập nhật `app_features.yml`.
7. Chạy thử:

```bash
tool run compress-files "path/to/folder"
tool run compress-files --des
```

---

## 10. Checklist chất lượng

Trước khi xem một feature là hoàn chỉnh:

- Command có trong dispatcher.
- Command có handler rõ ràng.
- Script con validate input.
- Command có mô tả trong `help.txt`.
- Command có mô tả trong `app_features.yml`.
- Command lỗi có thông báo dễ hiểu.
- Path/config local không hardcode nếu có thể đưa vào `.env`.
- Feature có ví dụ sử dụng.
- Nếu có thao tác xóa/ghi đè, có kiểm tra hoặc xác nhận.
- Thay đổi đã được commit và push lên remote repo.
