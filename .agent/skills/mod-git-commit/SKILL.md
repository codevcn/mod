---
name: mod-git-commit
description: >-
  Quy trình chuẩn hóa để xem lại thay đổi (code review), dọn dẹp file tạm, soạn commit message
  chuẩn Conventional Commits và tự động commit & push lên GitHub thông qua Mod CLI (`mod git commit`).
---

# Mod Git Commit & Review Workflow Standard

Skill này hướng dẫn AI Agent thực hiện chuẩn xác chu trình kiểm tra, hoàn thiện và đẩy mã nguồn lên remote repository bằng hệ thống lệnh của Mod CLI.

---

## Nguyên Tắc Cốt Lõi

1. **Không commit file rác / file tạm:** Luôn rà soát và xóa sạch các file scratch, test data tạm thời trước khi add.
2. **Không commit khi code bị vỡ:** Luôn đảm bảo mã nguồn vượt qua kiểm thử cú pháp (`py_compile` hoặc test run) trước khi commit.
3. **Sử dụng lệnh của Mod:** Ưu tiên dùng `python src/main.py git commit -m "..."` hoặc `mod git commit -m "..."` để đảm bảo quy trình 3 trong 1 (`add` -> `commit` -> `push`).
4. **Commit Message chuẩn:** Bắt buộc tuân thủ Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`...).

---

## Quy Trình Tác Nghiệp 5 Bước (SOP)

### Bước 1: Rà soát & Audit Trạng Thái Git
Trước khi commit, Agent chạy:
```bash
git status
```
- Phân tích danh sách:
  - `Changes not staged for commit`: File nào bị sửa đổi? Có đúng phạm vi công việc không?
  - `Untracked files`: Có file scratch/test nào vô tình tạo ra không?
- Kiểm tra chi tiết thay đổi:
```bash
git diff
```
- Đảm bảo không còn log debug thừa, token/secret lộ lọt hoặc file tạm chưa xóa.

---

### Bước 2: Dọn Dẹp & Chuẩn Bị Hoàn Tất
1. **Xóa file tạm:** Nếu có file scratch trong thư mục `.gemini/.../scratch/` hoặc dữ liệu test cục bộ, tiến hành xóa sạch.
2. **Làm mới cây thư mục (nếu có):**
   ```bash
   python print_project_tree.py
   ```
3. **Đồng bộ tài liệu 3 lớp (nếu có thay đổi tính năng):**
   - `src/contents/help.txt`
   - `src/contents/app_features.yml`
   - `PROJECT_CONTEXT.md`

---

### Bước 3: Soạn Thảo Commit Message Chuẩn
Cấu trúc chuẩn Conventional Commits:
`<type>(<scope>): <mô tả súc tích tiếng Anh>`

- `feat`: Tính năng mới hoặc bổ sung cờ/tham số mới.
- `fix`: Sửa lỗi logic, sửa exception, sửa hiển thị font UTF-8.
- `docs`: Cập nhật tài liệu, help text, YAML features.
- `refactor`: Tái cấu trúc mã nguồn, tối ưu hàm không đổi hành vi.
- `chore`: Cập nhật cấu hình, cây thư mục, dọn dẹp file.

*Ví dụ:*
`feat: add folder cr-linear, open alias management, tree level depth, and skill set agent flags`

---

### Bước 4: Thực Thi Commit & Push Qua Mod CLI
Chạy lệnh commit thông qua Mod CLI:
```bash
# Trong môi trường phát triển:
python src/main.py git commit -m "<commit_message>"

# Hoặc khi mod đã có trong PATH:
mod git commit -m "<commit_message>"
```

**Lưu ý cơ chế thực thi:**
- Lệnh này sẽ tuần tự chạy:
  1. `[1/3] git add .`
  2. `[2/3] git commit -m "<message>"`
  3. `[3/3] git push origin main`
- Nếu lệnh chạy dưới dạng background task do mạng trễ khi push, hãy để tiến trình tự kết thúc và lắng nghe thông báo hoàn thành từ hệ thống (reactive wakeup), không poll vòng lặp.

---

### Bước 5: Kiểm Tra Kết Quả & Báo Cáo
- Kiểm tra output terminal: Xác nhận thông báo `=== Hoàn tất thành công! ===` và mã thoát `0`.
- Báo cáo rõ ràng cho người dùng:
  - Commit Hash (ví dụ: `a872bf5`).
  - Branch được cập nhật (`main -> main`).
  - Danh sách tính năng chính đã được lưu trữ an toàn.
