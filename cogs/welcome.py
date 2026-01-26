import discord
from discord.ext import commands
from database import db
from utils import EmbedBuilder
from config import Config
import logging
from datetime import datetime

logger = logging.getLogger('DiscordBot.Welcome')

class Welcome(commands.Cog):
    """Система приветствий новых участников"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ Welcome инициализирован")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Приветствует нового участника"""
        try:
            guild = member.guild
            
            # Получаем канал приветствий из БД
            channel_id = db.get_config("welcome_channel_id", cast_type=int)
            
            if not channel_id:
                logger.debug(f"Канал приветствий не настроен для {guild.name}")
                return
            
            channel = guild.get_channel(channel_id)
            if not channel:
                logger.warning(f"Канал приветствий {channel_id} не найден в {guild.name}")
                return
            
            # Создаем красивый embed
            embed = discord.Embed(
                title=f"👋 Добро пожаловать, {member.name}!",
                description=f"Рады видеть тебя на **{guild.name}**!\n\n"
                           f"Ты стал **{guild.member_count}**-м участником нашего сервера! 🎉",
                color=Config.COLOR_SUCCESS
            )
            
            # Добавляем информацию о сервере
            embed.add_field(
                name="📚 Что дальше?",
                value=f"• Прочитай правила\n"
                     f"• Получи роли\n"
                     f"• Познакомься с участниками\n"
                     f"• Веселись!",
                inline=False
            )
            
            # Информация о командах
            embed.add_field(
                name="🤖 Команды бота",
                value=f"Используй `{Config.PREFIX}help` чтобы узнать все команды!",
                inline=False
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(
                text=f"ID: {member.id} • Присоединился",
                icon_url=guild.icon.url if guild.icon else None
            )
            embed.timestamp = datetime.utcnow()
            
            # Отправляем приветствие
            await channel.send(
                content=member.mention,
                embed=embed
            )
            
            # Даем начальные монеты новичку
            await db.add_coins(member.id, 100)
            
            logger.info(f"Приветствован новый участник: {member} ({member.id}) на {guild.name}")
            
        except Exception as e:
            logger.error(f"Ошибка при приветствии {member}: {e}", exc_info=True)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Прощается с участником, который покинул сервер"""
        try:
            guild = member.guild
            
            # Получаем канал приветствий
            channel_id = db.get_config("welcome_channel_id", cast_type=int)
            
            if not channel_id:
                return
            
            channel = guild.get_channel(channel_id)
            if not channel:
                return
            
            # Создаем embed о выходе
            embed = discord.Embed(
                title="👋 Участник покинул сервер",
                description=f"**{member.name}** покинул нас 😢\n\n"
                           f"Теперь на сервере **{guild.member_count}** участников.",
                color=Config.COLOR_ERROR
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.utcnow()
            
            await channel.send(embed=embed)
            
            logger.info(f"Участник {member} ({member.id}) покинул {guild.name}")
            
        except Exception as e:
            logger.error(f"Ошибка при прощании с {member}: {e}", exc_info=True)
    
    @commands.command(name='testwelcome', aliases=['тестприветствие'])
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        """
        🧪 Протестировать сообщение приветствия
        
        Отправляет пример приветствия с твоим аккаунтом
        
        Требуемые права: Administrator
        """
        channel_id = db.get_config("welcome_channel_id", cast_type=int)
        
        if not channel_id:
            embed = EmbedBuilder.error(
                "Ошибка",
                f"Канал приветствий не настроен!\n\n"
                f"Используй `{Config.PREFIX}setwelcome #канал` для настройки"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            embed = EmbedBuilder.error(
                "Ошибка",
                "Канал приветствий был удален. Настрой его заново."
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        # Создаем тестовое приветствие
        embed = discord.Embed(
            title=f"👋 [ТЕСТ] Добро пожаловать, {ctx.author.name}!",
            description=f"Рады видеть тебя на **{ctx.guild.name}**!\n\n"
                       f"Ты стал **{ctx.guild.member_count}**-м участником нашего сервера! 🎉",
            color=Config.COLOR_SUCCESS
        )
        
        embed.add_field(
            name="📚 Что дальше?",
            value=f"• Прочитай правила\n"
                 f"• Получи роли\n"
                 f"• Познакомься с участниками\n"
                 f"• Веселись!",
            inline=False
        )
        
        embed.add_field(
            name="🤖 Команды бота",
            value=f"Используй `{Config.PREFIX}help` чтобы узнать все команды!",
            inline=False
        )
        
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(
            text=f"ID: {ctx.author.id} • Это тестовое сообщение",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        embed.timestamp = datetime.utcnow()
        
        await channel.send(
            content=f"{ctx.author.mention} (тест)",
            embed=embed
        )
        
        success_embed = EmbedBuilder.success(
            "Тест отправлен!",
            f"Проверь канал {channel.mention}"
        )
        await ctx.send(embed=success_embed, delete_after=10)
        
        logger.info(f"{ctx.author} протестировал приветствие")
    
    @commands.command(name='welcomemessage', aliases=['приветствие'])
    @commands.has_permissions(administrator=True)
    async def welcome_message(self, ctx):
        """
        📝 Показать текущие настройки приветствия
        
        Отображает какой канал используется для приветствий
        
        Требуемые права: Administrator
        """
        channel_id = db.get_config("welcome_channel_id", cast_type=int)
        
        embed = discord.Embed(
            title="📝 Настройки приветствий",
            color=Config.COLOR_INFO
        )
        
        if channel_id:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                embed.add_field(
                    name="✅ Канал приветствий",
                    value=f"{channel.mention} (`{channel_id}`)",
                    inline=False
                )
                embed.add_field(
                    name="🎁 Бонус новичкам",
                    value="100 монет при присоединении",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Канал приветствий",
                    value=f"Канал `{channel_id}` не найден (был удален?)",
                    inline=False
                )
        else:
            embed.add_field(
                name="❌ Канал приветствий",
                value="Не настроен",
                inline=False
            )
        
        embed.add_field(
            name="⚙️ Команды настройки",
            value=f"`{Config.PREFIX}setwelcome #канал` - установить канал\n"
                 f"`{Config.PREFIX}testwelcome` - протестировать",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='welcomestats', aliases=['статистикаприветствий'])
    @commands.has_permissions(administrator=True)
    async def welcome_stats(self, ctx):
        """
        📊 Статистика новых участников
        
        Показывает статистику присоединений за последнее время
        
        Требуемые права: Administrator
        """
        guild = ctx.guild
        
        # Считаем участников за последние периоды
        from datetime import timedelta
        now = datetime.utcnow()
        
        today = 0
        week = 0
        month = 0
        
        for member in guild.members:
            if not member.joined_at:
                continue
            
            days_ago = (now - member.joined_at).days
            
            if days_ago == 0:
                today += 1
                week += 1
                month += 1
            elif days_ago <= 7:
                week += 1
                month += 1
            elif days_ago <= 30:
                month += 1
        
        embed = discord.Embed(
            title="📊 Статистика новых участников",
            description=f"Сервер: **{guild.name}**",
            color=Config.COLOR_INFO
        )
        
        embed.add_field(
            name="👥 Всего участников",
            value=f"**{guild.member_count}**",
            inline=True
        )
        
        embed.add_field(
            name="📅 Сегодня",
            value=f"+**{today}**",
            inline=True
        )
        
        embed.add_field(
            name="📆 За неделю",
            value=f"+**{week}**",
            inline=True
        )
        
        embed.add_field(
            name="📈 За месяц",
            value=f"+**{month}**",
            inline=True
        )
        
        # Средний прирост
        if month > 0:
            avg_per_day = month / 30
            embed.add_field(
                name="📊 Средний прирост",
                value=f"~**{avg_per_day:.1f}** чел/день",
                inline=True
            )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Welcome(bot))
