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
from FriendsWindow import FriendsPage
from ProfileWindow import ProfilePage

class ChatClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatApp - Discord Style")
        self.setGeometry(100, 100, 1100, 700)
        self.setMinimumSize(900, 650)

        self.user_id = None
        self.username = None
        self.tag = None

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # صفحات
        self.home_page = None
        self.chat_page = None
        self.profile_page = None
        self.friends_page = None

        # ویجت های ناوبری و اصلی
        self.nav_widget = None
        self.stacked_widget = None

        self.show_login_ui()

    def create_navigation(self):
        nav_layout = QVBoxLayout()
        
        self.home_btn = QPushButton("🏠 Home")
        self.chat_btn = QPushButton("💬 Chat")
        self.friends_btn = QPushButton("👥 Friends")  # اینجا تعریف میشه
        self.profile_btn = QPushButton("👤 Profile")
        self.logout_btn = QPushButton("🚪 Logout")

        buttons = [self.home_btn, self.chat_btn, self.friends_btn, self.profile_btn, self.logout_btn]

        for btn in buttons:
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

        # اتصال سیگنال‌ها
        self.home_btn.clicked.connect(self.open_home_page)
        self.chat_btn.clicked.connect(self.open_chat_page)
        self.friends_btn.clicked.connect(self.open_friends_page)
        self.profile_btn.clicked.connect(self.open_profile_page)
        self.logout_btn.clicked.connect(self.handle_logout)

        nav_widget = QWidget()
        nav_widget.setFixedWidth(220)
        nav_widget.setStyleSheet("background-color: #1E1F23;")
        nav_widget.setLayout(nav_layout)
        return nav_widget
    def show_main_ui(self):
        if self.chat_page:
            self.chat_page.stop_timers()

        self.nav_widget = self.create_navigation()

        self.stacked_widget = QStackedWidget()
        self.home_page = QLabel(f"🏠 Welcome {self.username}!", alignment=Qt.AlignmentFlag.AlignCenter)
        self.home_page.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        self.chat_page = ChatWindow.ChatWindow(self)
        self.profile_page = ProfilePage(self.user_id, self.username, self.tag)


        self.friends_page = FriendsPage(user_id=self.user_id)

        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.chat_page)
        self.stacked_widget.addWidget(self.friends_page)  # اضافه کردن صفحه دوستان به استک
        self.stacked_widget.addWidget(self.profile_page)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.nav_widget)
        main_layout.addWidget(self.stacked_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.open_home_page()
        self.status_bar.showMessage(f"Logged in as {self.username}")

    def open_friends_page(self):
        if self.chat_page:
            self.chat_page.stop_timers()
        self.stacked_widget.setCurrentWidget(self.friends_page)
        self.status_bar.showMessage("Viewing your friends.")

    def open_home_page(self):
        if self.chat_page:
            self.chat_page.stop_timers()
        self.stacked_widget.setCurrentWidget(self.home_page)
        self.status_bar.showMessage("You're at home.")

    def open_chat_page(self):
        self.stacked_widget.setCurrentWidget(self.chat_page)
        self.chat_page.start_timers_and_initial_fetch()
        self.status_bar.showMessage("You're now in the chat room.")

    def open_profile_page(self):
        if self.chat_page:
            self.chat_page.stop_timers()
        self.stacked_widget.setCurrentWidget(self.profile_page)
        self.status_bar.showMessage("Viewing your profile.")

    def handle_logout(self):
        confirm = QMessageBox.question(self, "Logout Confirmation",
                                       "Are you sure you want to log out?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.user_id = None
            self.username = None
            if self.chat_page:
                self.chat_page.stop_timers()
            self.show_login_ui()
            self.status_bar.showMessage("Logged out.", 3000)

    def closeEvent(self, event):
        if self.chat_page:
            self.chat_page.stop_timers()
        self.status_bar.showMessage("Goodbye!")
        event.accept()
    
    def switch_page(self, page_name):
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

    def open_friends_page(self):
        if self.chat_page:
            self.chat_page.stop_timers()
        self.stacked_widget.setCurrentWidget(self.friends_page)
        self.status_bar.showMessage("Viewing your friends.")

    def show_login_ui(self):
        self.login_widget = LoginWindow.LoginWindow(self)
        self.setCentralWidget(self.login_widget)
        self.status_bar.showMessage("Welcome! Please log in.")

    def show_registration_ui(self):
        self.registration_widget = RegistrationWindow.RegistrationWindow(self)
        self.setCentralWidget(self.registration_widget)
        self.status_bar.showMessage("Create a new account.")

    def open_friends_page(self):
        if self.chat_page:
            self.chat_page.stop_timers()
        self.stacked_widget.setCurrentWidget(self.friends_page)
        self.status_bar.showMessage("Viewing your friends.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatClient()
    window.show()
    sys.exit(app.exec())
