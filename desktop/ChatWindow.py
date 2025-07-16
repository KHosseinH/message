import html
from datetime import datetime
import pytz
import jdatetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QListWidget,
                             QMessageBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QTextCursor

import NetworkThread

def to_tehran_time_persian(utc_iso_string):
    utc_dt = datetime.fromisoformat(utc_iso_string.replace('Z', '+00:00'))
    tehran = pytz.timezone('Asia/Tehran')
    tehran_dt = utc_dt.astimezone(tehran)
    jdate = jdatetime.datetime.fromgregorian(datetime=tehran_dt)
    return jdate.strftime('%Y/%m/%d %H:%M')


class ChatWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.last_message_id = 0
        self.setup_ui()
        self.setup_timers()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Sidebar for online users
        right_panel = QVBoxLayout()
        online_label = QLabel("Online Users")
        online_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        online_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        online_label.setStyleSheet("color: #4CAF50;")
        self.online_users_list = QListWidget()
        self.online_users_list.setFixedWidth(220)
        self.online_users_list.setFont(QFont("Arial", 12))
        self.online_users_list.setStyleSheet("border: 1px solid #ddd; border-radius: 5px;")
        right_panel.addWidget(online_label)
        right_panel.addWidget(self.online_users_list)
        right_panel.addStretch(1)

        # Main chat area
        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 11))
        self.chat_display.setStyleSheet("""
            background-color: #2B2D31;
            color: #ddd;
            border: 1px solid #444;
            border-radius: 6px;
            padding: 8px;
        """)

        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setFont(QFont("Arial", 12))
        self.message_input.setMinimumHeight(38)
        self.message_input.setStyleSheet("""
            padding: 5px; 
            border: 1px solid #666; 
            border-radius: 5px;
            background-color: #1e1f23;
            color: #eee;
        """)
        self.send_btn = QPushButton("Send")
        self.send_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.send_btn.setFixedWidth(120)
        self.send_btn.setMinimumHeight(38)
        self.send_btn.setStyleSheet("background-color: #2196F3; color: white; border-radius: 8px;")
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)

        chat_layout.addWidget(self.chat_display)
        chat_layout.addLayout(input_layout)

        main_layout.addLayout(chat_layout, stretch=1)
        main_layout.addLayout(right_panel, stretch=0)
        self.setLayout(main_layout)

        # Connect signals
        self.send_btn.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)

    def setup_timers(self):
        self.update_messages_timer = QTimer(self)
        self.update_messages_timer.timeout.connect(self.update_messages)
        self.update_users_timer = QTimer(self)
        self.update_users_timer.timeout.connect(self.update_users)
        self.activity_ping_timer = QTimer(self)
        self.activity_ping_timer.timeout.connect(self.send_activity_ping)

    def start_timers_and_initial_fetch(self):
        self.update_messages_timer.start(1000)
        self.update_users_timer.start(5000)
        self.activity_ping_timer.start(20000)
        self.update_messages()
        self.update_users()
        self.send_activity_ping()

    def stop_timers(self):
        self.update_messages_timer.stop()
        self.update_users_timer.stop()
        self.activity_ping_timer.stop()

    def update_messages(self):
        if self.parent_app.user_id is None:
            return
        self.messages_thread = NetworkThread.NetworkThread(
            f"messages?last_id={self.last_message_id}&limit=50"
        )
        self.messages_thread.data_received.connect(self.update_messages_display)
        self.messages_thread.error_occurred.connect(lambda e: print(f"Error updating messages: {e}"))
        self.messages_thread.start()

    def update_messages_display(self, messages_data):
        if not isinstance(messages_data, list):
            print(f"Expected list, got {type(messages_data)}")
            return

        sorted_messages = sorted(messages_data, key=lambda x: x.get('id', 0))
        max_message_id = self.last_message_id

        scrollbar = self.chat_display.verticalScrollBar()
        at_bottom = scrollbar.value() >= (scrollbar.maximum() - 30)

        html_content = ""
        for msg in sorted_messages:
            msg_id = msg.get('id')
            if not msg_id or msg_id <= self.last_message_id:
                continue

            timestamp = to_tehran_time_persian(msg.get('timestamp', ''))
            sender_name = msg.get('sender', 'Unknown')
            message_text = html.escape(msg.get('message', ''))

            if msg.get('sender_id') == self.parent_app.user_id:
                line = (f'<div align="right">'
                        f'<b style="color:#4CAF50;">You:</b> {message_text}'
                        f'<br><span style="font-size:10px;color:#888;">{timestamp}</span>'
                        f'</div><hr style="border:none;height:1px;background:#444;">')
            else:
                line = (f'<div align="left">'
                        f'<b style="color:#2196F3;">{sender_name}:</b> {message_text}'
                        f'<br><span style="font-size:10px;color:#888;">{timestamp}</span>'
                        f'</div><hr style="border:none;height:1px;background:#444;">')

            html_content += line
            max_message_id = max(max_message_id, msg_id)

        if html_content:
            self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
            self.chat_display.insertHtml(html_content)

        self.last_message_id = max_message_id

        # smart scroll only if was at bottom
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return
        if self.parent_app.user_id is None:
            QMessageBox.warning(self, "Error", "Not logged in. Please log in again.")
            self.parent_app.switch_page("login")
            return

        self.set_ui_enabled(False)
        self.parent_app.status_bar.showMessage("Sending message...", 0)

        self.send_message_thread = NetworkThread.NetworkThread(
            "messages/send",
            {"sender_id": self.parent_app.user_id, "message": message},
            "POST"
        )
        self.send_message_thread.data_received.connect(self.message_sent_success)
        self.send_message_thread.error_occurred.connect(self.show_error)
        self.send_message_thread.finished.connect(lambda: self.set_ui_enabled(True))
        self.send_message_thread.start()

    def message_sent_success(self, _):
        self.message_input.clear()
        self.message_input.setFocus()
        self.parent_app.status_bar.showMessage("Message sent.", 2000)
        self.update_messages()

    def update_users(self):
        self.users_thread = NetworkThread.NetworkThread("users/online")
        self.users_thread.data_received.connect(self.update_users_list)
        self.users_thread.error_occurred.connect(lambda e: print(f"Error updating users: {e}"))
        self.users_thread.start()

    def update_users_list(self, users_data):
        self.online_users_list.clear()
        for user in users_data:
            self.online_users_list.addItem(user.get('username', 'Unknown'))

    def send_activity_ping(self):
        self.activity_thread = NetworkThread.NetworkThread(
            "/users/activity",
            {"user_id": self.parent_app.user_id},
            "POST"
        )
        self.activity_thread.start()

    def show_error(self, message):
        QMessageBox.warning(self, "Network Error", message)
        self.parent_app.status_bar.showMessage("Operation failed.", 3000)
        self.set_ui_enabled(True)

    def set_ui_enabled(self, enabled):
        self.message_input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
