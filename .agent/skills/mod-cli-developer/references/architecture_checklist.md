# Mod CLI Development Checklists

---

## 🟢 Checklist 1: THÊM TÍNH NĂNG MỚI (Add Feature)
- [ ] **Feature Script (`src/features/<script>.py`)**:
  - [ ] Import `paths.py` qua `Path(__file__).resolve().parents[1]`.
  - [ ] Parse `sys.argv` an toàn, validate đối số và cờ riêng.
  - [ ] Thoát đúng `sys.exit(0)` / `sys.exit(1)`.
- [ ] **Central Dispatcher (`src/main.py`)**:
  - [ ] Khai báo `MOD_TYPE_*` và `MOD_*_<ACTION>`.
  - [ ] Khai báo hàm `cmd_<feature>(action, remaining_args)`.
  - [ ] Bổ sung nhánh định tuyến trong `dispatch_command()`.
- [ ] **Tab Autocomplete & Error Handling**:
  - [ ] Cập nhật `VALID_TYPES` trong `src/utils/errors.py` (nếu có Type mới).
  - [ ] Cập nhật `TYPE_ACTION_MAP` (sắp xếp A-Z) và `TYPE_DESCRIPTIONS` trong `src/utils/interactive_cli.py`.
- [ ] **Đồng bộ tài liệu 3 lớp**:
  - [ ] `src/contents/help.txt`.
  - [ ] `src/contents/app_features.yml` (chuẩn bị cho cờ `--des`).
  - [ ] `PROJECT_CONTEXT.md`.
- [ ] **Kiểm thử nghiệm thu**:
  - [ ] `python src/main.py <type> <action> --des`
  - [ ] Test Tab Autocomplete
  - [ ] Chạy lệnh trực tiếp

---

## 🟡 Checklist 2: CHỈNH SỬA TÍNH NĂNG (Edit Feature)
- [ ] Cập nhật mã nguồn trong `src/features/<script>.py`.
- [ ] Kiểm tra xem có đổi cờ/đối số hay không $\rightarrow$ Nếu có, cập nhật lại cách forward trong `src/main.py`.
- [ ] Cập nhật mô tả trong `src/contents/help.txt`.
- [ ] Cập nhật trường `command`, `summary`, `details` trong `src/contents/app_features.yml`.
- [ ] Cập nhật bảng tra cứu lệnh trong `PROJECT_CONTEXT.md`.
- [ ] Chạy lệnh kiểm thử `--des` và lệnh thực thi.

---

## 🔴 Checklist 3: XÓA TÍNH NĂNG (Delete Feature)
- [ ] Xóa file script trong `src/features/`.
- [ ] Gỡ bỏ hằng số, hàm wrapper `cmd_*` và nhánh `dispatch_command()` trong `src/main.py`.
- [ ] Gỡ bỏ khỏi `TYPE_ACTION_MAP` và `TYPE_DESCRIPTIONS` trong `src/utils/interactive_cli.py`.
- [ ] Gỡ khỏi `VALID_TYPES` trong `src/utils/errors.py` (nếu xóa cả Type).
- [ ] Xóa mục tương ứng trong `src/contents/help.txt`.
- [ ] Xóa block YAML trong `src/contents/app_features.yml`.
- [ ] Xóa khỏi `PROJECT_CONTEXT.md`.
- [ ] Kiểm thử: Chạy `mod` kiểm tra menu Type sạch sẽ và không crash cú pháp.
