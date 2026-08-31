from abc import ABC, abstractmethod

class BaseNotifier(ABC):
    @abstractmethod
    def send_message(self, message: str, title: str = None, **kwargs) -> bool:
        """
        Gửi thông báo với nội dung message và các tùy chọn bổ sung (title, priority, tags, url, v.v.).
        Trả về True nếu thành công, False nếu thất bại.
        """
        pass
