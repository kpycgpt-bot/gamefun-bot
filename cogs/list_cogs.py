import os
from discord.ext import commands

class ListCogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def listcogs(self, ctx):
        """Показывает список файлов в директории /cogs."""
        folder = "cogs"
        files = os.listdir(folder)
        formatted = "\n".join(f"- {f}" for f in files)
        await ctx.send(f"**Файлы в папке /cogs:**\n{formatted}")

async def setup(bot):
    await bot.add_cog(ListCogs(bot))
