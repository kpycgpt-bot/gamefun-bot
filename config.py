import os
from dotenv import load_dotenv
from typing import Optional

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    """Класс для управления конфигурацией бота"""
    
    # Токен бота
    TOKEN: Optional[str] = os.getenv("DISCORD_TOKEN")
    
    # Префикс команд
    PREFIX: str = os.getenv("BOT_PREFIX", "!")
    
    # ID владельца бота (для особых прав)
    OWNER_ID: Optional[int] = None
    try:
        owner_id_str = os.getenv("OWNER_ID")
        if owner_id_str:
            OWNER_ID = int(owner_id_str)
    except ValueError:
        print("⚠️ [Config] OWNER_ID должен быть числом")
    
    # Настройки экономики
    XP_PER_MESSAGE: int = 5
    XP_COOLDOWN: int = 60  # Секунд между начислением XP
    COINS_PER_MESSAGE: int = 1
    
    # Настройки уровней (формула: XP = базовое * уровень)
    XP_BASE: int = 100
    
    # Цвета для embed сообщений
    COLOR_SUCCESS: int = 0x2ECC71  # Зеленый
    COLOR_ERROR: int = 0xE74C3C    # Красный
    COLOR_INFO: int = 0x3498DB     # Синий
    COLOR_WARNING: int = 0xF39C12  # Оранжевый
    
    # Эмодзи для бота
    EMOJI_SUCCESS: str = "✅"
    EMOJI_ERROR: str = "❌"
    EMOJI_WARNING: str = "⚠️"
    EMOJI_INFO: str = "ℹ️"
    EMOJI_COIN: str = "🪙"
    EMOJI_XP: str = "⭐"
    
    # Настройки магазина (ID предметов и цены)
    SHOP_ITEMS = {
        "role_color": {
            "name": "🎨 Цветная роль",
            "description": "Уникальная цветная роль на 30 дней",
            "price": 1000,
            "emoji": "🎨"
        },
        "xp_boost": {
            "name": "⚡ XP Буст",
            "description": "Удваивает получение опыта на 7 дней",
            "price": 500,
            "emoji": "⚡"
        },
        "coins_boost": {
            "name": "💰 Монетный буст",
            "description": "Удваивает получение монет на 7 дней",
            "price": 500,
            "emoji": "💰"
        },
        "custom_voice": {
            "name": "🔊 VIP Войс",
            "description": "Персональный голосовой канал с кастомизацией",
            "price": 2000,
            "emoji": "🔊"
        }
    }
    
    # Лимиты и ограничения
    MAX_WARNS: int = 3  # Максимум варнов до бана
    TICKET_CATEGORY_NAME: str = "📋 ТИКЕТЫ"
    VOICE_CATEGORY_NAME: str = "🔊 ГОЛОСОВЫЕ"
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Проверяет, что все необходимые настройки заданы"""
        if not cls.TOKEN:
            print("❌ [Config] DISCORD_TOKEN не найден в переменных окружения!")
            print("💡 Создайте файл .env и добавьте: DISCORD_TOKEN=ваш_токен")
            return False
        
        if len(cls.TOKEN) < 50:
            print("❌ [Config] DISCORD_TOKEN слишком короткий. Проверьте правильность токена.")
            return False
        
        print("✅ [Config] Конфигурация валидна")
        return True
    
    @classmethod
    def get_xp_for_level(cls, level: int) -> int:
        """Вычисляет необходимый XP для достижения уровня"""
        return cls.XP_BASE * level
    
    @classmethod
    def get_level_from_xp(cls, xp: int) -> int:
        """Вычисляет уровень по количеству XP"""
        level = 1
        total_xp = 0
        while total_xp <= xp:
            total_xp += cls.get_xp_for_level(level)
            if total_xp > xp:
                break
            level += 1
        return level

# Проверяем конфигурацию при импорте
if __name__ != "__main__":
    Config.validate()
