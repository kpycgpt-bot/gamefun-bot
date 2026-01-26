import discord
from discord.ext import commands
import asyncio
import random
from database import db
from utils import EmbedBuilder, Paginator, cooldown_manager, format_number, get_progress_bar
from config import Config
import logging

logger = logging.getLogger('DiscordBot.Economy')

class Economy(commands.Cog):
    """Система экономики: монеты, магазин, инвентарь"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ Economy инициализирован")
    
    @commands.command(name='balance', aliases=['bal', 'баланс'])
    async def balance(self, ctx, member: discord.Member = None):
        """
        💰 Посмотреть баланс
        
        Использование:
        !balance - твой баланс
        !balance @user - баланс другого пользователя
        """
        member = member or ctx.author
        user_data = await db.get_user(member.id)
        
        embed = discord.Embed(
            title=f"💰 Баланс {member.display_name}",
            color=Config.COLOR_INFO
        )
        
        embed.add_field(
            name=f"{Config.EMOJI_COIN} Монеты",
            value=f"**{format_number(user_data['coins'])}** монет",
            inline=True
        )
        
        embed.add_field(
            name=f"{Config.EMOJI_XP} Уровень",
            value=f"**{user_data['level']}** lvl",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Опыт",
            value=f"**{format_number(user_data['xp'])}** XP",
            inline=True
        )
        
        # Прогресс до следующего уровня
        current_xp = user_data['xp']
        next_level_xp = Config.get_xp_for_level(user_data['level'])
        progress = get_progress_bar(current_xp, next_level_xp)
        
        embed.add_field(
            name="📊 Прогресс до следующего уровня",
            value=f"{progress}\n{format_number(current_xp)}/{format_number(next_level_xp)} XP",
            inline=False
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='daily', aliases=['ежедневно'])
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 1 раз в 24 часа
    async def daily(self, ctx):
        """
        🎁 Получить ежедневную награду
        
        Награда: 100-500 монет
        Кулдаун: 24 часа
        """
        # Случайная награда от 100 до 500
        reward = random.randint(100, 500)
        
        # Добавляем монеты
        await db.add_coins(ctx.author.id, reward)
        
        embed = EmbedBuilder.success(
            "🎁 Ежедневная награда получена!",
            f"Ты получил **{format_number(reward)}** {Config.EMOJI_COIN} монет!\n\n"
            f"Возвращайся через 24 часа за новой наградой!"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} получил daily reward: {reward} монет")
    
    @daily.error
    async def daily_error(self, ctx, error):
        """Обработка ошибки кулдауна"""
        if isinstance(error, commands.CommandOnCooldown):
            hours = int(error.retry_after // 3600)
            minutes = int((error.retry_after % 3600) // 60)
            
            embed = EmbedBuilder.warning(
                "⏰ Ежедневная награда уже получена",
                f"Возвращайся через **{hours}ч {minutes}м**"
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='work', aliases=['работа'])
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 раз в час
    async def work(self, ctx):
        """
        💼 Поработать за монеты
        
        Награда: 50-150 монет
        Кулдаун: 1 час
        """
        jobs = [
            ("программистом", "💻"),
            ("врачом", "⚕️"),
            ("строителем", "🏗️"),
            ("поваром", "👨‍🍳"),
            ("учителем", "👨‍🏫"),
            ("художником", "🎨"),
            ("музыкантом", "🎵"),
            ("водителем", "🚗"),
        ]
        
        job, emoji = random.choice(jobs)
        reward = random.randint(50, 150)
        
        await db.add_coins(ctx.author.id, reward)
        
        embed = EmbedBuilder.success(
            f"{emoji} Ты поработал {job}",
            f"Заработано: **{format_number(reward)}** {Config.EMOJI_COIN} монет"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} поработал и получил {reward} монет")
    
    @work.error
    async def work_error(self, ctx, error):
        """Обработка ошибки кулдауна"""
        if isinstance(error, commands.CommandOnCooldown):
            minutes = int(error.retry_after // 60)
            seconds = int(error.retry_after % 60)
            
            embed = EmbedBuilder.warning(
                "😴 Ты устал",
                f"Отдохни еще **{minutes}м {seconds}с** перед следующей работой"
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='shop', aliases=['магазин'])
    async def shop(self, ctx):
        """
        🛒 Открыть магазин предметов
        
        Посмотреть доступные предметы для покупки
        """
        embed = discord.Embed(
            title="🛒 Магазин",
            description="Купи улучшения и предметы за монеты!\n\n"
                       f"Используй: `{Config.PREFIX}buy <предмет>`",
            color=Config.COLOR_INFO
        )
        
        for item_id, item_data in Config.SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item_data['emoji']} {item_data['name']}",
                value=f"{item_data['description']}\n"
                     f"**Цена:** {format_number(item_data['price'])} {Config.EMOJI_COIN}\n"
                     f"**ID:** `{item_id}`",
                inline=False
            )
        
        user_data = await db.get_user(ctx.author.id)
        embed.set_footer(text=f"Твой баланс: {format_number(user_data['coins'])} монет")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='buy', aliases=['купить'])
    async def buy(self, ctx, item_id: str):
        """
        💳 Купить предмет из магазина
        
        Использование:
        !buy role_color - купить цветную роль
        !buy xp_boost - купить XP буст
        """
        # Проверяем существование предмета
        if item_id not in Config.SHOP_ITEMS:
            embed = EmbedBuilder.error(
                "Предмет не найден",
                f"Используй `{Config.PREFIX}shop` чтобы посмотреть доступные предметы"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        item_data = Config.SHOP_ITEMS[item_id]
        user_data = await db.get_user(ctx.author.id)
        
        # Проверяем баланс
        if user_data['coins'] < item_data['price']:
            needed = item_data['price'] - user_data['coins']
            embed = EmbedBuilder.error(
                "Недостаточно монет",
                f"Нужно еще **{format_number(needed)}** {Config.EMOJI_COIN} монет"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        # Снимаем монеты
        await db.add_coins(ctx.author.id, -item_data['price'])
        
        # Добавляем предмет в инвентарь
        await db.add_item(ctx.author.id, item_id, 1)
        
        embed = EmbedBuilder.success(
            "✅ Покупка успешна!",
            f"Куплено: {item_data['emoji']} **{item_data['name']}**\n"
            f"Потрачено: **{format_number(item_data['price'])}** {Config.EMOJI_COIN}\n\n"
            f"Предмет добавлен в твой инвентарь!"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} купил {item_id} за {item_data['price']} монет")
    
    @commands.command(name='inventory', aliases=['inv', 'инвентарь'])
    async def inventory(self, ctx, member: discord.Member = None):
        """
        🎒 Посмотреть инвентарь
        
        Использование:
        !inventory - твой инвентарь
        !inventory @user - инвентарь другого игрока
        """
        member = member or ctx.author
        inventory = await db.get_inventory(member.id)
        
        if not inventory:
            embed = EmbedBuilder.info(
                "🎒 Инвентарь пуст",
                f"Купи предметы в магазине: `{Config.PREFIX}shop`"
            )
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title=f"🎒 Инвентарь {member.display_name}",
            color=Config.COLOR_INFO
        )
        
        for item in inventory:
            item_id = item['item_id']
            count = item['count']
            
            # Получаем данные предмета из конфига
            if item_id in Config.SHOP_ITEMS:
                item_data = Config.SHOP_ITEMS[item_id]
                embed.add_field(
                    name=f"{item_data['emoji']} {item_data['name']}",
                    value=f"Количество: **{count}**\n{item_data['description']}",
                    inline=False
                )
            else:
                # Неизвестный предмет
                embed.add_field(
                    name=f"❓ {item_id}",
                    value=f"Количество: **{count}**",
                    inline=False
                )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Всего предметов: {len(inventory)}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='give', aliases=['передать'])
    async def give(self, ctx, member: discord.Member, amount: int):
        """
        💸 Передать монеты другому игроку
        
        Использование:
        !give @user 100 - передать 100 монет пользователю
        """
        # Проверки
        if member.bot:
            embed = EmbedBuilder.error("Ошибка", "Нельзя передавать монеты ботам!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if member.id == ctx.author.id:
            embed = EmbedBuilder.error("Ошибка", "Нельзя передать монеты самому себе!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if amount <= 0:
            embed = EmbedBuilder.error("Ошибка", "Сумма должна быть больше 0!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Проверяем баланс отправителя
        sender_data = await db.get_user(ctx.author.id)
        if sender_data['coins'] < amount:
            needed = amount - sender_data['coins']
            embed = EmbedBuilder.error(
                "Недостаточно монет",
                f"Нужно еще **{format_number(needed)}** {Config.EMOJI_COIN} монет"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        # Переводим монеты
        await db.add_coins(ctx.author.id, -amount)
        await db.add_coins(member.id, amount)
        
        embed = EmbedBuilder.success(
            "💸 Перевод успешен!",
            f"{ctx.author.mention} → {member.mention}\n"
            f"Сумма: **{format_number(amount)}** {Config.EMOJI_COIN}"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} передал {amount} монет {member}")
    
    @commands.command(name='top', aliases=['leaderboard', 'топ'])
    async def leaderboard(self, ctx):
        """
        🏆 Топ игроков по уровню
        
        Показывает 10 лучших игроков сервера
        """
        top_users = await db.get_top_users(limit=10)
        
        if not top_users:
            embed = EmbedBuilder.info("Топ игроков", "Пока никого нет в топе")
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="🏆 Топ игроков сервера",
            description="Лучшие 10 игроков по уровню",
            color=Config.COLOR_INFO
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, user_data in enumerate(top_users, 1):
            user = self.bot.get_user(user_data['user_id'])
            if not user:
                continue
            
            medal = medals[idx - 1] if idx <= 3 else f"#{idx}"
            
            embed.add_field(
                name=f"{medal} {user.display_name}",
                value=f"Уровень: **{user_data['level']}** | "
                     f"XP: **{format_number(user_data['xp'])}** | "
                     f"Монеты: **{format_number(user_data['coins'])}**",
                inline=False
            )
        
        embed.set_footer(text=f"Всего игроков: {len(top_users)}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='coinflip', aliases=['cf', 'монетка'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def coinflip(self, ctx, bet: int):
        """
        🎲 Орел или решка - удвой или потеряй ставку
        
        Использование:
        !coinflip 100 - сделать ставку 100 монет
        
        Шанс выигрыша: 50%
        """
        if bet <= 0:
            embed = EmbedBuilder.error("Ошибка", "Ставка должна быть больше 0!")
            return await ctx.send(embed=embed, delete_after=5)
        
        user_data = await db.get_user(ctx.author.id)
        
        if user_data['coins'] < bet:
            needed = bet - user_data['coins']
            embed = EmbedBuilder.error(
                "Недостаточно монет",
                f"Нужно еще **{format_number(needed)}** {Config.EMOJI_COIN}"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        # Бросаем монетку
        result = random.choice([True, False])  # True = выигрыш
        
        if result:
            # Выигрыш
            await db.add_coins(ctx.author.id, bet)
            embed = EmbedBuilder.success(
                "🎉 Ты выиграл!",
                f"Ставка: **{format_number(bet)}** {Config.EMOJI_COIN}\n"
                f"Выигрыш: **{format_number(bet * 2)}** {Config.EMOJI_COIN}"
            )
        else:
            # Проигрыш
            await db.add_coins(ctx.author.id, -bet)
            embed = EmbedBuilder.error(
                "😢 Ты проиграл!",
                f"Потеряно: **{format_number(bet)}** {Config.EMOJI_COIN}"
            )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} сыграл в coinflip: ставка {bet}, результат {'WIN' if result else 'LOSE'}")

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Economy(bot))
