import discord
from discord.ext import commands
from datetime import datetime, timedelta
from database import db
from utils import EmbedBuilder, confirm_action, Paginator
from config import Config
import logging

logger = logging.getLogger('DiscordBot.Moderation')

class Moderation(commands.Cog):
    """Система модерации: варны, кик, бан, мут"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ Moderation инициализирован")
    
    @commands.command(name='warn', aliases=['варн'])
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "Не указана"):
        """
        ⚠️ Выдать предупреждение пользователю
        
        Использование:
        !warn @user причина - выдать варн
        
        Требуемые права: Manage Messages
        """
        # Проверки
        if member.bot:
            embed = EmbedBuilder.error("Ошибка", "Нельзя варнить ботов!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.id == ctx.author.id:
            embed = EmbedBuilder.error("Ошибка", "Нельзя варнить самого себя!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.top_role >= ctx.author.top_role:
            embed = EmbedBuilder.error("Ошибка", "Нельзя варнить пользователя с равной или выше ролью!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Добавляем варн
        await db.add_warn(member.id, ctx.author.id, reason)
        
        # Получаем все варны пользователя
        warns = await db.get_warns(member.id)
        warn_count = len(warns)
        
        # Создаем embed
        embed = discord.Embed(
            title="⚠️ Предупреждение выдано",
            color=Config.COLOR_WARNING
        )
        
        embed.add_field(name="Пользователь", value=member.mention, inline=True)
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.add_field(name="Всего варнов", value=f"**{warn_count}/{Config.MAX_WARNS}**", inline=False)
        
        # Предупреждение о максимальном количестве
        if warn_count >= Config.MAX_WARNS:
            embed.add_field(
                name="🚨 Достигнут лимит варнов!",
                value=f"Рекомендуется бан пользователя",
                inline=False
            )
            embed.color = Config.COLOR_ERROR
        
        await ctx.send(embed=embed)
        
        # Отправляем ЛС пользователю
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ Ты получил предупреждение на {ctx.guild.name}",
                color=Config.COLOR_WARNING
            )
            dm_embed.add_field(name="Причина", value=reason, inline=False)
            dm_embed.add_field(name="Модератор", value=ctx.author.name, inline=True)
            dm_embed.add_field(name="Всего варнов", value=f"{warn_count}/{Config.MAX_WARNS}", inline=True)
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # У пользователя закрыты ЛС
        
        # Логируем в лог-канал
        log_id = db.get_config("log_channel_id", cast_type=int)
        if log_id:
            log_channel = ctx.guild.get_channel(log_id)
            if log_channel:
                await log_channel.send(embed=embed)
        
        logger.info(f"{ctx.author} выдал варн {member}: {reason}")
    
    @commands.command(name='warns', aliases=['варны'])
    async def warns(self, ctx, member: discord.Member = None):
        """
        📋 Посмотреть предупреждения пользователя
        
        Использование:
        !warns - твои варны
        !warns @user - варны другого пользователя
        """
        member = member or ctx.author
        warns = await db.get_warns(member.id)
        
        if not warns:
            embed = EmbedBuilder.success(
                "✅ Нет предупреждений",
                f"{member.mention} не имеет предупреждений"
            )
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title=f"⚠️ Предупреждения {member.display_name}",
            description=f"Всего: **{len(warns)}/{Config.MAX_WARNS}**",
            color=Config.COLOR_WARNING
        )
        
        for idx, warn in enumerate(warns, 1):
            moderator = self.bot.get_user(warn['admin_id'])
            mod_name = moderator.name if moderator else f"ID: {warn['admin_id']}"
            
            date = datetime.fromisoformat(warn['date'])
            date_str = date.strftime("%d.%m.%Y %H:%M")
            
            embed.add_field(
                name=f"#{idx} | {date_str}",
                value=f"**Модератор:** {mod_name}\n"
                     f"**Причина:** {warn['reason']}\n"
                     f"**ID:** `{warn['id']}`",
                inline=False
            )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='clearwarns', aliases=['unwarn', 'снятьварны'])
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member):
        """
        🗑️ Очистить все предупреждения пользователя
        
        Использование:
        !clearwarns @user - снять все варны
        
        Требуемые права: Administrator
        """
        warns = await db.get_warns(member.id)
        
        if not warns:
            embed = EmbedBuilder.info("Нет предупреждений", f"{member.mention} не имеет варнов")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Подтверждение
        confirmed = await confirm_action(
            ctx,
            "Снять все предупреждения?",
            f"Будут удалены **{len(warns)}** варнов у {member.mention}"
        )
        
        if not confirmed:
            return
        
        # Очищаем варны
        await db.clear_warns(member.id)
        
        embed = EmbedBuilder.success(
            "✅ Варны очищены",
            f"Удалено **{len(warns)}** предупреждений у {member.mention}"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} очистил {len(warns)} варнов у {member}")
    
    @commands.command(name='kick', aliases=['кик'])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Не указана"):
        """
        👢 Кикнуть пользователя с сервера
        
        Использование:
        !kick @user причина
        
        Требуемые права: Kick Members
        """
        # Проверки
        if member.bot:
            embed = EmbedBuilder.error("Ошибка", "Нельзя кикать ботов!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.id == ctx.author.id:
            embed = EmbedBuilder.error("Ошибка", "Нельзя кикнуть самого себя!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.top_role >= ctx.author.top_role:
            embed = EmbedBuilder.error("Ошибка", "Нельзя кикнуть пользователя с равной или выше ролью!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Подтверждение
        confirmed = await confirm_action(
            ctx,
            f"Кикнуть {member.display_name}?",
            f"**Причина:** {reason}"
        )
        
        if not confirmed:
            return
        
        # Отправляем ЛС перед киком
        try:
            dm_embed = discord.Embed(
                title=f"👢 Ты был кикнут с {ctx.guild.name}",
                color=Config.COLOR_ERROR
            )
            dm_embed.add_field(name="Причина", value=reason, inline=False)
            dm_embed.add_field(name="Модератор", value=ctx.author.name, inline=True)
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        # Кикаем
        await member.kick(reason=f"{ctx.author}: {reason}")
        
        embed = EmbedBuilder.success(
            "👢 Пользователь кикнут",
            f"**Пользователь:** {member.mention}\n"
            f"**Модератор:** {ctx.author.mention}\n"
            f"**Причина:** {reason}"
        )
        
        await ctx.send(embed=embed)
        
        # Логируем
        log_id = db.get_config("log_channel_id", cast_type=int)
        if log_id:
            log_channel = ctx.guild.get_channel(log_id)
            if log_channel:
                await log_channel.send(embed=embed)
        
        logger.info(f"{ctx.author} кикнул {member}: {reason}")
    
    @commands.command(name='ban', aliases=['бан'])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Не указана"):
        """
        🔨 Забанить пользователя на сервере
        
        Использование:
        !ban @user причина
        
        Требуемые права: Ban Members
        """
        # Проверки
        if member.bot:
            embed = EmbedBuilder.error("Ошибка", "Нельзя банить ботов!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.id == ctx.author.id:
            embed = EmbedBuilder.error("Ошибка", "Нельзя забанить самого себя!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.top_role >= ctx.author.top_role:
            embed = EmbedBuilder.error("Ошибка", "Нельзя забанить пользователя с равной или выше ролью!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Подтверждение
        confirmed = await confirm_action(
            ctx,
            f"Забанить {member.display_name}?",
            f"**Причина:** {reason}\n⚠️ Это действие необратимо!"
        )
        
        if not confirmed:
            return
        
        # Отправляем ЛС перед баном
        try:
            dm_embed = discord.Embed(
                title=f"🔨 Ты был забанен на {ctx.guild.name}",
                color=Config.COLOR_ERROR
            )
            dm_embed.add_field(name="Причина", value=reason, inline=False)
            dm_embed.add_field(name="Модератор", value=ctx.author.name, inline=True)
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        # Баним
        await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=0)
        
        embed = EmbedBuilder.success(
            "🔨 Пользователь забанен",
            f"**Пользователь:** {member.mention}\n"
            f"**Модератор:** {ctx.author.mention}\n"
            f"**Причина:** {reason}"
        )
        
        await ctx.send(embed=embed)
        
        # Логируем
        log_id = db.get_config("log_channel_id", cast_type=int)
        if log_id:
            log_channel = ctx.guild.get_channel(log_id)
            if log_channel:
                await log_channel.send(embed=embed)
        
        logger.info(f"{ctx.author} забанил {member}: {reason}")
    
    @commands.command(name='unban', aliases=['разбан'])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "Не указана"):
        """
        🔓 Разбанить пользователя
        
        Использование:
        !unban 123456789 причина
        
        Требуемые права: Ban Members
        """
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            embed = EmbedBuilder.error("Ошибка", f"Пользователь с ID `{user_id}` не найден")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
        except discord.NotFound:
            embed = EmbedBuilder.error("Ошибка", f"{user.mention} не забанен на этом сервере")
            return await ctx.send(embed=embed, delete_after=5)
        
        embed = EmbedBuilder.success(
            "🔓 Пользователь разбанен",
            f"**Пользователь:** {user.mention}\n"
            f"**Модератор:** {ctx.author.mention}\n"
            f"**Причина:** {reason}"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} разбанил {user}: {reason}")
    
    @commands.command(name='clear', aliases=['purge', 'очистить'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """
        🗑️ Очистить сообщения в канале
        
        Использование:
        !clear 50 - удалить 50 сообщений
        
        Требуемые права: Manage Messages
        """
        if amount < 1 or amount > 100:
            embed = EmbedBuilder.error("Ошибка", "Количество должно быть от 1 до 100")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Удаляем сообщения (включая команду)
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        embed = EmbedBuilder.success(
            "🗑️ Сообщения удалены",
            f"Удалено **{len(deleted) - 1}** сообщений"
        )
        
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=5)
        
        logger.info(f"{ctx.author} очистил {len(deleted)-1} сообщений в {ctx.channel}")
    
    @commands.command(name='slowmode', aliases=['слоумод'])
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """
        ⏱️ Установить медленный режим
        
        Использование:
        !slowmode 10 - 10 секунд между сообщениями
        !slowmode 0 - отключить
        
        Требуемые права: Manage Channels
        """
        if seconds < 0 or seconds > 21600:
            embed = EmbedBuilder.error("Ошибка", "Время должно быть от 0 до 21600 секунд (6 часов)")
            return await ctx.send(embed=embed, delete_after=5)
        
        await ctx.channel.edit(slowmode_delay=seconds)
        
        if seconds == 0:
            embed = EmbedBuilder.success("Медленный режим отключен", f"В канале {ctx.channel.mention}")
        else:
            embed = EmbedBuilder.success(
                "Медленный режим включен",
                f"**Канал:** {ctx.channel.mention}\n"
                f"**Задержка:** {seconds} секунд"
            )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} установил slowmode {seconds}с в {ctx.channel}")

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Moderation(bot))
