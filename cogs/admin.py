import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ПЕРЕЗАГРУЗКА МОДУЛЯ ---
    @commands.command(name="reload")
    @commands.is_owner() # Только владелец бота может это делать
    async def reload_module(self, ctx, extension):
        """Перезагружает модуль без выключения бота. Пример: !reload shop"""
        try:
            # Сначала пробуем выгрузить, потом загрузить (рестарт модуля)
            await self.bot.reload_extension(f"cogs.{extension}")
            
            embed = discord.Embed(
                title="🔄 Перезагрузка",
                description=f"Модуль **{extension}.py** успешно обновлен!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            print(f"Админ {ctx.author} перезагрузил {extension}")
            
        except commands.ExtensionNotLoaded:
            # Если модуль еще не был загружен, загружаем его
            try:
                await self.bot.load_extension(f"cogs.{extension}")
                await ctx.send(f"✅ Модуль **{extension}** был выключен, но теперь ЗАГРУЖЕН.")
            except Exception as e:
                await ctx.send(f"❌ Ошибка загрузки: `{e}`")

        except Exception as e:
            await ctx.send(f"❌ **ОШИБКА:** Не удалось обновить модуль.\n`{e}`")

    # --- СПИСОК МОДУЛЕЙ ---
    @commands.command(name="cogs")
    @commands.is_owner()
    async def list_cogs(self, ctx):
        """Показывает, какие модули сейчас работают."""
        loaded_extensions = list(self.bot.extensions.keys())
        cogs_list = "\n".join([f"🧩 {ext}" for ext in loaded_extensions])
        
        embed = discord.Embed(
            title="⚙️ Активные модули",
            description=cogs_list,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))