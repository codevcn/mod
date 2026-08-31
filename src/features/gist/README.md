# 📖 Hướng Dẫn Sử Dụng Tính Năng GitHub Gist (`mod gist`)

Module `mod gist` cung cấp giải pháp toàn diện để **Quản lý CRUD** (Create, Read, Update, Delete) và **Kiểm toán dung lượng lưu trữ (Storage Audit)** trên GitHub Gist thông qua GitHub REST API v3.

---

## ⚙️ 1. Cấu Hình Ban Đầu

Tạo hoặc cập nhật file `.env` tại **thư mục gốc của dự án (`mod`)**:

```env
# GitHub Personal Access Token (yêu cầu quyền: gists)
GITHUB_GIST_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# (Tùy chọn) Thời gian timeout cho mỗi request (giây, mặc định: 15)
GITHUB_REQUEST_TIMEOUT=15
```

> [!TIP]
> **Cách tạo Token GitHub:**
> 1. Truy cập: `https://github.com/settings/tokens`
> 2. Chọn **Generate new token (classic)** hoặc **Fine-grained token**.
> 3. Tích chọn quyền `gist` (Create, update, and delete gists).
> 4. Copy token và dán vào biến `GITHUB_GIST_TOKEN` trong file `.env`.

---

## 📋 2. Bảng Tra Cứu Nhanh Các Lệnh

| Action | Cú pháp lệnh | Mục đích |
| :--- | :--- | :--- |
| `rate` | `mod gist rate` | Kiểm tra hạn mức GitHub API còn lại và thời gian reset |
| `audit` | `mod gist audit` | Quét toàn bộ Gist, tính dung lượng Byte/KB/MB, cảnh báo file lớn |
| `list` | `mod gist list [--page N] [--limit N] [--all] [--public-only] [--secret-only]` | Liệt kê danh sách Gist dưới dạng bảng màu sắc trực quan |
| `create` | `mod gist create [files...] [--desc <mô tả>] [--public]` | Tạo Gist mới từ file cục bộ hoặc nhập tương tác |
| `get` | `mod gist get <gist_id> [--raw <file>] [--save <dir>]` | Xem metadata, in raw file hoặc tải toàn bộ file về máy |
| `update` | `mod gist update <gist_id> [--add <name> <path>] [--delete <name>] [--desc <desc>]` | Cập nhật file và mô tả trong Gist |
| `delete` | `mod gist delete <gist_id> [-y]` | Xóa vĩnh viễn Gist (có xác nhận an toàn) |
| `reset` | `mod gist reset [gist_id] [-y]` | Reset toàn bộ Gist của tài khoản (hoặc reset 1 Gist chỉ định) |



---

## 🚀 3. Hướng Dẫn Chi Tiết Từng Lệnh

### 3.1. Kiểm tra API Rate Limit (`mod gist rate`)
Xem số lượng request GitHub API còn lại trong giờ hiện tại và thời điểm hạn mức được làm mới:
```powershell
mod gist rate
```
**Output mẫu:**
```text
⚡ GITHUB API RATE LIMIT STATUS:
  • Tổng hạn mức : 5,000 requests/giờ
  • Còn lại      : 4,985 requests
  • Đã dùng      : 15 requests
  • Reset vào lúc: 2026-08-25 16:45:00 UTC
```

---

### 3.2. Kiểm toán dung lượng & Cảnh báo file lớn (`mod gist audit`)
Quét 100% Gist của tài khoản để phân tích:
- Tổng số Gist (Secret vs Public).
- Tổng dung lượng lưu trữ (Bytes, KB, MB).
- Bảng phân bố dung lượng theo định dạng file (`.json`, `.md`, `.txt`, `.py`...).
- Bảng xếp hạng Top 10 file lớn nhất.
- Cảnh báo file $\ge 8\text{ MB}$ (tiệm cận ngưỡng giới hạn 10 MB của GitHub Gist).

```powershell
mod gist audit
```

---

### 3.3. Liệt kê danh sách Gist (`mod gist list`)
Hiển thị danh sách Gist dưới dạng bảng trực quan:
```powershell
# Liệt kê trang 1 (mặc định 30 items)
mod gist list

# Liệt kê tất cả Gist của tài khoản
mod gist list --all

# Phân trang và tùy chỉnh số lượng
mod gist list --page 2 --limit 50

# Lọc chỉ xem Public hoặc Secret Gists
mod gist list --public-only
mod gist list --secret-only
```

---

### 3.4. Tạo Gist mới (`mod gist create`)

**Cách 1: Tạo từ một hoặc nhiều file cục bộ:**
```powershell
# Tạo Secret Gist (mặc định)
mod gist create "notes.md" "config.json" --desc "Tài liệu và cấu hình dự án"

# Tạo Public Gist
mod gist create "snippet.py" --desc "Code mẫu Python" --public
```

**Cách 2: Chế độ nhập tương tác (Interactive):**
```powershell
mod gist create
```
*Script sẽ nhắc bạn nhập tên file, mô tả và nội dung (kết thúc bằng dòng `EOF`).*

**Output mẫu sau khi tạo:**
```text
ℹ Đang tạo Gist (Secret)...
✔ Tạo Gist thành công!
  • Gist ID : 65def476f3824c6b982eb8894c45974c
  • Web URL : https://gist.github.com/codevcn/65def476f3824c6b982eb8894c45974c
  • Raw URL : https://gist.githubusercontent.com/codevcn/65def476f3824c6b982eb8894c45974c/raw/.../.gitignore
  • Files   : .gitignore
```


---

### 3.5. Xem chi tiết & Tải file từ Gist (`mod gist get`)

**Xem thông tin metadata và danh sách file trong Gist:**
```powershell
mod gist get <gist_id>
```

**In trực tiếp nội dung raw của 1 file ra terminal:**
```powershell
mod gist get <gist_id> --raw "notes.md"
```

**Tải toàn bộ file trong Gist về thư mục cục bộ:**
```powershell
mod gist get <gist_id> --save "./my_downloaded_gist"
```

---

### 3.6. Cập nhật Gist (`mod gist update`)
Cập nhật nội dung, thêm file mới, xóa file hoặc đổi mô tả trong cùng một lệnh:
```powershell
# Đổi mô tả Gist
mod gist update <gist_id> --desc "Mô tả mới cho dự án"

# Thêm hoặc ghi đè nội dung file từ máy cục bộ
mod gist update <gist_id> --add "main.py" "d:/projects/app/main.py"

# Xóa một file khỏi Gist
mod gist update <gist_id> --delete "old_config.json"

# Kết hợp nhiều thao tác cùng lúc
mod gist update <gist_id> --add "README.md" "README.md" --delete "temp.txt" --desc "Phiên bản 2.0"
```

---

### 3.7. Xóa Gist (`mod gist delete`)
Xóa vĩnh viễn Gist theo ID:
```powershell
# Xóa có bước xác nhận an toàn (y/N)
mod gist delete <gist_id>

# Xóa ngay lập tức không cần xác nhận
mod gist delete <gist_id> -y
```

---

### 3.8. Reset Gist (`mod gist reset`)

**Cách 1: Reset toàn bộ tài khoản (Xóa sạch tất cả các Gist):**
```powershell
# Reset/xóa toàn bộ Gist của tài khoản (có danh sách và bước hỏi xác nhận y/N)
mod gist reset

# Reset/xóa toàn bộ Gist ngay lập tức không cần xác nhận
mod gist reset -y
```

**Cách 2: Reset một Gist cụ thể về file placeholder:**
```powershell
# Reset 1 Gist về file README.md mặc định (có xác nhận y/N)
mod gist reset <gist_id>

# Reset 1 Gist ngay lập tức không cần xác nhận
mod gist reset <gist_id> -y

# Đặt tên file placeholder tùy chỉnh
mod gist reset <gist_id> --placeholder ".gitkeep"

# Reset và nạp nội dung từ 1 file cục bộ
mod gist reset <gist_id> --file "d:/template.md" --desc "Gist đã được làm mới"
```


---

### 3.9. Xem mô tả chi tiết của từng lệnh (`--des`)
Bạn có thể thêm cờ `--des` vào sau bất kỳ lệnh nào để xem tóm tắt, giải thích tham số và điều kiện thực thi:
```powershell
# Xem toàn bộ tài liệu hướng dẫn này
mod gist --des

# Xem chi tiết lệnh audit
mod gist audit --des

# Xem chi tiết lệnh reset
mod gist reset --des

# Xem chi tiết lệnh create
mod gist create --des
```


---

## 📌 4. Các Lưu Ý Kỹ Thuật Quan Trọng

1. **Giới hạn kích thước file:** GitHub Gist giới hạn tối đa **10 MB** cho mỗi file. Không nên upload các file binary nặng, video hoặc dataset lớn.
2. **Khuyến nghị dung lượng repo:** Mỗi Gist được quản lý như một git repo ngầm; khuyến nghị dung lượng toàn bộ gist $\le 1\text{ GB}$.
3. **Bảo mật:** Tuyệt đối không commit file `.env` chứa `GITHUB_GIST_TOKEN` lên các kho mã nguồn công khai.
