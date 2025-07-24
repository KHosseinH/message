from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QApplication, QMessageBox
)
from PyQt6.QtGui import QFont, QClipboard
from PyQt6.QtCore import Qt
import sys

class ProfilePage(QWidget):
    def __init__(self, user_id, username, tag, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.username = username
        self.tag = tag

        self.setWindowTitle(f"Profile - {self.username}#{self.tag}")
        self.resize(400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # عنوان صفحه
        title = QLabel(f"👤 Profile of {self.username}")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # نمایش username#tag که قابل انتخاب باشه
        self.username_tag_label = QLabel(f"{self.username}#{self.tag}")
        self.username_tag_label.setFont(QFont("Courier New", 20))
        self.username_tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_tag_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.username_tag_label)

        # دکمه کپی به کلیپ بورد
        self.copy_btn = QPushButton("Copy to Clipboard 📋")
        self.copy_btn.setFixedHeight(40)
        self.copy_btn.setFont(QFont("Arial", 14))
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_btn)

        layout.addStretch(1)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(f"{self.username}#{self.tag}")
        QMessageBox.information(self, "Copied", f"Copied '{self.username}#{self.tag}' to clipboard!")

# تست صفحه به صورت مستقل
if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = ProfilePage(user_id=123, username="Hossein", tag="0420")
    demo.show()
    sys.exit(app.exec())
