import threading
import time
import socket
import sys
import os
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS
import customtkinter as ctk

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
app_logger = logging.getLogger('chat_server_app')

# ---------- Import ChatDatabase ----------
try:
    from chat_db import ChatDatabase
    app_logger.info("Successfully imported ChatDatabase from chat_db.py")
except ImportError:
    app_logger.critical("\n--- CRITICAL ERROR ---")
    app_logger.critical("chat_db.py not found or ChatDatabase class not defined within it.")
    app_logger.critical("Make sure chat_db.py is in the same directory and contains ChatDatabase class.")
    app_logger.critical("Exiting application.")
    sys.exit(1)
except Exception as e:
    app_logger.critical(f"Unexpected error importing ChatDatabase: {e}", exc_info=True)
    sys.exit(1)

# ---------- Initialize Database ----------
db = ChatDatabase()
app_logger.info("ChatDatabase instance initialized.")

# ---------- Flask App Setup ----------
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for all domains

# ------------------ API Endpoints ------------------

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
        # Only expose safe fields
        safe_users = [
            {
                "id": u["id"],
                "username": u["username"],
                "email": u.get("email", ""),
                "created_at": u.get("created_at", ""),
                "last_activity": u.get("last_activity", "")
            }
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
        safe_users = [
            {"id": u["id"], "username": u["username"], "last_activity": u.get("last_activity", "")}
            for u in online_users
        ]
        return jsonify(safe_users), 200
    except Exception as e:
        app_logger.error(f"Error getting online users: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/activity", methods=["POST"])
def api_update_user_activity():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')

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
    data = request.get_json(force=True, silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

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
    data = request.get_json(force=True, silent=True) or {}
    username = data.get('username')
    password = data.get('password')

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
    data = request.get_json(force=True, silent=True) or {}
    sender_id = data.get('sender_id')
    message = data.get('message')

    if not sender_id or not message:
        return jsonify({"message": "Sender ID and message are required"}), 400

    try:
        user = db.get_user_by_id(sender_id)
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


# ------------- Friend System APIs -------------

@app.route("/api/friends/requests", methods=["GET"])
def get_friend_requests_api():
    user_id = request.args.get("user_id")
    if not user_id or not user_id.isdigit():
        return jsonify({"message": "Missing or invalid user_id"}), 400
    user_id = int(user_id)
    try:
        requests = db.get_pending_friend_requests(user_id)
        app_logger.info(f"Friend requests for user_id={user_id}: {requests}")
        return jsonify(requests), 200
    except Exception as e:
        app_logger.error(f"Error getting friend requests for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/friends/request", methods=["POST"])
def send_friend_request():
    data = request.get_json(force=True, silent=True) or {}
    from_user_id = data.get("from_user_id")
    to_identifier = data.get("to_identifier")  # مثل username#1234

    if not from_user_id or not to_identifier:
        return jsonify({"message": "Missing data"}), 400

    try:
        success, message = db.send_friend_request(int(from_user_id), to_identifier)
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"message": message}), 400
    except Exception as e:
        app_logger.error(f"Error sending friend request from {from_user_id} to {to_identifier}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/friends/respond", methods=["POST"])
def respond_friend_request():
    data = request.get_json(force=True, silent=True) or {}
    requester_id = data.get("requester_id")
    addressee_id = data.get("addressee_id")
    accept = data.get("accept")

    if not all([requester_id, addressee_id]) or accept is None:
        return jsonify({"error": "requester_id, addressee_id and accept(boolean) are required"}), 400

    try:
        success, msg = db.respond_to_friend_request(requester_id, addressee_id, accept=bool(accept))
        if success:
            return jsonify({"message": msg}), 200
        else:
            return jsonify({"error": msg}), 400
    except Exception as e:
        app_logger.error(f"Error responding to friend request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/friends/all", methods=["GET"])
def get_all_friends():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400

    try:
        all_friends = db.get_friends(int(user_id))
        return jsonify(all_friends), 200
    except Exception as e:
        app_logger.error(f"Error getting all friends for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/friends/online", methods=["GET"])
def get_online_friends():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400

    try:
        online_friends = db.get_online_friends(int(user_id))
        return jsonify(online_friends), 200
    except Exception as e:
        app_logger.error(f"Error getting online friends for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/friends/remove", methods=["POST"])
def remove_friend():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")
    friend_id = data.get("friend_id")

    if not user_id or not friend_id:
        return jsonify({"error": "user_id and friend_id are required"}), 400

    try:
        db.remove_friend(user_id, friend_id)
        return jsonify({"message": "Friend removed"}), 200
    except Exception as e:
        app_logger.error(f"Error removing friend {friend_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ----------------- Admin Panel GUI -----------------

class AdminPanel(ctk.CTk):
    def __init__(self):
        super().__init__()

        app_logger.info("AdminPanel: Initializing GUI...")

        self.title("🛠️ Chat Server Admin Panel")
        self.geometry("1200x800")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.is_running = True

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        try:
            self._setup_ui()
        except Exception as e:
            app_logger.critical(f"AdminPanel: Error during UI setup: {e}", exc_info=True)
            sys.exit(1)

        # Start initial data load and recurring updates
        self.after(100, self._initial_data_load_and_start_timer)

    def _initial_data_load_and_start_timer(self):
        app_logger.info("AdminPanel: Loading initial data and starting update timer.")
        try:
            self._update_data()
        except Exception as e:
            app_logger.error(f"AdminPanel: Error during initial data update: {e}", exc_info=True)

        if self.is_running:
            self.after(5000, self._start_update_timer)

    def _start_update_timer(self):
        if self.is_running:
            try:
                self._update_data()
            except Exception as e:
                app_logger.error(f"AdminPanel: Error during periodic data update: {e}", exc_info=True)
            self.after(5000, self._start_update_timer)

    def _setup_ui(self):
        app_logger.info("AdminPanel: Setting up UI components.")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar Frame
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Sidebar buttons and commands
        menu_items = [
            ("👥 Users", self._show_users),
            ("🟢 Online Users", self._show_online_users),
            ("📨 Messages", self._show_messages),
            ("📊 Statistics", self._show_stats),
            ("🤝 Friend Requests", self._show_friend_requests),
            ("👫 Friends List", self._show_friends)
        ]

        for i, (text, cmd) in enumerate(menu_items):
            btn = ctk.CTkButton(
                master=self.sidebar,
                text=text,
                command=cmd,
                height=40,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")

        # Main content frame
        self.main_panel = ctk.CTkFrame(self)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.data_text = ctk.CTkTextbox(
            master=self.main_panel,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled"
        )
        self.data_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Status bar
        self.status_bar = ctk.CTkLabel(
            master=self,
            text="🟢 Server is starting...",
            anchor="w"
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        app_logger.info("AdminPanel: UI setup completed.")

    def _update_data(self):
        # Update status bar with server stats
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
                {
                    "id": u["id"],
                    "username": u["username"],
                    "email": u.get("email", ""),
                    "created_at": u.get("created_at", ""),
                    "last_activity": u.get("last_activity", "")
                }
                for u in users
            ]
            self._display_data(display_users, ["id", "username", "email", "created_at", "last_activity"], "All Users")
        except Exception as e:
            self._display_error(f"Error loading users: {e}")

    def _show_online_users(self):
        try:
            online_users = db.get_online_users()
            self._display_data(online_users, ["id", "username", "last_activity"], "Online Users")
        except Exception as e:
            self._display_error(f"Error loading online users: {e}")

    def _show_messages(self):
        try:
            messages = db.get_recent_messages()
            self._display_data(messages, ["id", "sender", "message", "timestamp"], "Recent Messages")
        except Exception as e:
            self._display_error(f"Error loading messages: {e}")

    def _show_stats(self):
        try:
            stats = db.get_statistics()
            stats_text = "\n".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in stats.items())
            self._set_data_text("📊 Server Statistics\n\n" + stats_text)
        except Exception as e:
            self._display_error(f"Error loading stats: {e}")

    def _show_friend_requests(self):
        try:
            requests = db.get_all_pending_friend_requests()
            self._display_data(requests, ["requester", "addressee", "requested_at"], "Pending Friend Requests")
        except Exception as e:
            self._display_error(f"Error loading friend requests: {e}")

    def _show_friends(self):
        try:
            friends = db.get_all_friends()
            self._display_data(friends, ["user_id", "friend_id", "since"], "Friends List")
        except Exception as e:
            self._display_error(f"Error loading friends list: {e}")

    def _display_data(self, data, headers, title):
        self._set_data_text(f"{title}\n\n")
        if not data:
            self._append_data_text("No data available.\n")
            return

        # Calculate column widths
        column_widths = {header: len(header) for header in headers}
        for row in data:
            for header in headers:
                column_widths[header] = max(column_widths[header], len(str(row.get(header, ""))))

        # Header line
        header_line = " | ".join(f"{header.replace('_', ' ').title():<{column_widths[header]}}" for header in headers)
        separator = "-" * len(header_line)
        self._append_data_text(header_line + "\n")
        self._append_data_text(separator + "\n")

        # Rows
        for row in data:
            line = " | ".join(f"{str(row.get(header, '')):<{column_widths[header]}}" for header in headers)
            self._append_data_text(line + "\n")

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
        app_logger.info("AdminPanel: Window close requested. Shutting down...")
        self.is_running = False
        self.destroy()


# ----------------- Run Server and GUI -----------------

def run_flask_server():
    app_logger.info("Starting Flask server...")
    try:
        # For production, you might want to use waitress/gunicorn instead
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        app_logger.critical(f"Failed to start Flask server: {e}", exc_info=True)
        os._exit(1)


if __name__ == "__main__":
    app_logger.info("Application starting...")

    # Check if port 5000 is free before running Flask
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', 5000))
        sock.listen(1)
        sock.close()
        app_logger.info("Port 5000 is free.")
    except socket.error as e:
        app_logger.critical(f"Port 5000 is already in use: {e}. Please close the conflicting application or use a different port.", exc_info=True)
        sys.exit(1)

    # Start Flask server in a background thread
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    app_logger.info("Flask server thread started.")

    # Small delay to ensure Flask server starts
    time.sleep(1)

    # Run Admin Panel GUI in main thread
    app_logger.info("Starting CustomTkinter Admin Panel GUI...")
    try:
        admin_panel = AdminPanel()
        admin_panel.mainloop()
        app_logger.info("Admin Panel GUI closed.")
    except Exception as e:
        app_logger.critical(f"Error during Admin Panel GUI mainloop: {e}", exc_info=True)

    app_logger.info("Application exiting.")
    sys.exit(0)
