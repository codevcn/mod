# 📋 YÊU CẦU PHÁT TRIỂN: MODULE PYTHON QUẢN LÝ VÀ KIỂM TOÁN DUNG LƯỢNG GITHUB GIST

---

## 🎯 1. TỔNG QUAN DỰ ÁN

Xây dựng một thư viện / CLI tool bằng **Python** cho phép:
1. **CRUD toàn diện file (`.json`, `.md`, `.txt`,...) trên GitHub Gist** thông qua GitHub REST API v3, cấu hình token qua file `.env` đặt tại root folder.
2. **Kiểm toán dung lượng & Thống kê lưu trữ (Storage Audit)**: Quét toàn bộ Gist của tài khoản để tính tổng dung lượng đã sử dụng, phân tích dung lượng từng file/Gist, kiểm tra giới hạn kích thước file và theo dõi hạn mức GitHub API Rate Limit.

---

## ⚙️ 2. CẤU HÌNH MÔI TRƯỜNG (`.env`)

Tạo file `.env` tại thư mục gốc của dự án với cấu trúc:

```env
# GitHub Fine-grained Personal Access Token (yêu cầu quyền: Gists Read & Write)
GITHUB_GIST_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# (Tùy chọn) Timeout cho mỗi request (giây)
GITHUB_REQUEST_TIMEOUT=15
```

### Yêu cầu phụ thuộc (Dependencies):
```text
python-dotenv>=1.0.0
requests>=2.31.0
rich>=13.0.0          # Để in bảng và báo cáo CLI đẹp mắt (hoặc tabulate)
```

---

## 🛠️ 3. YÊU CẦU CHI TIẾT CÁC TÍNH NĂNG

### PHẦN A: QUẢN LÝ CRUD GIST (`GistManager`)

Cần xây dựng class `GistManager` với các phương thức sau:

1. **Khởi tạo (`__init__`)**:
   * Tự động load `GITHUB_GIST_TOKEN` từ file `.env` (báo lỗi rõ ràng nếu thiếu token hoặc file `.env` không tồn tại).
   * Thiết lập HTTP Headers chuẩn:
     * `Authorization: Bearer <TOKEN>`
     * `Accept: application/vnd.github+json`
     * `X-GitHub-Api-Version: 2022-11-28`
     * `User-Agent: GitHub-Gist-Storage-Agent`

2. **Create Gist (`create_gist`)**:
   * **Tham số**:
     * `files`: Dict dạng `{"filename.ext": "file content"}` (hỗ trợ nhiều file cùng lúc).
     * `description`: Chuỗi mô tả Gist (mặc định chuỗi rỗng).
     * `public`: Boolean (mặc định `False` - secret gist).
   * **Trả về**: Dict thông tin Gist tạo thành công (gồm `id`, `html_url`, danh sách `raw_url` của từng file).

3. **Read Gist (`get_gist` & `get_raw_file`)**:
   * `get_gist(gist_id)`: Trả về metadata và nội dung các file trong Gist.
   * `get_raw_file(raw_url)`: Tải trực tiếp nội dung raw (văn bản hoặc JSON) từ đường link raw.

4. **Update Gist (`update_gist`)**:
   * **Tham số**:
     * `gist_id`: ID của Gist cần cập nhật.
     * `files`: Dict các file cần thêm hoặc sửa `{"filename.ext": {"content": "nội dung mới"}}`.
     * `files_to_delete`: Danh sách tên file cần xóa trong Gist (gán giá trị `null` theo API GitHub).
     * `description`: Cập nhật mô tả nếu có.
   * **Trả về**: Object Gist sau khi cập nhật.

5. **Delete Gist (`delete_gist`)**:
   * **Tham số**: `gist_id`.
   * **Trả về**: `True` nếu xóa thành công (HTTP 204), `False` nếu thất bại.

6. **List Gists (`list_gists`)**:
   * Lấy danh sách tất cả Gist của tài khoản (có xử lý phân trang `page` & `per_page=100`).

---

### PHẦN B: KIỂM TOÁN DUNG LƯỢNG & TÀI NGUYÊN (`GistStorageAuditor`)

> 💡 **Lưu ý kiến trúc GitHub Gist**:
> * GitHub Gist **không giới hạn tổng số lượng Gist** và không có quota cố định toàn cục cứng (như 15GB của Google Drive).
> * **Giới hạn kỹ thuật**:
>   * Kích thước tối đa mỗi file: **10 MB** (File $\ge 10\text{ MB}$ không thể upload hoặc bị cắt ngắn).
>   * Giới hạn kích thước khuyến nghị mỗi repository Gist: $\le \mathbf{1\text{ GB}}$.
>   * Giới hạn Rate Limit API: **5,000 requests/giờ** đối với Authenticated Token.

Cần xây dựng class `GistStorageAuditor` thực hiện các phân tích sau:

1. **Tổng hợp dung lượng đã dùng (Total Storage Used)**:
   * Quét toàn bộ Gist của user (tự động phân trang `per_page=100`).
   * Tính tổng dung lượng (Byte, KB, MB) của tất cả file trong tất cả Gist.
   * Đếm tổng số Gist (phân loại Secret vs Public).
   * Đếm tổng số lượng file lưu trữ và phân loại theo đuôi mở rộng (`.json`, `.md`, `.txt`,...).

2. **Cảnh báo giới hạn & File lớn (Limit Warnings)**:
   * Liệt kê Top các file lớn nhất.
   * Cảnh báo nếu có file nào tiến gần ngưỡng giới hạn **10 MB** của GitHub Gist (ví dụ $> 8\text{ MB}$).

3. **Kiểm tra API Rate Limit**:
   * Gọi `GET https://api.github.com/rate_limit`.
   * Thống kê: `limit` (tổng số request/giờ), `remaining` (số lượt còn lại), `reset_time` (thời gian reset).

4. **Báo cáo định dạng bảng (Visual Report)**:
   * Xuất báo cáo trực quan ra terminal (sử dụng bảng ASCII hoặc thư viện `rich`).

---

## 📂 4. CẤU TRÚC DỰ ÁN ĐỀ XUẤT

```text
gist_storage/
├── .env                    # Chứa GITHUB_GIST_TOKEN
├── .gitignore              # Bắt buộc ignore .env và các file cache
├── requirements.txt        # python-dotenv, requests, rich
├── gist_manager.py         # Module CRUD Gist
├── gist_auditor.py         # Module thống kê dung lượng & Rate limit
└── main.py                 # File demo / CLI interface
```

---

## 📋 5. CODE MẪU THAM KHẢO

### `gist_auditor.py` (Mẫu logic đo dung lượng)
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GistStorageAuditor:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_GIST_TOKEN")
        if not self.token:
            raise ValueError("Thiếu GITHUB_GIST_TOKEN trong .env")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def audit(self):
        gists = []
        page = 1
        while True:
            res = requests.get(
                f"https://api.github.com/gists?per_page=100&page={page}",
                headers=self.headers,
                timeout=15
            )
            res.raise_for_status()
            data = res.json()
            if not data:
                break
            gists.extend(data)
            page += 1

        total_bytes = 0
        total_files = 0
        public_count = sum(1 for g in gists if g.get("public"))
        secret_count = len(gists) - public_count
        file_types = {}
        files_detail = []

        for gist in gists:
            for fname, finfo in gist.get("files", {}).items():
                fsize = finfo.get("size", 0)
                total_bytes += fsize
                total_files += 1
                ext = os.path.splitext(fname)[1] or "no_ext"
                file_types[ext] = file_types.get(ext, 0) + fsize
                files_detail.append({
                    "filename": fname,
                    "size": fsize,
                    "gist_id": gist["id"],
                    "public": gist["public"]
                })

        # Lấy Rate Limit
        rate_res = requests.get("https://api.github.com/rate_limit", headers=self.headers)
        rate_data = rate_res.json().get("resources", {}).get("core", {})

        return {
            "total_gists": len(gists),
            "public_gists": public_count,
            "secret_gists": secret_count,
            "total_files": total_files,
            "total_size_kb": round(total_bytes / 1024, 2),
            "total_size_mb": round(total_bytes / (1024 * 1024), 4),
            "file_type_breakdown": file_types,
            "rate_limit_remaining": rate_data.get("remaining"),
            "rate_limit_total": rate_data.get("limit")
        }
```

---

## 🎯 6. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

1. [x] Đọc token an toàn từ `.env`, không hardcode token trong code.
2. [x] Thực hiện đầy đủ 4 thao tác: Tạo mới Gist, Đọc file/raw URL, Cập nhật Gist, Xóa Gist.
3. [x] Hỗ trợ lưu trữ nhiều file cùng lúc trên 1 Gist (`.json`, `.md`, `.txt`).
4. [x] Quét được toàn bộ Gist của tài khoản và tính đúng tổng dung lượng Byte/KB/MB.
5. [x] Có thống kê chi tiết số lượng Gist Secret/Public và dung lượng theo từng loại file.
6. [x] Kiểm tra và hiển thị được Rate Limit API còn lại của GitHub.
7. [x] Xử lý ngoại lệ đầy đủ (Token sai, Gist không tồn tại, mất kết nối mạng).
