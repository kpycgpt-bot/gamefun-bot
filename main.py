import discord
from discord.ext import commands
import asyncio
import os
import config

# Настройка интентов (прав доступа бота)
intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=None # Полностью отключаем стандартный help
)

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} успешно запущен!")
    print(f"📡 Префикс: {config.PREFIX}")
    await bot.change_presence(activity=discord.Game("GameFun Realms"))

async def load_extensions():
    """Автоматическая загрузка всех модулей из папки cogs."""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"[+] Загружен модуль: {filename}")
            except Exception as e:
                print(f"[!] Ошибка загрузки {filename}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(config.TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен.")