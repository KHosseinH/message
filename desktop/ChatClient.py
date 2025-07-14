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
import ChatWindow

# Required for timestamp parsing
from datetime import datetime

# --- Configuration ---
SERVER_URL = "http://localhost:5000/api" # Base API URL


# --- Main Application Window ---
class ChatClient(QMainWindow):
    """
    The main window of the chat application, managing different views
    (login, register, chat) using a QStackedWidget.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 1000, 700) # Initial size and position
        self.setMinimumSize(850, 650) # Set a minimum size to ensure usability

        self.user_id = None
        self.username = None

        self.setup_ui()
        self.setup_status_bar()
        self.switch_page("login") # Start with the login page

    def setup_ui(self):
        self.stacked_widget = QStackedWidget()

        self.login_page = LoginWindow.LoginWindow(self)
        self.registration_page = RegistrationWindow.RegistrationWindow(self)
        self.chat_page = ChatWindow.ChatWindow(self) # Instance of ChatWindow

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.registration_page)
        self.stacked_widget.addWidget(self.chat_page)

        self.setCentralWidget(self.stacked_widget)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Welcome to ChatApp! Please log in or register.", 0) # Persistent welcome message initially

    def switch_page(self, page_name):
        """
        Switches the currently displayed page in the stacked widget.
        Manages timer states for the chat window.
        Args:
            page_name (str): 'login', 'register', or 'chat'.
        """
        # Always stop timers when switching away from chat page
        if self.stacked_widget.currentWidget() == self.chat_page:
            self.chat_page.stop_timers()

        if page_name == "login":
            self.stacked_widget.setCurrentWidget(self.login_page)
            self.setWindowTitle("Chat Application - Login")
        elif page_name == "register":
            self.stacked_widget.setCurrentWidget(self.registration_page)
            self.setWindowTitle("Chat Application - Register")
        elif page_name == "chat":
            if self.user_id is None: # Prevent direct access without login
                QMessageBox.warning(self, "Access Denied", "Please log in to access the chat.", QMessageBox.StandardButton.Ok)
                self.switch_page("login") # Redirect to login
                return

            self.stacked_widget.setCurrentWidget(self.chat_page)
            self.setWindowTitle(f"Chat Application - {self.username}")
            self.status_bar.showMessage(f"Logged in as {self.username}", 5000)
            self.chat_page.start_timers_and_initial_fetch() # Start timers when chat page is active
        else:
            print(f"Unknown page name: {page_name}")

    def closeEvent(self, event):
        """Handles the window close event to stop chat timers and perform cleanup."""
        # Ensure timers are stopped when application closes
        if self.chat_page:
            self.chat_page.stop_timers()
        super().closeEvent(event) # Call the base class closeEvent
