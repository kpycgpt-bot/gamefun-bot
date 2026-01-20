import json
import os

class Database:
    def __init__(self, db_file="players.json"):
        self.db_file = db_file
        self.players = self.load()

    def load(self):
        if not os.path.exists(self.db_file):
            return {}
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}

    def save(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.players, f, indent=4, ensure_ascii=False)

    def get_user(self, uid: int):
        uid = str(uid)
        # Если "all_members" случайно попал в ключи юзеров, игнорируем его при поиске конкретного юзера
        if uid not in self.players:
            self.players[uid] = {
                "xp": 0,
                "level": 1,
                "coins": 0,
                "invites": 0,
                "invited_list": []
            }
            self.save()
        return self.players[uid]

    def add_referral(self, inviter_id: int, joined_id: int):
        """Добавляет приглашение, если человек зашел впервые."""
        inviter = self.get_user(inviter_id)
        joined_id_str = str(joined_id)

        # Системный ключ для хранения всех, кто когда-либо заходил
        if "all_members" not in self.players:
            self.players["all_members"] = []

        if joined_id_str not in self.players["all_members"]:
            inviter["invites"] += 1
            inviter["invited_list"].append(joined_id_str)
            self.players["all_members"].append(joined_id_str)
            self.save()
            return True 
        return False

    # --- НОВЫЕ ФУНКЦИИ (ИСПРАВЛЕНИЕ ОШИБКИ) ---
    def add_xp(self, uid: int, amount: int):
        """Добавляет опыт и обрабатывает повышение уровня."""
        user = self.get_user(uid)
        user["xp"] += amount
        
        # Формула: каждые 500 XP = новый уровень
        new_level = 1 + (user["xp"] // 500)
        
        leveled_up = False
        if new_level > user["level"]:
            user["level"] = new_level
            leveled_up = True
            
        self.save()
        # Возвращаем данные + флаг, повысился ли уровень
        return {**user, "leveled_up": leveled_up}

    def add_coins(self, uid: int, amount: int):
        """Начисляет монеты."""
        user = self.get_user(uid)
        user["coins"] += amount
        self.save()
        return user

# Создаем единственный экземпляр БД
db = Database()