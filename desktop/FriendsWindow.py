from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox,
    QTabWidget, QLabel, QLineEdit, QHBoxLayout, QListWidgetItem
)
import requests
from functools import partial

SERVER_URL = "http://localhost:5000/api"  # Base API URL

class FriendsPage(QWidget):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # --- Online Friends Tab ---
        self.online_tab = QWidget()
        self.online_layout = QVBoxLayout()
        self.online_tab.setLayout(self.online_layout)
        self.online_list = QListWidget()
        self.online_refresh_btn = QPushButton("Refresh Online Friends")
        self.online_refresh_btn.clicked.connect(self.load_online_friends)
        self.online_layout.addWidget(self.online_list)
        self.online_layout.addWidget(self.online_refresh_btn)
        self.tabs.addTab(self.online_tab, "Online Friends")

        # --- All Friends Tab ---
        self.all_tab = QWidget()
        self.all_layout = QVBoxLayout()
        self.all_tab.setLayout(self.all_layout)
        self.all_list = QListWidget()
        self.all_refresh_btn = QPushButton("Refresh All Friends")
        self.all_refresh_btn.clicked.connect(self.load_all_friends)
        self.all_layout.addWidget(self.all_list)
        self.all_layout.addWidget(self.all_refresh_btn)
        self.tabs.addTab(self.all_tab, "All Friends")

        # --- Friend Requests Tab ---
        self.requests_tab = QWidget()
        self.requests_layout = QVBoxLayout()
        self.requests_tab.setLayout(self.requests_layout)
        self.requests_list = QListWidget()
        self.requests_refresh_btn = QPushButton("Refresh Friend Requests")
        self.requests_refresh_btn.clicked.connect(self.load_friend_requests)
        self.requests_layout.addWidget(self.requests_list)
        self.requests_layout.addWidget(self.requests_refresh_btn)
        self.tabs.addTab(self.requests_tab, "Friend Requests")

        # --- Add Friend Tab ---
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

        # Load initial data
        self.load_online_friends()
        self.load_all_friends()
        self.load_friend_requests()

    def load_online_friends(self):
        self.online_list.clear()
        try:
            friends = self.fetch_online_friends()
            if not friends:
                self.online_list.addItem("No online friends.")
            else:
                for f in friends:
                    # فرض می‌کنیم f شامل username و since هست
                    self.online_list.addItem(f"{f.get('username', 'Unknown')} 🤝 | Since: {f.get('since', 'N/A')}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load online friends:\n{e}")

    def load_all_friends(self):
        self.all_list.clear()
        try:
            friends = self.fetch_all_friends()
            if not friends:
                self.all_list.addItem("No friends found.")
            else:
                for f in friends:
                    # فرض می‌کنیم f شامل username، friend_name و since هست
                    user_name = f.get('username', 'Unknown')
                    friend_name = f.get('friend_name', 'Unknown')
                    since = f.get('since', 'N/A')
                    self.all_list.addItem(f"{user_name} 🤝 {friend_name} | Since: {since}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load all friends:\n{e}")

    def load_friend_requests(self):
        self.requests_list.clear()
        try:
            requests = self.fetch_friend_requests()
            # print("Friend requests data:", requests)  # <--- چک کردن داده دریافتی
            if not requests:
                self.requests_list.addItem("No pending friend requests.")
            else:
                for r in requests:
                    requester_id = r.get('from_user')
                    print("requester_id:", requester_id)  # <--- چک کردن تک تک آی‌دی‌ها
                    from_user = r.get('from_user', "unknown")
                    requested_at = r.get('requested_at', 'N/A')

                    item_widget = QWidget()
                    layout = QHBoxLayout(item_widget)
                    layout.setContentsMargins(5, 0, 5, 0)

                    label = QLabel(f"From {from_user} ({requested_at})")
                    btn_accept = QPushButton("✔")
                    btn_reject = QPushButton("✖")

                    btn_accept.setStyleSheet("background-color: lightgreen;")
                    btn_reject.setStyleSheet("background-color: lightcoral;")

                    # اتصال صحیح
                    btn_accept.clicked.connect(partial(self.accept_request, requester_id))
                    btn_reject.clicked.connect(partial(self.reject_request, requester_id))

                    layout.addWidget(label)
                    layout.addStretch()
                    layout.addWidget(btn_accept)
                    layout.addWidget(btn_reject)

                    item = QListWidgetItem()
                    item.setSizeHint(item_widget.sizeHint())

                    self.requests_list.addItem(item)
                    self.requests_list.setItemWidget(item, item_widget)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load friend requests:\n{e}")

    def accept_request(self, requester_id):
        try:
            payload = {
                "requester_id": requester_id,
                "addressee_id": self.user_id,
                "accept": True
            }
            print("ACCEPT PAYLOAD:", payload)  # 👈 لاگ اضافه کن

            response = requests.post(
                f"{SERVER_URL}/friends/respond",
                json=payload,
                timeout=5
            )
            if response.status_code == 200:
                QMessageBox.information(self, "Friend Request", f"Accepted {requester_id}")
                self.load_friend_requests()
            else:
                error = response.json().get("error", "Unknown error")
                # print("SERVER ERROR:", error)
                QMessageBox.warning(self, "Error", f"Could not accept: {error}")
        except Exception as e:
            print("NETWORK ERROR:", e)
            QMessageBox.critical(self, "Error", f"Network error: {e}")


    def reject_request(self, requester_id):
        try:
            response = requests.post(
                f"{SERVER_URL}/friends/respond",
                json={
                    "requester_id": requester_id,
                    "addressee_id": self.user_id,
                    "accept": False
                },
                timeout=5
            )
            if response.status_code == 200:
                QMessageBox.information(self, "Friend Request", f"Rejected {requester_id}")
                self.load_friend_requests()
            else:
                error = response.json().get("error", "Unknown error")
                QMessageBox.warning(self, "Error", f"Could not reject: {error}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Network error: {e}")


    def send_friend_request(self):
        friend_id = self.add_input.text().strip()
        if not friend_id:
            QMessageBox.warning(self, "Input Error", "Please enter a friend ID.")
            return

        try:
            success, message = self.api_send_friend_request(friend_id)
            if success:
                QMessageBox.information(self, "Success", message)
                self.add_input.clear()
                self.load_friend_requests()
            else:
                QMessageBox.warning(self, "Failed", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send friend request:\n{e}")

    # ----------- Actual API Calls ------------

    def fetch_online_friends(self):
        try:
            response = requests.get(
                f"{SERVER_URL}/friends/online",
                params={"user_id": self.user_id},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch online friends: {e}")

    def fetch_friend_requests(self):
        try:
            response = requests.get(
                f"{SERVER_URL}/friends/requests",
                params={
                    "user_id": self.user_id,
                    "user_tag": self.user_tag,  # اضافه کردن تگ
                },
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            print(data)
            return data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch friend requests: {e}")


    def fetch_friend_requests(self):
        try:
            response = requests.get(
                f"{SERVER_URL}/friends/requests",
                params={"user_id": self.user_id},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            print(data)
            return data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch friend requests: {e}")

    def api_send_friend_request(self, friend_id):
        try:
            response = requests.post(
                f"{SERVER_URL}/friends/request",
                json={
                    "from_user_id": self.user_id,
                    "to_identifier": friend_id
                },
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return True, data.get("message", "Friend request sent successfully.")

        except requests.exceptions.HTTPError as http_err:
            try:
                error_msg = response.json().get("message", str(http_err))
            except Exception:
                error_msg = str(http_err)
            return False, f"HTTP error occurred: {error_msg}"

        except requests.exceptions.Timeout:
            return False, "Request timed out. Please try again."

        except requests.exceptions.RequestException as err:
            return False, f"Network error: {err}"

        except Exception as e:
            return False, f"Unexpected error: {e}"
