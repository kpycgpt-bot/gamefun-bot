import discord
from discord.ext import commands
from database import db
import config

# --- НАСТРОЙКИ МАГАЗИНА ---
# Формат: "Команда_для_покупки": {"price": Цена, "role_name": "Точное имя роли", "desc": "Описание"}
SHOP_ITEMS = {
    "vip": {
        "price": 500,
        "role_name": "💎 Окрылённый Поддерживатель",
        "desc": "Уникальная роль поддержки сервера"
    },
    "legend": {
        "price": 2000,
        "role_name": "🏆🔥 Легенда Архонтов",
        "desc": "Статус легенды и уважение"
    },
    "rich": {
        "price": 5000,
        "role_name": "🥇 Избранный Реалма",
        "desc": "Самая дорогая роль для элиты"
    }
}

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop")
    async def show_shop(self, ctx):
        """Показывает витрину магазина."""
        embed = discord.Embed(
            title="🛒 МАГАЗИН РОЛЕЙ",
            description=f"Твой баланс: **{db.get_user(ctx.author.id)['coins']} 💰**\nИспользуй `!buy <название>` для покупки.",
            color=discord.Color.gold()
        )

        for item_key, info in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{info['role_name']}",
                value=f"🏷️ Код: `{item_key}`\n💰 Цена: **{info['price']}**\n📜 {info['desc']}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy_item(self, ctx, item_code: str = None):
        """Покупка товара."""
        if not item_code:
            return await ctx.send("❌ Укажите код товара! Например: `!buy vip`")

        item_code = item_code.lower()
        if item_code not in SHOP_ITEMS:
            return await ctx.send("❌ Такого товара нет в магазине.")

        item = SHOP_ITEMS[item_code]
        price = item["price"]
        role_name = item["role_name"]
        
        # 1. Проверка баланса
        user_data = db.get_user(ctx.author.id)
        if user_data["coins"] < price:
            return await ctx.send(f"❌ Недостаточно средств! Нужно: {price}, у тебя: {user_data['coins']}.")

        # 2. Проверка роли (есть ли она уже?)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"⚠️ Ошибка: Роль '{role_name}' не найдена на сервере. Зови админа!")
        
        if role in ctx.author.roles:
            return await ctx.send("❌ У тебя уже есть эта роль!")

        # 3. Покупка (Списание денег + Выдача роли)
        try:
            # Списываем монеты (добавляем отрицательную сумму)
            db.add_coins(ctx.author.id, -price)
            await ctx.author.add_roles(role)
            
            embed = discord.Embed(
                title="🛍️ Успешная покупка!",
                description=f"Ты купил роль **{role.mention}** за **{price}** монет.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Ошибка прав: Роль бота должна быть ВЫШЕ продаваемой роли!")

async def setup(bot):
    await bot.add_cog(Shop(bot))