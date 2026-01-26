import discord
from discord.ext import commands
from database import db
from utils import EmbedBuilder, format_number
from config import Config
import logging

logger = logging.getLogger('DiscordBot.Invites')

class Invites(commands.Cog):
    """Система отслеживания приглашений"""
    
    def __init__(self, bot):
        self.bot = bot
        self.invites_cache = {}
        logger.info("✅ Invites инициализирован")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Кэширует приглашения при запуске"""
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invites_cache[guild.id] = {invite.code: invite.uses for invite in invites}
            except:
                self.invites_cache[guild.id] = {}
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Отслеживает кто пригласил нового участника"""
        try:
            guild = member.guild
            
            # Получаем новые приглашения
            new_invites = await guild.invites()
            old_invites = self.invites_cache.get(guild.id, {})
            
            # Ищем использованное приглашение
            inviter = None
            for invite in new_invites:
                old_uses = old_invites.get(invite.code, 0)
                if invite.uses > old_uses:
                    inviter = invite.inviter
                    # Обновляем счетчик
                    await db.add_invites(inviter.id, 1)
                    break
            
            # Обновляем кэш
            self.invites_cache[guild.id] = {invite.code: invite.uses for invite in new_invites}
            
            if inviter:
                logger.info(f"{member} приглашен пользователем {inviter}")
                
                # Награда за приглашение
                await db.add_coins(inviter.id, 50)
                
        except Exception as e:
            logger.error(f"Ошибка отслеживания приглашения: {e}", exc_info=True)
    
    @commands.command(name='invites', aliases=['приглашения', 'инвайты'])
    async def invites(self, ctx, member: discord.Member = None):
        """
        📨 Посмотреть количество приглашений
        
        Использование:
        !invites - твои приглашения
        !invites @user - приглашения пользователя
        """
        member = member or ctx.author
        user_data = await db.get_user(member.id)
        
        embed = discord.Embed(
            title=f"📨 Приглашения {member.display_name}",
            description=f"Пригласил на сервер **{user_data['invites']}** человек",
            color=Config.COLOR_INFO
        )
        
        embed.add_field(
            name="🎁 Награды",
            value=f"За каждое приглашение: **+50** {Config.EMOJI_COIN}",
            inline=False
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='inviteleaderboard', aliases=['топинвайтов'])
    async def invite_leaderboard(self, ctx):
        """
        🏆 Топ по приглашениям
        
        Показывает топ-10 пользователей по количеству приглашений
        """
        # Получаем всех пользователей с приглашениями
        async with db.conn.execute(
            "SELECT user_id, invites FROM users WHERE invites > 0 ORDER BY invites DESC LIMIT 10"
        ) as cursor:
            top_inviters = await cursor.fetchall()
        
        if not top_inviters:
            embed = EmbedBuilder.info("Топ приглашений", "Пока никого нет")
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="🏆 Топ по приглашениям",
            color=Config.COLOR_INFO
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, row in enumerate(top_inviters, 1):
            user = self.bot.get_user(row['user_id'])
            if not user:
                continue
            
            medal = medals[idx - 1] if idx <= 3 else f"**#{idx}**"
            
            embed.add_field(
                name=f"{medal} {user.display_name}",
                value=f"Приглашений: **{row['invites']}**",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
