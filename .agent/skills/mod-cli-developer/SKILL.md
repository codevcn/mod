---
name: mod-cli-developer
description: >-
  Hướng dẫn toàn diện và quy chuẩn chuẩn hóa dành cho AI Agent khi THÊM, SỬA, hoặc XÓA
  các tính năng (types/actions) trong hệ thống Mod CLI.
---

# Mod CLI Developer Skill (Master Standard)

Tài liệu này là **Quy chuẩn tác nghiệp chuẩn (SOP)** dành cho AI Agent khi thao tác trên codebase **Mod CLI (`mod`)**.

---

> [!CAUTION]
> ### NGUYÊN TẮC BẢO VỆ MÃ NGUỒN TUYỆT ĐỐI (ZERO DATA LOSS)
> 1. **Trước mỗi lần bắt tay vào code bất kỳ tính năng nào:** AI Agent **BẮT BUỘC** phải kiểm tra `git status --porcelain`. Nếu có bất kỳ thay đổi nào (tracked hoặc untracked), **PHẢI** chạy `git stash push -u -m "<message_chi_tiết>"` để cất toàn bộ thay đổi an toàn vào Git stash trước khi sửa file.
> 2. **Bắt buộc dùng cờ `-u` (`--include-untracked`):** Không có cờ này, Git sẽ bỏ sót toàn bộ file mới tạo (untracked files), dẫn đến nguy cơ mất code tính năng mới.
> 3. **Message Git Stash phải rõ nghĩa, chi tiết:** Nêu rõ bối cảnh đang lưu những gì và chuẩn bị bắt tay vào làm tính năng nào kèm thời gian (ví dụ: `checkpoint: cất toàn bộ thay đổi trước khi triển khai mod git dl-folder - 2026-11-04 16:20`).
> 4. **Tuyệt đối không tự ý hoàn tác:** Không bao giờ chạy `git checkout <file>` hay `git restore <file>` nếu chưa chắc chắn 100% các thay đổi đã được commit hoặc đã nằm an toàn trong Git stash.

---

## 1. Kiến Trúc & Các Nguyên Tắc Bất Di Bất Dịch

```text
User: mod <type> <action> [args...] [-a] [--info]
  │
  ├── mod.cmd (Wrapper mỏng) ──► src/main.py (Central Dispatcher)
  │                                    │
  │     ┌──────────────────────────────┴──────────────────────────────┐
  │     ▼                                                             ▼
  │  [Không đối số]                                             [Có đối số]
  │  src/utils/interactive_cli.py                              dispatch_command()
  │  (Menu + Tab Autocomplete)                                        │
  │                                                                   ▼
  └───────────────────────────────────────────────────────► src/features/<script>.py
                                                            (Thực thi nghiệp vụ)
```

### 4 Nguyên Tắc Cốt Lõi:
1. **Bảo Toàn Mã Nguồn & Git Stash Checkpoint BẮT BUỘC Trước Khi Code:**
   - Luôn chạy `git stash push -u -m "checkpoint: <mô_tả_chi_tiết>"` trước khi can thiệp vào codebase nếu có uncommitted changes.
   - Tuyệt đối không để xảy ra tình trạng checkout/restore làm mất công sức chưa commit của người dùng hoặc phiên làm việc trước.
2. **Phân định cờ (Flag Separation):** 
   - Central Dispatcher (`src/main.py`) **CHỈ xử lý 2 cờ toàn cục**: `--info` (in mô tả YAML) và `-a` / `--antigravity-IDE` (chọn IDE).
   - Mọi cờ tính năng khác (`-m`, `-p`, `-d`, `-f`, `--audio`, `--protocol`...) **BẮT BUỘC** do script trong `src/features/` tự parse từ `remaining_args`.
3. **Không hardcode đường dẫn:** Mọi đường dẫn thư mục/tập tin phải lấy từ [`src/configs/paths.py`](file:///d:/D-Documents/TOOLs/mod/src/configs/paths.py).
4. **Mã hóa UTF-8 Console:** Luôn đặt `PYTHONIOENCODING=utf-8` và `sys.stdout.reconfigure(encoding='utf-8')` ở đầu các script để tránh lỗi vỡ font tiếng Việt trên Windows.

---

## 2. SOP 1: Quy Trình THÊM Tính Năng Mới (Add Feature)

Khi nhận yêu cầu thêm lệnh mới (ví dụ: `mod <type> <action>`):

### Bước 0: Tạo Git Stash Checkpoint (-u) Lưu Toàn Bộ Thay Đổi Hiện Tại (BẮT BUỘC)
- Kiểm tra trạng thái: `git status --porcelain`
- Nếu phát hiện có file modified hoặc untracked (`??`), thực hiện ngay lệnh cất tạm:
  ```bash
  git stash push -u -m "checkpoint: cất toàn bộ thay đổi chưa commit trước khi thêm tính năng mod <type> <action> - <YYYY-MM-DD HH:MM>"
  ```
- **Yêu cầu đối với Message của Git Stash:**
  - Message PHẢI rõ nghĩa, chi tiết: mô tả đang lưu công việc gì, chuẩn bị code tính năng gì.
  - **Bắt buộc có cờ `-u`** để gom cả file untracked.
  - Sau khi cất thành công mới bắt đầu thực hiện Bước 1.

### Bước 1: Tạo Feature Script (`src/features/<tên_tính_năng>.py`)
- Import `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))` và các cấu hình từ `configs.paths`.
- Parse đối số đầu vào, validate logic nghiệp vụ.
- Thoát bằng `sys.exit(0)` khi thành công hoặc `sys.exit(1)` khi có lỗi kèm thông báo màu ANSI.

### Bước 2: Khai báo Dispatcher trong `src/main.py`
- Khai báo `MOD_TYPE_<NAME>` và `MOD_<NAME>_<ACTION>`.
- Viết hàm `cmd_<name>(action, remaining_args)` gọi `subprocess.run` sang feature script.
- Thêm nhánh trong hàm `dispatch_command()`:
  - Validate action hợp lệ bằng `MissingActionError` hoặc `InvalidActionError`.
  - Gọi hàm `cmd_<name>`.

### Bước 3: Đăng ký Autocomplete & Error Handling
- Trong [`src/utils/errors.py`](file:///d:/D-Documents/TOOLs/mod/src/utils/errors.py): Bổ sung type mới vào `VALID_TYPES` (nếu là type mới).
- Trong [`src/utils/interactive_cli.py`](file:///d:/D-Documents/TOOLs/mod/src/utils/interactive_cli.py):
  - Thêm `type: [actions...]` vào `TYPE_ACTION_MAP` (sắp xếp danh sách action theo thứ tự A-Z).
  - Thêm mô tả tiếng Việt vào `TYPE_DESCRIPTIONS`.

### Bước 4: Đồng bộ tài liệu tính năng
- [`src/contents/help.txt`](file:///d:/D-Documents/TOOLs/mod/src/contents/help.txt): Bổ sung mục type, action và ví dụ chạy lệnh (phục vụ `mod --help`).
- [`src/contents/app_features.yml`](file:///d:/D-Documents/TOOLs/mod/src/contents/app_features.yml): Bổ sung action ID, title, command, summary, details, conditions để phục vụ cờ `--info` và làm Single Source of Truth cho AI Agent tra cứu.
- *(Lưu ý: [`PROJECT_CONTEXT.md`](file:///d:/D-Documents/TOOLs/mod/PROJECT_CONTEXT.md) đóng vai trò là tài liệu kiến trúc tổng quan dành cho AI Agent, KHÔNG cần bổ sung từng lệnh/action vào đó để tránh phình file theo thời gian; chỉ cập nhật file này khi có thay đổi về kiến trúc hệ thống, cấu hình runtime hoặc cơ chế nền tảng).*

### Bước 5: Kiểm thử bắt buộc (Verification)
- `python src/main.py <type> <action> --info` → Phải in ra đúng mô tả YAML.
- Test Tab Autocomplete qua Python runtime.
- Test thực thi lệnh trực tiếp.

---

## 3. SOP 2: Quy Trình CHỈNH SỬA Tính Năng (Edit Feature)

Khi chỉnh sửa một tính năng đã tồn tại:

0. **Checkpoint an toàn trước khi sửa (BẮT BUỘC):**
   - Chạy `git status --porcelain`.
   - Nếu có thay đổi chưa commit, chạy:
     ```bash
     git stash push -u -m "checkpoint: cất thay đổi trước khi chỉnh sửa tính năng <tên_tính_năng> - <YYYY-MM-DD HH:MM>"
     ```
1. **Trường hợp sửa logic nội bộ:** Chỉ sửa file script tương ứng trong `src/features/`.
2. **Trường hợp thay đổi cú pháp / tham số / cờ:**
   - Cập nhật script trong `src/features/`.
   - Cập nhật hàm gọi trong `src/main.py` nếu cách truyền `remaining_args` thay đổi.
   - Cập nhật nội dung giải thích và ví dụ trong `src/contents/help.txt`.
   - Cập nhật `command`, `summary`, `details` trong `src/contents/app_features.yml`.
   - Cập nhật lại dòng mô tả trong `PROJECT_CONTEXT.md`.
3. **Kiểm thử lại:** Chạy lệnh `--info` và lệnh thực thi để đảm bảo không gãy tương thích.

---

## 4. SOP 3: Quy Trình XÓA Tính Năng (Delete Feature)

Khi xóa bỏ hoàn toàn một lệnh hoặc một nhóm lệnh:

0. **Checkpoint an toàn trước khi xóa (BẮT BUỘC):**
   - Chạy `git stash push -u -m "checkpoint: cất toàn bộ thay đổi trước khi xóa tính năng <tên_tính_năng> - <YYYY-MM-DD HH:MM>"`.
1. **Xóa Script:** Xóa file script liên quan trong `src/features/` (nếu không còn action nào khác dùng chung).
2. **Dọn dẹp `src/main.py`:**
   - Xóa hằng số `MOD_*` của type/action bị xóa.
   - Xóa hàm wrapper `cmd_*`.
   - Xóa nhánh `elif type_included == ...` trong `dispatch_command()`.
3. **Dọn dẹp Autocomplete & Errors:**
   - Gỡ bỏ khỏi `TYPE_ACTION_MAP` và `TYPE_DESCRIPTIONS` trong `src/utils/interactive_cli.py`.
   - Nếu xóa cả nhóm Type: Gỡ khỏi `VALID_TYPES` trong `src/utils/errors.py`.
4. **Dọn dẹp Tài Liệu:**
   - Xóa mục tương ứng trong `src/contents/help.txt`.
   - Xóa block YAML trong `src/contents/app_features.yml`.
   - Xóa khỏi bảng tra cứu trong `PROJECT_CONTEXT.md`.
5. **Kiểm thử hồi quy:** Chạy `python src/main.py` kiểm tra danh sách Type không còn tính năng cũ và không phát sinh lỗi cú pháp.

---

## 5. Danh Mục File Bản Đồ (File Map Reference)

| File | Vai trò | Khi nào cần sửa? |
| :--- | :--- | :--- |
| `src/main.py` | Central Dispatcher | Thêm/sửa/xóa Type hoặc Action |
| `src/configs/paths.py` | Central Paths Config | Thêm thư mục/file cấu hình mới ngoài project |
| `src/utils/errors.py` | Central Exceptions | Thêm/xóa nhóm Type |
| `src/utils/interactive_cli.py` | UI & Tab Autocomplete | Thêm/sửa/xóa Type hoặc Action |
| `src/contents/help.txt` | Text Help | Thêm/sửa/xóa Type hoặc Action |
| `src/contents/app_features.yml` | Catalog cho cờ `--info` | Thêm/sửa/xóa Type hoặc Action |
| `PROJECT_CONTEXT.md` | Tài liệu ngữ cảnh cho AI | Luôn luôn cập nhật đồng bộ sau mọi thay đổi |
