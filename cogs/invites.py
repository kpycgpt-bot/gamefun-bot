import discord
from discord.ext import commands
import config
from database import db

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Кэш приглашений: {guild_id: {invite_code: uses}}
        self.invites_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        # Заполняем кэш при запуске
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = {i.code: i.uses for i in await guild.invites()}
            except:
                continue

    @commands.command()
    async def myinvite(self, ctx):
        """Создает индивидуальную ссылку для пользователя."""
        guild = ctx.guild
        # Ищем, нет ли уже созданной ссылки этим пользователем
        existing_invites = await guild.invites()
        for invite in existing_invites:
            if invite.inviter == ctx.author and not invite.temporary:
                return await ctx.send(f"✉️ Твоя ссылка: {invite.url}\nПриглашено: **{db.get_user(ctx.author.id)['invites']}** чел.")

        # Если нет, создаем новую (бессрочную) в приветственный канал
        channel = guild.get_channel(config.WELCOME_CHANNEL) or ctx.channel
        new_invite = await channel.create_invite(reason=f"Индивидуальная ссылка для {ctx.author}", max_age=0)
        
        # Обновляем кэш, чтобы бот знал о новой ссылке
        self.invites_cache[guild.id][new_invite.code] = new_invite.uses
        
        await ctx.send(f"✅ Твоя новая ссылка: {new_invite.url}\nТеперь ты можешь приглашать друзей!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild.id not in self.invites_cache:
            return

        # Получаем обновленный список приглашений
        new_invites = await guild.invites()
        old_invites = self.invites_cache[guild.id]

        inviter = None
        for invite in new_invites:
            # Ищем, у какой ссылки увеличилось число использований
            if invite.code in old_invites and invite.uses > old_invites[invite.code]:
                inviter = invite.inviter
                # Обновляем кэш для этого кода
                self.invites_cache[guild.id][invite.code] = invite.uses
                break
        
        # Если нашли пригласившего, проверяем на абуз через БД
        if inviter and not inviter.bot:
            success = db.add_referral(inviter.id, member.id)
            if success:
                # Можно выдать награду (монеты или XP)
                db.add_coins(inviter.id, 50) 
                log_channel = guild.get_channel(config.LOG_CHANNEL)
                if log_channel:
                    await log_channel.send(f"📈 **{inviter}** пригласил **{member}**. Начислено 50 монет!")
            else:
                # Это повторный вход или абуз
                pass

async def setup(bot):
    await bot.add_cog(Invites(bot))