"""
CLI Handler cho tính năng mod notify:
Cú pháp tổng quát: mod notify <action> [args...] [--channel <name>]
Các actions hỗ trợ:
  - send "<message>" [--title "<title>"] [--channel <name>] [--priority <priority>] [--tags <tags>] [--url <click_url>] [--topic <topic>]
  - test [--channel <name>] [--topic <topic>]
  - channels
  - config
"""
import os
import sys
from pathlib import Path

# Đảm bảo UTF-8 và nạp đường dẫn gốc
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from configs.paths import PROJECT_ROOT
from utils.errors import ModCLIError, handle_cli_error
from utils.notifications import (
    get_notifier,
    get_channel_statuses,
    SUPPORTED_CHANNELS,
    DEFAULT_NTFY_TOPIC,
    DEFAULT_NTFY_SERVER,
)

# Mã màu ANSI cơ bản
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_RED = "\033[91m"
C_GRAY = "\033[90m"
C_WHITE = "\033[97m"


def print_syntax():
    print(f"\n{C_YELLOW}{C_BOLD}💡 Cú pháp lệnh Mod Notify (trên 1 dòng để dễ copy):{C_RESET}\n")
    print('mod notify send "<message>" [--title "<title>"] [--channel ntfy] [--priority high] [--tags warning] [--url "https://..."] [--topic custom-topic]\n')
    print("mod notify test [--channel ntfy] [--topic custom-topic]\n")
    print("mod notify channels\n")
    print("mod notify config\n")


def handle_channels():
    statuses = get_channel_statuses()
    print(f"\n{C_CYAN}{C_BOLD}=== DANH SÁCH CÁC KÊNH THÔNG BÁO HỖ TRỢ (NOTIFICATION CHANNELS) ==={C_RESET}")
    print(f"{C_GRAY}{'─' * 75}{C_RESET}")

    for ch in statuses:
        def_tag = f"{C_GREEN}[MẶC ĐỊNH]{C_RESET}" if ch["is_default"] else ""
        status_tag = f"{C_GREEN}● Sẵn sàng{C_RESET}" if ch["configured"] else f"{C_YELLOW}○ Chưa cấu hình .env{C_RESET}"
        print(f"  {C_BOLD}{ch['id']:<10}{C_RESET} {C_GRAY}│{C_RESET} {C_WHITE}{ch['name']}{C_RESET} {def_tag}")
        print(f"             {C_GRAY}├── Trạng thái: {status_tag}")
        print(f"             {C_GRAY}├── Chi tiết  : {C_WHITE}{ch['details']}{C_RESET}")
        print(f"             {C_GRAY}└── Mô tả     : {C_GRAY}{ch['description']}{C_RESET}")
        print()

    print(f"{C_GRAY}{'─' * 75}{C_RESET}")
    print(f"{C_YELLOW}{C_BOLD}💡 Cách dùng cờ --channel:{C_RESET} Thêm `{C_CYAN}--channel <tên_kênh>{C_RESET}` vào lệnh `send` hoặc `test`.")
    print(f"   Ví dụ: `mod notify send \"Done!\" --channel telegram` hoặc `mod notify send \"Done!\" --channel toast`")
    print()


def handle_config():
    print(f"\n{C_CYAN}{C_BOLD}=== HƯỚNG DẪN CẤU HÌNH CÁC KÊNH THÔNG BÁO (.env & THIẾT BỊ) ==={C_RESET}")
    print(f"{C_GRAY}{'─' * 75}{C_RESET}")

    print(f"\n{C_GREEN}{C_BOLD}1. Kênh NTFY (App điện thoại - Mặc định):{C_RESET}")
    print(f"   • {C_WHITE}Cài đặt app:{C_RESET} Tải app {C_BOLD}ntfy{C_RESET} trên Google Play Store hoặc Apple App Store.")
    print(f"   • {C_WHITE}Đăng ký Topic:{C_RESET} Mở app ntfy -> bấm dấu [+] -> nhập tên topic: `{DEFAULT_NTFY_TOPIC}` (hoặc topic riêng của bạn).")
    print(f"   • {C_WHITE}Tùy chỉnh server/token (tùy chọn trong .env):{C_RESET}")
    print(f"     {C_GRAY}NTFY_SERVER_URL=https://ntfy.sh{C_RESET}")
    print(f"     {C_GRAY}NTFY_TOKEN=tk_xxxxxxxxxxxxxx (nếu dùng private topic cần auth){C_RESET}")

    print(f"\n{C_GREEN}{C_BOLD}2. Kênh TELEGRAM BOT:{C_RESET}")
    print(f"   • Tạo bot qua @BotFather trên Telegram để lấy {C_BOLD}Bot Token{C_RESET}.")
    print(f"   • Lấy {C_BOLD}Chat ID{C_RESET} của bạn qua bot @userinfobot.")
    print(f"   • Khai báo vào file `.env` ở thư mục gốc dự án:")
    print(f"     {C_CYAN}TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz{C_RESET}")
    print(f"     {C_CYAN}TELEGRAM_CHAT_ID=987654321{C_RESET}")

    print(f"\n{C_GREEN}{C_BOLD}3. Kênh WINDOWS TOAST (Desktop Notification):{C_RESET}")
    print(f"   • Hoạt động trực tiếp trên Windows qua module PowerShell BurntToast và WinMM audio API.")
    print(f"   • Không yêu cầu cấu hình thêm trong .env.")

    print(f"\n{C_GRAY}{'─' * 75}{C_RESET}\n")


def parse_common_args(args: list[str]) -> tuple[dict, list[str]]:
    """
    Tách các flags phổ biến: --channel, --title, --topic, --priority, --tags, --url
    """
    options = {
        "channel": "ntfy",
        "title": None,
        "topic": DEFAULT_NTFY_TOPIC,
        "priority": None,
        "tags": None,
        "url": None,
    }
    positional_args = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--channel", "-c"):
            if i + 1 < len(args):
                options["channel"] = args[i + 1]
                i += 2
            else:
                raise ModCLIError(
                    title="Thiếu giá trị cho cờ --channel",
                    reason="Cờ `--channel` yêu cầu phải có tên kênh thông báo đi kèm phía sau.",
                    suggestion=f"Các kênh hỗ trợ: {', '.join(SUPPORTED_CHANNELS)}. Ví dụ: `--channel ntfy`"
                )
        elif arg.startswith("--channel="):
            options["channel"] = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--title", "-t"):
            if i + 1 < len(args):
                options["title"] = args[i + 1]
                i += 2
            else:
                raise ModCLIError(
                    title="Thiếu giá trị cho cờ --title",
                    reason="Cờ `--title` yêu cầu phải có chuỗi tiêu đề đi kèm phía sau.",
                    suggestion="Ví dụ: `mod notify send \"Done!\" --title \"Build Success\"`"
                )
        elif arg.startswith("--title="):
            options["title"] = arg.split("=", 1)[1]
            i += 1
        elif arg == "--topic":
            if i + 1 < len(args):
                options["topic"] = args[i + 1]
                i += 2
            else:
                raise ModCLIError(
                    title="Thiếu giá trị cho cờ --topic",
                    reason="Cờ `--topic` yêu cầu phải có tên topic đi kèm phía sau.",
                    suggestion="Ví dụ: `--topic my-custom-topic`"
                )
        elif arg.startswith("--topic="):
            options["topic"] = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--priority", "-p"):
            if i + 1 < len(args):
                options["priority"] = args[i + 1]
                i += 2
            else:
                raise ModCLIError(
                    title="Thiếu giá trị cho cờ --priority",
                    reason="Cờ `--priority` yêu cầu phải có độ ưu tiên đi kèm (min, low, default, high, urgent).",
                    suggestion="Ví dụ: `--priority urgent` hoặc `--priority 5`"
                )
        elif arg.startswith("--priority="):
            options["priority"] = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--tags", "--tag"):
            if i + 1 < len(args):
                options["tags"] = args[i + 1]
                i += 2
            else:
                raise ModCLIError(
                    title="Thiếu giá trị cho cờ --tags",
                    reason="Cờ `--tags` yêu cầu danh sách tag hoặc emoji phân cách bằng dấu phẩy.",
                    suggestion="Ví dụ: `--tags warning,skull` hoặc `--tags tada`"
                )
        elif arg.startswith("--tags="):
            options["tags"] = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--url", "--link"):
            if i + 1 < len(args):
                options["url"] = args[i + 1]
                i += 2
            else:
                raise ModCLIError(
                    title="Thiếu giá trị cho cờ --url",
                    reason="Cờ `--url` yêu cầu một đường dẫn URL hợp lệ đi kèm.",
                    suggestion="Ví dụ: `--url https://example.com`"
                )
        elif arg.startswith("--url="):
            options["url"] = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--syntax", "-s"):
            print_syntax()
            sys.exit(0)
        else:
            positional_args.append(arg)
            i += 1

    return options, positional_args


def handle_send(args: list[str]):
    options, pos_args = parse_common_args(args)

    if not pos_args:
        raise ModCLIError(
            title="Thiếu nội dung thông báo",
            reason="Lệnh `mod notify send` yêu cầu ít nhất một đoạn văn bản nội dung message.",
            suggestion='Ví dụ: `mod notify send "Hoàn thành tiến trình đồng bộ dữ liệu." --title "Thông Báo"`'
        )

    message = " ".join(pos_args)
    channel = options["channel"]
    notifier = get_notifier(channel, topic=options["topic"], title=options["title"])

    print(f"📡 Đang gửi thông báo qua kênh [{C_CYAN}{channel}{C_RESET}]...")
    success = notifier.send_message(
        message=message,
        title=options["title"],
        topic=options["topic"],
        priority=options["priority"],
        tags=options["tags"],
        url=options["url"],
    )

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


def handle_test(args: list[str]):
    options, pos_args = parse_common_args(args)
    channel = options["channel"]
    topic = options["topic"]
    title = options["title"] or f"Mod CLI Test ({channel})"

    test_message = "🔔 Đây là thông báo kiểm tra kết nối từ hệ thống Mod CLI! Nếu bạn nhận được tin nhắn này, kênh thông báo đã hoạt động hoàn hảo."
    if options["tags"] is None:
        options["tags"] = "tada,bell"

    notifier = get_notifier(channel, topic=topic, title=title)

    print(f"🔔 Đang gửi thông báo TEST qua kênh [{C_CYAN}{channel}{C_RESET}]...")
    success = notifier.send_message(
        message=test_message,
        title=title,
        topic=topic,
        priority="high",
        tags=options["tags"],
        url=options["url"] or "https://github.com/codevcn/tools-box",
    )

    if success:
        print(f"🎉 Kênh thông báo '{channel}' đã sẵn sàng sử dụng!")
        sys.exit(0)
    else:
        sys.exit(1)


def main():
    try:
        args = sys.argv[1:]
        if not args:
            handle_channels()
            sys.exit(0)

        action = args[0].lower()
        remaining = args[1:]

        if action in ("-s", "--syntax"):
            print_syntax()
            sys.exit(0)
        elif action in ("channels", "list", "ls"):
            handle_channels()
            sys.exit(0)
        elif action in ("config", "guide", "env"):
            handle_config()
            sys.exit(0)
        elif action == "send":
            handle_send(remaining)
        elif action in ("test", "ping"):
            handle_test(remaining)
        else:
            # Nếu user gõ trực tiếp `mod notify "nội dung"` mà không gõ action `send`, tự hiểu là send
            if not action.startswith("-"):
                handle_send(args)
            else:
                valid_actions = ["send", "test", "channels", "config"]
                raise ModCLIError(
                    title=f"Action không hợp lệ: '{action}'",
                    reason=f"Action '{action}' không nằm trong danh sách action của `mod notify`.",
                    suggestion=f"Các action hợp lệ: {', '.join(f'`{a}`' for a in valid_actions)}.\n💡 Gõ `mod notify --des` để xem chi tiết."
                )

    except Exception as e:
        handle_cli_error(e)


if __name__ == "__main__":
    main()
