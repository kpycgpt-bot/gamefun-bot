import discord
from discord.ext import commands
from database import db
import config

SHOP_ITEMS = {
    "vip": {"price": 500, "role_name": "💎 Окрылённый Поддерживатель", "desc": "Уникальная роль поддержки сервера"},
    "legend": {"price": 2000, "role_name": "🏆🔥 Легенда Архонтов", "desc": "Статус легенды и уважение"},
    "rich": {"price": 5000, "role_name": "🥇 Избранный Реалма", "desc": "Самая дорогая роль для элиты"}
}

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop")
    async def show_shop(self, ctx):
        # 🔥 await получения данных
        user_data = await db.get_user(ctx.author.id)
        user_balance = user_data['coins']
        
        embed = discord.Embed(
            title="🛒 МАГАЗИН РОЛЕЙ",
            description=f"# 💰 Твой баланс: {user_balance}\n\n👇 **КАК КУПИТЬ?**\nПиши команду: `!buy код`",
            color=discord.Color.gold()
        )

        for item_key, info in SHOP_ITEMS.items():
            price_text = f"### 💸 Цена: {info['price']} монет"
            embed.add_field(
                name=f"🏷️ ТОВАР: {info['role_name']}",
                value=f"{price_text}\n**Код для покупки:** `{item_key}`\n📜 *{info['desc']}*\n----------------",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy_item(self, ctx, item_code: str = None):
        if not item_code:
            return await ctx.send("❌ **Ошибка!** Пиши так: `!buy vip`")

        item_code = item_code.lower()
        if item_code not in SHOP_ITEMS:
            return await ctx.send("❌ Такого товара нет в магазине.")

        item = SHOP_ITEMS[item_code]
        price = item["price"]
        role_name = item["role_name"]
        
        # 1. Проверка баланса (async)
        user_data = await db.get_user(ctx.author.id)
        if user_data["coins"] < price:
            return await ctx.send(f"❌ **Не хватает денег!**\nНужно: {price} 💰\nУ тебя: {user_data['coins']} 💰")

        # 2. Проверка роли
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"⚠️ Ошибка админа: Роль '{role_name}' не создана!")
        
        if role in ctx.author.roles:
            return await ctx.send("❌ У тебя уже есть эта роль!")

        # 3. Покупка
        try:
            # 🔥 await списания
            await db.add_coins(ctx.author.id, -price)
            await ctx.author.add_roles(role)
            
            embed = discord.Embed(
                title="🛍️ Успешная покупка!",
                description=f"# ✅ ТЫ КУПИЛ РОЛЬ!\nТы потратил **{price}** монет и получил: **{role.mention}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Ошибка прав: Роль бота должна быть ВЫШЕ продаваемой роли!")

async def setup(bot):
    await bot.add_cog(Shop(bot))