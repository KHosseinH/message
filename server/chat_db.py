import sqlite3
from datetime import datetime, timedelta
import random

class ChatDatabase:
    def __init__(self, db_name="chat_app.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _execute_query(self, query, params=(), fetch_one=False, fetch_all=False):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        if fetch_one:
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

        if fetch_all:
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

        last_id = cursor.lastrowid
        conn.close()
        return last_id
    
    def _create_tables(self):
        queries = [
            # جدول کاربران (همونی که داری)
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tag TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, tag)  -- ترکیب یوزرنیم+تگ باید یکتا باشه
            );
            """,
            # جدول پیام‌ها
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id)
            );
            """,
            # جدول درخواست‌ها و روابط دوستانه
            """
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id INTEGER NOT NULL,
                addressee_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected')),
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP,
                UNIQUE(requester_id, addressee_id),
                FOREIGN KEY(requester_id) REFERENCES users(id),
                FOREIGN KEY(addressee_id) REFERENCES users(id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS private_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            );
            """
        ]

        for query in queries:
            self._execute_query(query)

        # ارتقا/اضافه کردن ستون‌های جدید در جدول friends (مثال)
        conn = self._connect()
        cursor = conn.cursor()

        # چک کردن وجود ستون requested_at در friends (برای مثال)
        cursor.execute("PRAGMA table_info(friends)")
        columns = [row["name"] for row in cursor.fetchall()]

        # اگر ستون requested_at وجود نداشت، اضافه کن
        if "requested_at" not in columns:
            cursor.execute("ALTER TABLE friends ADD COLUMN requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        if "responded_at" not in columns:
            cursor.execute("ALTER TABLE friends ADD COLUMN responded_at TIMESTAMP")

        conn.commit()
        conn.close()

    # ----------------- User ------------------
    def _generate_tag(self, username):
        existing_tags = self._execute_query(
            "SELECT tag FROM users WHERE username = ?", (username,), fetch_all=True
        )
        existing_tag_nums = {int(u["tag"]) for u in existing_tags}
        for _ in range(10000):
            tag = random.randint(0, 9999)
            if tag not in existing_tag_nums:
                return f"{tag:04}"
        raise Exception("Too many users with the same username")

    def register_user(self, username, password, email=None):
        tag = self._generate_tag(username)
        query = "INSERT INTO users (username, tag, password, email) VALUES (?, ?, ?, ?)"
        try:
            return self._execute_query(query, (username, tag, password, email))
        except sqlite3.IntegrityError:
            return None  # Duplicate username#tag

    def get_user_by_username_tag(self, username_tag):
        if '#' not in username_tag:
            return None
        username, tag = username_tag.split('#')
        query = "SELECT * FROM users WHERE username = ? AND tag = ?"
        return self._execute_query(query, (username, tag), fetch_one=True)

    def get_user_by_id(self, user_id):
        return self._execute_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch_one=True)

    def authenticate_user(self, username, password):
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        return self._execute_query(query, (username, password), fetch_one=True)

    # ------------------ Friends ------------------
    def get_friend_requests(self, user_id):
        query = """
            SELECT f.id, u.username || '#' || u.tag as from_user, f.status
            FROM friends f
            JOIN users u ON f.requester_id = u.id
            WHERE f.addressee_id = ? AND f.status = 'pending'
        """
        return self._execute_query(query, (user_id,), fetch_all=True)

    def accept_friend_request(self, request_id):
        req = self._execute_query(
            "SELECT requester_id, addressee_id FROM friends WHERE id = ?", (request_id,), fetch_one=True
        )
        if not req:
            return False
        uid1, uid2 = sorted([req["requester_id"], req["addressee_id"]])
        self._execute_query(
            "UPDATE friends SET status = 'accepted' WHERE id = ?", (request_id,)
        )
        # این خط احتمالا لازم نیست چون دوطرفه با ستون status کنترل می‌شود
        # اگر نیاز داری رکورد خاصی اضافه کنی می‌توانی اضافه کنی، اما الان کافیست status را بروز کن
        return True


    def get_friends(self, user_id):
        query = """
            SELECT u.id, u.username || '#' || u.tag AS username_tag
            FROM friends f
            JOIN users u ON 
                ( (f.requester_id = ? AND f.addressee_id = u.id) OR (f.addressee_id = ? AND f.requester_id = u.id) )
            WHERE f.status = 'accepted'
        """
        return self._execute_query(query, (user_id, user_id), fetch_all=True)


    def are_friends(self, user_id_1, user_id_2):
        uid1, uid2 = sorted([user_id_1, user_id_2])
        query = "SELECT 1 FROM friends WHERE ((requester_id = ? AND addressee_id = ?) OR (requester_id = ? AND addressee_id = ?)) AND status = 'accepted'"
        result = self._execute_query(query, (user_id_1, user_id_2, user_id_2, user_id_1), fetch_one=True)
        return result is not None

    # ----------------- Messages ------------------
    def add_message(self, sender_id, content):
        return self._execute_query(
            "INSERT INTO messages (sender_id, message) VALUES (?, ?)",
            (sender_id, content)
        )

    def get_recent_messages(self, since_id=0, limit=100):
        query = """
            SELECT m.id, u.username || '#' || u.tag as sender, m.message, m.timestamp
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.id > ?
            ORDER BY m.id ASC
            LIMIT ?
        """
        return self._execute_query(query, (since_id, limit), fetch_all=True)
    
        # ارسال درخواست دوستی
    def send_friend_request(self, requester_id, addressee_id):
        if requester_id == addressee_id:
            return False, "You cannot add yourself as a friend."

        # بررسی اینکه قبلاً درخواست مشابهی ارسال نشده یا دوست نیستند
        existing = self._execute_query(
            "SELECT * FROM friends WHERE requester_id = ? AND addressee_id = ?",
            (requester_id, addressee_id), fetch_one=True)
        if existing:
            return False, "Friend request already sent or relationship exists."

        # همچنین باید بررسی کنیم ممکنه addressee به requester قبلاً درخواست داده باشه (دوطرفه)
        reverse = self._execute_query(
            "SELECT * FROM friends WHERE requester_id = ? AND addressee_id = ?",
            (addressee_id, requester_id), fetch_one=True)
        if reverse and reverse['status'] == 'accepted':
            return False, "You are already friends."

        # ذخیره درخواست
        self._execute_query(
            "INSERT INTO friends (requester_id, addressee_id, status) VALUES (?, ?, 'pending')",
            (requester_id, addressee_id)
        )
        return True, "Friend request sent."

    # پاسخ به درخواست دوستی (قبول یا رد)
    def respond_to_friend_request(self, requester_id, addressee_id, accept=True):
        request = self._execute_query(
            "SELECT * FROM friends WHERE requester_id = ? AND addressee_id = ? AND status = 'pending'",
            (requester_id, addressee_id), fetch_one=True)
        if not request:
            return False, "No pending friend request found."

        status = 'accepted' if accept else 'rejected'
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self._execute_query(
            "UPDATE friends SET status = ?, responded_at = ? WHERE id = ?",
            (status, now, request['id'])
        )
        return True, f"Friend request {'accepted' if accept else 'rejected'}."

    # گرفتن لیست دوستان یک کاربر
    def get_friends(self, user_id):
        # دوستانی که user_id درخواست داده و قبول شده
        friends1 = self._execute_query(
            """SELECT u.id, u.username, u.tag FROM friends f
            JOIN users u ON f.addressee_id = u.id
            WHERE f.requester_id = ? AND f.status = 'accepted'""",
            (user_id,), fetch_all=True)
        # دوستانی که به user_id درخواست داده و قبول شده
        friends2 = self._execute_query(
            """SELECT u.id, u.username, u.tag FROM friends f
            JOIN users u ON f.requester_id = u.id
            WHERE f.addressee_id = ? AND f.status = 'accepted'""",
            (user_id,), fetch_all=True)
        return friends1 + friends2

    def get_pending_friend_requests(self, user_identifier):
        # اگر identifier به صورت tag بود، اول آی‌دی عددی رو بگیر
        if isinstance(user_identifier, str) and "#" in user_identifier:
            username, tag = user_identifier.split("#")
            id_query = "SELECT id FROM users WHERE username = ? AND tag = ?"
            result = self._execute_query(id_query, (username, tag), fetch_one=True)
            if not result:
                return []  # یا raise Exception("User not found")
            user_id = result[0]
        else:
            user_id = user_identifier  # فرض بر اینه که عددی هست

        query = """
            SELECT f.id, u.username || '#' || u.tag AS from_user, f.requested_at
            FROM friends f
            JOIN users u ON f.requester_id = u.id
            WHERE f.addressee_id = ? AND f.status = 'pending'
        """
        print(self._execute_query(query, (user_id,), fetch_all=True))
        return self._execute_query(query, (user_id,), fetch_all=True)


    # حذف دوست (قطع رابطه دوطرفه)
    def remove_friend(self, user_id, friend_id):
        self._execute_query(
            """DELETE FROM friends
            WHERE (requester_id = ? AND addressee_id = ? AND status = 'accepted')
                OR (requester_id = ? AND addressee_id = ? AND status = 'accepted')""",
            (user_id, friend_id, friend_id, user_id)
        )
        return True
    
    def get_all_users(self):
        query = "SELECT id, username, tag, email, created_at, last_activity FROM users ORDER BY id"
        return self._execute_query(query, fetch_all=True)
    
    def get_statistics(self):
        total_users = self._execute_query("SELECT COUNT(*) as count FROM users", fetch_one=True)['count']
        total_messages = self._execute_query("SELECT COUNT(*) as count FROM messages", fetch_one=True)['count']
        
        # تعریف کاربران آنلاین: مثلاً 5 دقیقه آخر فعال بودن
        threshold = datetime.utcnow() - timedelta(minutes=5)
        online_users_count = self._execute_query(
            "SELECT COUNT(*) as count FROM users WHERE last_activity >= ?", 
            (threshold.strftime('%Y-%m-%d %H:%M:%S'),), fetch_one=True)['count']
        
        return {
            "total_users": total_users,
            "total_messages": total_messages,
            "online_users": online_users_count
        }
    
    def get_online_users(self, minutes=5):
        threshold = datetime.utcnow() - timedelta(minutes=minutes)
        query = """
            SELECT id, username, tag, last_activity 
            FROM users 
            WHERE last_activity >= ? 
            ORDER BY last_activity DESC
        """
        return self._execute_query(query, (threshold.strftime('%Y-%m-%d %H:%M:%S'),), fetch_all=True)

    def get_all_pending_friend_requests(self):
        query = """
            SELECT 
                u1.username || '#' || u1.tag AS requester, 
                u2.username || '#' || u2.tag AS addressee, 
                f.requested_at 
            FROM friends f
            JOIN users u1 ON f.requester_id = u1.id
            JOIN users u2 ON f.addressee_id = u2.id
            WHERE f.status = 'pending'
        """
        return self._execute_query(query, fetch_all=True)

    def get_all_friends(self):
        query = """
            SELECT f.id, u1.username || '#' || u1.tag as user1, u2.username || '#' || u2.tag as user2, f.status
            FROM friends f
            JOIN users u1 ON f.requester_id = u1.id
            JOIN users u2 ON f.addressee_id = u2.id
            WHERE f.status = 'accepted'
        """
        return self._execute_query(query, fetch_all=True)
    
    def update_activity(self, user_id):
        query = "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE id = ?"
        self._execute_query(query, (user_id,))

    def is_user_online(self, user_id: int, minutes=5):
        threshold = datetime.utcnow() - timedelta(minutes=minutes)
        query = "SELECT 1 FROM users WHERE id = ? AND last_activity >= ?"
        result = self._execute_query(query, (user_id, threshold.strftime('%Y-%m-%d %H:%M:%S')), fetch_one=True)
        return result is not None

    def get_online_friends(self, user_id: int, minutes=5):
        threshold = datetime.utcnow() - timedelta(minutes=minutes)
        query = """
            SELECT u.id, u.username, u.tag
            FROM friends f
            JOIN users u ON 
                ((f.requester_id = ? AND f.addressee_id = u.id) OR
                (f.addressee_id = ? AND f.requester_id = u.id))
            WHERE f.status = 'accepted' AND u.last_activity >= ?
        """
        return self._execute_query(query, (user_id, user_id, threshold.strftime('%Y-%m-%d %H:%M:%S')), fetch_all=True)

    def get_username_tag_by_id(self, user_id):
        query = "SELECT username, tag FROM users WHERE id = ?"
        result = self._execute_query(query, (user_id,), fetch_one=True)
        if result:
            return f"{result['username']}#{result['tag']}"
        return None

    def send_private_message(self, sender_id, receiver_id, message):
        if not self.are_friends(sender_id, receiver_id):
            return False, "You can only message your friends."
        query = "INSERT INTO private_messages (sender_id, receiver_id, message) VALUES (?, ?, ?)"
        self._execute_query(query, (sender_id, receiver_id, message))
        return True, "Message sent."
    
    def get_private_messages(self, user1_id, user2_id, limit=100):
        query = """
            SELECT 
                pm.id,
                u.username || '#' || u.tag AS sender,
                pm.message,
                pm.timestamp
            FROM private_messages pm
            JOIN users u ON pm.sender_id = u.id
            WHERE 
                (pm.sender_id = ? AND pm.receiver_id = ?)
                OR
                (pm.sender_id = ? AND pm.receiver_id = ?)
            ORDER BY pm.timestamp ASC
            LIMIT ?
        """
        return self._execute_query(query, (user1_id, user2_id, user2_id, user1_id, limit), fetch_all=True)

    def get_last_messages_with_friends(self, user_id):
        query = """
            SELECT 
                u.id as friend_id,
                u.username || '#' || u.tag as friend,
                pm.message,
                pm.timestamp
            FROM (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY 
                            CASE 
                                WHEN sender_id = ? THEN receiver_id 
                                ELSE sender_id 
                            END 
                        ORDER BY timestamp DESC
                    ) as rn
                FROM private_messages
                WHERE sender_id = ? OR receiver_id = ?
            ) pm
            JOIN users u ON u.id = 
                CASE 
                    WHEN pm.sender_id = ? THEN pm.receiver_id
                    ELSE pm.sender_id
                END
            WHERE rn = 1
            ORDER BY timestamp DESC
        """
        return self._execute_query(query, (user_id, user_id, user_id, user_id), fetch_all=True)

