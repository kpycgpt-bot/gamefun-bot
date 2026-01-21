import sqlite3
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
                coins INTEGER DEFAULT 0
            )
        """)
        
        # --- ТАБЛИЦА ВАРНОВ (Новая) ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id INTEGER,
                reason TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = self.cursor.fetchone()
        if not user:
            self.cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
            return {"xp": 0, "level": 1, "coins": 0}
        return {"xp": user[1], "level": user[2], "coins": user[3]}

    def update_user(self, user_id, xp=None, level=None, coins=None):
        if xp is not None:
            self.cursor.execute("UPDATE users SET xp = ? WHERE user_id = ?", (xp, user_id))
        if level is not None:
            self.cursor.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
        if coins is not None:
            self.cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
        self.conn.commit()

    def add_coins(self, user_id, amount):
        user = self.get_user(user_id)
        new_balance = user['coins'] + amount
        self.update_user(user_id, coins=new_balance)

    # --- ФУНКЦИИ ВАРНОВ ---
    def add_warn(self, user_id, admin_id, reason):
        self.cursor.execute("INSERT INTO warns (user_id, admin_id, reason) VALUES (?, ?, ?)", 
                            (user_id, admin_id, reason))
        self.conn.commit()

    def get_warns(self, user_id):
        self.cursor.execute("SELECT admin_id, reason, date FROM warns WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()

    def remove_warns(self, user_id):
        self.cursor.execute("DELETE FROM warns WHERE user_id = ?", (user_id,))
        self.conn.commit()

db = Database()