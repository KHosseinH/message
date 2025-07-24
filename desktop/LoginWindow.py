import sys
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QStackedWidget, QListWidget,
                             QMessageBox, QStatusBar, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor, QColor

import NetworkThread

# Required for timestamp parsing
from datetime import datetime

# --- Configuration ---
SERVER_URL = "http://localhost:5000/api" # Base API URL

# --- Login Window ---
class LoginWindow(QWidget):
    """
    Login interface for the chat application.
    Allows users to log in or switch to the registration page.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent # Reference to the main ChatClient window
        self.setup_ui()

    def setup_ui(self):
        # Main layout for the login window
        layout = QVBoxLayout()
        layout.setContentsMargins(80, 80, 80, 80) # Increased margins
        layout.setSpacing(20) # Spacing between major elements

        # Title Label
        title = QLabel("Welcome to ChatApp")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4CAF50;") # Green color for the title

        # Form layout for input fields and buttons
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Username Input
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Arial", 12))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFont(QFont("Arial", 12))
        self.username_input.setMinimumHeight(35) # Make input fields taller
        self.username_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")


        # Password Input
        password_label = QLabel("Password:")
        password_label.setFont(QFont("Arial", 12))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.login_btn = QPushButton("Login")
        self.login_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.login_btn.setMinimumHeight(45) # Make buttons taller
        self.login_btn.setStyleSheet("background-color: #2196F3; color: white; border-radius: 8px;") # Blue button

        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.signup_btn.setMinimumHeight(45)
        self.signup_btn.setStyleSheet("background-color: #607D8B; color: white; border-radius: 8px;") # Grey button

        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.signup_btn)

        # Add widgets to form layout
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(20) # More space before buttons
        form_layout.addLayout(button_layout)

        # Add all components to the main layout
        layout.addWidget(title)
        layout.addStretch(1) # Push content towards center
        layout.addLayout(form_layout)
        layout.addStretch(2) # More stretch at the bottom to center form vertically

        self.setLayout(layout)

        # Connect signals
        self.login_btn.clicked.connect(self.handle_login)
        self.signup_btn.clicked.connect(lambda: self.parent_app.switch_page("register"))
        self.password_input.returnPressed.connect(self.handle_login) # Allow login with Enter key

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.", QMessageBox.StandardButton.Ok)
            return

        self.set_ui_enabled(False) # Disable UI during network request
        self.parent_app.status_bar.showMessage("Attempting to log in...", 0) # 0 means persistent message
        self.thread = NetworkThread.NetworkThread(
            "login",
            {"username": username, "password": password},
            "POST"
        )
        self.thread.data_received.connect(self.login_success)
        self.thread.error_occurred.connect(self.show_error)
        self.thread.start()

    def login_success(self, data):
        # Ensure data is a dictionary for login success
        if not isinstance(data, dict):
            self.show_error("Login failed: Unexpected server response format for login.")
            return

        self.parent_app.user_id = data.get("user_id")
        self.parent_app.username = self.username_input.text().strip()
        self.parent_app.tag = data.get("tag", "0000")  # اضافه شده برای رفع ارور
        self.parent_app.status_bar.showMessage(f"Login successful for {self.parent_app.username}.", 3000) # Message for 3 seconds
        self.parent_app.switch_page("chat")
        self.set_ui_enabled(True)
        # Clear fields after successful login for security/next use
        self.username_input.clear()
        self.password_input.clear()


    def show_error(self, message):
        QMessageBox.warning(self, "Login Error", message, QMessageBox.StandardButton.Ok)
        self.parent_app.status_bar.showMessage("Login failed.", 3000)
        self.set_ui_enabled(True)

    def set_ui_enabled(self, enabled):
        """Enables/disables input fields and buttons."""
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.login_btn.setEnabled(enabled)
        self.signup_btn.setEnabled(enabled)