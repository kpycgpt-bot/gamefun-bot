import discord
from discord.ext import commands
from datetime import datetime, timedelta
from database import db
from utils import EmbedBuilder, Paginator, get_progress_bar, format_number, cooldown_manager
from config import Config
import logging
import random

logger = logging.getLogger('DiscordBot.Levels')

class Levels(commands.Cog):
    """Система уровней и опыта"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ Levels инициализирован")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Начисляет XP за сообщения"""
        # Игнорируем ботов и системные сообщения
        if message.author.bot or not message.guild:
            return
        
        # Игнорируем команды
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        
        user_id = message.author.id
        
        # Проверяем кулдаун
        if cooldown_manager.is_on_cooldown(user_id, "xp_gain"):
            return
        
        # Ставим кулдаун
        cooldown_manager.set_cooldown(user_id, "xp_gain", Config.XP_COOLDOWN)
        
        # Начисляем XP
        xp_gain = Config.XP_PER_MESSAGE
        
        # Бонусный XP (10% шанс получить x2)
        if random.random() < 0.1:
            xp_gain *= 2
        
        user_data = await db.get_user(user_id)
        new_xp = user_data['xp'] + xp_gain
        current_level = user_data['level']
        
        # Проверяем повышение уровня
        new_level = Config.get_level_from_xp(new_xp)
        
        await db.update_user(user_id, xp=new_xp, level=new_level)
        
        # Если повысился уровень
        if new_level > current_level:
            await self.handle_level_up(message, message.author, new_level)
    
    async def handle_level_up(self, message: discord.Message, member: discord.Member, new_level: int):
        """Обрабатывает повышение уровня"""
        try:
            # Награда за уровень
            coin_reward = new_level * 50
            await db.add_coins(member.id, coin_reward)
            
            embed = discord.Embed(
                title="🎉 ПОВЫШЕНИЕ УРОВНЯ!",
                description=f"{member.mention} достиг **уровня {new_level}**!",
                color=Config.COLOR_SUCCESS
            )
            
            embed.add_field(
                name="🎁 Награда",
                value=f"+**{coin_reward}** {Config.EMOJI_COIN} монет",
                inline=True
            )
            
            embed.add_field(
                name="⭐ Новый уровень",
                value=f"**{new_level}**",
                inline=True
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await message.channel.send(embed=embed, delete_after=20)
            
            # Проверяем роли за уровень
            await self.check_level_roles(member, new_level)
            
            logger.info(f"{member} достиг уровня {new_level}")
            
        except Exception as e:
            logger.error(f"Ошибка повышения уровня для {member}: {e}", exc_info=True)
    
    async def check_level_roles(self, member: discord.Member, level: int):
        """Выдает роли за достижение уровня"""
        # Настройки ролей за уровни (можно вынести в конфиг)
        level_roles = {
            5: "Новичок",
            10: "Активный",
            25: "Ветеран",
            50: "Легенда",
            100: "Мастер"
        }
        
        if level in level_roles:
            role_name = level_roles[level]
            role = discord.utils.get(member.guild.roles, name=role_name)
            
            if role:
                try:
                    await member.add_roles(role, reason=f"Достигнут уровень {level}")
                    logger.info(f"{member} получил роль {role_name} за уровень {level}")
                except discord.Forbidden:
                    logger.warning(f"Нет прав для выдачи роли {role_name}")
    
    @commands.command(name='rank', aliases=['ранг', 'level', 'lvl'])
    async def rank(self, ctx, member: discord.Member = None):
        """
        📊 Посмотреть свой ранг и прогресс
        
        Использование:
        !rank - твой ранг
        !rank @user - ранг другого пользователя
        """
        member = member or ctx.author
        user_data = await db.get_user(member.id)
        
        # Получаем позицию в топе
        top_users = await db.get_top_users(limit=1000)
        position = None
        for idx, user in enumerate(top_users, 1):
            if user['user_id'] == member.id:
                position = idx
                break
        
        embed = discord.Embed(
            title=f"📊 Ранг {member.display_name}",
            color=member.color or Config.COLOR_INFO
        )
        
        # Уровень
        embed.add_field(
            name="⭐ Уровень",
            value=f"**{user_data['level']}**",
            inline=True
        )
        
        # Позиция в топе
        if position:
            embed.add_field(
                name="🏆 Место в топе",
                value=f"**#{position}**",
                inline=True
            )
        
        # Монеты
        embed.add_field(
            name=f"{Config.EMOJI_COIN} Монеты",
            value=f"**{format_number(user_data['coins'])}**",
            inline=True
        )
        
        # Прогресс до следующего уровня
        current_xp = user_data['xp']
        current_level = user_data['level']
        xp_for_next = Config.get_xp_for_level(current_level + 1)
        xp_for_current = Config.get_xp_for_level(current_level)
        
        # XP от начала текущего уровня
        xp_progress = current_xp - xp_for_current
        xp_needed = xp_for_next - xp_for_current
        
        progress_bar = get_progress_bar(xp_progress, xp_needed, length=15)
        
        embed.add_field(
            name="📈 Прогресс до следующего уровня",
            value=f"{progress_bar}\n"
                 f"**{format_number(xp_progress)}** / **{format_number(xp_needed)}** XP\n"
                 f"Всего XP: **{format_number(current_xp)}**",
            inline=False
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='leaderboard', aliases=['lb', 'топуровни'])
    async def leaderboard(self, ctx):
        """
        🏆 Таблица лидеров по уровням
        
        Показывает топ-10 игроков по уровню и опыту
        """
        top_users = await db.get_top_users(limit=10)
        
        if not top_users:
            embed = EmbedBuilder.info("Таблица лидеров", "Пока никого нет в топе")
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="🏆 Таблица лидеров",
            description="Топ-10 игроков по уровню",
            color=Config.COLOR_INFO
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, user_data in enumerate(top_users, 1):
            user = self.bot.get_user(user_data['user_id'])
            if not user:
                continue
            
            medal = medals[idx - 1] if idx <= 3 else f"**#{idx}**"
            
            embed.add_field(
                name=f"{medal} {user.display_name}",
                value=f"Уровень: **{user_data['level']}** • "
                     f"XP: **{format_number(user_data['xp'])}**\n"
                     f"Монеты: **{format_number(user_data['coins'])}** {Config.EMOJI_COIN}",
                inline=False
            )
        
        embed.set_footer(text=f"Всего игроков: {len(top_users)}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='givexp', aliases=['дать-xp'])
    @commands.has_permissions(administrator=True)
    async def give_xp(self, ctx, member: discord.Member, amount: int):
        """
        ⭐ Выдать XP пользователю (админ)
        
        Использование:
        !givexp @user 1000 - выдать 1000 XP
        
        Требуемые права: Administrator
        """
        if amount <= 0:
            embed = EmbedBuilder.error("Ошибка", "Количество XP должно быть положительным")
            return await ctx.send(embed=embed, delete_after=5)
        
        user_data = await db.get_user(member.id)
        old_level = user_data['level']
        new_xp = user_data['xp'] + amount
        new_level = Config.get_level_from_xp(new_xp)
        
        await db.update_user(member.id, xp=new_xp, level=new_level)
        
        embed = EmbedBuilder.success(
            "XP выдан",
            f"{member.mention} получил **+{format_number(amount)}** XP"
        )
        
        if new_level > old_level:
            embed.add_field(
                name="🎉 Повышение уровня!",
                value=f"**{old_level}** → **{new_level}**",
                inline=False
            )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} выдал {amount} XP пользователю {member}")
    
    @commands.command(name='removexp', aliases=['забрать-xp'])
    @commands.has_permissions(administrator=True)
    async def remove_xp(self, ctx, member: discord.Member, amount: int):
        """
        ➖ Забрать XP у пользователя (админ)
        
        Использование:
        !removexp @user 500 - забрать 500 XP
        
        Требуемые права: Administrator
        """
        if amount <= 0:
            embed = EmbedBuilder.error("Ошибка", "Количество XP должно быть положительным")
            return await ctx.send(embed=embed, delete_after=5)
        
        user_data = await db.get_user(member.id)
        old_level = user_data['level']
        new_xp = max(0, user_data['xp'] - amount)
        new_level = Config.get_level_from_xp(new_xp)
        
        await db.update_user(member.id, xp=new_xp, level=new_level)
        
        embed = EmbedBuilder.success(
            "XP забран",
            f"У {member.mention} забрано **-{format_number(amount)}** XP"
        )
        
        if new_level < old_level:
            embed.add_field(
                name="⬇️ Понижение уровня",
                value=f"**{old_level}** → **{new_level}**",
                inline=False
            )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} забрал {amount} XP у пользователя {member}")
    
    @commands.command(name='setlevel', aliases=['установить-уровень'])
    @commands.has_permissions(administrator=True)
    async def set_level(self, ctx, member: discord.Member, level: int):
        """
        🎯 Установить уровень пользователю (админ)
        
        Использование:
        !setlevel @user 50 - установить 50 уровень
        
        Требуемые права: Administrator
        """
        if level < 1 or level > 1000:
            embed = EmbedBuilder.error("Ошибка", "Уровень должен быть от 1 до 1000")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Рассчитываем необходимый XP для этого уровня
        xp_for_level = sum(Config.get_xp_for_level(l) for l in range(1, level + 1))
        
        await db.update_user(member.id, xp=xp_for_level, level=level)
        
        embed = EmbedBuilder.success(
            "Уровень установлен",
            f"{member.mention} теперь **{level}** уровня\n"
            f"XP: **{format_number(xp_for_level)}**"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} установил уровень {level} пользователю {member}")
    
    @commands.command(name='resetlevel', aliases=['сброс-уровня'])
    @commands.has_permissions(administrator=True)
    async def reset_level(self, ctx, member: discord.Member):
        """
        🔄 Сбросить уровень пользователя (админ)
        
        Использование:
        !resetlevel @user - сбросить до 1 уровня
        
        Требуемые права: Administrator
        """
        from utils import confirm_action
        
        confirmed = await confirm_action(
            ctx,
            "Сбросить уровень?",
            f"У {member.mention} будет сброшен весь прогресс (уровень и XP)"
        )
        
        if not confirmed:
            return
        
        await db.update_user(member.id, xp=0, level=1)
        
        embed = EmbedBuilder.success(
            "Уровень сброшен",
            f"Прогресс {member.mention} сброшен до **1** уровня"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} сбросил уровень пользователя {member}")
    
    @commands.command(name='levelroles', aliases=['роли-уровней'])
    @commands.has_permissions(administrator=True)
    async def level_roles(self, ctx):
        """
        🎭 Показать роли за уровни
        
        Отображает какие роли выдаются за достижение уровней
        
        Требуемые права: Administrator
        """
        embed = discord.Embed(
            title="🎭 Роли за уровни",
            description="Роли автоматически выдаются при достижении уровня",
            color=Config.COLOR_INFO
        )
        
        level_roles = {
            5: "Новичок",
            10: "Активный",
            25: "Ветеран",
            50: "Легенда",
            100: "Мастер"
        }
        
        for level, role_name in level_roles.items():
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            
            if role:
                value = f"{role.mention} ✅"
            else:
                value = f"⚠️ Роль `{role_name}` не найдена"
            
            embed.add_field(
                name=f"Уровень {level}",
                value=value,
                inline=True
            )
        
        embed.set_footer(text="Создай эти роли на сервере для автоматической выдачи")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Levels(bot))
