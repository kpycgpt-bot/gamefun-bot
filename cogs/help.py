import discord
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        # Цвета
        MAIN_COLOR = 0x00AAFF
        ADMIN_COLOR = 0xFF0000

        # --- 1. ЗАГОЛОВОК ---
        embed_header = discord.Embed(
            title="📘 Справочник Команд",
            description="# 👇 СПИСОК КОМАНД",
            color=MAIN_COLOR
        )
        if self.bot.user.avatar:
            embed_header.set_thumbnail(url=self.bot.user.avatar.url)
        await ctx.send(embed=embed_header)

        # --- 2. ЭКОНОМИКА ---
        embed_eco = discord.Embed(
            description=(
                "## 👤 `!profile`\n"
                "### 📄 Твой уровень, опыт и баланс монет.\n\n"
                "## ✨ `!myxp`\n"
                "### 📊 Точное количество опыта до уровня.\n\n"
                "## 💰 `!farm`\n"
                "### 💸 Ежедневная награда (XP + Деньги)."
            ),
            color=MAIN_COLOR
        )
        await ctx.send(embed=embed_eco)

        # --- 3. КОМНАТЫ ---
        embed_rooms = discord.Embed(
            description=(
                "# 🏰 ЛИЧНАЯ КОМНАТА\n"
                "*(Только внутри голосового канала)*\n\n"
                "## 🔒 `!lock`\n"
                "### ⛔ Закрыть доступ (никто не войдет).\n\n"
                "## 🔓 `!unlock`\n"
                "### ✅ Открыть комнату для всех."
            ),
            color=MAIN_COLOR
        )
        await ctx.send(embed=embed_rooms)

        # --- 4. ПОЛЕЗНОЕ ---
        embed_misc = discord.Embed(
            description=(
                "# 🎈 ПРОЧЕЕ\n\n"
                "## ✉️ `!myinvite`\n"
                "### 🔗 Создать твою ссылку-приглашение."
            ),
            color=MAIN_COLOR
        )
        embed_misc.set_footer(text=f"Запросил: {ctx.author.display_name}")
        await ctx.send(embed=embed_misc)

        # --- 5. АДМИНКА ---
        if ctx.author.guild_permissions.administrator:
            embed_admin = discord.Embed(
                title="🛡️ АДМИН-ПАНЕЛЬ",
                description=(
                    "## ⚙️ НАСТРОЙКА\n"
                    "### `!setupserver` — Установка каналов\n"
                    "### `!textpanel` — Кнопка приватных баз\n"
                    "### `!rolespanel` — Меню ролей\n"
                    "### `!setup_tools` — Репорты\n\n"
                    "## 🛠️ УПРАВЛЕНИЕ\n"
                    "### `!clear` — Очистка чата\n"
                    "### `!announce` — Объявление\n"
                    "### `!upd` — Патчноут\n"
                    "### `!reloadall` — Рестарт бота"
                ),
                color=ADMIN_COLOR
            )
            await ctx.send(embed=embed_admin)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))