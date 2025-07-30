from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

class PrivateChatWidget(QWidget):
    # سیگنال برای اطلاع به برنامه که پیام جدید ارسال شده (اختیاری)
    message_sent = pyqtSignal(dict)

    def __init__(self, user_id, friend_id, friend_username, network_thread, parent=None):
        super().__init__(parent)

        self.user_id = user_id
        self.friend_id = friend_id
        self.friend_username = friend_username
        self.network_thread = network_thread

        layout = QVBoxLayout(self)

        self.label = QLabel(f"Private chat with {friend_username}")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        self.input = QLineEdit()
        layout.addWidget(self.input)

        self.send_btn = QPushButton("Send")
        layout.addWidget(self.send_btn)

        self.send_btn.clicked.connect(self.send_message)

        self.load_chat_history()

    def load_chat_history(self):
        # نمونه درخواست تاریخچه پیام (باید متد ارسال در network_thread اینجا کار کنه)
        payload = {
            "action": "get_chat_history",
            "user_id": self.user_id,
            "friend_id": self.friend_id
        }
        try:
            history = self.network_thread.send(payload)  # فرض که send هم پاسخ میده
            for msg in history:
                sender = "You" if msg['from_id'] == self.user_id else self.friend_username
                self.chat_display.append(f"{sender}: {msg['message']}")
        except Exception as e:
            self.chat_display.append("Failed to load chat history.")

    def send_message(self):
        message = self.input.text().strip()
        if not message:
            return

        payload = {
            "from_user_id": self.user_id,
            "to_user_id": self.friend_id,
            "message": message
        }

        self.thread = NetworkThread("messages/send", data=payload, method="POST")
        self.thread.worker.data_received.connect(self.on_message_sent)
        self.thread.worker.error_occurred.connect(self.on_error)
        self.thread.start()

    def on_message_sent(self, data):
        self.chat_display.append(f"You: {self.input.text()}")
        self.input.clear()

    def on_error(self, error_msg):
        QMessageBox.critical(self, "Error Sending Message", error_msg)

    def receive_message(self, message):
        self.chat_display.append(f"{self.friend_username}: {message}")
