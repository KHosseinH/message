from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
)
import requests

SERVER_URL = "http://localhost:5000/api"  # آدرس سرور

class PrivateChatDialog(QDialog):
    def __init__(self, user_id, friend_id, friend_username, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.friend_id = friend_id
        self.friend_username = friend_username

        self.setWindowTitle(f"Chat with {friend_username}")
        self.resize(400, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        self.layout.addWidget(QLabel(f"Chat with {friend_username}"))
        self.layout.addWidget(self.chat_history)
        self.layout.addWidget(self.message_input)
        self.layout.addWidget(self.send_button)

        self.load_messages()

    def load_messages(self):
        try:
            response = requests.get(
                f"{SERVER_URL}/private/messages",
                params={"user1_id": self.user_id, "user2_id": self.friend_id},
                timeout=5
            )
            response.raise_for_status()
            messages = response.json()
            self.chat_history.clear()
            for msg in messages:
                sender = msg.get("sender", "unknown")
                text = msg.get("message", "")
                timestamp = msg.get("timestamp", "")
                self.chat_history.append(f"[{timestamp}] {sender}: {text}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load messages:\n{e}")

    def send_message(self):
        text = self.message_input.text().strip()
        if not text:
            return
        try:
            payload = {
                "sender_id": self.user_id,
                "receiver_id": self.friend_id,
                "message": text
            }
            response = requests.post(
                f"{SERVER_URL}/private/send",
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            self.message_input.clear()
            self.load_messages()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send message:\n{e}")
