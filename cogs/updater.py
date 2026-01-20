import discord
from discord.ext import commands
import os

class Updater(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reloadall")
    @commands.has_permissions(administrator=True)
    async def reload_all(self, ctx):
        """🔄 Автоматически перезагружает все модули в папке cogs."""
        reloaded = []
        failed = []

        # Сканируем папку cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                cog_name = f'cogs.{filename[:-3]}'
                try:
                    # Пытаемся перезагрузить модуль
                    await self.bot.reload_extension(cog_name)
                    reloaded.append(f"✅ `{filename}`")
                except Exception as e:
                    failed.append(f"❌ `{filename}`: {str(e)[:50]}...")

        embed = discord.Embed(
            title="🔄 Массовое обновление модулей",
            description=f"Бот просканировал папку и обновил расширения.",
            color=discord.Color.gold()
        )

        if reloaded:
            embed.add_field(name="Успешно обновлено:", value="\n".join(reloaded), inline=False)
        
        if failed:
            embed.add_field(name="Ошибки (проверьте код):", value="\n".join(failed), inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Updater(bot))