Để tùy chỉnh âm báo cho thông báo Toast, bạn có hai phương pháp chính: sử dụng các âm thanh được tích hợp sẵn của hệ điều hành Windows hoặc sử dụng tệp tin âm thanh cá nhân của riêng bạn. Dưới đây là hướng dẫn chi tiết cho từng phương pháp.

### 1. Sử dụng các âm thanh tích hợp sẵn của Windows

Những âm thanh này không phải là các tệp tin `.mp3` hay `.wav` nằm rải rác trong thư mục hệ thống, mà chúng được tích hợp sâu vào bên trong giao diện lập trình ứng dụng (API) của trung tâm thông báo (Windows Action Center) trên Windows 10 và Windows 11.

Bạn có thể gọi chúng ra bằng cách sử dụng tham số `-Sound` trong lệnh `New-BurntToastNotification`. Danh sách các âm thanh này đã được định nghĩa sẵn.

**Các giá trị âm thanh cơ bản (chỉ phát một lần):**

- `Default`: Âm thanh thông báo tiêu chuẩn.
- `IM`: Âm thanh tin nhắn tức thời.
- `Mail`: Âm thanh nhận thư điện tử mới.
- `Reminder`: Âm thanh nhắc nhở nhẹ nhàng.
- `SMS`: Âm thanh tin nhắn văn bản.

**Các giá trị âm thanh lặp lại (phát liên tục cho đến khi bạn tắt thông báo):**

- `Notification.Looping.Alarm` (có thể thay thế bằng `Alarm2` cho đến `Alarm10`): Các kiểu âm báo thức khác nhau.
- `Notification.Looping.Call` (có thể thay thế bằng `Call2` cho đến `Call10`): Các kiểu nhạc chuông điện thoại.

**Ví dụ về cách sử dụng:**

```powershell
# Thông báo với âm báo thư điện tử
New-BurntToastNotification -Text "Có tin nhắn mới", "Kiểm tra hộp thư của bạn." -Sound 'Mail'

# Thông báo với âm báo động lặp lại liên tục
New-BurntToastNotification -Text "Cảnh báo hệ thống!", "Vui lòng kiểm tra lại tiến trình." -Sound 'Notification.Looping.Alarm'

```

### 2. Sử dụng tệp tin âm thanh tùy chỉnh cá nhân

Nếu bạn không muốn sử dụng âm thanh mặc định của Windows, module BurntToast cho phép bạn sử dụng các tệp tin âm thanh của riêng mình. Hệ thống thường hỗ trợ tốt nhất đối với các định dạng như `.wav` hoặc `.mp3`.

Về nguồn gốc âm thanh, bạn hoàn toàn có thể tải chúng từ các trang web chia sẻ hiệu ứng âm thanh miễn phí, sử dụng các bài hát có sẵn trên máy tính, hoặc dùng các công cụ trí tuệ nhân tạo để tổng hợp giọng nói đọc ra chính nội dung thông báo.

Để sử dụng tệp âm thanh bên ngoài, bạn không dùng tham số `-Sound` trực tiếp nữa, mà phải tạo ra một đối tượng âm thanh thông qua lệnh `New-BTAudio`, sau đó truyền đối tượng này vào thông báo.

**Ví dụ về cách sử dụng:**

```powershell
# Bước 1: Khởi tạo đối tượng âm thanh từ một tệp tin có sẵn trên máy tính
$customAudio = New-BTAudio -Path "C:\Sounds\am-thanh-canh-bao.wav"

# Bước 2: Hiển thị thông báo kèm theo đối tượng âm thanh vừa tạo
New-BurntToastNotification -Text "Tiến trình hoàn tất", "Dữ liệu đã được xử lý xong." -Audio $customAudio

```

**Một số lưu ý quan trọng khi dùng âm thanh tùy chỉnh:**

- Đường dẫn đến tệp tin âm thanh cần phải chính xác và tài khoản người dùng đang chạy PowerShell phải có đủ quyền hạn để đọc tệp tin đó.
- Hệ thống Windows thường giới hạn thời gian phát của một thông báo thông thường trong khoảng vài giây. Nếu tệp tin âm thanh của bạn quá dài, nó có thể bị cắt ngang khi thông báo biến mất khỏi màn hình.

Bạn có muốn thử thiết kế một kịch bản hoàn chỉnh, trong đó thông báo Toast vừa phát một đoạn âm thanh tùy chỉnh, vừa hiển thị thanh tiến trình xử lý công việc không?
