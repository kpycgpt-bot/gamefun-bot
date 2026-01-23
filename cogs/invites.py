import discord
from discord.ext import commands
import config
from database import db

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = {i.code: i.uses for i in await guild.invites()}
            except:
                continue

    @commands.command()
    async def myinvite(self, ctx):
        """Создает индивидуальную ссылку."""
        guild = ctx.guild
        existing_invites = await guild.invites()
        
        # Получаем данные пользователя заранее
        user_data = await db.get_user(ctx.author.id)
        
        for invite in existing_invites:
            if invite.inviter == ctx.author and not invite.temporary:
                return await ctx.send(f"✉️ Твоя ссылка: {invite.url}\nПриглашено: **{user_data['invites']}** чел.")

        channel = guild.get_channel(config.WELCOME_CHANNEL) or ctx.channel
        new_invite = await channel.create_invite(reason=f"Индивидуальная ссылка для {ctx.author}", max_age=0)
        
        self.invites_cache[guild.id][new_invite.code] = new_invite.uses
        await ctx.send(f"✅ Твоя новая ссылка: {new_invite.url}\nТеперь ты можешь приглашать друзей!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild.id not in self.invites_cache: return

        new_invites = await guild.invites()
        old_invites = self.invites_cache[guild.id]

        inviter = None
        for invite in new_invites:
            if invite.code in old_invites and invite.uses > old_invites[invite.code]:
                inviter = invite.inviter
                self.invites_cache[guild.id][invite.code] = invite.uses
                break
        
        if inviter and not inviter.bot:
            # 🔥 await регистрации реферала
            success = await db.add_referral(inviter.id, member.id)
            if success:
                await db.add_coins(inviter.id, 50) 
                log_channel = guild.get_channel(config.LOG_CHANNEL)
                if log_channel:
                    await log_channel.send(f"📈 **{inviter}** пригласил **{member}**. Начислено 50 монет!")

async def setup(bot):
    await bot.add_cog(Invites(bot))