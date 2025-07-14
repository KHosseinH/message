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
import ChatClient

# Required for timestamp parsing
from datetime import datetime

# --- Configuration ---
SERVER_URL = "http://localhost:5000/api" # Base API URL

# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)


    client = ChatClient.ChatClient()
    client.show()
    sys.exit(app.exec())