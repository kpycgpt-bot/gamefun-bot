import discord
from discord.ext import commands, tasks
import shutil
import os
import datetime

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_loop.start()

    def cog_unload(self):
        self.backup_loop.cancel()

    @tasks.loop(hours=6) # Делаем копию каждые 6 часов
    async def backup_loop(self):
        await self.bot.wait_until_ready()
        
        # Создаем папку, если нет
        if not os.path.exists("./backups"):
            os.makedirs("./backups")

        # Имя файла с датой: database_2026-01-22_15-30.db
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        src = "database.db"
        dst = f"./backups/database_{timestamp}.db"

        try:
            shutil.copy(src, dst)
            print(f"[Backup] ✅ База сохранена: {dst}")
            
            # Очистка старых (оставляем последние 10)
            files = sorted(os.listdir("./backups"))
            if len(files) > 10:
                os.remove(f"./backups/{files[0]}") # Удаляем самый старый
                print("[Backup] 🗑️ Старый бэкап удален.")
                
        except Exception as e:
            print(f"[Backup] ❌ Ошибка: {e}")

    @commands.command(name="forcebackup")
    @commands.has_permissions(administrator=True)
    async def force_backup(self, ctx):
        """Создать бэкап прямо сейчас."""
        await self.backup_loop()
        await ctx.send("✅ Бэкап создан принудительно!")

async def setup(bot):
    await bot.add_cog(Backup(bot))