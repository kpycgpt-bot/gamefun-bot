import discord
from discord.ext import commands
import sys
import os
import asyncio

# --- КНОПКИ УПРАВЛЕНИЯ ---
class AdminControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="💀 ПОЛНЫЙ РЕСТАРТ", style=discord.ButtonStyle.danger, emoji="🔌", row=0)
    async def restart_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Не трогай, это для админов!", ephemeral=True)

        await interaction.response.send_message("🔌 **Перезагрузка систем...**\nБот вернется через 5 секунд!", ephemeral=False)
        print(f"[RESTART] Команду запросил {interaction.user}")
        await asyncio.sleep(1)
        sys.exit(0) # Systemd сам перезапустит бота

    @discord.ui.button(label="♻️ Обновить код", style=discord.ButtonStyle.primary, row=0)
    async def reload_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator: return

        await interaction.response.defer(ephemeral=True)
        log_text = ""
        error_count = 0
        success_count = 0

        # Перебираем все файлы
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                extension_name = f'cogs.{filename[:-3]}'
                try:
                    await self.bot.reload_extension(extension_name)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    log_text += f"❌ **{filename}**: {e}\n"

        embed = discord.Embed(title="📊 Отчет обновления", color=0x00FF00 if error_count == 0 else 0xFF0000)
        embed.add_field(name="Успешно", value=f"✅ {success_count}", inline=True)
        if error_count > 0:
            embed.add_field(name="Ошибки", value=f"🚫 {error_count}", inline=True)
            embed.description = log_text
        else:
            embed.description = "Все модули перезагружены!"
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class AdminSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ГЛАВНАЯ ПАНЕЛЬ ---
    @commands.command(name="panel")
    @commands.has_permissions(administrator=True)
    async def admin_panel(self, ctx):
        """Вызывает пульт управления ботом."""
        embed = discord.Embed(
            title="🛡️ ЦЕНТР УПРАВЛЕНИЯ",
            description="Управление жизненным циклом бота.",
            color=0x2b2d31
        )
        await ctx.send(embed=embed, view=AdminControlView(self.bot))

    # --- РУЧНАЯ ПЕРЕЗАГРУЗКА (ИЗ admin.py) ---
    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_module(self, ctx, extension):
        """Точечная перезагрузка одного модуля."""
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"✅ Модуль **{extension}** обновлен!")
        except Exception as e:
            await ctx.send(f"❌ Ошибка: `{e}`")

    # --- СПИСОК МОДУЛЕЙ (ИЗ admin.py) ---
    @commands.command(name="cogs")
    @commands.is_owner()
    async def list_cogs(self, ctx):
        loaded = "\n".join([f"🧩 {ext}" for ext in self.bot.extensions.keys()])
        await ctx.send(f"**Активные модули:**\n```\n{loaded}\n```")

async def setup(bot):
    await bot.add_cog(AdminSystem(bot))