import discord
from discord.ext import commands
import random
import asyncio
from database import db
from utils import EmbedBuilder, cooldown_manager, format_number
from config import Config
import logging

logger = logging.getLogger('DiscordBot.Casino')

class Casino(commands.Cog):
    """Казино: блэкджек, рулетка, слоты"""
    
    def __init__(self, bot):
        self.bot = bot
        # Активные игры (чтобы не было дублирования)
        self.active_games = {}
        logger.info("✅ Casino инициализирован")
    
    # ==========================================
    # 🎰 СЛОТЫ
    # ==========================================
    
    @commands.command(name='slots', aliases=['слоты'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def slots(self, ctx, bet: int):
        """
        🎰 Игровой автомат (слоты)
        
        Использование:
        !slots 100 - ставка 100 монет
        
        Выигрыши:
        🍒🍒🍒 - x10
        🍋🍋🍋 - x5
        🍊🍊🍊 - x3
        Две одинаковые - x2
        """
        if bet < 10:
            embed = EmbedBuilder.error("Ошибка", "Минимальная ставка: 10 монет")
            return await ctx.send(embed=embed, delete_after=5)
        
        user_data = await db.get_user(ctx.author.id)
        
        if user_data['coins'] < bet:
            needed = bet - user_data['coins']
            embed = EmbedBuilder.error(
                "Недостаточно монет",
                f"Нужно еще {format_number(needed)} {Config.EMOJI_COIN}"
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        # Символы слотов
        symbols = ['🍒', '🍋', '🍊', '🍇', '🍉', '⭐', '💎']
        
        # Анимация
        embed = discord.Embed(
            title="🎰 СЛОТЫ",
            description="🎲 Крутим барабаны...",
            color=Config.COLOR_INFO
        )
        msg = await ctx.send(embed=embed)
        
        await asyncio.sleep(1)
        
        # Результат
        result = [random.choice(symbols) for _ in range(3)]
        
        # Расчет выигрыша
        multiplier = 0
        
        if result[0] == result[1] == result[2]:
            # Три одинаковых
            if result[0] == '🍒':
                multiplier = 10
            elif result[0] == '💎':
                multiplier = 20
            elif result[0] == '⭐':
                multiplier = 15
            else:
                multiplier = 5
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            # Две одинаковых
            multiplier = 2
        
        winnings = int(bet * multiplier) - bet
        
        # Обновляем баланс
        await db.add_coins(ctx.author.id, winnings)
        
        # Результат
        result_text = f"**{result[0]} | {result[1]} | {result[2]}**"
        
        if winnings > 0:
            embed = EmbedBuilder.success(
                "🎰 ВЫИГРЫШ!",
                f"{result_text}\n\n"
                f"Множитель: **x{multiplier}**\n"
                f"Выигрыш: **+{format_number(winnings)}** {Config.EMOJI_COIN}"
            )
        elif winnings == 0:
            embed = EmbedBuilder.warning(
                "🎰 НИЧЬЯ",
                f"{result_text}\n\n"
                f"Ставка возвращена"
            )
        else:
            embed = EmbedBuilder.error(
                "🎰 ПРОИГРЫШ",
                f"{result_text}\n\n"
                f"Потеряно: **{format_number(bet)}** {Config.EMOJI_COIN}"
            )
        
        user_data = await db.get_user(ctx.author.id)
        embed.set_footer(text=f"Баланс: {format_number(user_data['coins'])} монет")
        
        await msg.edit(embed=embed)
        logger.info(f"{ctx.author} сыграл в слоты: ставка {bet}, результат {winnings}")
    
    # ==========================================
    # 🎲 РУЛЕТКА
    # ==========================================
    
    @commands.command(name='roulette', aliases=['рулетка'])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def roulette(self, ctx, bet: int, choice: str):
        """
        🎲 Рулетка
        
        Использование:
        !roulette 100 red - ставка на красное
        !roulette 100 black - ставка на черное
        !roulette 100 green - ставка на зеленое (0)
        !roulette 100 15 - ставка на число
        
        Выигрыши:
        Красное/Черное - x2
        Зеленое (0) - x14
        Число - x36
        """
        if bet < 10:
            embed = EmbedBuilder.error("Ошибка", "Минимальная ставка: 10 монет")
            return await ctx.send(embed=embed, delete_after=5)
        
        user_data = await db.get_user(ctx.author.id)
        
        if user_data['coins'] < bet:
            needed = bet - user_data['coins']
            embed = EmbedBuilder.error(
                "Недостаточно монет",
                f"Нужно еще {format_number(needed)} {Config.EMOJI_COIN}"
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        choice = choice.lower()
        
        # Проверка ставки
        valid_choices = ['red', 'black', 'green', 'красное', 'черное', 'зеленое']
        
        if choice.isdigit():
            number_bet = int(choice)
            if number_bet < 0 or number_bet > 36:
                embed = EmbedBuilder.error("Ошибка", "Число должно быть от 0 до 36")
                return await ctx.send(embed=embed, delete_after=5)
        elif choice not in valid_choices:
            embed = EmbedBuilder.error(
                "Ошибка",
                "Выбери: `red/black/green` или число `0-36`"
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        # Крутим рулетку
        embed = discord.Embed(
            title="🎲 РУЛЕТКА",
            description="🌀 Шарик крутится...",
            color=Config.COLOR_INFO
        )
        msg = await ctx.send(embed=embed)
        
        await asyncio.sleep(2)
        
        # Результат
        result_number = random.randint(0, 36)
        
        # Определяем цвет
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        
        if result_number == 0:
            result_color = "green"
            color_emoji = "🟢"
        elif result_number in red_numbers:
            result_color = "red"
            color_emoji = "🔴"
        else:
            result_color = "black"
            color_emoji = "⚫"
        
        # Проверяем выигрыш
        won = False
        multiplier = 0
        
        if choice.isdigit() and int(choice) == result_number:
            won = True
            multiplier = 36
        elif choice in ['red', 'красное'] and result_color == 'red':
            won = True
            multiplier = 2
        elif choice in ['black', 'черное'] and result_color == 'black':
            won = True
            multiplier = 2
        elif choice in ['green', 'зеленое'] and result_color == 'green':
            won = True
            multiplier = 14
        
        if won:
            winnings = bet * multiplier - bet
            await db.add_coins(ctx.author.id, winnings)
            
            embed = EmbedBuilder.success(
                "🎲 ВЫИГРЫШ!",
                f"Результат: {color_emoji} **{result_number}**\n\n"
                f"Множитель: **x{multiplier}**\n"
                f"Выигрыш: **+{format_number(winnings)}** {Config.EMOJI_COIN}"
            )
        else:
            await db.add_coins(ctx.author.id, -bet)
            
            embed = EmbedBuilder.error(
                "🎲 ПРОИГРЫШ",
                f"Результат: {color_emoji} **{result_number}**\n\n"
                f"Потеряно: **{format_number(bet)}** {Config.EMOJI_COIN}"
            )
        
        user_data = await db.get_user(ctx.author.id)
        embed.set_footer(text=f"Баланс: {format_number(user_data['coins'])} монет")
        
        await msg.edit(embed=embed)
        logger.info(f"{ctx.author} сыграл в рулетку: ставка {bet} на {choice}, результат {result_number}")
    
    # ==========================================
    # 🃏 БЛЭКДЖЕК
    # ==========================================
    
    @commands.command(name='blackjack', aliases=['bj', 'блэкджек'])
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int):
        """
        🃏 Блэкджек (21)
        
        Использование:
        !blackjack 100 - ставка 100 монет
        
        Правила:
        • Цель: набрать 21 или ближе к 21, чем дилер
        • Туз = 11 или 1
        • Картинки = 10
        • Блэкджек (21 с двух карт) = x2.5
        """
        if bet < 10:
            embed = EmbedBuilder.error("Ошибка", "Минимальная ставка: 10 монет")
            return await ctx.send(embed=embed, delete_after=5)
        
        user_data = await db.get_user(ctx.author.id)
        
        if user_data['coins'] < bet:
            needed = bet - user_data['coins']
            embed = EmbedBuilder.error(
                "Недостаточно монет",
                f"Нужно еще {format_number(needed)} {Config.EMOJI_COIN}"
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        # Проверяем активную игру
        if ctx.author.id in self.active_games:
            embed = EmbedBuilder.warning("Игра уже идет", "Закончи текущую игру!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Колода
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        def create_deck():
            return [{'rank': rank, 'suit': suit} for suit in suits for rank in ranks]
        
        def card_value(card):
            if card['rank'] in ['J', 'Q', 'K']:
                return 10
            elif card['rank'] == 'A':
                return 11
            else:
                return int(card['rank'])
        
        def hand_value(hand):
            value = sum(card_value(card) for card in hand)
            aces = sum(1 for card in hand if card['rank'] == 'A')
            
            while value > 21 and aces:
                value -= 10
                aces -= 1
            
            return value
        
        def format_hand(hand):
            return ' '.join([f"{card['rank']}{card['suit']}" for card in hand])
        
        # Раздаем карты
        deck = create_deck()
        random.shuffle(deck)
        
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        player_value = hand_value(player_hand)
        dealer_value = hand_value(dealer_hand)
        
        # Сохраняем игру
        self.active_games[ctx.author.id] = {
            'bet': bet,
            'deck': deck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand
        }
        
        # Проверка на блэкджек
        if player_value == 21:
            winnings = int(bet * 2.5) - bet
            await db.add_coins(ctx.author.id, winnings)
            del self.active_games[ctx.author.id]
            
            embed = discord.Embed(
                title="🃏 БЛЭКДЖЕК!",
                description=f"**Твои карты:** {format_hand(player_hand)} = **21**\n"
                           f"**Карты дилера:** {format_hand(dealer_hand)} = **{dealer_value}**\n\n"
                           f"💰 Выигрыш: **+{format_number(winnings)}** {Config.EMOJI_COIN}",
                color=Config.COLOR_SUCCESS
            )
            return await ctx.send(embed=embed)
        
        # Показываем карты
        embed = discord.Embed(
            title="🃏 БЛЭКДЖЕК",
            description=f"**Твои карты:** {format_hand(player_hand)} = **{player_value}**\n"
                       f"**Карта дилера:** {dealer_hand[0]['rank']}{dealer_hand[0]['suit']} 🎴\n\n"
                       f"Что делаешь?",
            color=Config.COLOR_INFO
        )
        embed.set_footer(text=f"Ставка: {format_number(bet)} монет")
        
        view = BlackjackView(self, ctx.author.id)
        await ctx.send(embed=embed, view=view)
    
    async def blackjack_hit(self, user_id, interaction):
        """Взять карту"""
        game = self.active_games.get(user_id)
        if not game:
            return
        
        # Берем карту
        card = game['deck'].pop()
        game['player_hand'].append(card)
        
        def hand_value(hand):
            value = sum(self.card_value_helper(card) for card in hand)
            aces = sum(1 for card in hand if card['rank'] == 'A')
            while value > 21 and aces:
                value -= 10
                aces -= 1
            return value
        
        def format_hand(hand):
            return ' '.join([f"{card['rank']}{card['suit']}" for card in hand])
        
        player_value = hand_value(game['player_hand'])
        
        # Перебор
        if player_value > 21:
            await db.add_coins(user_id, -game['bet'])
            del self.active_games[user_id]
            
            embed = EmbedBuilder.error(
                "🃏 ПЕРЕБОР!",
                f"**Твои карты:** {format_hand(game['player_hand'])} = **{player_value}**\n\n"
                f"💸 Потеряно: **{format_number(game['bet'])}** {Config.EMOJI_COIN}"
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        # Обновляем
        embed = discord.Embed(
            title="🃏 БЛЭКДЖЕК",
            description=f"**Твои карты:** {format_hand(game['player_hand'])} = **{player_value}**\n"
                       f"**Карта дилера:** {game['dealer_hand'][0]['rank']}{game['dealer_hand'][0]['suit']} 🎴",
            color=Config.COLOR_INFO
        )
        
        view = BlackjackView(self, user_id)
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def blackjack_stand(self, user_id, interaction):
        """Остановиться"""
        game = self.active_games.get(user_id)
        if not game:
            return
        
        def hand_value(hand):
            value = sum(self.card_value_helper(card) for card in hand)
            aces = sum(1 for card in hand if card['rank'] == 'A')
            while value > 21 and aces:
                value -= 10
                aces -= 1
            return value
        
        def format_hand(hand):
            return ' '.join([f"{card['rank']}{card['suit']}" for card in hand])
        
        # Дилер берет карты
        while hand_value(game['dealer_hand']) < 17:
            game['dealer_hand'].append(game['deck'].pop())
        
        player_value = hand_value(game['player_hand'])
        dealer_value = hand_value(game['dealer_hand'])
        
        # Определяем победителя
        if dealer_value > 21 or player_value > dealer_value:
            winnings = game['bet']
            await db.add_coins(user_id, winnings)
            result_text = "ПОБЕДА!"
            result_color = Config.COLOR_SUCCESS
            result_emoji = "🎉"
        elif player_value == dealer_value:
            winnings = 0
            result_text = "НИЧЬЯ"
            result_color = Config.COLOR_WARNING
            result_emoji = "🤝"
        else:
            winnings = -game['bet']
            await db.add_coins(user_id, winnings)
            result_text = "ПРОИГРЫШ"
            result_color = Config.COLOR_ERROR
            result_emoji = "😢"
        
        del self.active_games[user_id]
        
        embed = discord.Embed(
            title=f"🃏 {result_text} {result_emoji}",
            description=f"**Твои карты:** {format_hand(game['player_hand'])} = **{player_value}**\n"
                       f"**Карты дилера:** {format_hand(game['dealer_hand'])} = **{dealer_value}**\n\n"
                       f"{'💰 Выигрыш' if winnings > 0 else '💸 Потеряно' if winnings < 0 else '🤝 Возврат'}: "
                       f"**{format_number(abs(winnings))}** {Config.EMOJI_COIN}",
            color=result_color
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    def card_value_helper(self, card):
        """Вспомогательная функция для значения карты"""
        if card['rank'] in ['J', 'Q', 'K']:
            return 10
        elif card['rank'] == 'A':
            return 11
        else:
            return int(card['rank'])

class BlackjackView(discord.ui.View):
    """Кнопки для блэкджека"""
    
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
    
    @discord.ui.button(label="🃏 Взять карту", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не твоя игра!", ephemeral=True)
            return
        await self.cog.blackjack_hit(self.user_id, interaction)
    
    @discord.ui.button(label="✋ Остановиться", style=discord.ButtonStyle.success)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не твоя игра!", ephemeral=True)
            return
        await self.cog.blackjack_stand(self.user_id, interaction)

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Casino(bot))
