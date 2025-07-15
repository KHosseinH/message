import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import LoginWindow
import RegistrationWindow
import ChatWindow

class ChatClient(QMainWindow):
    """
    Main application window with a Discord-like layout.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatApp - Discord Style")
        self.setGeometry(100, 100, 1100, 700)
        self.setMinimumSize(900, 650)

        # User state
        self.user_id = None
        self.username = None

        self.setup_status_bar()
        self.show_login_ui()

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def show_login_ui(self):
        self.login_widget = LoginWindow.LoginWindow(self)
        self.setCentralWidget(self.login_widget)
        self.status_bar.showMessage("Welcome! Please log in.")

    def show_registration_ui(self):
        self.registration_widget = RegistrationWindow.RegistrationWindow(self)
        self.setCentralWidget(self.registration_widget)
        self.status_bar.showMessage("Create a new account.")

    def show_main_ui(self):
        # -----------------------------
        # Left navigation panel
        # -----------------------------
        nav_layout = QVBoxLayout()
        self.home_btn = QPushButton("🏠 Home")
        self.chat_btn = QPushButton("💬 Chat")
        self.profile_btn = QPushButton("👤 Profile")
        self.logout_btn = QPushButton("🚪 Logout")

        for btn in [self.home_btn, self.chat_btn, self.profile_btn, self.logout_btn]:
            btn.setFixedHeight(45)
            btn.setFont(QFont("Arial", 11))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2B2D31;
                    color: #ddd;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #3A3C42;
                }
            """)
            nav_layout.addWidget(btn)

        nav_layout.addStretch(1)
        nav_widget = QWidget()
        nav_widget.setFixedWidth(220)
        nav_widget.setStyleSheet("background-color: #1E1F23;")
        nav_widget.setLayout(nav_layout)

        # -----------------------------
        # Right content area
        # -----------------------------
        self.stacked_widget = QStackedWidget()
        self.home_page = QLabel(f"🏠 Welcome {self.username}!", alignment=Qt.AlignmentFlag.AlignCenter)
        self.home_page.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        
        self.chat_page = ChatWindow.ChatWindow(self)
        
        self.profile_page = QLabel(f"👤 Profile of {self.username}", alignment=Qt.AlignmentFlag.AlignCenter)
        self.profile_page.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.chat_page)
        self.stacked_widget.addWidget(self.profile_page)

        # -----------------------------
        # Connect navigation buttons
        # -----------------------------
        self.home_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.home_page))
        self.chat_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.chat_page))
        self.profile_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.profile_page))
        self.logout_btn.clicked.connect(self.handle_logout)

        # -----------------------------
        # Main layout
        # -----------------------------
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(nav_widget)
        main_layout.addWidget(self.stacked_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.stacked_widget.setCurrentWidget(self.home_page)
        self.status_bar.showMessage(f"Logged in as {self.username}")

    def switch_page(self, page_name):
        """
        Handles switching between app modes.
        """
        if page_name == "login":
            self.show_login_ui()
        elif page_name == "register":
            self.show_registration_ui()
        elif page_name == "chat":
            if self.user_id is None:
                QMessageBox.warning(self, "Access Denied", "Please log in first.")
                return
            self.show_main_ui()
        else:
            print(f"Unknown page: {page_name}")

    def handle_logout(self):
        if QMessageBox.question(self, "Logout Confirmation",
                                "Are you sure you want to log out?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                               ) == QMessageBox.StandardButton.Yes:
            self.user_id = None
            self.username = None
            if hasattr(self, "chat_page"):
                self.chat_page.stop_timers()
            self.switch_page("login")
            self.status_bar.showMessage("Logged out.", 3000)

    def closeEvent(self, event):
        if hasattr(self, "chat_page"):
            self.chat_page.stop_timers()
        self.status_bar.showMessage("Goodbye!")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatClient()
    window.show()
    sys.exit(app.exec())
