#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
git_download.py - Tải thư mục hoặc tệp trực tiếp từ GitHub Repository:
- mod git dl-folder <git_folder_url> [dest_download_path]
- mod git dl-file <git_file_url> [dest_download_path]

Bảo đảm giữ nguyên vẹn 100% nội dung gốc trên GitHub, không tự ý can thiệp
hay khởi tạo file/thư mục cấu hình git (.git) ở đích.
"""

import os
import re
import sys
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from colorama import init, Fore, Style

# Cấu hình UTF-8 cho Windows Console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

init(autoreset=True)


def parse_github_folder_url(url: str):
    """
    Phân tích URL thư mục trên GitHub.
    Định dạng hợp lệ: https://github.com/<owner>/<repo>/tree/<branch>/<sub_path>
    """
    clean_url = url.strip().rstrip("/")
    pattern = r"^https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*?)$"
    match = re.match(pattern, clean_url)

    if not match:
        # Kiểm tra nếu người dùng truyền URL gốc repo
        repo_root_pattern = r"^https?://github\.com/([^/]+)/([^/]+)/?$"
        if re.match(repo_root_pattern, clean_url):
            raise ValueError(
                "URL bạn cung cấp là gốc của repository, không phải thư mục con.\n"
                "💡 Gợi ý: Để tải một thư mục cụ thể, URL cần có dạng: https://github.com/<owner>/<repo>/tree/<branch>/<path_to_folder>\n"
                "Nếu muốn tải toàn bộ repo, bạn có thể dùng lệnh 'git clone <repo_url>'."
            )
        raise ValueError(
            f"URL thư mục GitHub không hợp lệ: '{url}'\n"
            "Định dạng chuẩn yêu cầu:\n"
            "  https://github.com/<owner>/<repo>/tree/<branch>/<path_to_folder>\n"
            "Ví dụ:\n"
            "  https://github.com/obra/superpowers/tree/main/skills/systematic-debugging"
        )

    owner = match.group(1)
    repo = match.group(2)
    branch = match.group(3)
    sub_path = match.group(4).strip("/")

    folder_name = os.path.basename(sub_path)
    clone_url = f"https://github.com/{owner}/{repo}.git"

    return owner, repo, branch, sub_path, folder_name, clone_url


def parse_github_file_url(url: str):
    """
    Phân tích URL tệp trên GitHub.
    Hỗ trợ 2 định dạng:
    1. https://github.com/<owner>/<repo>/blob/<branch>/<file_path>
    2. https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<file_path>
    """
    clean_url = url.strip()

    # Dạng 1: GitHub Web blob URL
    blob_pattern = r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*?)$"
    blob_match = re.match(blob_pattern, clean_url)
    if blob_match:
        owner = blob_match.group(1)
        repo = blob_match.group(2)
        branch = blob_match.group(3)
        file_path = blob_match.group(4)
        filename = os.path.basename(file_path)
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        return filename, raw_url

    # Dạng 2: GitHub Raw URL
    raw_pattern = r"^https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.*?)$"
    raw_match = re.match(raw_pattern, clean_url)
    if raw_match:
        file_path = raw_match.group(4)
        filename = os.path.basename(file_path)
        return filename, clean_url

    raise ValueError(
        f"URL tệp GitHub không hợp lệ: '{url}'\n"
        "Định dạng chuẩn yêu cầu:\n"
        "  https://github.com/<owner>/<repo>/blob/<branch>/<path_to_file>\n"
        "  hoặc https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path_to_file>\n"
        "Ví dụ:\n"
        "  https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md"
    )


def download_github_folder(url: str, dest_base_path: str):
    """
    Tải toàn bộ thư mục từ GitHub sử dụng kỹ thuật Git Sparse Checkout,
    sau đó copy vào dest_base_path và dọn sạch thư mục tạm.
    """
    try:
        owner, repo, branch, sub_path, folder_name, clone_url = parse_github_folder_url(url)
    except ValueError as e:
        print(f"{Fore.RED}❌ Lỗi định dạng URL:{Style.RESET_ALL} {e}")
        sys.exit(1)

    dest_folder_abs = os.path.abspath(dest_base_path)
    target_output_dir = os.path.join(dest_folder_abs, folder_name)

    # Kiểm tra trùng lặp tại thư mục đích
    if os.path.exists(target_output_dir):
        print(f"\n{Fore.YELLOW}⚠️ Cảnh báo: Thư mục đích đã tồn tại:{Style.RESET_ALL} {target_output_dir}")
        try:
            ans = input("   Bạn có muốn ghi đè/thay thế thư mục này không? (y/N): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n>>> Hủy thao tác.")
            sys.exit(0)

        if ans != "y":
            print(">>> Hủy thao tác tải xuống an toàn.")
            sys.exit(0)

    print(f"\n{Fore.CYAN}=== BẮT ĐẦU TẢI THƯ MỤC TỪ GITHUB (DL-FOLDER) ==={Style.RESET_ALL}")
    print(f"  • Repository : {owner}/{repo} (nhánh: {branch})")
    print(f"  • Thư mục    : {sub_path}")
    print(f"  • Đích đến   : {target_output_dir}")
    print(f"\n{Fore.LIGHTBLACK_EX}>>> Đang kết nối và trích xuất dữ liệu qua Git Sparse Checkout...{Style.RESET_ALL}")

    temp_clone_dir = tempfile.mkdtemp(prefix="mod_git_sparse_")

    try:
        # Bước 1: Clone với bộ lọc blob:none (chỉ lấy commit/tree metadata, cực nhanh)
        clone_cmd = [
            "git",
            "clone",
            "--depth", "1",
            "--filter=blob:none",
            "--sparse",
            clone_url,
            temp_clone_dir,
            "--branch", branch,
        ]

        proc_clone = subprocess.run(
            clone_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if proc_clone.returncode != 0:
            err_msg = proc_clone.stderr.strip()
            print(f"\n{Fore.RED}❌ Lỗi: Không thể kết nối hoặc clone repository từ GitHub.{Style.RESET_ALL}")
            if "could not read Username" in err_msg or "Authentication failed" in err_msg:
                print("Chi tiết: Repository có thể là private hoặc yêu cầu xác thực tài khoản GitHub.")
            elif "Remote branch" in err_msg and "not found" in err_msg:
                print(f"Chi tiết: Không tìm thấy nhánh '{branch}' trong repository.")
            elif "not found" in err_msg.lower():
                print(f"Chi tiết: Không tìm thấy repository '{clone_url}'.")
            else:
                print(f"Chi tiết lỗi từ Git: {err_msg}")
            sys.exit(1)

        # Bước 2: Thiết lập sparse-checkout cho đúng sub_path
        sparse_cmd = ["git", "sparse-checkout", "set", sub_path]
        proc_sparse = subprocess.run(
            sparse_cmd,
            cwd=temp_clone_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if proc_sparse.returncode != 0:
            print(f"\n{Fore.RED}❌ Lỗi khi thực thi git sparse-checkout:{Style.RESET_ALL} {proc_sparse.stderr.strip()}")
            sys.exit(1)

        source_extracted_dir = os.path.join(temp_clone_dir, sub_path)
        if not os.path.exists(source_extracted_dir):
            print(f"\n{Fore.RED}❌ Lỗi: Thư mục '{sub_path}' không tồn tại trong nhánh '{branch}' của repository.{Style.RESET_ALL}")
            sys.exit(1)

        # Bước 3: Sao chép nguyên vẹn sang đích (giữ nguyên tệp con, không tự tạo .git)
        os.makedirs(dest_folder_abs, exist_ok=True)
        if os.path.exists(target_output_dir):
            shutil.rmtree(target_output_dir)

        shutil.copytree(source_extracted_dir, target_output_dir)

        # Đếm thống kê tệp và thư mục con
        total_files = 0
        total_dirs = 0
        for _, dirs, files in os.walk(target_output_dir):
            total_dirs += len(dirs)
            total_files += len(files)

        print(f"\n{Fore.GREEN}✅ Tải thư mục thành công!{Style.RESET_ALL}")
        print(f"  • Thư mục đã lưu: {Fore.CYAN}{target_output_dir}{Style.RESET_ALL}")
        print(f"  • Tổng số tệp   : {total_files} files (trong {total_dirs} thư mục con)")
        print(f"  • Đảm bảo       : Giữ nguyên 100% nội dung gốc, không chèn metadata .git.\n")

    except Exception as e:
        print(f"\n{Fore.RED}❌ Có lỗi xảy ra trong quá trình tải thư mục:{Style.RESET_ALL} {e}")
        sys.exit(1)
    finally:
        # Luôn dọn dẹp thư mục tạm an toàn
        shutil.rmtree(temp_clone_dir, ignore_errors=True)


def download_github_file(url: str, dest_base_path: str):
    """
    Tải 1 tệp đơn lẻ từ GitHub qua URL raw và lưu vào dest_base_path.
    """
    try:
        filename, raw_url = parse_github_file_url(url)
    except ValueError as e:
        print(f"{Fore.RED}❌ Lỗi định dạng URL:{Style.RESET_ALL} {e}")
        sys.exit(1)

    dest_folder_abs = os.path.abspath(dest_base_path)

    # Nếu dest_base_path kết thúc bằng tên file hoặc đã là file
    if os.path.isfile(dest_folder_abs) or (not os.path.isdir(dest_folder_abs) and os.path.splitext(dest_folder_abs)[1]):
        target_file_path = dest_folder_abs
    else:
        target_file_path = os.path.join(dest_folder_abs, filename)

    # Kiểm tra trùng lặp
    if os.path.exists(target_file_path):
        print(f"\n{Fore.YELLOW}⚠️ Cảnh báo: Tệp đích đã tồn tại:{Style.RESET_ALL} {target_file_path}")
        try:
            ans = input("   Bạn có muốn ghi đè tệp này không? (y/N): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n>>> Hủy thao tác.")
            sys.exit(0)

        if ans != "y":
            print(">>> Hủy thao tác tải xuống an toàn.")
            sys.exit(0)

    print(f"\n{Fore.CYAN}=== BẮT ĐẦU TẢI TỆP TỪ GITHUB (DL-FILE) ==={Style.RESET_ALL}")
    print(f"  • Tệp cần tải : {filename}")
    print(f"  • Nguồn URL   : {raw_url}")
    print(f"  • Đích lưu    : {target_file_path}")
    print(f"\n{Fore.LIGHTBLACK_EX}>>> Đang kết nối và tải tệp...{Style.RESET_ALL}")

    target_parent = os.path.dirname(target_file_path)
    if target_parent:
        os.makedirs(target_parent, exist_ok=True)

    try:
        # Mở request kèm User-Agent để tránh bị GitHub CDN từ chối
        req = urllib.request.Request(
            raw_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ModCLI/1.0"}
        )

        with urllib.request.urlopen(req, timeout=30) as response, open(target_file_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)

        file_size = os.path.getsize(target_file_path)
        print(f"\n{Fore.GREEN}✅ Tải tệp thành công!{Style.RESET_ALL}")
        print(f"  • Vị trí tệp : {Fore.CYAN}{target_file_path}{Style.RESET_ALL}")
        print(f"  • Dung lượng : {file_size:,} bytes\n")

    except urllib.error.HTTPError as e:
        print(f"\n{Fore.RED}❌ Lỗi HTTP {e.code}: Không thể tải tệp từ GitHub.{Style.RESET_ALL}")
        if e.code == 404:
            print("Chi tiết: Không tìm thấy tệp tại đường dẫn chỉ định (HTTP 404 Not Found).")
        elif e.code == 403:
            print("Chi tiết: Truy cập bị từ chối hoặc đạt giới hạn lượt yêu cầu (HTTP 403 Forbidden).")
        else:
            print(f"Chi tiết lỗi: {e.reason}")
        # Dọn dẹp tệp tải dở nếu có
        if os.path.exists(target_file_path) and os.path.getsize(target_file_path) == 0:
            try:
                os.remove(target_file_path)
            except Exception:
                pass
        sys.exit(1)

    except urllib.error.URLError as e:
        print(f"\n{Fore.RED}❌ Lỗi kết nối mạng: Không thể kết nối đến GitHub.{Style.RESET_ALL}")
        print(f"Chi tiết: {e.reason}")
        sys.exit(1)

    except Exception as e:
        print(f"\n{Fore.RED}❌ Có lỗi xảy ra trong quá trình tải tệp:{Style.RESET_ALL} {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(f"{Fore.RED}❌ Lỗi: Thiếu lệnh tải (dl-folder hoặc dl-file).{Style.RESET_ALL}")
        sys.exit(1)

    action = sys.argv[1].lower()
    args = sys.argv[2:]

    if action in ("dl-folder", "dld-folder", "download-folder"):
        if not args:
            print(f"{Fore.RED}❌ Lỗi: Thiếu URL thư mục GitHub cần tải.{Style.RESET_ALL}")
            print("Cú pháp: mod git dl-folder <git_folder_url> [dest_download_path]")
            print("Ví dụ:")
            print('  mod git dl-folder "https://github.com/obra/superpowers/tree/main/skills/systematic-debugging" .')
            sys.exit(1)

        url = args[0]
        dest_path = args[1] if len(args) > 1 else "."
        download_github_folder(url, dest_path)

    elif action in ("dl-file", "dld-file", "download-file"):
        if not args:
            print(f"{Fore.RED}❌ Lỗi: Thiếu URL tệp GitHub cần tải.{Style.RESET_ALL}")
            print("Cú pháp: mod git dl-file <git_file_url> [dest_download_path]")
            print("Ví dụ:")
            print('  mod git dl-file "https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md" .')
            sys.exit(1)

        url = args[0]
        dest_path = args[1] if len(args) > 1 else "."
        download_github_file(url, dest_path)

    else:
        print(f"{Fore.RED}❌ Lỗi: Lệnh không hợp lệ '{action}'. Chỉ hỗ trợ 'dl-folder' hoặc 'dl-file'.{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n>>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
        sys.exit(0)
