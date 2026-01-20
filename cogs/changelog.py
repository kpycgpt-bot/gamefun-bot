import discord
from discord.ext import commands
from datetime import datetime

class Changelog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="upd")
    @commands.has_permissions(administrator=True)
    async def update(self, ctx, version: str, *, details: str):
        news_ch = discord.utils.get(ctx.guild.text_channels, name="📢-announcements")
        if not news_ch: return
        
        # Выносим замену символа из f-строки
        fmt_text = details.replace('|', '\n')
        
        embed = discord.Embed(title=f"🚀 ОБНОВЛЕНИЕ {version}", description=fmt_text, color=0x00FF7F)
        await news_ch.send("@everyone", embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Changelog(bot))