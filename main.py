import discord
from discord.ext import commands
import config
import os
import asyncio
from database import db  # Импортируем нашу новую БД

# Настройка намерений (Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class GameFunBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Эта функция запускается ДО того, как бот выйдет в онлайн"""
        print("🔄 --- ЗАГРУЗКА СИСТЕМ ---")
        
        # 1. Подключаемся к базе данных
        await db.connect()
        
        # 2. Сканируем папку cogs
        print("🔄 --- ЗАГРУЗКА МОДУЛЕЙ ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Модуль загружен: {filename}")
                except Exception as e:
                    print(f"❌ ОШИБКА в модуле {filename}: {e}")
        print("---------------------------")

    async def close(self):
        """При выключении бота закрываем соединение с БД"""
        await db.close()
        await super().close()

    async def on_ready(self):
        print(f'🚀 Бот {self.user} запущен и готов к работе!')
        print(f'ID: {self.user.id}')
        await self.change_presence(activity=discord.Game(name="!help | GameFun"))

bot = GameFunBot()

if __name__ == "__main__":
    # [cite_start]Загружаем токен из config (который теперь берет его из .env) [cite: 1]
    bot.run(config.TOKEN)