import discord
from discord.ext import commands
import random
from database import db

RANK_ROLES = [
    ("✨ Искра Начала", 0, 499),
    ("🔥 Огненная Ступень", 500, 1499),
    ("🌪️ Пепельный Шторм", 1500, 2999),
    ("🔥👑 Архонт Пламени+", 3000, 999999),
]

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_rank_role(self, member: discord.Member, xp: int):
        guild = member.guild
        target_role_name = None
        for name, min_xp, max_xp in RANK_ROLES:
            if min_xp <= xp <= max_xp:
                target_role_name = name
                break
        if not target_role_name: return
        target_role = discord.utils.get(guild.roles, name=target_role_name)
        if not target_role: return
        all_rank_names = [r[0] for r in RANK_ROLES]
        roles_to_remove = [r for r in member.roles if r.name in all_rank_names and r.name != target_role_name]
        if roles_to_remove: await member.remove_roles(*roles_to_remove)
        if target_role not in member.roles: await member.add_roles(target_role)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        gained_xp = random.randint(5, 15)
        user_data = db.add_xp(message.author.id, gained_xp)
        await self.update_rank_role(message.author, user_data["xp"])

    @commands.command()
    async def myxp(self, ctx):
        user = db.get_user(ctx.author.id)
        await ctx.send(f"🌟 **{ctx.author.display_name}**, уровень: **{user['level']}** | XP: **{user['xp']}**")

async def setup(bot):
    await bot.add_cog(Levels(bot))