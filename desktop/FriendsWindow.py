from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox,
    QTabWidget, QHBoxLayout, QLineEdit, QLabel
)

class FriendsPage(QWidget):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # ساخت تب‌ها
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # تب آنلاین‌ها
        self.online_tab = QWidget()
        self.online_layout = QVBoxLayout()
        self.online_tab.setLayout(self.online_layout)
        self.online_list = QListWidget()
        self.online_refresh_btn = QPushButton("Refresh Online Friends")
        self.online_refresh_btn.clicked.connect(self.load_online_friends)
        self.online_layout.addWidget(self.online_list)
        self.online_layout.addWidget(self.online_refresh_btn)
        self.tabs.addTab(self.online_tab, "Online Friends")

        # تب همه دوستان
        self.all_tab = QWidget()
        self.all_layout = QVBoxLayout()
        self.all_tab.setLayout(self.all_layout)
        self.all_list = QListWidget()
        self.all_refresh_btn = QPushButton("Refresh All Friends")
        self.all_refresh_btn.clicked.connect(self.load_all_friends)
        self.all_layout.addWidget(self.all_list)
        self.all_layout.addWidget(self.all_refresh_btn)
        self.tabs.addTab(self.all_tab, "All Friends")

        # تب درخواست‌های دوستی
        self.requests_tab = QWidget()
        self.requests_layout = QVBoxLayout()
        self.requests_tab.setLayout(self.requests_layout)
        self.requests_list = QListWidget()
        self.requests_refresh_btn = QPushButton("Refresh Friend Requests")
        self.requests_refresh_btn.clicked.connect(self.load_friend_requests)
        self.requests_layout.addWidget(self.requests_list)
        self.requests_layout.addWidget(self.requests_refresh_btn)
        self.tabs.addTab(self.requests_tab, "Friend Requests")

        # تب افزودن دوست
        self.add_tab = QWidget()
        self.add_layout = QVBoxLayout()
        self.add_tab.setLayout(self.add_layout)
        self.add_label = QLabel("Enter friend ID (e.g. Username#1234):")
        self.add_input = QLineEdit()
        self.add_button = QPushButton("Send Friend Request")
        self.add_button.clicked.connect(self.send_friend_request)
        self.add_layout.addWidget(self.add_label)
        self.add_layout.addWidget(self.add_input)
        self.add_layout.addWidget(self.add_button)
        self.tabs.addTab(self.add_tab, "Add Friend")

        # بارگذاری اولیه داده‌ها در تب‌ها
        self.load_online_friends()
        self.load_all_friends()
        self.load_friend_requests()

    def load_online_friends(self):
        self.online_list.clear()
        try:
            friends = self.fetch_online_friends()
            if not friends:
                self.online_list.addItem("No online friends found.")
            else:
                for f in friends:
                    self.online_list.addItem(f"{f['username']} (Online since {f['last_active']})")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load online friends: {e}")

    def load_all_friends(self):
        self.all_list.clear()
        try:
            friends = self.fetch_all_friends()
            if not friends:
                self.all_list.addItem("No friends found.")
            else:
                for f in friends:
                    self.all_list.addItem(f"{f['username']}  🤝  {f['friend_name']} | Since: {f['since']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load all friends: {e}")

    def load_friend_requests(self):
        self.requests_list.clear()
        try:
            requests = self.fetch_friend_requests()
            if not requests:
                self.requests_list.addItem("No pending friend requests.")
            else:
                for r in requests:
                    self.requests_list.addItem(f"From {r['from_username']} (Requested at {r['requested_at']})")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load friend requests: {e}")

    def send_friend_request(self):
        friend_id = self.add_input.text().strip()
        if not friend_id:
            QMessageBox.warning(self, "Input Error", "Please enter a friend ID.")
            return

        try:
            # فرض کن این متد API درخواست دوستی رو ارسال میکنه
            success, message = self.api_send_friend_request(friend_id)
            if success:
                QMessageBox.information(self, "Success", message)
                self.add_input.clear()
                self.load_friend_requests()  # بروزرسانی درخواست‌ها
            else:
                QMessageBox.warning(self, "Failed", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send friend request: {e}")

    # ----------- متدهای fetch و api (نمونه‌ها) -------------

    def fetch_online_friends(self):
        # TODO: درخواست API برای گرفتن دوستان آنلاین
        return [
            {"username": "Sara", "last_active": "10:23 AM"},
            {"username": "Reza", "last_active": "09:55 AM"},
        ]

    def fetch_all_friends(self):
        # TODO: درخواست API برای گرفتن همه دوستان
        return [
            {"username": "Ali", "friend_name": "Sara", "since": "2024-07-15"},
            {"username": "Ali", "friend_name": "Reza", "since": "2024-05-02"},
        ]

    def fetch_friend_requests(self):
        # TODO: درخواست API برای گرفتن درخواست‌های دوستی
        return [
            {"from_username": "Mahdi", "requested_at": "2024-07-18 15:22"},
            {"from_username": "Neda", "requested_at": "2024-07-19 09:10"},
        ]

    def api_send_friend_request(self, friend_id):
        # TODO: درخواست API برای ارسال درخواست دوستی
        # نمونه پاسخ فرضی
        if friend_id == "Invalid#0000":
            return False, "User not found."
        else:
            return True, "Friend request sent successfully."
