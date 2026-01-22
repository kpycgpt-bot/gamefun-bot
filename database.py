import sqlite3
import json
import os

DB_NAME = "database.db"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Таблица пользователей
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                coins INTEGER DEFAULT 0,
                invites INTEGER DEFAULT 0
            )
        """)
        # Таблица инвентаря
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_id TEXT,
                count INTEGER,
                PRIMARY KEY (user_id, item_id)
            )
        """)
        # Таблица варнов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id INTEGER,
                reason TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # --- 🔥 ТАБЛИЦА ИВЕНТОВ (СУНДУКИ) ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_events (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                reward INTEGER,
                required_users INTEGER,
                users_list TEXT
            )
        """)
        self.conn.commit()

    # --- ЮЗЕРЫ ---
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = self.cursor.fetchone()
        if not user:
            self.cursor.execute("INSERT INTO users (user_id, invites) VALUES (?, 0)", (user_id,))
            self.conn.commit()
            return {"xp": 0, "level": 1, "coins": 0, "invites": 0}
        return {"xp": user[1], "level": user[2], "coins": user[3], "invites": user[4]}

    def update_user(self, user_id, xp=None, level=None, coins=None):
        if xp is not None: self.cursor.execute("UPDATE users SET xp = ? WHERE user_id = ?", (xp, user_id))
        if level is not None: self.cursor.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
        if coins is not None: self.cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
        self.conn.commit()

    def add_coins(self, user_id, amount):
        user = self.get_user(user_id)
        self.update_user(user_id, coins=user['coins'] + amount)

    # --- ИНВЕНТАРЬ ---
    def add_item(self, user_id, item_id, amount=1):
        self.cursor.execute("SELECT count FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute("UPDATE inventory SET count = ? WHERE user_id = ? AND item_id = ?", (result[0] + amount, user_id, item_id))
        else:
            self.cursor.execute("INSERT INTO inventory (user_id, item_id, count) VALUES (?, ?, ?)", (user_id, item_id, amount))
        self.conn.commit()

    def remove_item(self, user_id, item_id, amount=1):
        self.cursor.execute("SELECT count FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        result = self.cursor.fetchone()
        if not result or result[0] < amount: return False
        new_count = result[0] - amount
        if new_count > 0:
            self.cursor.execute("UPDATE inventory SET count = ? WHERE user_id = ? AND item_id = ?", (new_count, user_id, item_id))
        else:
            self.cursor.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        self.conn.commit()
        return True
    
    def get_inventory(self, user_id):
        self.cursor.execute("SELECT item_id, count FROM inventory WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()

    # --- РЕФЕРАЛЫ ---
    def add_referral(self, inviter_id, new_user_id):
        user = self.get_user(inviter_id)
        self.cursor.execute("UPDATE users SET invites = ? WHERE user_id = ?", (user['invites'] + 1, inviter_id))
        self.conn.commit()
        return True

    # --- ВАРНЫ ---
    def add_warn(self, user_id, admin_id, reason):
        self.cursor.execute("INSERT INTO warns (user_id, admin_id, reason) VALUES (?, ?, ?)", (user_id, admin_id, reason))
        self.conn.commit()
    def get_warns(self, user_id):
        self.cursor.execute("SELECT admin_id, reason, date FROM warns WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()
    def remove_warns(self, user_id):
        self.cursor.execute("DELETE FROM warns WHERE user_id = ?", (user_id,))
        self.conn.commit()

    # --- 🔥 МЕТОДЫ ИВЕНТОВ (БЕЗ НИХ ВСЁ СЛОМАЕТСЯ) ---
    def create_event(self, message_id, channel_id, reward, required):
        self.cursor.execute("INSERT INTO active_events VALUES (?, ?, ?, ?, ?)", 
                            (message_id, channel_id, reward, required, "[]"))
        self.conn.commit()

    def get_event(self, message_id):
        self.cursor.execute("SELECT * FROM active_events WHERE message_id = ?", (message_id,))
        return self.cursor.fetchone()

    def update_event_users(self, message_id, users_list):
        users_json = json.dumps(users_list)
        self.cursor.execute("UPDATE active_events SET users_list = ? WHERE message_id = ?", (users_json, message_id))
        self.conn.commit()

    def delete_event(self, message_id):
        self.cursor.execute("DELETE FROM active_events WHERE message_id = ?", (message_id,))
        self.conn.commit()

db = Database()