import qrcode
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs.paths import APPDATA_FOLDER

data_folder_path = APPDATA_FOLDER

if data_folder_path is None:
    print("Cảnh báo: Không tìm thấy APPDATA_FOLDER trong configs/paths.py")
else:
    link = input("Nhập text cần tạo QR: ").strip()

    if not link:
        print("Cảnh báo: Text không được để trống.")
        exit(1)

    # Tạo đối tượng QR code
    img = qrcode.make(link)

    try:
        # 1. Tạo timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qr_{timestamp}.png"

        # 2. Tạo đường dẫn và chuẩn hóa dấu "/"
        # os.path.join sẽ dùng "\" trên Windows, nên ta replace nó ngay lập tức
        full_file_path = os.path.join(data_folder_path, filename).replace("\\", "/")

        with open(full_file_path, "wb") as qr_file:
            img.save(qr_file)

        print(f"Đã tạo thành công mã QR tại: {full_file_path}")

        # --- Hỏi người dùng có muốn mở thư mục không ---
        ask_open = (
            input("Mở thư mục lưu mã QR khi đã tạo xong mã QR? [y/n]: ").strip().lower()
        )

        if ask_open == "y":
            # Khi mở thư mục bằng startfile, Windows vẫn hiểu tốt cả "/" và "\"
            os.startfile(data_folder_path)

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
