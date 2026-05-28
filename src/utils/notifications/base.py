from abc import ABC, abstractmethod

class BaseNotifier(ABC):
    @abstractmethod
    def send_message(self, message: str) -> bool:
        """
        Gửi thông báo với nội dung message.
        Trả về True nếu thành công, False nếu thất bại.
        """
        pass
