import discord
from discord.ext import commands
import re
from database import db
from utils import EmbedBuilder
from config import Config
import logging

logger = logging.getLogger('DiscordBot.AutoMod')

class AutoMod(commands.Cog):
    """Система автомодерации"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Настройки автомодерации (можно вынести в БД)
        self.spam_threshold = 5  # сообщений
        self.spam_interval = 5  # секунд
        self.user_messages = {}  # кэш сообщений
        
        # Запрещенные слова
        self.bad_words = [
            # Добавь свои слова
        ]
        
        logger.info("✅ AutoMod инициализирован")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Проверяет сообщения на нарушения"""
        # Игнорируем ботов и админов
        if message.author.bot or not message.guild:
            return
        
        if message.author.guild_permissions.administrator:
            return
        
        # Антиспам
        if await self.check_spam(message):
            return
        
        # Проверка на запрещенные слова
        if await self.check_bad_words(message):
            return
        
        # Проверка на caps
        if await self.check_caps(message):
            return
        
        # Проверка на массовые упоминания
        if await self.check_mass_mentions(message):
            return
    
    async def check_spam(self, message):
        """Проверка на спам"""
        import time
        
        user_id = message.author.id
        current_time = time.time()
        
        # Инициализируем данные пользователя
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Добавляем сообщение
        self.user_messages[user_id].append(current_time)
        
        # Удаляем старые сообщения
        self.user_messages[user_id] = [
            t for t in self.user_messages[user_id]
            if current_time - t < self.spam_interval
        ]
        
        # Проверяем спам
        if len(self.user_messages[user_id]) > self.spam_threshold:
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} не спамь!",
                    delete_after=3
                )
                logger.warning(f"Спам от {message.author}")
                return True
            except:
                pass
        
        return False
    
    async def check_bad_words(self, message):
        """Проверка на мат"""
        content_lower = message.content.lower()
        
        for word in self.bad_words:
            if word in content_lower:
                try:
                    await message.delete()
                    embed = EmbedBuilder.warning(
                        "Неприемлемое слово",
                        f"{message.author.mention} следи за своим языком!"
                    )
                    await message.channel.send(embed=embed, delete_after=5)
                    logger.warning(f"Мат от {message.author}: {word}")
                    return True
                except:
                    pass
        
        return False
    
    async def check_caps(self, message):
        """Проверка на капс"""
        if len(message.content) < 10:
            return False
        
        caps_count = sum(1 for c in message.content if c.isupper())
        if caps_count / len(message.content) > 0.7:
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} не кричи!",
                    delete_after=3
                )
                logger.warning(f"Капс от {message.author}")
                return True
            except:
                pass
        
        return False
    
    async def check_mass_mentions(self, message):
        """Проверка на массовые упоминания"""
        if len(message.mentions) > 5:
            try:
                await message.delete()
                embed = EmbedBuilder.warning(
                    "Массовые упоминания",
                    f"{message.author.mention} не спамь упоминаниями!"
                )
                await message.channel.send(embed=embed, delete_after=5)
                logger.warning(f"Массовые упоминания от {message.author}")
                return True
            except:
                pass
        
        return False
    
    @commands.command(name='automod', aliases=['автомод'])
    @commands.has_permissions(administrator=True)
    async def automod_status(self, ctx):
        """
        🛡️ Показать статус автомодерации
        
        Требуемые права: Administrator
        """
        embed = discord.Embed(
            title="🛡️ Автомодерация",
            description="Система автоматической модерации активна",
            color=Config.COLOR_INFO
        )
        
        embed.add_field(
            name="📊 Настройки",
            value=f"• Антиспам: {self.spam_threshold} сообщений за {self.spam_interval}с\n"
                 f"• Фильтр мата: {len(self.bad_words)} слов\n"
                 f"• Проверка капса: Включена\n"
                 f"• Проверка упоминаний: Макс 5",
            inline=False
        )
        
        embed.add_field(
            name="✅ Защищает от",
            value="• Спама сообщениями\n"
                 f"• Запрещенных слов\n"
                 f"• Капса\n"
                 f"• Массовых упоминаний",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
