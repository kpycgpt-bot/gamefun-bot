from discord.ext import commands
import discord
from database import db

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def profile(self, ctx):
        # 🔥 Добавлен await
        user = await db.get_user(ctx.author.id)
        embed = discord.Embed(
            title=f"Профиль {ctx.author.display_name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Уровень", value=user["level"])
        embed.add_field(name="XP", value=user["xp"])
        embed.add_field(name="Монеты", value=user["coins"])
        await ctx.send(embed=embed)

    @commands.command()
    async def farm(self, ctx):
        # 🔥 Добавлены await
        await db.add_xp(ctx.author.id, 10)
        await db.add_coins(ctx.author.id, 5)
        await ctx.send(f"{ctx.author.mention} получил 10 XP и 5 монет.")

async def setup(bot):
    await bot.add_cog(Game(bot))