import discord
from discord.ext import commands
from database import db
import random

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.member) 

    def get_ratelimit(self, message: discord.Message):
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if self.get_ratelimit(message): return 

        xp_gain = random.randint(5, 15)
        
        # 🔥 await получения данных
        user_data = await db.get_user(message.author.id)
        
        current_xp = user_data['xp'] + xp_gain
        current_level = user_data['level']
        xp_needed = current_level * 100

        if current_xp >= xp_needed:
            current_xp -= xp_needed
            current_level += 1
            
            # 🔥 await обновления
            await db.update_user(message.author.id, xp=current_xp, level=current_level)
            
            embed = discord.Embed(
                title="🎉 ПОВЫШЕНИЕ УРОВНЯ!",
                description=f"{message.author.mention}, ты достиг **{current_level}-го уровня**! 🚀",
                color=discord.Color.gold()
            )
            reward = current_level * 50
            await db.add_coins(message.author.id, reward)
            embed.set_footer(text=f"Бонус: +{reward} монет")
            
            await message.channel.send(embed=embed)
        else:
            await db.update_user(message.author.id, xp=current_xp)

    @commands.command(name="rank", aliases=["lvl", "level"])
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        # 🔥 await
        user = await db.get_user(member.id)
        
        xp_now = user['xp']
        lvl_now = user['level']
        xp_need = lvl_now * 100
        
        percent = int((xp_now / xp_need) * 10)
        bar = "█" * percent + "░" * (10 - percent)

        embed = discord.Embed(title=f"📊 Ранг: {member.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.add_field(name="Уровень", value=f"**{lvl_now}**", inline=True)
        embed.add_field(name="Опыт", value=f"{xp_now} / {xp_need} XP", inline=True)
        embed.add_field(name="Прогресс", value=f"`[{bar}]`", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="top", aliases=["leaderboard", "lb"])
    async def leaderboard(self, ctx):
        # 🔥 await получения топа
        top_users = await db.get_top_users(10)
        
        if not top_users:
            return await ctx.send("❌ База данных пуста.")

        embed = discord.Embed(title="🏆 ТОП-10 ИГРОКОВ", color=discord.Color.gold())
        description = ""
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, level, xp) in enumerate(top_users):
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f"ID: {user_id}"
            
            prefix = medals[i] if i < 3 else f"**#{i+1}**"
            description += f"{prefix} **{name}** — Ур. {level} ({xp} XP)\n"

        embed.description = description
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))