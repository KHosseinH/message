import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import customtkinter as ctk
from datetime import datetime, timedelta
import os
import sys
import logging
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger('chat_server_app')

# Import ChatDatabase from chat_db.py
try:
    from chat_db import ChatDatabase
    app_logger.info("Successfully imported ChatDatabase from chat_db.py")
except ImportError:
    app_logger.critical("\n--- CRITICAL ERROR ---")
    app_logger.critical("Error: chat_db.py not found or ChatDatabase class not defined within it. "
                        "Please ensure 'chat_db.py' is in the same directory and contains the ChatDatabase class.")
    app_logger.critical("Exiting application.")
    sys.exit(1)
except Exception as e:
    app_logger.critical(f"An unexpected error occurred during ChatDatabase import: {e}", exc_info=True)
    sys.exit(1)

# Initialize the database globally
db = ChatDatabase()
app_logger.info("ChatDatabase instance initialized.")

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Flask API endpoints

@app.route("/api/status", methods=["GET"])
def get_status():
    try:
        stats = db.get_statistics()
        return jsonify({"status": "online", "stats": stats}), 200
    except Exception as e:
        app_logger.error(f"Error getting server status: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/users", methods=["GET"])
def api_get_users():
    try:
        users = db.get_all_users()
        safe_users = [
            {"id": u["id"], "username": u["username"], "email": u["email"],
             "created_at": u["created_at"], "last_activity": u["last_activity"]}
            for u in users
        ]
        return jsonify(safe_users), 200
    except Exception as e:
        app_logger.error(f"Error getting all users: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/online", methods=["GET"])
def api_get_online_users():
    try:
        online_users = db.get_online_users()
        return jsonify([
            {"id": u["id"], "username": u["username"], "last_activity": u["last_activity"]}
            for u in online_users
        ]), 200
    except Exception as e:
        app_logger.error(f"Error getting online users: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/activity", methods=["POST"])
def api_update_user_activity():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"message": "User ID is required"}), 400
    try:
        if db.update_activity(user_id):
            return jsonify({"message": "Activity updated"}), 200
        else:
            return jsonify({"message": "User ID not found"}), 404
    except Exception as e:
        app_logger.error(f"Error updating user activity for {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/register", methods=["POST"])
def api_register_user():
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    try:
        user_id = db.register_user(username, password, email)
        if user_id:
            db.update_activity(user_id)
            return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
        else:
            return jsonify({"message": "Username already taken"}), 409
    except Exception as e:
        app_logger.error(f"Error during registration: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def api_login_user():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    try:
        user = db.authenticate_user(username, password)
        if user:
            db.update_activity(user['id'])
            return jsonify({"message": "Login successful", "user_id": user['id']}), 200
        else:
            return jsonify({"message": "Invalid username or password"}), 401
    except Exception as e:
        app_logger.error(f"Error during login: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/messages/send", methods=["POST"])
def api_send_message():
    sender_id = request.json.get('sender_id')
    message = request.json.get('message')

    if not sender_id or not message:
        return jsonify({"message": "Sender ID and message are required"}), 400

    try:
        user = db.get_user(sender_id)
        if not user:
            return jsonify({"message": "Sender ID does not exist."}), 404

        message_id = db.add_message(sender_id, message)
        db.update_activity(sender_id)
        return jsonify({"message": "Message sent", "message_id": message_id}), 200
    except Exception as e:
        app_logger.error(f"Error sending message: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/messages", methods=["GET"])
def api_get_messages():
    last_id = request.args.get('last_id', 0, type=int)
    try:
        messages = db.get_recent_messages(since_id=last_id)
        return jsonify(messages), 200
    except Exception as e:
        app_logger.error(f"Error getting messages: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Admin Panel GUI Setup
class AdminPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        app_logger.info("AdminPanel: __init__ started.")
        self.title("🛠️ Chat Server Admin Panel")
        self.geometry("1200x800")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.is_running = True

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        try:
            self._setup_ui()
            app_logger.info("AdminPanel: _setup_ui completed.")
        except Exception as e:
            app_logger.critical(f"AdminPanel: Error during _setup_ui: {e}", exc_info=True)
            sys.exit(1)

        self.after(100, self._initial_data_load_and_timer_start)
        app_logger.info("AdminPanel: Scheduled initial data load and timer start.")

    def _initial_data_load_and_timer_start(self):
        app_logger.info("AdminPanel: _initial_data_load_and_timer_start called.")
        try:
            self._update_data()
            app_logger.info("AdminPanel: Initial _update_data completed.")
        except Exception as e:
            app_logger.error(f"AdminPanel: Error during initial _update_data (non-fatal): {e}", exc_info=True)

        if self.is_running:
            self.after(5000, self._start_update_timer_recurring)
            app_logger.info("AdminPanel: Recurring update timer scheduled.")

    def _start_update_timer_recurring(self):
        if self.is_running:
            try:
                self._update_data()
            except Exception as e:
                app_logger.error(f"AdminPanel: Error during recurring _update_data: {e}", exc_info=True)
            self.after(5000, self._start_update_timer_recurring)

    def _setup_ui(self):
        app_logger.info("AdminPanel: _setup_ui started.")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        menu_items = [
            ("👥 Users", self._show_users),
            ("🟢 Online Users", self._show_online_users),
            ("📨 Messages", self._show_messages),
            ("📊 Statistics", self._show_stats)
        ]

        for i, (text, command) in enumerate(menu_items):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                height=40,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")

        self.main_panel = ctk.CTkFrame(self)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.data_text = ctk.CTkTextbox(
            self.main_panel,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.data_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.status_bar = ctk.CTkLabel(
            self,
            text="🟢 Server is starting...",
            anchor="w"
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        app_logger.info("AdminPanel: _setup_ui components created.")

    def _update_data(self):
        try:
            stats = db.get_statistics()
            self.status_bar.configure(
                text=f"🟢 Server is running | Users: {stats.get('total_users', 0)} | "
                     f"Online: {stats.get('online_users', 0)} | Messages: {stats.get('total_messages', 0)}"
            )
        except Exception as e:
            self.status_bar.configure(text=f"🔴 Server error: {e}")
            app_logger.error(f"Error updating status in Admin Panel: {e}", exc_info=True)

    def _show_users(self):
        try:
            users = db.get_all_users()
            display_users = [
                {"id": u["id"], "username": u["username"], "email": u["email"],
                 "created_at": u["created_at"], "last_activity": u["last_activity"]}
                for u in users
            ]
            self._display_data(display_users, ["id", "username", "email", "created_at", "last_activity"], "All Users")
        except Exception as e:
            self._display_error(f"Error loading users: {e}")
            app_logger.error(f"Admin Panel: Error loading users: {e}", exc_info=True)

    def _show_online_users(self):
        try:
            online_users = db.get_online_users()
            self._display_data(online_users, ["id", "username", "last_activity"], "Online Users")
        except Exception as e:
            self._display_error(f"Error loading online users: {e}")
            app_logger.error(f"Admin Panel: Error loading online users: {e}", exc_info=True)

    def _show_messages(self):
        try:
            messages = db.get_recent_messages()
            self._display_data(messages, ["id", "sender", "message", "timestamp"], "Recent Messages")
        except Exception as e:
            self._display_error(f"Error loading messages: {e}")
            app_logger.error(f"Admin Panel: Error loading messages: {e}", exc_info=True)

    def _show_stats(self):
        try:
            stats = db.get_statistics()
            stats_text = "\n".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in stats.items())
            self._set_data_text("📊 Server Statistics\n\n" + stats_text)
        except Exception as e:
            self._display_error(f"Error loading stats: {e}")
            app_logger.error(f"Admin Panel: Error loading stats: {e}", exc_info=True)

    def _display_data(self, data, headers, title):
        self._set_data_text(f"{title}\n\n")
        if not data:
            self._append_data_text("No data available.\n")
            return

        column_widths = {header: len(header) for header in headers}
        for item in data:
            for header in headers:
                column_widths[header] = max(column_widths[header], len(str(item.get(header, ""))))

        header_line_parts = [f"{header.replace('_', ' ').title():<{column_widths[header]}}" for header in headers]
        header_line = " | ".join(header_line_parts)
        self._append_data_text(f"{header_line}\n")
        self._append_data_text(f"{'-' * len(header_line)}\n")

        for item in data:
            line_parts = [f"{str(item.get(header, '')):<{column_widths[header]}}" for header in headers]
            line = " | ".join(line_parts)
            self._append_data_text(f"{line}\n")

    def _set_data_text(self, text):
        self.data_text.configure(state="normal")
        self.data_text.delete("1.0", "end")
        self.data_text.insert("end", text)
        self.data_text.configure(state="disabled")

    def _append_data_text(self, text):
        self.data_text.configure(state="normal")
        self.data_text.insert("end", text)
        self.data_text.configure(state="disabled")

    def _display_error(self, message):
        self._set_data_text(f"❗ Error: {message}")
        app_logger.error(f"Admin Panel Error: {message}")

    def _on_close(self):
        app_logger.info("AdminPanel: Window close requested. Stopping.")
        self.is_running = False
        self.destroy()

# Main Application Execution
def run_flask_server():
    app_logger.info("Flask Server: Attempting to start...")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        app_logger.critical(f"Flask Server: CRITICAL ERROR - Failed to start: {e}", exc_info=True)
        os._exit(1)

if __name__ == "__main__":
    app_logger.info("Main: Starting application sequence.")

    # Port availability check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', 5000))
        sock.listen(1)
        sock.close()
        app_logger.info("Main: Port 5000 is available.")
    except socket.error as e:
        app_logger.critical(f"Main: Port 5000 is already in use: {e}. Please close the application using it or choose a different port.", exc_info=True)
        sys.exit(1)

    # Run Flask server in a daemon thread
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    app_logger.info("Main: Flask server thread started.")

    # Wait a moment for Flask to start
    time.sleep(1)

    # Run CustomTkinter admin panel in main thread
    app_logger.info("Main: Starting CustomTkinter Admin Panel GUI...")
    try:
        admin_panel = AdminPanel()
        app_logger.info("Main: AdminPanel instance created. Calling mainloop().")
        admin_panel.mainloop()
        app_logger.info("Main: Admin Panel mainloop exited.")
    except Exception as e:
        app_logger.critical(f"Main: Error during Admin Panel GUI mainloop: {e}", exc_info=True)

    app_logger.info("Main: Application finished.")
    sys.exit(0)
