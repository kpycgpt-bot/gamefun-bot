import discord
from discord.ext import commands
from database import db
import random
import time

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.member) 
        # Кулдаун: опыт дается раз в 60 секунд (защита от спама)

    def get_ratelimit(self, message: discord.Message):
        """Проверяет, прошло ли 60 секунд с прошлого сообщения."""
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return # Боты не получают опыт
        
        # Проверка кулдауна (чтобы не фармили спамом)
        retry_after = self.get_ratelimit(message)
        if retry_after: return 

        # 1. Выдаем случайный опыт (от 5 до 15)
        xp_gain = random.randint(5, 15)
        user_data = db.get_user(message.author.id)
        
        current_xp = user_data['xp'] + xp_gain
        current_level = user_data['level']
        
        # 2. Формула уровня: Новый уровень каждые (Level * 100) XP
        # Ур 1 -> 2 нужно 100 xp
        # Ур 2 -> 3 нужно 200 xp
        xp_needed = current_level * 100

        if current_xp >= xp_needed:
            # LEVEL UP! 🎉
            current_xp = current_xp - xp_needed # Остаток переносим
            current_level += 1
            
            # Сохраняем новый уровень
            db.update_user(message.author.id, xp=current_xp, level=current_level)
            
            # Отправляем красивое сообщение
            embed = discord.Embed(
                title="🎉 ПОВЫШЕНИЕ УРОВНЯ!",
                description=f"{message.author.mention}, ты достиг **{current_level}-го уровня**! 🚀",
                color=discord.Color.gold()
            )
            # Иногда можно дать награду деньгами
            reward = current_level * 50
            db.add_coins(message.author.id, reward)
            embed.set_footer(text=f"Бонус: +{reward} монет")
            
            await message.channel.send(embed=embed)
        else:
            # Просто сохраняем опыт
            db.update_user(message.author.id, xp=current_xp)

    # --- КОМАНДА: МОЙ РАНГ ---
    @commands.command(name="rank", aliases=["lvl", "level"])
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = db.get_user(member.id)
        
        xp_now = user['xp']
        lvl_now = user['level']
        xp_need = lvl_now * 100
        
        # Рисуем прогресс бар [████░░░░░░]
        percent = int((xp_now / xp_need) * 10)
        bar = "█" * percent + "░" * (10 - percent)

        embed = discord.Embed(title=f"📊 Ранг: {member.name}", color=discord.Color.blue())
        embed.add_field(name="Уровень", value=f"**{lvl_now}**", inline=True)
        embed.add_field(name="Опыт", value=f"{xp_now} / {xp_need} XP", inline=True)
        embed.add_field(name="Прогресс", value=f"`[{bar}]`", inline=False)
        
        await ctx.send(embed=embed)

    # --- КОМАНДА: ТОП ИГРОКОВ ---
    @commands.command(name="top", aliases=["leaderboard"])
    async def leaderboard(self, ctx):
        # Получаем всех из базы и сортируем по уровню (SQL пока не умеет сортировать в нашем коде, сделаем Python-ом)
        # В идеале нужно добавить метод get_all_users в database.py, но пока сделаем хитро
        # Сейчас команда топ будет работать, только если добавить функцию в DB.
        # Давай пока оставим без топа, или я дам код для DB ниже.
        await ctx.send("🏆 Таблица лидеров пока на ремонте (нужно обновить базу данных). Пользуйся `!rank`!")

async def setup(bot):
    await bot.add_cog(Levels(bot))