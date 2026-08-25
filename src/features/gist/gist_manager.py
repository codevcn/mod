"""
Module GistManager: Thực hiện các thao tác CRUD với GitHub Gist thông qua GitHub REST API v3.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from dotenv import load_dotenv

# Đảm bảo đường dẫn gốc dự án được thêm vào sys.path
SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from configs.paths import PROJECT_ROOT


class GistManager:
    """Quản lý CRUD GitHub Gist sử dụng Personal Access Token."""

    def __init__(self, token: Optional[str] = None, timeout: Optional[int] = None):
        # Nạp biến môi trường từ file .env tại thư mục gốc
        env_path = Path(PROJECT_ROOT) / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path))

        self.token = token or os.getenv("GITHUB_GIST_TOKEN")
        if not self.token:
            raise ValueError(
                "Thiếu GITHUB_GIST_TOKEN trong file .env hoặc biến môi trường.\n"
                f"Vui lòng thêm GITHUB_GIST_TOKEN=github_pat_... vào file: {env_path}"
            )

        env_timeout = os.getenv("GITHUB_REQUEST_TIMEOUT", "15")
        try:
            self.timeout = int(timeout) if timeout is not None else int(env_timeout)
        except ValueError:
            self.timeout = 15

        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-Gist-Storage-Agent",
        }

    def _handle_response_error(self, response: requests.Response, context: str = ""):
        """Xử lý và chuẩn hóa thông báo lỗi HTTP từ GitHub API."""
        try:
            err_data = response.json()
            err_msg = err_data.get("message", response.text)
        except Exception:
            err_msg = response.text or response.reason

        status = response.status_code
        if status == 401:
            raise PermissionError(
                f"GitHub API 401 Unauthorized: Token không hợp lệ hoặc đã hết hạn. ({context})"
            )
        elif status == 403:
            raise PermissionError(
                f"GitHub API 403 Forbidden: Bị từ chối quyền truy cập hoặc vượt quá Rate Limit. ({context})\nChi tiết: {err_msg}"
            )
        elif status == 404:
            raise FileNotFoundError(
                f"GitHub API 404 Not Found: Tài nguyên hoặc Gist ID không tồn tại. ({context})"
            )
        elif status == 422:
            raise ValueError(
                f"GitHub API 422 Unprocessable Entity: Dữ liệu gửi lên không hợp lệ. ({context})\nChi tiết: {err_msg}"
            )
        else:
            raise RuntimeError(
                f"GitHub API Error [{status}]: {err_msg} ({context})"
            )

    def create_gist(
        self,
        files: Dict[str, Union[str, Dict[str, str]]],
        description: str = "",
        public: bool = False,
    ) -> Dict[str, Any]:
        """
        Tạo Gist mới.
        :param files: Dict dạng {"filename.ext": "content"} hoặc {"filename.ext": {"content": "..."}}
        :param description: Mô tả Gist
        :param public: True là public gist, False là secret gist (mặc định)
        :return: Dict metadata Gist trả về từ GitHub
        """
        if not files:
            raise ValueError("Cần ít nhất 1 file để tạo Gist.")

        files_payload = {}
        for fname, fval in files.items():
            if isinstance(fval, str):
                files_payload[fname] = {"content": fval}
            elif isinstance(fval, dict) and "content" in fval:
                files_payload[fname] = fval
            else:
                raise ValueError(f"Dữ liệu nội dung của file '{fname}' không hợp lệ.")

        payload = {
            "description": description or "",
            "public": bool(public),
            "files": files_payload,
        }

        try:
            res = requests.post(
                f"{self.base_url}/gists",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            if not res.ok:
                self._handle_response_error(res, "Create Gist")
            return res.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi kết nối mạng khi tạo Gist: {e}")

    def get_gist(self, gist_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết và danh sách file trong Gist theo ID.
        """
        if not gist_id:
            raise ValueError("Thiếu gist_id.")

        try:
            res = requests.get(
                f"{self.base_url}/gists/{gist_id}",
                headers=self.headers,
                timeout=self.timeout,
            )
            if not res.ok:
                self._handle_response_error(res, f"Get Gist {gist_id}")
            return res.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi kết nối mạng khi lấy thông tin Gist: {e}")

    def get_raw_file(self, raw_url: str) -> str:
        """
        Tải nội dung thô (raw) của file từ đường dẫn raw_url.
        """
        if not raw_url:
            raise ValueError("Thiếu raw_url.")

        try:
            res = requests.get(raw_url, headers=self.headers, timeout=self.timeout)
            if not res.ok:
                self._handle_response_error(res, f"Download Raw File: {raw_url}")
            return res.text
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi kết nối mạng khi tải raw file: {e}")

    def update_gist(
        self,
        gist_id: str,
        files: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
        files_to_delete: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cập nhật nội dung Gist (thêm/sửa file, xóa file, sửa description).
        :param gist_id: ID của Gist
        :param files: Dict file cần thêm/sửa {"filename.ext": "new content"}
        :param files_to_delete: Danh sách tên file cần xóa khỏi Gist
        :param description: Mô tả mới nếu cần sửa
        """
        if not gist_id:
            raise ValueError("Thiếu gist_id.")

        payload: Dict[str, Any] = {}
        if description is not None:
            payload["description"] = description

        files_payload: Dict[str, Any] = {}
        if files:
            for fname, fval in files.items():
                if isinstance(fval, str):
                    files_payload[fname] = {"content": fval}
                elif isinstance(fval, dict):
                    files_payload[fname] = fval

        if files_to_delete:
            for fname in files_to_delete:
                files_payload[fname] = None

        if files_payload:
            payload["files"] = files_payload

        if not payload:
            raise ValueError("Không có nội dung thay đổi nào được cung cấp để cập nhật Gist.")

        try:
            res = requests.patch(
                f"{self.base_url}/gists/{gist_id}",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            if not res.ok:
                self._handle_response_error(res, f"Update Gist {gist_id}")
            return res.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi kết nối mạng khi cập nhật Gist: {e}")

    def reset_gist(
        self,
        gist_id: str,
        placeholder_name: str = "README.md",
        placeholder_content: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reset Gist bằng cách xóa toàn bộ các file hiện có và tạo 1 file placeholder tối thiểu.
        (GitHub API yêu cầu 1 Gist luôn phải chứa ít nhất 1 file).
        """
        if not gist_id:
            raise ValueError("Thiếu gist_id.")

        # Lấy thông tin các file hiện có trong Gist
        gist = self.get_gist(gist_id)
        current_files = gist.get("files", {})

        # Danh sách các file cần xóa (trừ file placeholder nếu trùng tên)
        files_to_delete = [fname for fname in current_files.keys() if fname != placeholder_name]

        # File placeholder mới
        if placeholder_content is None:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            placeholder_content = (
                f"# Gist Reset\n\n"
                f"Tất cả các file trước đó đã được xóa bỏ hoàn toàn.\n"
                f"Thời gian reset: {now_str}\n"
            )

        files_to_add = {placeholder_name: placeholder_content}

        return self.update_gist(
            gist_id=gist_id,
            files=files_to_add,
            files_to_delete=files_to_delete,
            description=description if description is not None else gist.get("description", ""),
        )

    def delete_gist(self, gist_id: str) -> bool:

        """
        Xóa Gist vĩnh viễn theo ID.
        :return: True nếu xóa thành công (HTTP 204), False nếu thất bại.
        """
        if not gist_id:
            raise ValueError("Thiếu gist_id.")

        try:
            res = requests.delete(
                f"{self.base_url}/gists/{gist_id}",
                headers=self.headers,
                timeout=self.timeout,
            )
            if res.status_code == 204:
                return True
            self._handle_response_error(res, f"Delete Gist {gist_id}")
            return False
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi kết nối mạng khi xóa Gist: {e}")

    def list_gists(self, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """
        Lấy danh sách Gist theo trang.
        """
        try:
            res = requests.get(
                f"{self.base_url}/gists",
                params={"per_page": per_page, "page": page},
                headers=self.headers,
                timeout=self.timeout,
            )
            if not res.ok:
                self._handle_response_error(res, f"List Gists (page {page})")
            return res.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi kết nối mạng khi lấy danh sách Gist: {e}")

    def get_all_gists(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        Quét và tải toàn bộ Gist của tài khoản (tự động phân trang per_page=100).
        """
        all_gists: List[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            data = self.list_gists(per_page=100, page=page)
            if not data:
                break
            all_gists.extend(data)
            if len(data) < 100:
                break
            page += 1
        return all_gists

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Lấy thông tin hạn mức GitHub API Rate Limit hiện tại.
        """
        try:
            res = requests.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers,
                timeout=self.timeout,
            )
            if not res.ok:
                self._handle_response_error(res, "Get Rate Limit")
            return res.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi kết nối mạng khi kiểm tra Rate Limit: {e}")
