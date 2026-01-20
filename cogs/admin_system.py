import discord
from discord.ext import commands
import sys
import os
import traceback

class AdminControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    # --- КРАСНАЯ КНОПКА (ПОЛНЫЙ РЕСТАРТ) ---
    @discord.ui.button(label="💀 ПОЛНЫЙ РЕСТАРТ", style=discord.ButtonStyle.danger, emoji="🔌", row=0)
    async def restart_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Не трогай, это для админов!", ephemeral=True)

        await interaction.response.send_message("🔌 **Перезагрузка систем...**\nБот вернется через 5 секунд!", ephemeral=False)
        print(f"[RESTART] Команду запросил {interaction.user}")
        
        # --- ДОБАВЬ ВОТ ЭТУ СТРОЧКУ НИЖЕ ---
        import asyncio
        await asyncio.sleep(1) # Даем боту 1 секунду, чтобы отправить сообщение перед смертью
        # -----------------------------------

        sys.exit(0)

    # --- СИНЯЯ КНОПКА (МЯГКАЯ ПЕРЕЗАГРУЗКА) ---
    @discord.ui.button(label="♻️ Обновить код", style=discord.ButtonStyle.primary, row=0)
    async def reload_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return

        # Сразу говорим Дискорду "подожди", чтобы не было ошибки взаимодействия
        await interaction.response.defer(ephemeral=True)

        log_text = ""
        error_count = 0
        success_count = 0

        # Перебираем все файлы в папке cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                extension_name = f'cogs.{filename[:-3]}'
                try:
                    # Пытаемся перезагрузить модуль
                    await self.bot.reload_extension(extension_name)
                    success_count += 1
                except Exception as e:
                    # Если ошибка - записываем её
                    error_count += 1
                    log_text += f"❌ **{filename}**: {e}\n"
                    print(f"Ошибка в {filename}: {e}")

        # Формируем отчет
        embed = discord.Embed(title="📊 Отчет обновления", color=0x00FF00 if error_count == 0 else 0xFF0000)
        embed.add_field(name="Успешно", value=f"✅ {success_count} модулей", inline=True)
        
        if error_count > 0:
            embed.add_field(name="Ошибки", value=f"🚫 {error_count} модулей", inline=True)
            embed.description = f"**Детали ошибок:**\n{log_text}"
        else:
            embed.description = "Все системы работают нормально!"

        await interaction.followup.send(embed=embed, ephemeral=True)

class AdminSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel")
    @commands.has_permissions(administrator=True)
    async def admin_panel(self, ctx):
        embed = discord.Embed(
            title="🛡️ ЦЕНТР УПРАВЛЕНИЯ",
            description="**💀 Полный Рестарт** — Выключить и включить (Надежно)\n**♻️ Обновить код** — Быстро обновить без выключения",
            color=0x2b2d31
        )
        await ctx.send(embed=embed, view=AdminControlView(self.bot))

async def setup(bot):
    await bot.add_cog(AdminSystem(bot))