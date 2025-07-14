import sys
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QStackedWidget, QListWidget,
                             QMessageBox, QStatusBar, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor, QColor

SERVER_URL = "http://localhost:5000/api" # Base API URL

# --- Network Thread for Async Operations ---
class NetworkThread(QThread):
    """
    A QThread subclass to perform network requests in a non-blocking way.
    Emits data_received on success (can be dict or list) or error_occurred on failure.
    """
    # *** THIS IS THE CRUCIAL CHANGE: Accept any Python object ***
    data_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, endpoint, data=None, method="GET", parent=None):
        super().__init__(parent)
        self.endpoint = endpoint
        self.data = data
        self.method = method

    def run(self):
        full_url = f"{SERVER_URL.rstrip('/')}/{self.endpoint.lstrip('/')}"
        try:
            if self.method == "POST":
                response = requests.post(full_url, json=self.data, timeout=5)
            else: # Default to GET
                # For GET requests, if 'data' is passed, treat it as query parameters
                params = self.data if self.method == "GET" else None
                response = requests.get(full_url, params=params, timeout=5)

            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

            # Emit the JSON response as an object (can be dict or list)
            self.data_received.emit(response.json())

        except requests.exceptions.HTTPError as e:
            # Try to get specific error message from server response
            try:
                error_msg = e.response.json().get('message', f'HTTP Error: {e.response.status_code}')
            except (ValueError, requests.exceptions.JSONDecodeError): # Handle cases where response is not valid JSON
                error_msg = f'HTTP Error {e.response.status_code}: {e.response.text}'
            self.error_occurred.emit(f"Server error: {error_msg}")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Network error: Could not connect to server. Is it running?")
        except requests.exceptions.Timeout:
            self.error_occurred.emit("Network error: Server response timed out.")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"An unexpected network error occurred: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"An unexpected error occurred: {str(e)}")
        self.quit()
    
