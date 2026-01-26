import discord
from discord.ext import commands, tasks
import shutil
import os
from datetime import datetime
from utils import EmbedBuilder
from config import Config
import logging

logger = logging.getLogger('DiscordBot.Backup')

class Backup(commands.Cog):
    """Система бэкапов базы данных"""
    
    def __init__(self, bot):
        self.bot = bot
        self.backup_dir = "backups"
        
        # Создаем папку для бэкапов
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # Запускаем автоматические бэкапы
        self.auto_backup.start()
        logger.info("✅ Backup инициализирован")
    
    def cog_unload(self):
        """Останавливаем задачу при выгрузке"""
        self.auto_backup.cancel()
    
    @tasks.loop(hours=24)
    async def auto_backup(self):
        """Автоматический бэкап каждые 24 часа"""
        try:
            await self.create_backup()
            logger.info("✅ Автоматический бэкап выполнен")
        except Exception as e:
            logger.error(f"❌ Ошибка автобэкапа: {e}", exc_info=True)
    
    @auto_backup.before_loop
    async def before_auto_backup(self):
        """Ждем пока бот будет готов"""
        await self.bot.wait_until_ready()
    
    async def create_backup(self):
        """Создает бэкап базы данных"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"database_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # Копируем БД
        shutil.copy2("database.db", backup_path)
        
        # Удаляем старые бэкапы (оставляем последние 7)
        backups = sorted([f for f in os.listdir(self.backup_dir) if f.endswith('.db')])
        if len(backups) > 7:
            for old_backup in backups[:-7]:
                os.remove(os.path.join(self.backup_dir, old_backup))
        
        return backup_path
    
    @commands.command(name='backup', aliases=['бэкап'])
    @commands.has_permissions(administrator=True)
    async def manual_backup(self, ctx):
        """
        💾 Создать бэкап базы данных
        
        Создает резервную копию БД и отправляет файл
        
        Требуемые права: Administrator
        """
        try:
            backup_path = await self.create_backup()
            
            # Отправляем файл
            file = discord.File(backup_path)
            
            embed = EmbedBuilder.success(
                "💾 Бэкап создан",
                f"Файл: `{os.path.basename(backup_path)}`\n"
                f"Размер: {os.path.getsize(backup_path) / 1024:.2f} KB"
            )
            
            await ctx.send(embed=embed, file=file)
            logger.info(f"{ctx.author} создал бэкап БД")
            
        except Exception as e:
            embed = EmbedBuilder.error(
                "Ошибка бэкапа",
                f"```{str(e)}```"
            )
            await ctx.send(embed=embed)
            logger.error(f"Ошибка создания бэкапа: {e}", exc_info=True)
    
    @commands.command(name='backups', aliases=['бэкапы'])
    @commands.has_permissions(administrator=True)
    async def list_backups(self, ctx):
        """
        📋 Список всех бэкапов
        
        Показывает все существующие бэкапы
        
        Требуемые права: Administrator
        """
        backups = sorted([f for f in os.listdir(self.backup_dir) if f.endswith('.db')], reverse=True)
        
        if not backups:
            embed = EmbedBuilder.info("Нет бэкапов", "Бэкапы еще не создавались")
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="💾 Список бэкапов",
            description=f"Всего бэкапов: **{len(backups)}**",
            color=Config.COLOR_INFO
        )
        
        for backup in backups[:10]:  # Показываем последние 10
            path = os.path.join(self.backup_dir, backup)
            size = os.path.getsize(path) / 1024
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            
            embed.add_field(
                name=backup,
                value=f"Размер: {size:.2f} KB\n"
                     f"Дата: {mtime.strftime('%d.%m.%Y %H:%M')}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Backup(bot))
