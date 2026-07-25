import argparse
import subprocess
import sys
import shutil

def check_cloudflared_installed():
    print("[mod tunnel] Đang kiểm tra cloudflared...")
    if shutil.which("cloudflared") is None:
        print("❌ Lỗi: Không tìm thấy 'cloudflared' trong PATH.")
        print("Vui lòng cài đặt cloudflared (https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)")
        sys.exit(1)
    
    try:
        result = subprocess.run(["cloudflared", "--version"], capture_output=True, text=True, check=True)
        print(f"✅ Đã tìm thấy: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Lỗi: Không thể thực thi 'cloudflared --version'.")
        sys.exit(1)

import re
import io
import qrcode

def run_quick_tunnel(port):
    print(f"[mod tunnel] Đang khởi động quick tunnel tại http://localhost:{port}...")
    cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]
    print(f"[mod tunnel] Lệnh: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        # Cấu hình stdout sang utf-8 để hiển thị qrcode không bị lỗi encoding trên Windows
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8')
        url_found = False
        cloudflare_error = False
        
        for line in iter(process.stdout.readline, ''):
            print(line, end='', flush=True)
            
            # Phát hiện lỗi từ Cloudflare
            if "Error unmarshaling QuickTunnel response" in line or "500 Internal Server Error" in line or "error code: 1101" in line:
                cloudflare_error = True
            
            if not url_found and "trycloudflare.com" in line:
                match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                if match:
                    url = match.group(1)
                    print("\n" + "="*50)
                    print(f"🔗 Public URL: {url}")
                    print("="*50)
                    
                    qr = qrcode.QRCode()
                    qr.add_data(url)
                    qr.make()
                    qr.print_ascii(invert=True)
                    print("="*50 + "\n")
                    url_found = True
                    
        process.stdout.close()
        process.wait()
        
        if cloudflare_error:
            print("\n" + "!"*50)
            print("⚠️ CẢNH BÁO: Máy chủ Cloudflare đang gặp sự cố (Lỗi 500/1101)!")
            print("Đây là lỗi tạm thời từ hệ thống cấp phát Quick Tunnel miễn phí của Cloudflare.")
            print("Vui lòng đợi vài phút và thử chạy lại lệnh.")
            print("!"*50 + "\n")
            
    except KeyboardInterrupt:
        if 'process' in locals():
            process.terminate()
        print("\n[mod tunnel] Đã đóng tunnel.")
    except Exception as e:
        print(f"❌ Lỗi khi chạy tunnel: {e}")
        sys.exit(1)

def main():
    args = sys.argv[1:]
    
    # Tính năng hiện tại: mod tunnel [port]
    port = "3000"
    
    if args:
        if args[0].isdigit():
            port = args[0]
        else:
            # Nếu truyền lệnh khác không phải số, hiện tại báo lỗi (để dành cho mở rộng sau này)
            print(f"❌ Lệnh không được hỗ trợ hoặc port không hợp lệ: {args[0]}")
            print("💡 Cách dùng hiện tại: mod tunnel [port]")
            sys.exit(1)
            
    check_cloudflared_installed()
    run_quick_tunnel(port)

if __name__ == "__main__":
    main()
