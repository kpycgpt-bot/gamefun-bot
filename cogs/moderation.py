import discord
from discord.ext import commands
import asyncio
import config
from datetime import datetime
from database import db  # Импортируем базу данных

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild):
        return guild.get_channel(config.LOG_CHANNEL)

    async def get_or_create_muted_role(self, guild):
        """Создает роль Muted, если её нет"""
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted", reason="Для системы мутов")
            for channel in guild.channels:
                try:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)
                except:
                    pass
        return muted_role

    # ==========================
    # 👮‍♂️ ПОЛИЦЕЙСКИЙ УЧАСТОК 
    # ==========================

    # --- МУТ ---
    @commands.command(name="mute")
    @commands.has_permissions(kick_members=True)
    async def mute(self, ctx, member: discord.Member, time_str: str, *, reason="Нарушение правил"):
        """Мут на время. Пример: !mute @User 10m Спам"""
        
        # Разбор времени
        time_unit = time_str[-1]
        try:
            time_val = int(time_str[:-1])
        except ValueError:
            return await ctx.send("❌ Ошибка! Формат: `10m`, `1h`.")

        seconds = 0
        if time_unit == "s": seconds = time_val
        elif time_unit == "m": seconds = time_val * 60
        elif time_unit == "h": seconds = time_val * 3600
        else:
            return await ctx.send("❌ Используй m (минуты) или h (часы).")

        muted_role = await self.get_or_create_muted_role(ctx.guild)
        
        if muted_role not in member.roles:
            await member.add_roles(muted_role, reason=reason)
            await ctx.send(f"🤐 **{member.name}** замучен на **{time_str}**.\n📝 Причина: {reason}")
        else:
            await ctx.send(f"⚠️ **{member.name}** уже в муте!")

        await asyncio.sleep(seconds)
        
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f"🗣️ **{member.name}** свободен (время мута вышло).")

    # --- РАЗМУТ ---
    @commands.command(name="unmute")
    @commands.has_permissions(kick_members=True)
    async def unmute(self, ctx, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f"✅ Мут снят с **{member.name}**.")
        else:
            await ctx.send("❌ Этот пользователь не в муте.")

    # --- ВАРН (ПРЕДУПРЕЖДЕНИЕ) ---
    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="Нарушение"):
        """Выдать варн. Пример: !warn @User Мат"""
        db.add_warn(member.id, ctx.author.id, reason)
        warns = db.get_warns(member.id)
        count = len(warns)
        
        embed = discord.Embed(title="⚠️ ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.red())
        embed.add_field(name="Нарушитель", value=member.mention)
        embed.add_field(name="Модератор", value=ctx.author.mention)
        embed.add_field(name="Причина", value=reason)
        embed.set_footer(text=f"Варн {count}/3")
        await ctx.send(embed=embed)

        # 3 Варна = Мут
        if count >= 3:
            await ctx.send(f"🚨 **{member.name}** набрал 3 варна! Авто-мут на 1 час.")
            db.remove_warns(member.id)
            await self.mute(ctx, member, "1h", reason="3 варна")

    # --- ИСТОРИЯ ВАРНОВ ---
    @commands.command(name="warns")
    async def check_warns(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        warns = db.get_warns(member.id)
        
        if not warns:
            return await ctx.send(f"✅ У **{member.name}** нет варнов.")

        embed = discord.Embed(title=f"📜 История {member.name}", color=discord.Color.orange())
        for row in warns:
            embed.add_field(name=f"📅 {row[2]}", value=f"**Причина:** {row[1]}\n**От:** <@{row[0]}>", inline=False)
        await ctx.send(embed=embed)

    # ==========================
    # 📝 СИСТЕМА ЛОГОВ (Твоя старая)
    # ==========================

    @commands.command(name="testlog")
    @commands.has_permissions(administrator=True)
    async def testlog(self, ctx):
        channel = self.get_log_channel(ctx.guild)
        if channel:
            await channel.send("✅ Тест логов прошел успешно!")
            await ctx.send(f"✅ Сообщение отправлено в {channel.mention}.")
        else:
            await ctx.send("❌ Не найден канал логов! Проверь config.py")

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ Удалено {amount} сообщений.", delete_after=5)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.command and ctx.command.name in ["testlog", "warn", "mute"]: return
        channel = self.get_log_channel(ctx.guild)
        if not channel: return
        
        embed = discord.Embed(title="🤖 Команда", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Кто", value=ctx.author.mention)
        embed.add_field(name="Что написал", value=f"`{ctx.message.content}`")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        channel = self.get_log_channel(message.guild)
        if channel:
            embed = discord.Embed(title="🗑️ Удалено", color=discord.Color.red(), timestamp=datetime.now())
            embed.description = f"**Автор:** {message.author.mention}\n**Канал:** {message.channel.mention}"
            content = message.content or "[Вложение]"
            embed.add_field(name="Текст:", value=content[:1000], inline=False)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))