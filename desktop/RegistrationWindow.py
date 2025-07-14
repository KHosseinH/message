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

# Required for timestamp parsing
from datetime import datetime

# --- Configuration ---
SERVER_URL = "http://localhost:5000/api" # Base API URL


# --- Registration Window ---
class RegistrationWindow(QWidget):
    """
    Registration interface for new users.
    Allows users to sign up or go back to the login page.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setup_ui()

    def setup_ui(self):
        # Main layout for the registration window
        layout = QVBoxLayout()
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(20)

        # Title Label
        title = QLabel("Register New Account")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FF9800;") # Orange color for the title

        # Form layout for input fields and buttons
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Username Input
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Arial", 12))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a unique username")
        self.username_input.setFont(QFont("Arial", 12))
        self.username_input.setMinimumHeight(35)
        self.username_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")

        # Password Input
        password_label = QLabel("Password:")
        password_label.setFont(QFont("Arial", 12))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Choose a strong password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")

        # Email Input
        email_label = QLabel("Email (optional):")
        email_label.setFont(QFont("Arial", 12))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        self.email_input.setFont(QFont("Arial", 12))
        self.email_input.setMinimumHeight(35)
        self.email_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;")

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.register_btn = QPushButton("Register")
        self.register_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.register_btn.setMinimumHeight(45)
        self.register_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 8px;") # Green button

        self.back_btn = QPushButton("Back to Login")
        self.back_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.back_btn.setMinimumHeight(45)
        self.back_btn.setStyleSheet("background-color: #607D8B; color: white; border-radius: 8px;") # Grey button

        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.back_btn)

        # Add widgets to form layout
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addSpacing(20)
        form_layout.addLayout(button_layout)

        # Add all components to the main layout
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addLayout(form_layout)
        layout.addStretch(2)

        self.setLayout(layout)

        # Connect signals
        self.register_btn.clicked.connect(self.handle_registration)
        self.back_btn.clicked.connect(lambda: self.parent_app.switch_page("login"))
        self.email_input.returnPressed.connect(self.handle_registration) # Allow registration with Enter key

    def handle_registration(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        email = self.email_input.text().strip() or None # Send None if empty

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please choose a username and password.", QMessageBox.StandardButton.Ok)
            return

        self.set_ui_enabled(False)
        self.parent_app.status_bar.showMessage("Attempting to register...", 0)
        self.thread = NetworkThread.NetworkThread(
            "register",
            {"username": username, "password": password, "email": email},
            "POST"
        )
        self.thread.data_received.connect(self.registration_success)
        self.thread.error_occurred.connect(self.show_error)
        self.thread.start()

    def registration_success(self, data):
        # Ensure data is a dictionary for registration success
        if not isinstance(data, dict):
            self.show_error("Registration failed: Unexpected server response format for registration.")
            return

        QMessageBox.information(self, "Registration Success", "Account created successfully! You can now log in.", QMessageBox.StandardButton.Ok)
        self.parent_app.status_bar.showMessage("Registration successful.", 3000)
        self.set_ui_enabled(True)
        # Clear fields and go back to login page
        self.username_input.clear()
        self.password_input.clear()
        self.email_input.clear()
        self.parent_app.switch_page("login")

    def show_error(self, message):
        QMessageBox.warning(self, "Registration Error", message, QMessageBox.StandardButton.Ok)
        self.parent_app.status_bar.showMessage("Registration failed.", 3000)
        self.set_ui_enabled(True)

    def set_ui_enabled(self, enabled):
        """Enables/disables input fields and buttons."""
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.email_input.setEnabled(enabled)
        self.register_btn.setEnabled(enabled)
        self.back_btn.setEnabled(enabled)
