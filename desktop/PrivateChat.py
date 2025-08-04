from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
import requests

SERVER_URL = "http://localhost:5000/api"

class PrivateChatWidget(QWidget):
    def __init__(self, user_id, friend_id, friend_username, parent=None):
        super().__init__(parent)

        self.user_id = user_id
        self.friend_id = friend_id
        self.friend_username = friend_username

        self.username = getattr(parent, "username", "Unknown")
        self.tag = getattr(parent, "tag", "0000")

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
        try:
            params = {
                "user1_id": self.user_id,
                "user2_id": self.friend_id,
                "limit": 100  # می‌تونی اینو تنظیم کنی
            }
            response = requests.get(f"{SERVER_URL}/private/messages", params=params, timeout=5)
            response.raise_for_status()
            history = response.json()
            print(history)

            self.chat_display.clear()
            for msg in history:
                sender = "You" if msg['sender'] == self.username + "#" + self.tag else self.friend_username
                self.chat_display.append(f"{sender}: {msg['message']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load chat history:\n{e}")

    def send_message(self):
        message = self.input.text().strip()
        if not message:
            return

        try:
            payload = {
                "sender_id": self.user_id,
                "receiver_id": self.friend_id,
                "message": message
            }
            response = requests.post(f"{SERVER_URL}/private/send", json=payload, timeout=5)
            response.raise_for_status()

            # اگر سرور تایید کرد، پیام را در چت نمایش بده
            self.chat_display.append(f"You: {message}")
            self.input.clear()

        except requests.exceptions.HTTPError as http_err:
            try:
                err_msg = response.json().get("error", str(http_err))
            except Exception:
                err_msg = str(http_err)
            QMessageBox.warning(self, "Send Failed", f"HTTP error: {err_msg}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send message:\n{e}")
