import discord
from discord.ext import commands
import asyncio

# --- ОКНО ДЛЯ ОТПРАВКИ РЕПОРТА ---
class ReportModal(discord.ui.Modal, title="Отправка репорта / жалобы"):
    subject = discord.ui.TextInput(
        label="Тема", 
        placeholder="Например: Баг в экономике или жалоба на игрока",
        min_length=5, max_length=100
    )
    description = discord.ui.TextInput(
        label="Подробное описание",
        style=discord.TextStyle.paragraph,
        placeholder="Опишите проблему как можно подробнее...",
        min_length=10, max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Ищем канал для стаффа (🚨-reports)
        report_log = discord.utils.get(interaction.guild.text_channels, name="🚨-reports")
        
        if not report_log:
            return await interaction.response.send_message("❌ Ошибка: Канал для администрации не найден.", ephemeral=True)

        embed = discord.Embed(
            title="🚨 НОВЫЙ РЕПОРТ",
            color=discord.Color.red(),
            timestamp=interaction.created_at
        )
        embed.add_field(name="Отправитель:", value=f"{interaction.user.mention} (ID: `{interaction.user.id}`)")
        embed.add_field(name="Тема:", value=self.subject.value, inline=False)
        embed.add_field(name="Описание:", value=self.description.value, inline=False)
        
        await report_log.send(embed=embed)
        await interaction.response.send_message("✅ Ваш репорт успешно отправлен администрации сервера!", ephemeral=True)

# --- ПАНЕЛЬ РЕПОРТОВ ---
class ReportPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Написать репорт", emoji="🛠️", style=discord.ButtonStyle.danger, custom_id="send_report_btn")
    async def send_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal())

# --- ПАНЕЛЬ ПОМОЩНИКА (FAQ) ---
class HelperPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Как получить роль?", emoji="🎭", style=discord.ButtonStyle.blurple)
    async def roles_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Чтобы выбрать игры, которые тебя интересуют, перейди в канал <#🎭-choose-your-interest> и нажми на соответствующие кнопки!", 
            ephemeral=True
        )

    @discord.ui.button(label="Личная комната", emoji="🏰", style=discord.ButtonStyle.gray)
    async def room_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Голосовой канал: Зайди в **'🔊 ➕ Создать комнату'**.\nТекстовая база: Напиши `!textpanel` в канале управления.", 
            ephemeral=True
        )

    @discord.ui.button(label="Список команд", emoji="📘", style=discord.ButtonStyle.success)
    async def commands_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Используй команду `!help`, чтобы увидеть все доступные функции бота.", 
            ephemeral=True
        )

class AiTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_tools(self, ctx):
        """Автоматическая установка панелей в нужные каналы."""
        # 1. Настройка Помощника
        helper_ch = discord.utils.get(ctx.guild.text_channels, name="🤖-бот-помощник")
        if helper_ch:
            embed_h = discord.Embed(
                title="🤖 Центр поддержки GameFun",
                description="Привет! Я твой автоматический помощник. Нажми на кнопку ниже, если у тебя есть вопрос.",
                color=discord.Color.blue()
            )
            await helper_ch.send(embed=embed_h, view=HelperPanelView())

        # 2. Настройка Репортов
        report_ch = discord.utils.get(ctx.guild.text_channels, name="🛠️-репорты")
        if report_ch:
            embed_r = discord.Embed(
                title="🛠️ Система репортов и багов",
                description=(
                    "Нашли ошибку в работе бота? Или кто-то нарушает правила?\n"
                    "Нажмите кнопку ниже, чтобы отправить жалобу администрации сервера."
                ),
                color=discord.Color.red()
            )
            await report_ch.send(embed=embed_r, view=ReportPanelView())
        
        await ctx.send("✅ Панели в категории AI & Tools успешно установлены!")

async def setup(bot):
    await bot.add_cog(AiTools(bot))