import discord
from discord.ext import commands, tasks
import random
from database import db
from utils import EmbedBuilder
from config import Config
import logging

logger = logging.getLogger('DiscordBot.RandomEvents')

class RandomEvents(commands.Cog):
    """Система случайных событий"""
    
    def __init__(self, bot):
        self.bot = bot
        self.random_events.start()
        logger.info("✅ RandomEvents инициализирован")
    
    def cog_unload(self):
        self.random_events.cancel()
    
    @tasks.loop(hours=6)
    async def random_events(self):
        """Случайное событие каждые 6 часов"""
        try:
            # Выбираем случайное событие
            event_type = random.choice(['airdrop', 'bonus', 'rain'])
            
            for guild in self.bot.guilds:
                # Находим общий канал
                general = discord.utils.get(guild.text_channels, name='general') or guild.text_channels[0]
                
                if event_type == 'airdrop':
                    await self.airdrop_event(general)
                elif event_type == 'bonus':
                    await self.bonus_event(general)
                elif event_type == 'rain':
                    await self.rain_event(general)
            
            logger.info(f"Случайное событие: {event_type}")
            
        except Exception as e:
            logger.error(f"Ошибка случайного события: {e}", exc_info=True)
    
    @random_events.before_loop
    async def before_random_events(self):
        await self.bot.wait_until_ready()
    
    async def airdrop_event(self, channel):
        """Событие: Airdrop монет"""
        amount = random.randint(100, 500)
        
        embed = discord.Embed(
            title="🎁 AIRDROP!",
            description=f"Первый кто напишет `claim` получит **{amount}** {Config.EMOJI_COIN}!",
            color=Config.COLOR_SUCCESS
        )
        
        await channel.send(embed=embed)
        
        def check(m):
            return m.channel == channel and m.content.lower() == 'claim' and not m.author.bot
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            await db.add_coins(msg.author.id, amount)
            
            embed = EmbedBuilder.success(
                "Поздравляем!",
                f"{msg.author.mention} получил **{amount}** {Config.EMOJI_COIN}!"
            )
            await channel.send(embed=embed)
            
        except:
            embed = EmbedBuilder.info("Время вышло", "Никто не забрал airdrop 😢")
            await channel.send(embed=embed)
    
    async def bonus_event(self, channel):
        """Бонус XP для всех онлайн"""
        bonus_xp = random.randint(50, 150)
        
        online_members = [m for m in channel.guild.members if m.status != discord.Status.offline and not m.bot]
        
        for member in online_members:
            await db.add_xp(member.id, bonus_xp)
        
        embed = discord.Embed(
            title="⭐ БОНУС XP!",
            description=f"Все онлайн пользователи получили **+{bonus_xp}** XP!",
            color=Config.COLOR_SUCCESS
        )
        await channel.send(embed=embed)
    
    async def rain_event(self, channel):
        """Дождь монет"""
        total_amount = random.randint(1000, 5000)
        
        active_members = [
            m for m in channel.guild.members
            if not m.bot and m.status != discord.Status.offline
        ][:10]  # Максимум 10 человек
        
        if not active_members:
            return
        
        per_person = total_amount // len(active_members)
        
        for member in active_members:
            await db.add_coins(member.id, per_person)
        
        embed = discord.Embed(
            title="🌧️ ДОЖДЬ МОНЕТ!",
            description=f"**{len(active_members)}** активных пользователей получили по **{per_person}** {Config.EMOJI_COIN}!",
            color=Config.COLOR_SUCCESS
        )
        
        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RandomEvents(bot))
