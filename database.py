import aiosqlite
import json
import os
from typing import Optional, Dict, Any, List

DB_NAME = "database.db"

class Database:
    def __init__(self):
        self.conn = None
        # Кэш для настроек, чтобы не дергать БД каждую миллисекунду
        self.settings_cache = {}

    async def connect(self):
        """Создает подключение к БД и таблицы."""
        try:
            self.conn = await aiosqlite.connect(DB_NAME)
            self.conn.row_factory = aiosqlite.Row
            await self.create_tables()
            await self.load_settings_cache()
            print("✅ [Database] Подключение успешно! Таблицы проверены.")
        except Exception as e:
            print(f"❌ [Database] Ошибка подключения: {e}")
            raise

    async def create_tables(self):
        """Создает все необходимые таблицы"""
        try:
            # --- ПОЛЬЗОВАТЕЛИ И ЭКОНОМИКА ---
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    coins INTEGER DEFAULT 0,
                    invites INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # --- ИНВЕНТАРЬ ---
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_id TEXT,
                    count INTEGER DEFAULT 1,
                    PRIMARY KEY (user_id, item_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # --- ПРЕДУПРЕЖДЕНИЯ ---
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS warns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    admin_id INTEGER NOT NULL,
                    reason TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # --- АКТИВНЫЕ СОБЫТИЯ ---
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS active_events (
                    message_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    reward INTEGER DEFAULT 0,
                    required_users INTEGER DEFAULT 1,
                    users_list TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # --- НАСТРОЙКИ СЕРВЕРА (Key-Value хранилище) ---
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS server_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # --- ПРИВАТНЫЕ ГОЛОСОВЫЕ КАНАЛЫ ---
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_channels (
                    channel_id INTEGER PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создаем индексы для ускорения запросов
            await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_users_level ON users(level DESC, xp DESC)")
            await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_warns_user ON warns(user_id)")
            await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_voice_owner ON voice_channels(owner_id)")
            
            await self.conn.commit()
            print("✅ [Database] Все таблицы созданы и проверены.")
        except Exception as e:
            print(f"❌ [Database] Ошибка создания таблиц: {e}")
            raise

    async def close(self):
        """Закрывает соединение с БД"""
        if self.conn:
            await self.conn.close()
            print("✅ [Database] Соединение закрыто.")

    # ==========================================
    # ⚙️ МЕНЕДЖЕР КОНФИГУРАЦИИ (Config System)
    # ==========================================
    
    async def load_settings_cache(self):
        """Выгружает настройки в RAM для быстрого доступа."""
        try:
            async with self.conn.execute("SELECT key, value FROM server_settings") as cursor:
                rows = await cursor.fetchall()
                self.settings_cache = {row['key']: row['value'] for row in rows}
            print(f"✅ [Database] Загружено {len(self.settings_cache)} настроек в кэш.")
        except Exception as e:
            print(f"❌ [Database] Ошибка загрузки кэша: {e}")
            self.settings_cache = {}

    async def set_config(self, key: str, value):
        """Сохраняет настройку (ID канала/роли)."""
        try:
            str_value = str(value)
            await self.conn.execute(
                """INSERT INTO server_settings (key, value) VALUES (?, ?) 
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP""",
                (key, str_value)
            )
            await self.conn.commit()
            self.settings_cache[key] = str_value
            print(f"✅ [Config] Сохранено: {key} = {str_value}")
        except Exception as e:
            print(f"❌ [Config] Ошибка сохранения {key}: {e}")

    def get_config(self, key: str, default=None, cast_type=int):
        """
        Получает значение из кэша мгновенно.
        Используй cast_type=int для ID каналов.
        """
        val = self.settings_cache.get(key)
        if val is None: 
            return default
        try:
            return cast_type(val)
        except (ValueError, TypeError):
            print(f"⚠️ [Config] Ошибка преобразования {key}: {val}")
            return default

    async def delete_config(self, key: str):
        """Удаляет настройку"""
        try:
            await self.conn.execute("DELETE FROM server_settings WHERE key = ?", (key,))
            await self.conn.commit()
            if key in self.settings_cache:
                del self.settings_cache[key]
            print(f"✅ [Config] Удалено: {key}")
        except Exception as e:
            print(f"❌ [Config] Ошибка удаления {key}: {e}")

    # ==========================================
    # 🔊 УПРАВЛЕНИЕ ВОЙСАМИ (Voice System)
    # ==========================================
    
    async def add_voice_channel(self, channel_id: int, owner_id: int):
        """Добавляет голосовой канал в БД"""
        try:
            await self.conn.execute(
                "INSERT OR IGNORE INTO voice_channels (channel_id, owner_id) VALUES (?, ?)", 
                (channel_id, owner_id)
            )
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Voice] Ошибка добавления канала {channel_id}: {e}")

    async def get_voice_owner(self, channel_id: int) -> Optional[int]:
        """Получает ID владельца голосового канала"""
        try:
            async with self.conn.execute(
                "SELECT owner_id FROM voice_channels WHERE channel_id = ?", 
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row['owner_id'] if row else None
        except Exception as e:
            print(f"❌ [Voice] Ошибка получения владельца {channel_id}: {e}")
            return None

    async def remove_voice_channel(self, channel_id: int):
        """Удаляет голосовой канал из БД"""
        try:
            await self.conn.execute("DELETE FROM voice_channels WHERE channel_id = ?", (channel_id,))
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Voice] Ошибка удаления канала {channel_id}: {e}")

    async def get_user_voice_channels(self, owner_id: int) -> List[int]:
        """Получает все голосовые каналы пользователя"""
        try:
            async with self.conn.execute(
                "SELECT channel_id FROM voice_channels WHERE owner_id = ?", 
                (owner_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row['channel_id'] for row in rows]
        except Exception as e:
            print(f"❌ [Voice] Ошибка получения каналов пользователя {owner_id}: {e}")
            return []

    # ==========================================
    # 👤 ЮЗЕРЫ И ЭКОНОМИКА
    # ==========================================
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """Получает данные пользователя или создает новую запись"""
        try:
            async with self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?", 
                (user_id,)
            ) as cursor:
                user = await cursor.fetchone()
                if not user:
                    await self.conn.execute(
                        "INSERT INTO users (user_id) VALUES (?)", 
                        (user_id,)
                    )
                    await self.conn.commit()
                    return {"user_id": user_id, "xp": 0, "level": 1, "coins": 0, "invites": 0}
                return dict(user)
        except Exception as e:
            print(f"❌ [Users] Ошибка получения пользователя {user_id}: {e}")
            return {"user_id": user_id, "xp": 0, "level": 1, "coins": 0, "invites": 0}

    async def update_user(self, user_id: int, xp: int = None, level: int = None, coins: int = None):
        """Обновляет данные пользователя"""
        try:
            updates = []
            values = []
            
            if xp is not None:
                updates.append("xp = ?")
                values.append(xp)
            if level is not None:
                updates.append("level = ?")
                values.append(level)
            if coins is not None:
                updates.append("coins = ?")
                values.append(coins)
            
            if not updates:
                return
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            
            await self.conn.execute(query, values)
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Users] Ошибка обновления пользователя {user_id}: {e}")

    async def add_coins(self, user_id: int, amount: int):
        """Добавляет монеты пользователю"""
        try:
            user = await self.get_user(user_id)
            new_coins = max(0, user['coins'] + amount)  # Не даем уйти в минус
            await self.update_user(user_id, coins=new_coins)
        except Exception as e:
            print(f"❌ [Economy] Ошибка добавления монет пользователю {user_id}: {e}")
    
    async def add_xp(self, user_id: int, amount: int):
        """Добавляет опыт пользователю"""
        try:
            user = await self.get_user(user_id)
            new_xp = max(0, user['xp'] + amount)
            await self.update_user(user_id, xp=new_xp)
        except Exception as e:
            print(f"❌ [XP] Ошибка добавления опыта пользователю {user_id}: {e}")

    async def add_invites(self, user_id: int, amount: int = 1):
        """Добавляет приглашения пользователю"""
        try:
            user = await self.get_user(user_id)
            new_invites = max(0, user['invites'] + amount)
            await self.conn.execute(
                "UPDATE users SET invites = ? WHERE user_id = ?", 
                (new_invites, user_id)
            )
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Invites] Ошибка добавления приглашений пользователю {user_id}: {e}")

    async def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Получает топ пользователей по уровню"""
        try:
            async with self.conn.execute(
                "SELECT user_id, level, xp, coins FROM users ORDER BY level DESC, xp DESC LIMIT ?", 
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ [Users] Ошибка получения топа: {e}")
            return []

    # ==========================================
    # 🎒 ИНВЕНТАРЬ
    # ==========================================
    
    async def add_item(self, user_id: int, item_id: str, amount: int = 1):
        """Добавляет предмет в инвентарь"""
        try:
            async with self.conn.execute(
                "SELECT count FROM inventory WHERE user_id = ? AND item_id = ?", 
                (user_id, item_id)
            ) as cursor:
                result = await cursor.fetchone()
                
                if result:
                    new_count = result['count'] + amount
                    await self.conn.execute(
                        "UPDATE inventory SET count = ? WHERE user_id = ? AND item_id = ?",
                        (new_count, user_id, item_id)
                    )
                else:
                    await self.conn.execute(
                        "INSERT INTO inventory (user_id, item_id, count) VALUES (?, ?, ?)",
                        (user_id, item_id, amount)
                    )
                await self.conn.commit()
        except Exception as e:
            print(f"❌ [Inventory] Ошибка добавления предмета {item_id} пользователю {user_id}: {e}")

    async def remove_item(self, user_id: int, item_id: str, amount: int = 1) -> bool:
        """Удаляет предмет из инвентаря. Возвращает True если успешно"""
        try:
            async with self.conn.execute(
                "SELECT count FROM inventory WHERE user_id = ? AND item_id = ?",
                (user_id, item_id)
            ) as cursor:
                result = await cursor.fetchone()
                
                if not result or result['count'] < amount:
                    return False
                
                new_count = result['count'] - amount
                
                if new_count <= 0:
                    await self.conn.execute(
                        "DELETE FROM inventory WHERE user_id = ? AND item_id = ?",
                        (user_id, item_id)
                    )
                else:
                    await self.conn.execute(
                        "UPDATE inventory SET count = ? WHERE user_id = ? AND item_id = ?",
                        (new_count, user_id, item_id)
                    )
                
                await self.conn.commit()
                return True
        except Exception as e:
            print(f"❌ [Inventory] Ошибка удаления предмета {item_id} у пользователя {user_id}: {e}")
            return False

    async def get_inventory(self, user_id: int) -> List[Dict]:
        """Получает весь инвентарь пользователя"""
        try:
            async with self.conn.execute(
                "SELECT item_id, count FROM inventory WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ [Inventory] Ошибка получения инвентаря пользователя {user_id}: {e}")
            return []

    async def get_item_count(self, user_id: int, item_id: str) -> int:
        """Получает количество определенного предмета"""
        try:
            async with self.conn.execute(
                "SELECT count FROM inventory WHERE user_id = ? AND item_id = ?",
                (user_id, item_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            print(f"❌ [Inventory] Ошибка получения количества предмета {item_id}: {e}")
            return 0

    # ==========================================
    # ⚠️ СИСТЕМА ПРЕДУПРЕЖДЕНИЙ
    # ==========================================
    
    async def add_warn(self, user_id: int, admin_id: int, reason: str = "Не указана"):
        """Добавляет предупреждение пользователю"""
        try:
            await self.conn.execute(
                "INSERT INTO warns (user_id, admin_id, reason) VALUES (?, ?, ?)",
                (user_id, admin_id, reason)
            )
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Warns] Ошибка добавления варна пользователю {user_id}: {e}")

    async def get_warns(self, user_id: int) -> List[Dict]:
        """Получает все предупреждения пользователя"""
        try:
            async with self.conn.execute(
                "SELECT * FROM warns WHERE user_id = ? ORDER BY date DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ [Warns] Ошибка получения варнов пользователя {user_id}: {e}")
            return []

    async def remove_warn(self, warn_id: int) -> bool:
        """Удаляет конкретное предупреждение по ID"""
        try:
            cursor = await self.conn.execute(
                "DELETE FROM warns WHERE id = ?",
                (warn_id,)
            )
            await self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ [Warns] Ошибка удаления варна {warn_id}: {e}")
            return False

    async def clear_warns(self, user_id: int):
        """Очищает все предупреждения пользователя"""
        try:
            await self.conn.execute("DELETE FROM warns WHERE user_id = ?", (user_id,))
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Warns] Ошибка очистки варнов пользователя {user_id}: {e}")

    # ==========================================
    # 🎉 СИСТЕМА СОБЫТИЙ
    # ==========================================
    
    async def add_event(self, message_id: int, channel_id: int, reward: int, required_users: int):
        """Создает новое событие"""
        try:
            await self.conn.execute(
                "INSERT INTO active_events (message_id, channel_id, reward, required_users, users_list) VALUES (?, ?, ?, ?, ?)",
                (message_id, channel_id, reward, required_users, '[]')
            )
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Events] Ошибка создания события {message_id}: {e}")

    async def get_event(self, message_id: int) -> Optional[Dict]:
        """Получает данные события"""
        try:
            async with self.conn.execute(
                "SELECT * FROM active_events WHERE message_id = ?",
                (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    data = dict(row)
                    data['users_list'] = json.loads(data['users_list'])
                    return data
                return None
        except Exception as e:
            print(f"❌ [Events] Ошибка получения события {message_id}: {e}")
            return None

    async def add_event_participant(self, message_id: int, user_id: int) -> bool:
        """Добавляет участника в событие. Возвращает True если успешно"""
        try:
            event = await self.get_event(message_id)
            if not event:
                return False
            
            users = event['users_list']
            if user_id in users:
                return False
            
            users.append(user_id)
            await self.conn.execute(
                "UPDATE active_events SET users_list = ? WHERE message_id = ?",
                (json.dumps(users), message_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ [Events] Ошибка добавления участника в событие {message_id}: {e}")
            return False

    async def remove_event(self, message_id: int):
        """Удаляет событие"""
        try:
            await self.conn.execute("DELETE FROM active_events WHERE message_id = ?", (message_id,))
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Events] Ошибка удаления события {message_id}: {e}")

    async def cleanup_old_events(self, days: int = 7):
        """Удаляет старые события"""
        try:
            await self.conn.execute(
                "DELETE FROM active_events WHERE created_at < datetime('now', ?)",
                (f'-{days} days',)
            )
            await self.conn.commit()
        except Exception as e:
            print(f"❌ [Events] Ошибка очистки старых событий: {e}")

# Создаем глобальный экземпляр для импорта в других модулях
db = Database()
