import discord
from discord.ext import commands
import config
from datetime import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild):
        # Принудительно читаем конфиг, если вдруг переменная не обновилась (хотя рестарт лучше)
        return guild.get_channel(config.LOG_CHANNEL)

    # --- ТЕСТОВАЯ КОМАНДА (НОВАЯ) ---
    @commands.command(name="testlog")
    @commands.has_permissions(administrator=True)
    async def testlog(self, ctx):
        """Проверяет, работает ли канал логов."""
        channel_id = config.LOG_CHANNEL
        channel = self.get_log_channel(ctx.guild)

        if channel is None:
            await ctx.send(f"❌ **Ошибка:** Бот не видит канал логов!\n"
                           f"ID в конфиге: `{channel_id}`.\n"
                           f"Совет: Проверь `config.py` и перезапусти бота.")
        else:
            try:
                await channel.send("✅ **Тест логов:** Если вы это видите, система работает!")
                await ctx.send(f"✅ Тестовое сообщение отправлено в {channel.mention}.")
            except discord.Forbidden:
                await ctx.send(f"❌ **Ошибка прав:** Бот видит канал {channel.mention}, но не может туда писать!")

    # --- ОСТАЛЬНЫЕ КОМАНДЫ ---
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ Удалено {amount} сообщений.", delete_after=5)

    @commands.command(name="announce")
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, *, text: str):
        embed = discord.Embed(title="📢 ОБЪЯВЛЕНИЕ", description=text, color=discord.Color.red())
        embed.set_footer(text=f"Администрация {ctx.guild.name}")
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name="reload")
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, extension: str):
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"✅ Модуль {extension} перезагружен.")
        except Exception as e:
            await ctx.send(f"❌ Ошибка: {e}")

    # --- ЛОГИРОВАНИЕ ---

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Игнорируем саму команду настройки, чтобы не спамить при старте
        if ctx.command and ctx.command.name in ["testlog", "setupserver", "resetserver"]:
            return

        channel = self.get_log_channel(ctx.guild)
        if not channel: return

        embed = discord.Embed(
            title="🤖 Использована команда",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Пользователь", value=f"{ctx.author.mention}", inline=True)
        embed.add_field(name="📍 Канал", value=ctx.channel.mention, inline=True)
        embed.add_field(name="💬 Команда", value=f"```{ctx.message.content}```", inline=False)
        embed.add_field(name="🔗 Перейти", value=f"[Клик]({ctx.message.jump_url})", inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.get_log_channel(member.guild)
        if channel:
            embed = discord.Embed(
                title="📤 Участник вышел",
                description=f"**{member}** (ID: {member.id})",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        channel = self.get_log_channel(message.guild)
        if channel:
            embed = discord.Embed(title="🗑️ Сообщение удалено", color=discord.Color.red(), timestamp=datetime.now())
            embed.description = f"**Автор:** {message.author.mention}\n**Канал:** {message.channel.mention}"
            content = message.content or "[Вложение]"
            if len(content) > 1000: content = content[:1000] + "..."
            embed.add_field(name="Содержимое:", value=content, inline=False)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))