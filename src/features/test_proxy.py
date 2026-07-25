import sys
import requests
import subprocess
from colorama import init, Fore

init(autoreset=True)

def main():
    args = sys.argv[1:]
    protocol = "socks5"
    
    if "--protocol" in args:
        idx = args.index("--protocol")
        if idx + 1 < len(args):
            protocol = args[idx + 1]
            args.pop(idx + 1)
            args.pop(idx)
        else:
            print(f"{Fore.RED}Lỗi: Thiếu giá trị cho cờ --protocol.{Fore.RESET}")
            sys.exit(1)

    if not args:
        print(f"{Fore.RED}Lỗi: Thiếu tham số proxy. Cú pháp: mod proxy test {{ip}}:{{port}}:{{login}}:{{password}} [--protocol http|socks5]{Fore.RESET}")
        sys.exit(1)

    proxy_str = ":".join(args).replace("::", ":")
    
    scheme = ""
    if "://" in proxy_str:
        scheme, proxy_str = proxy_str.split("://", 1)
        scheme += "://"
    else:
        scheme = f"{protocol}://"

    parts = proxy_str.split(":")
    
    if len(parts) == 4:
        ip, port, login, password = parts
        if not login or not password:
            print(f"{Fore.RED}Lỗi: Đã nhập thông tin xác thực thì bắt buộc phải nhập đủ cả login và password.{Fore.RESET}")
            sys.exit(1)
        base_proxy = f"{login}:{password}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        base_proxy = f"{ip}:{port}"
    else:
        print(f"{Fore.RED}Lỗi: Sai định dạng proxy. Cú pháp bắt buộc: [scheme://]ip:port hoặc [scheme://]ip:port:login:password{Fore.RESET}")
        sys.exit(1)

    working_proxy_url = f"{scheme}{base_proxy}"
    print(f"{Fore.CYAN}=== Kiểm tra proxy: {working_proxy_url} ==={Fore.RESET}\n")

    proxies = {
        "http": working_proxy_url,
        "https": working_proxy_url,
    }

    # 1. Test bằng code Python (kết nối httpbin.org)
    print(f"{Fore.YELLOW}[1] Kiểm tra kết nối bằng Python (requests)...{Fore.RESET}")
    python_success = False
    try:
        res = requests.get("http://httpbin.org/get", proxies=proxies, timeout=10)
        if res.status_code == 200:
            print(f"{Fore.GREEN}=> Thành công! (Status code: {res.status_code}){Fore.RESET}\n")
            python_success = True
        else:
            print(f"{Fore.RED}=> Thất bại! Status code: {res.status_code}{Fore.RESET}\n")
    except Exception as e:
        err_name = type(e).__name__
        if "ProxyError" in err_name:
            print(f"{Fore.RED}=> Thất bại! Lỗi Proxy: Không thể kết nối hoặc xác thực thất bại (Sai user/pass).{Fore.RESET}\n")
        elif "Timeout" in err_name:
            print(f"{Fore.RED}=> Thất bại! Lỗi Timeout: Hết thời gian chờ kết nối tới proxy.{Fore.RESET}\n")
        elif "ConnectionError" in err_name:
            print(f"{Fore.RED}=> Thất bại! Lỗi Kết nối: Proxy từ chối kết nối hoặc không phản hồi.{Fore.RESET}\n")
        else:
            print(f"{Fore.RED}=> Thất bại! Lỗi không xác định: {err_name}{Fore.RESET}\n")

    if not python_success:
        print(f"{Fore.RED}=> Quá trình kiểm tra bằng Python thất bại. Tiếp tục chạy cURL và API ipify...{Fore.RESET}\n")

    # 2. Test bằng cURL
    print(f"{Fore.YELLOW}[2] Kiểm tra kết nối bằng cURL ({working_proxy_url})...{Fore.RESET}")
    try:
        cmd = ["curl", "-x", working_proxy_url, "-s", "-I", "--max-time", "10", "http://httpbin.org/get"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        
        if "200" in output:
            print(f"{Fore.GREEN}=> Thành công! Có nhận được HTTP 200 OK.{Fore.RESET}\n")
        else:
            if result.stderr.strip():
                err_msg = result.stderr.strip().split('\n')[0]
                print(f"{Fore.RED}=> Thất bại! Lỗi cURL: {err_msg}{Fore.RESET}\n")
            elif output:
                first_line = output.split('\n')[0]
                print(f"{Fore.RED}=> Thất bại! Proxy trả về: {first_line}{Fore.RESET}\n")
            else:
                print(f"{Fore.RED}=> Thất bại! Proxy không phản hồi, đóng kết nối đột ngột hoặc timeout.{Fore.RESET}\n")
    except Exception as e:
        print(f"{Fore.RED}=> Lỗi hệ thống khi chạy lệnh curl: {type(e).__name__}{Fore.RESET}\n")

    # 3. Check IP proxy bằng https://api.ipify.org
    print(f"{Fore.YELLOW}[3] Kiểm tra IP qua API ipify.org...{Fore.RESET}")
    try:
        res = requests.get("https://api.ipify.org", proxies=proxies, timeout=10)
        if res.status_code == 200:
            print(f"{Fore.GREEN}=> IP của Proxy trả về: {res.text.strip()}{Fore.RESET}\n")
        else:
            print(f"{Fore.RED}=> Không thể lấy IP! Status code từ API: {res.status_code}{Fore.RESET}\n")
    except Exception as e:
        err_name = type(e).__name__
        if "ProxyError" in err_name:
            print(f"{Fore.RED}=> Không thể lấy IP! Lỗi Proxy: Không thể kết nối hoặc xác thực thất bại.{Fore.RESET}\n")
        elif "Timeout" in err_name:
            print(f"{Fore.RED}=> Không thể lấy IP! Lỗi Timeout: Hết thời gian kết nối.{Fore.RESET}\n")
        elif "ConnectionError" in err_name:
            print(f"{Fore.RED}=> Không thể lấy IP! Lỗi Kết nối: Proxy từ chối kết nối hoặc đóng đột ngột.{Fore.RESET}\n")
        else:
            print(f"{Fore.RED}=> Lỗi không xác định: {err_name}{Fore.RESET}\n")

if __name__ == "__main__":
    main()
