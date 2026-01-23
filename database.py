import aiosqlite
import json
import os

DB_NAME = "database.db"

class Database:
    def __init__(self):
        self.conn = None

    async def connect(self):
        """Создает подключение к БД и таблицы, если их нет."""
        self.conn = await aiosqlite.connect(DB_NAME)
        # Позволяет обращаться к полям по имени (row['xp']), а не по индексу (row[1])
        self.conn.row_factory = aiosqlite.Row 
        await self.create_tables()
        print("✅ [Database] Подключение к базе данных успешно!")

    async def create_tables(self):
        # Юзеры
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                coins INTEGER DEFAULT 0,
                invites INTEGER DEFAULT 0
            )
        """)
        # Инвентарь
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_id TEXT,
                count INTEGER,
                PRIMARY KEY (user_id, item_id)
            )
        """)
        # Варны
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id INTEGER,
                reason TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Ивенты
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS active_events (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                reward INTEGER,
                required_users INTEGER,
                users_list TEXT
            )
        """)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    # --- ЮЗЕРЫ ---
    async def get_user(self, user_id):
        async with self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user:
                await self.conn.execute("INSERT INTO users (user_id, invites) VALUES (?, 0)", (user_id,))
                await self.conn.commit()
                return {"xp": 0, "level": 1, "coins": 0, "invites": 0}
            return dict(user) # Превращаем объект Row в обычный словарь

    async def update_user(self, user_id, xp=None, level=None, coins=None):
        if xp is not None:
            await self.conn.execute("UPDATE users SET xp = ? WHERE user_id = ?", (xp, user_id))
        if level is not None:
            await self.conn.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
        if coins is not None:
            await self.conn.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
        await self.conn.commit()

    async def add_coins(self, user_id, amount):
        user = await self.get_user(user_id)
        await self.update_user(user_id, coins=user['coins'] + amount)
    
    async def add_xp(self, user_id, amount):
        user = await self.get_user(user_id)
        await self.update_user(user_id, xp=user['xp'] + amount)

    # 🔥 ТОП ИГРОКОВ
    async def get_top_users(self, limit=10):
        async with self.conn.execute("SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()

    # --- ИНВЕНТАРЬ ---
    async def add_item(self, user_id, item_id, amount=1):
        async with self.conn.execute("SELECT count FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id)) as cursor:
            result = await cursor.fetchone()
            if result:
                await self.conn.execute("UPDATE inventory SET count = ? WHERE user_id = ? AND item_id = ?", (result['count'] + amount, user_id, item_id))
            else:
                await self.conn.execute("INSERT INTO inventory (user_id, item_id, count) VALUES (?, ?, ?)", (user_id, item_id, amount))
            await self.conn.commit()

    async def remove_item(self, user_id, item_id, amount=1):
        async with self.conn.execute("SELECT count FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id)) as cursor:
            result = await cursor.fetchone()
            if not result or result['count'] < amount:
                return False
            
            new_count = result['count'] - amount
            if new_count > 0:
                await self.conn.execute("UPDATE inventory SET count = ? WHERE user_id = ? AND item_id = ?", (new_count, user_id, item_id))
            else:
                await self.conn.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            await self.conn.commit()
            return True

    async def get_inventory(self, user_id):
        async with self.conn.execute("SELECT item_id, count FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()

    # --- ДРУГОЕ ---
    async def add_referral(self, inviter_id, new_user_id):
        user = await self.get_user(inviter_id)
        await self.conn.execute("UPDATE users SET invites = ? WHERE user_id = ?", (user['invites'] + 1, inviter_id))
        await self.conn.commit()
        return True

    async def add_warn(self, user_id, admin_id, reason):
        await self.conn.execute("INSERT INTO warns (user_id, admin_id, reason) VALUES (?, ?, ?)", (user_id, admin_id, reason))
        await self.conn.commit()

    async def get_warns(self, user_id):
        async with self.conn.execute("SELECT admin_id, reason, date FROM warns WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()

    async def remove_warns(self, user_id):
        await self.conn.execute("DELETE FROM warns WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    # --- ИВЕНТЫ ---
    async def create_event(self, message_id, channel_id, reward, required):
        await self.conn.execute("INSERT INTO active_events VALUES (?, ?, ?, ?, ?)", (message_id, channel_id, reward, required, "[]"))
        await self.conn.commit()

    async def get_event(self, message_id):
        async with self.conn.execute("SELECT * FROM active_events WHERE message_id = ?", (message_id,)) as cursor:
            return await cursor.fetchone()

    async def update_event_users(self, message_id, users_list):
        users_json = json.dumps(users_list)
        await self.conn.execute("UPDATE active_events SET users_list = ? WHERE message_id = ?", (users_json, message_id))
        await self.conn.commit()

    async def delete_event(self, message_id):
        await self.conn.execute("DELETE FROM active_events WHERE message_id = ?", (message_id,))
        await self.conn.commit()

# Создаем глобальный объект, но НЕ подключаемся сразу
db = Database()