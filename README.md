# Mod CLI

Mod CLI là công cụ dòng lệnh viết bằng Python để gom các tác vụ tự động hóa thường dùng trên Windows vào một lệnh `mod` thống nhất. Project này hoạt động theo mô hình dispatcher: `src/main.py` nhận lệnh, phân tích `type/action/value/extra`, rồi gọi các script con trong `src/system-codes` hoặc `src/useful-codes`.

---

## Tính Năng Chính

- Mở nhanh thư mục project, workspace, Environment Variables và thư mục prompts.
- Mở các preset code/workspace bằng IDE command (`code` mặc định, hoặc `anti` khi dùng `-a`).
- Chạy helper Git để `git add .`, `git commit`, `git push origin main` bằng một lệnh.
- Thao tác file nhanh: tạo file từ template, đổi tên hàng loạt, xóa theo extension, chỉ giữ một extension.
- Cấu hình nhanh download path cho các profile Chrome.
- Sinh QR image từ input text.
- In thông tin hệ thống, status, cURL snippet, command snippet và đường dẫn source.
- Đồng bộ, liệt kê, xóa folder, lấy URL và reset cấu hình Google Drive qua `rclone`.
- Tra cứu mô tả tính năng bằng `--des`, dữ liệu lấy từ `src/contents/app_features.yml`.

---

## Yêu Cầu

- Windows.
- Python 3.12 hoặc mới hơn.
- Git trong PATH nếu dùng nhóm lệnh `git`.
- `rclone` trong PATH nếu dùng nhóm lệnh `gdrive`.
- VSCode CLI `code` hoặc IDE CLI tương thích nếu dùng nhóm lệnh `code`.
- Các package Python trong `requirements.txt`.
- Package `qrcode` nếu dùng `mod run gen-qr`.

---

## Cài Đặt

1. Clone hoặc tải project về một thư mục cố định.

2. Cài dependencies:

```bash
pip install -r requirements.txt
```

3. Tạo file `.env` ở thư mục gốc.

4. Thêm thư mục gốc project vào PATH để gọi được `mod` từ terminal.

---

## Cấu Hình `.env`

Các biến đang được code sử dụng:

```env
ROOT_FOLDER_PATH=<absolute-path-to-project-root>
USEFUL_CODES_FOLDER_PATH=<absolute-path-to-project-root>/src/useful-codes
CONTENTS_FOLDER_PATH=<absolute-path-to-project-root>/src/contents
TEMPLATE_REPLACER_FOLDER_PATH=<absolute-path-to-template-replacer>
MOD_APPDATA_FOLDER_PATH=<absolute-path-to-folder-for-generated-assets>
```

Ý nghĩa:

| Biến                            | Dùng cho                                                        |
| ------------------------------- | --------------------------------------------------------------- |
| `ROOT_FOLDER_PATH`              | Mở project, gọi script nội bộ, chạy Git helper.                 |
| `USEFUL_CODES_FOLDER_PATH`      | Gọi các script trong `src/useful-codes`.                        |
| `CONTENTS_FOLDER_PATH`          | Đọc `help.txt`, `statuses.txt`, `cURL.txt`, `files_source.txt`. |
| `TEMPLATE_REPLACER_FOLDER_PATH` | Mở/chỉnh sửa prompts của Template Replacer.                     |
| `MOD_APPDATA_FOLDER_PATH`       | Nơi lưu ảnh QR được tạo bởi `mod run gen-qr`.                   |

---

## Cú Pháp

```bash
mod [<type> [<action> [<value> [<extra>]]]] [flags]
```

Flags:

| Flag                      | Mô tả                                                                                             |
| ------------------------- | ------------------------------------------------------------------------------------------------- |
| `-h`, `--help`            | In help mặc định của argparse. Khi không truyền type, tool in `src/contents/help.txt`.            |
| `--des`                   | In mô tả chi tiết command từ `src/contents/app_features.yml`.                                     |
| `-m`, `--message`         | Commit message cho `mod git commit`.                                                              |
| `-a`, `--antigravity-IDE` | Dùng IDE command `anti` thay cho `code`.                                                          |
| `-p`, `--powershell-only` | Với workspace preset, chỉ mở terminal, bỏ qua IDE.                                                |
| `-d`, `--deep`            | Dùng cho `mod gdrive list` để liệt kê đệ quy.                                                     |
| `-f`, `--file`            | Dùng cho `mod gdrive list` để liệt kê file; dùng với `mod open` để mở project bằng File Explorer. |

---

## Các Nhóm Lệnh

### `open`

```bash
mod open
mod open -f
mod open ws
mod open env
mod open proms
```

- `mod open`: mở project trong IDE mặc định.
- `mod open -f`: mở project bằng File Explorer.
- `mod open ws`: mở thư mục workspace.
- `mod open env`: mở Environment Variables panel.
- `mod open proms`: mở thư mục prompts.

### `code`

```bash
mod code
mod code ws <value> [-a] [-p]
mod code test
mod code ts-template
mod code js
mod code ts
mod code nestjs
mod code py
mod code ext
```

- `mod code`: mở project trong IDE.
- `mod code ws <value>`: mở workspace preset được định nghĩa trong `open_main_ws.py`.
- Các action còn lại mở những thư mục code/testing/template đã cấu hình trong source.

### `edit`

```bash
mod edit proms
mod edit to
```

- `mod edit proms`: chạy script chỉnh prompts.
- `mod edit to`: mở PowerShell profile trong Notepad.

### `git`

```bash
mod git commit -m "message"
mod git remote
```

- `commit`: chạy `git add .`, `git commit -m`, rồi `git push origin main`.
- `remote`: in danh sách remote của repository.

### `run`

```bash
mod run unikey
mod run cr-files
mod run dld-path [folder_name]
mod run rn-files <folder_path> [prefix]
mod run del-files <folder_path> <ext1,ext2,...>
mod run keep-files <folder_path> <ext>
mod run gen-qr
```

- `unikey`: mở UniKey theo path trong source.
- `cr-files`: tạo file/folder từ template trong `src/contents/files_source.txt`.
- `dld-path`: tạo và set Chrome download path cho các profile.
- `rn-files`: đổi tên toàn bộ file cấp 1 trong folder theo prefix.
- `del-files`: xóa file cấp 1 có extension nằm trong danh sách.
- `keep-files`: giữ một extension, xóa các file còn lại trong folder.
- `gen-qr`: nhập text tương tác và lưu QR image vào `MOD_APPDATA_FOLDER_PATH`.

### `print`

```bash
mod print os
mod print stts
mod print ws
mod print curl
mod print dir
mod print cmds
```

- `os`: in thông tin OS, CPU, memory và IP.
- `stts`: in mô tả status code.
- `ws`: in danh sách file trong thư mục workspace.
- `curl`: in mẫu cURL CRUD.
- `dir`: in đường dẫn thư mục `src`.
- `cmds`: in danh sách command snippet hữu ích.

### `gdrive`

```bash
mod gdrive sync "<source_folder>" "<dest_path>"
mod gdrive list [target_path] [-d] [--file]
mod gdrive remote
mod gdrive del-fd <remote_folder>
mod gdrive url <remote_path>
mod gdrive reset
mod gdrive guide
```

- `sync`: đồng bộ folder local lên Google Drive bằng `rclone sync`.
- `list`: liệt kê folder hoặc file trên remote.
- `remote`: in thông tin remote đang chọn.
- `del-fd`: xóa một folder trên remote, có hỏi xác nhận.
- `url`: lấy link truy cập remote path.
- `reset`: reset cấu hình `rclone` hoặc config nội bộ.
- `guide`: mở hướng dẫn cấu hình Google Drive/rclone.

### `init` và `py`

```bash
mod init
mod py env
```

- `mod init`: chạy `src/cmd/init.cmd`.
- `mod py env`: chạy helper setup Python virtual environment cho project hiện tại.

---

## Tài Liệu Tính Năng

Project dùng hai file trong `src/contents` để mô tả CLI:

- `help.txt`: tài liệu ngắn, in khi chạy `mod` không tham số.
- `app_features.yml`: catalog chi tiết để `mod <type> <action> --des` in mô tả từng command.

Khi thêm hoặc xóa một command, cần cập nhật cả dispatcher trong `src/main.py`, `help.txt`, và `app_features.yml` để tránh tài liệu lệch với code.

---

## Ví Dụ

```bash
# Xem mô tả chi tiết của lệnh đổi tên file
mod run rn-files --des

# Xóa tất cả file .tmp và .log trong một folder
mod run del-files "D:/D-Downloads/Trash" "tmp,log"

# Tạo QR image từ text nhập trong terminal
mod run gen-qr

# Liệt kê toàn bộ folder trên Google Drive remote
mod gdrive list "" -d

# Commit và push nhanh project hiện tại
mod git commit -m "update docs"

# In thông tin hệ thống
mod print os
```

---

## Ghi Chú Bảo Trì

- Một số helper vẫn chứa path Windows cụ thể trong source; khi chuyển máy nên kiểm tra lại `.env` và các path hardcoded trong script liên quan.
- Không commit `.env`, token, file cache hoặc backup chứa dữ liệu nhạy cảm.
- Những tính năng có thao tác xóa file/folder nên được chạy cẩn thận và kiểm tra folder đích trước khi xác nhận.
