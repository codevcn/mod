import sys


def sort_srt_blocks_by_line_count(file_path):
    try:
        # Mở và đọc nội dung của tệp SRT
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Các khối phụ đề trong tệp SRT được phân tách bằng hai dấu xuống dòng
        raw_blocks = content.strip().split("\n\n")

        blocks_info = []

        for block in raw_blocks:
            # Tách mỗi khối thành các dòng riêng biệt
            lines = block.split("\n")

            # Một khối SRT hợp lệ thường có ít nhất 3 dòng:
            # Dòng 1: Số thứ tự
            # Dòng 2: Thời gian (Timestamp)
            # Dòng 3 trở đi: Nội dung câu thoại (Sentence)
            if len(lines) >= 3:
                # Lấy phần nội dung câu thoại (bỏ qua số thứ tự và thời gian)
                text_lines = lines[2:]

                # Đếm số dòng của phần nội dung
                line_count = len(text_lines)

                # Lưu thông tin của khối vào danh sách
                blocks_info.append({"original_block": block, "line_count": line_count})

        # Sắp xếp danh sách các khối theo số lượng dòng giảm dần
        # Tham số reverse=True đảm bảo thứ tự từ lớn đến bé
        sorted_blocks = sorted(blocks_info, key=lambda x: x["line_count"], reverse=True)

        # In kết quả ra màn hình
        print(
            f"Đã tìm thấy {len(sorted_blocks)} khối phụ đề. Dưới đây là kết quả đã được sắp xếp:\n"
        )
        for item in sorted_blocks:
            print(f"=== Số lượng dòng văn bản: {item['line_count']} ===")
            print(item["original_block"])
            print("\n")

    except FileNotFoundError:
        print(
            f"Lỗi: Không tìm thấy tệp tại đường dẫn '{file_path}'. Vui lòng kiểm tra lại."
        )
    except Exception as e:
        print(f"Đã xảy ra một lỗi không xác định: {e}")


if __name__ == "__main__":
    # sys.argv là một danh sách chứa các tham số dòng lệnh được truyền vào chương trình.
    # sys.argv[0] luôn luôn là tên của tệp mã nguồn đang chạy (ví dụ: main.py).
    # sys.argv[1] sẽ là tham số tiếp theo, chính là đường dẫn tệp do người dùng nhập vào.

    # Kiểm tra xem người dùng có truyền đủ tham số đường dẫn tệp hay không
    if len(sys.argv) < 2:
        print("Lỗi: Bạn chưa cung cấp đường dẫn tới tệp SRT.")
        print(
            'Cú pháp chính xác để chạy chương trình: python main.py "đường_dẫn_tới_file.srt"'
        )
        sys.exit(1)  # Thoát chương trình với mã lỗi 1

    # Lấy đường dẫn tệp từ tham số dòng lệnh đầu tiên
    input_file_path = sys.argv[1]

    # Gọi hàm xử lý với đường dẫn tệp vừa nhận được
    sort_srt_blocks_by_line_count(input_file_path)
