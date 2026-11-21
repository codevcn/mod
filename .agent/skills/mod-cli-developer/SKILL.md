---
name: mod-cli-developer
description: >-
  Quy chuẩn tác nghiệp chuẩn hóa cho AI Agent khi THÊM, SỬA hoặc XÓA
  tính năng (types/actions) trong hệ thống Mod CLI.
---

# Mod CLI Developer Skill

Quy chuẩn phát triển codebase **Mod CLI (`mod`)**: `mod.cmd` → `src/main.py` (Dispatcher mỏng) → `src/features/<script>.py` (Nghiệp vụ) / `src/utils/interactive_cli.py` (REPL khi không có đối số).

---

## 1. Nguyên tắc cốt lõi

1. **An toàn Git trước khi sửa:** Kiểm tra `git status --porcelain`. Nếu có thay đổi chưa commit dễ xung đột hoặc sửa rủi ro cao, hãy tạo checkpoint an toàn (commit hoặc `git stash push -u -m "checkpoint: ..."` rồi `git stash apply` nếu cần giữ working tree); tuyệt đối không `git checkout`/`git restore` làm mất code chưa lưu.
2. **Dispatcher mỏng & Tách cờ:** [`src/main.py`](file:///d:/D-Documents/TOOLs/mod/src/main.py) chỉ xử lý cờ toàn cục (`--info`/`--des`, `--version`/`-v`, `--help`/`-h`), validate `type`/`action` và forward nguyên `remaining_args` cho script tính năng tự parse (`argparse` hoặc parse thủ công).
3. **Không hardcode đường dẫn & quản lý dependencies:** Mọi đường dẫn ngoài project đặt tại [`src/configs/paths.py`](file:///d:/D-Documents/TOOLs/mod/src/configs/paths.py). Nếu thêm thư viện ngoài mới, cập nhật [`requirements.txt`](file:///d:/D-Documents/TOOLs/mod/requirements.txt).
4. **UTF-8 Console:** Các script chạy độc lập cần thiết lập `PYTHONIOENCODING="utf-8"` và `reconfigure(encoding="utf-8", errors="replace")` cho `sys.stdout`/`sys.stderr` để tránh lỗi font trên Windows.
5. **Versioning theo độ phức tạp (SemVer):** [`src/configs/version.py`](file:///d:/D-Documents/TOOLs/mod/src/configs/version.py) (`__version__`) là nguồn phiên bản duy nhất. Mỗi lần cập nhật tool, phân tích độ phức tạp & phạm vi ảnh hưởng để nâng phiên bản tương ứng:
   - `PATCH` (`+0.0.1`): Sửa lỗi, dọn code thừa, refactor nội bộ, cập nhật docs, hoặc thêm flag phụ nhỏ tương thích ngược.
   - `MINOR` (`+0.1.0`, đặt `PATCH = 0`): Thêm `type`/`action` mới hoàn chỉnh hoặc mở rộng chức năng đáng kể tương thích ngược.
   - `MAJOR` (`+1.0.0`, đặt `MINOR = 0, PATCH = 0`): Tái cấu trúc kiến trúc lõi hoặc Breaking Change (xóa/đổi cú pháp lệnh công khai).

---

## 2. Bản đồ điểm chạm (Thêm / Sửa / Xóa)

| File | Thêm tính năng | Sửa tính năng | Xóa tính năng |
| :--- | :--- | :--- | :--- |
| `src/features/<script>.py` | Tạo script mới (tham khảo feature hiện có làm mẫu), thoát `0`/`1`. | Sửa logic/parser bên trong. | Xóa file (nếu không còn action dùng chung). |
| `src/main.py` | Thêm `MOD_TYPE_*`, `MOD_*` (nếu có action), `cmd_*`, nhánh `dispatch_command()`. | Cập nhật nếu đổi tên action/cách forward args. | Gỡ hằng số, hàm wrapper và nhánh `dispatch_command()`. |
| `src/utils/errors.py` | Thêm vào `VALID_TYPES` nếu là `type` mới. | Giữ nguyên (trừ khi đổi tên `type`). | Gỡ khỏi `VALID_TYPES` nếu xóa cả `type`. |
| `src/utils/interactive_cli.py` | Thêm vào `TYPE_ACTION_MAP` (`[]` nếu không có action, xếp A-Z) và `TYPE_DESCRIPTIONS`. *(Tự cập nhật `mod ls`)*. | Cập nhật `TYPE_ACTION_MAP` / `TYPE_DESCRIPTIONS` nếu đổi tên hoặc thêm alias. | Gỡ action/type khỏi `TYPE_ACTION_MAP` và `TYPE_DESCRIPTIONS`. |
| `src/contents/help.txt` | Bổ sung cú pháp tóm tắt và ví dụ (`mod --help`). | Cập nhật cú pháp/ví dụ liên quan. | Xóa mục tương ứng. |
| `src/contents/app_features.yml` | Thêm block YAML (mỗi `type` cần ≥ 1 item trong `actions:` để `mod seek` tìm được). | Cập nhật `command`, `summary`, `details`, `conditions`. | Xóa block YAML tương ứng. |
| `src/configs/version.py` | Tăng `MINOR` (hoặc `PATCH` nếu chỉ thêm flag nhỏ). | Tăng `PATCH`/`MINOR`/`MAJOR` tùy mức độ thay đổi. | Tăng `MAJOR` hoặc `MINOR` tùy mức Breaking Change. |
| `requirements.txt` | Bổ sung package ngoài nếu script mới dùng thêm thư viện. | Cập nhật nếu đổi/bỏ dependency. | Gỡ package nếu không còn file nào trong repo dùng. |
| `PROJECT_CONTEXT.md` | **Không** thêm lệnh lẻ; chỉ sửa nếu đổi kiến trúc hoặc `paths.py` chính. | Chỉ sửa nếu đổi cơ chế nền tảng. | Chỉ sửa nếu gỡ cả cơ chế kiến trúc. |

### Template nhanh cho `src/contents/app_features.yml`
```yaml
    - name: "<type_name>"
      description: "<Mô tả ngắn nhóm lệnh>"
      actions:
        - id: "ACTION <số_thứ_tự>"
          title: "<Tiêu đề tính năng>"
          command: "mod <type> [<action>] [args...]"
          summary: "<Tóm tắt 1 câu>"
          details: "<Chi tiết cách hoạt động và các cờ>"
          conditions: "<Điều kiện hoặc tham số bắt buộc>"
```

---

## 3. Kiểm thử bắt buộc sau thay đổi

- Kiểm tra cú pháp toàn `src/`: `python -m compileall -q src`
- Kiểm tra version mới: `python src/main.py --version`
- Kiểm tra catalog `--info` & `seek`/`ls`: `python src/main.py <type> [<action>] --info`
- Kiểm tra runtime: Import `utils.interactive_cli` (đảm bảo `TYPE_ACTION_MAP`/`TYPE_DESCRIPTIONS` hợp lệ) và chạy thử trực tiếp các nhánh chính/trường hợp lỗi của lệnh vừa sửa.
