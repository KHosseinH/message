import sqlite3
from datetime import datetime, timedelta
import sys

class ChatDatabase:
    def __init__(self, db_name="chat_app.db"):
        self.db_name = db_name
        self._create_tables()

    def _execute_query(self, query, params=(), fetch_one=False, fetch_all=False):
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row  # دسترسی به ستون‌ها با نام
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            if fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            return cursor.lastrowid  # برای INSERT
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Database error executing query '{query}' with params {params}: {e}")
        finally:
            if conn:
                conn.close()

    def _create_tables(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id)
            );
            """
        ]
        for query in queries:
            try:
                self._execute_query(query)
            except Exception as e:
                print(f"CRITICAL: Error creating table with query: {query} - {e}")
                sys.exit(1)

    # --- User Management ---
    def register_user(self, username, password, email=None):
        query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
        try:
            return self._execute_query(query, (username, password, email))
        except sqlite3.IntegrityError:
            return None  # username taken

    def authenticate_user(self, username, password):
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        return self._execute_query(query, (username, password), fetch_one=True)

    def get_user_by_username(self, username):
        query = "SELECT * FROM users WHERE username = ?"
        return self._execute_query(query, (username,), fetch_one=True)

    def get_user(self, user_id):
        query = "SELECT * FROM users WHERE id = ?"
        return self._execute_query(query, (user_id,), fetch_one=True)

    def get_all_users(self):
        query = "SELECT id, username, email, created_at, last_activity FROM users ORDER BY username ASC"
        return self._execute_query(query, fetch_all=True)

    def update_activity(self, user_id):
        if not self.get_user(user_id):
            return False
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        query = "UPDATE users SET last_activity = ? WHERE id = ?"
        self._execute_query(query, (now, user_id))
        return True

    def get_online_users(self, activity_threshold_seconds=30):
        # زمان فعلی UTC
        now_utc = datetime.utcnow()
        # حد آستانه که یعنی 2 دقیقه پیش UTC
        threshold_time = now_utc - timedelta(seconds=activity_threshold_seconds)
        threshold_time_str = threshold_time.strftime('%Y-%m-%d %H:%M:%S')

        query = "SELECT id, username, last_activity FROM users WHERE last_activity >= ? ORDER BY username ASC"
        online_users = self._execute_query(query, (threshold_time_str,), fetch_all=True)
        return online_users

    # --- Message Management ---
    def add_message(self, sender_id, message_content):
        query = "INSERT INTO messages (sender_id, message) VALUES (?, ?)"
        return self._execute_query(query, (sender_id, message_content))

    def get_recent_messages(self, limit=100, since_id=0):
        query = """
            SELECT m.id, m.sender_id, u.username AS sender, m.message, m.timestamp
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.id > ?
            ORDER BY m.id ASC
            LIMIT ?
        """
        messages = self._execute_query(query, (since_id, limit), fetch_all=True)
        for msg in messages:
            if 'timestamp' in msg and isinstance(msg['timestamp'], str):
                try:
                    dt_obj = datetime.fromisoformat(msg['timestamp'].replace(' ', 'T'))
                    msg['timestamp'] = dt_obj.isoformat(timespec='seconds') + 'Z'
                except ValueError:
                    pass
        return messages

    # --- Statistics ---
    def get_statistics(self):
        total_users_query = "SELECT COUNT(*) FROM users"
        total_messages_query = "SELECT COUNT(*) FROM messages"

        total_users = self._execute_query(total_users_query, fetch_one=True)['COUNT(*)']
        total_messages = self._execute_query(total_messages_query, fetch_one=True)['COUNT(*)']
        online_users_count = len(self.get_online_users())

        return {
            "total_users": total_users,
            "total_messages": total_messages,
            "online_users": online_users_count,
            "last_updated": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
