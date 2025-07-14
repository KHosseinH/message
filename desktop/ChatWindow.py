import html
import sys
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QStackedWidget, QListWidget,
                             QMessageBox, QStatusBar, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor, QColor

import NetworkThread
import LoginWindow
import RegistrationWindow

from datetime import datetime
import pytz
import jdatetime

SERVER_URL = "http://localhost:5000/api"


def to_tehran_time_persian(utc_iso_string):
    """تبدیل تاریخ UTC به تاریخ شمسی تهران"""
    utc_dt = datetime.fromisoformat(utc_iso_string.replace('Z', '+00:00'))
    tehran = pytz.timezone('Asia/Tehran')
    tehran_dt = utc_dt.astimezone(tehran)

    jdate = jdatetime.datetime.fromgregorian(datetime=tehran_dt)
    return jdate.strftime('%Y/%m/%d %H:%M')


class ChatWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.last_message_id = 0  # To fetch only new messages
        self.setup_ui()
        self.setup_timers()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Left panel (Online Users & Logout)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        online_label = QLabel("Online Users")
        online_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        online_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        online_label.setStyleSheet("color: #4CAF50;")

        self.online_users_list = QListWidget()
        self.online_users_list.setFixedWidth(220)
        self.online_users_list.setFont(QFont("Arial", 12))
        self.online_users_list.setStyleSheet("border: 1px solid #ddd; border-radius: 5px;")

        left_panel.addWidget(online_label)
        left_panel.addWidget(self.online_users_list)
        left_panel.addStretch(1)

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.logout_btn.setMinimumHeight(40)
        self.logout_btn.setStyleSheet("background-color: #F44336; color: white; border-radius: 8px;")
        left_panel.addWidget(self.logout_btn)

        # Main chat area
        chat_layout = QVBoxLayout()
        chat_layout.setSpacing(8)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 11))
        self.chat_display.setStyleSheet("background-color: #E8E8E8; border: 1px solid #ccc; border-radius: 5px; padding: 5px;")

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setFont(QFont("Arial", 12))
        self.message_input.setMinimumHeight(38)
        self.message_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")

        self.send_btn = QPushButton("Send")
        self.send_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.send_btn.setFixedWidth(120)
        self.send_btn.setMinimumHeight(38)
        self.send_btn.setStyleSheet("background-color: #2196F3; color: white; border-radius: 8px;")

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)

        chat_layout.addWidget(self.chat_display)
        chat_layout.addLayout(input_layout)

        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(chat_layout, stretch=4)

        self.setLayout(main_layout)

        # Connect signals
        self.send_btn.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        self.logout_btn.clicked.connect(self.handle_logout)

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

    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return

        if self.parent_app.user_id is None:
            QMessageBox.warning(self, "Error", "Not logged in. Please log in again.", QMessageBox.StandardButton.Ok)
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

    def message_sent_success(self, data):
        if not isinstance(data, dict):
            print(f"Warning: message_sent_success received unexpected data type: {type(data)}")
        self.message_input.clear()
        self.message_input.setFocus()
        self.parent_app.status_bar.showMessage("Message sent.", 2000)
        self.update_messages()

    def update_users(self):
        if self.parent_app.user_id is None:
            return

        self.users_thread = NetworkThread.NetworkThread("users/online")
        self.users_thread.data_received.connect(self.update_users_list)
        self.users_thread.error_occurred.connect(lambda e: print(f"Error updating online users: {e}"))
        self.users_thread.start()

    def update_users_list(self, users_data):
        if not isinstance(users_data, list):
            print(f"Error: update_users_list received unexpected data type: {type(users_data)}. Expected list.")
            return

        current_users_in_list = {self.online_users_list.item(i).text() for i in range(self.online_users_list.count())}
        online_usernames = {user['username'] for user in users_data if 'username' in user}

        to_add = online_usernames - current_users_in_list
        to_remove = current_users_in_list - online_usernames

        for username in sorted(list(to_add)):
            self.online_users_list.addItem(username)

        for i in range(self.online_users_list.count() - 1, -1, -1):
            item_text = self.online_users_list.item(i).text()
            if item_text in to_remove:
                self.online_users_list.takeItem(i)

    def update_messages(self):
        if self.parent_app.user_id is None:
            return

        self.messages_thread = NetworkThread.NetworkThread(f"messages?last_id={self.last_message_id}")
        self.messages_thread.data_received.connect(self.update_messages_display)
        self.messages_thread.error_occurred.connect(lambda e: print(f"Error updating messages: {e}"))
        self.messages_thread.start()

    def update_messages_display(self, messages_data):
        if not isinstance(messages_data, list):
            print(f"Error: update_messages_display received unexpected data type: {type(messages_data)}. Expected list.")
            return

        if not messages_data:
            return

        sorted_messages = sorted(messages_data, key=lambda x: x.get('id', 0))
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        full_html = ""
        max_message_id = self.last_message_id

        for msg in sorted_messages:
            msg_id = msg.get('id')
            if msg_id is None or msg_id <= self.last_message_id:
                continue

            timestamp_raw = msg.get('timestamp', '')
            try:
                timestamp = to_tehran_time_persian(timestamp_raw)
            except Exception as e:
                print(f"Timestamp conversion error for message id {msg_id}: {e}")
                timestamp = timestamp_raw or "Unknown time"

            sender_name = msg.get('sender', 'Unknown')
            message_text = msg.get('message', '')
            sender_id = msg.get('sender_id')

            if not isinstance(message_text, str):
                message_text = str(message_text)

            safe_message = html.escape(message_text).replace('\n', '<br>')

            if sender_id == self.parent_app.user_id:
                html_block = f"""
                <div style='
                    background: #cfe9ff;
                    color: #000;
                    border-radius: 12px;
                    padding: 8px 12px;
                    margin: 8px 0;
                    max-width: 70%;
                    margin-left: auto;
                    font-family: Arial, sans-serif;
                    word-wrap: break-word;
                    white-space: pre-wrap;
                '>
                    <div style='font-size: 11px; color: #555; text-align: right;'>{timestamp} • You</div>
                    <div style='margin-top: 4px;'>{safe_message}</div>
                </div>
                """
            else:
                html_block = f"""
                <div style='
                    background: #f1f0f0;
                    color: #000;
                    border-radius: 12px;
                    padding: 8px 12px;
                    margin: 8px 0;
                    max-width: 70%;
                    margin-right: auto;
                    font-family: Arial, sans-serif;
                    word-wrap: break-word;
                    white-space: pre-wrap;
                '>
                    <div style='font-size: 11px; color: #555;'>{sender_name} • {timestamp}</div>
                    <div style='margin-top: 4px;'>{safe_message}</div>
                </div>
                """

            full_html += html_block
            if msg_id > max_message_id:
                max_message_id = msg_id

        if full_html:
            try:
                cursor.insertHtml(full_html)
                scrollbar = self.chat_display.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                self.last_message_id = max_message_id
            except Exception as e:
                print(f"Error inserting HTML: {e}")

    def send_activity_ping(self):
        if self.parent_app.user_id is None:
            return

        self.activity_thread = NetworkThread.NetworkThread(
            "/users/activity",
            {"user_id": self.parent_app.user_id},
            "POST"
        )
        self.activity_thread.data_received.connect(
            lambda data: self.parent_app.status_bar.showMessage("Activity ping sent.", 500)
        )
        self.activity_thread.error_occurred.connect(
            lambda e: print(f"Activity ping error: {e}")
        )
        self.activity_thread.start()

    def handle_logout(self):
        reply = QMessageBox.question(self, "Logout Confirmation",
                                     "Are you sure you want to log out?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.stop_timers()
            self.parent_app.user_id = None
            self.parent_app.username = None
            self.last_message_id = 0
            self.chat_display.clear()
            self.online_users_list.clear()
            self.parent_app.status_bar.showMessage("Logged out.", 3000)
            self.parent_app.switch_page("login")
            QMessageBox.information(self, "Logged Out", "You have been successfully logged out.", QMessageBox.StandardButton.Ok)

    def show_error(self, message):
        QMessageBox.warning(self, "Network Error", message, QMessageBox.StandardButton.Ok)
        self.parent_app.status_bar.showMessage("Operation failed.", 3000)
        self.set_ui_enabled(True)

    def set_ui_enabled(self, enabled):
        self.message_input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
