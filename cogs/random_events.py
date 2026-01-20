import discord
from discord.ext import commands, tasks
import asyncio
import random
from datetime import datetime, timedelta

# Импорт базы данных
from database import db

class EventView(discord.ui.View):
    def __init__(self, required_clicks, reward, channel_log):
        super().__init__(timeout=None) # Кнопка вечная, пока не нажмут
        self.required_clicks = required_clicks
        self.current_clicks = 0
        self.clicked_users = [] # Список ID тех, кто уже нажал
        self.reward = reward
        self.channel_log = channel_log

    @discord.ui.button(label="🖐️ Участвовать!", style=discord.ButtonStyle.success, emoji="💰")
    async def join_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        # Проверка: нажимал ли уже?
        if user.id in self.clicked_users:
            return await interaction.response.send_message("❌ Ты уже участвуешь! Дай другим тоже нажать.", ephemeral=True)

        # Добавляем участника
        self.clicked_users.append(user.id)
        self.current_clicks += 1
        
        # Выдаем награду сразу (или можно в конце, но сразу приятнее)
        db.add_coins(user.id, self.reward)

        remaining = self.required_clicks - self.current_clicks
        
        # Если нужное количество набралось
        if remaining <= 0:
            # Отключаем кнопку
            for child in self.children:
                child.disabled = True
                child.label = f"✅ Сбор закрыт ({self.required_clicks}/{self.required_clicks})"
            
            await interaction.response.edit_message(view=self)
            
            # Отправляем сообщение об успехе
            await interaction.channel.send(
                f"🎉 **ИВЕНТ ЗАВЕРШЕН!**\n"
                f"🏆 Участники ({len(self.clicked_users)} чел.) получили по **{self.reward}** монет!"
            )
        else:
            # Обновляем кнопку (счетчик)
            button.label = f"🖐️ Участвовать! ({self.current_clicks}/{self.required_clicks})"
            await interaction.response.edit_message(view=self)
            
            # Тихо уведомляем нажавшего
            await interaction.followup.send(f"✅ Ты записался! Получено **{self.reward}** монет. Осталось мест: {remaining}", ephemeral=True)

class RandomEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_loop_task = None

    @commands.Cog.listener()
    async def on_ready(self):
        # Запускаем цикл ивентов при старте бота
        if not self.event_loop_task:
            self.event_loop_task = self.bot.loop.create_task(self.event_loop())

    async def event_loop(self):
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            # 1. Выбираем случайный интервал (1 - 4 часа) в секундах
            # 3600 сек = 1 час, 14400 сек = 4 часа
            wait_seconds = random.randint(3600, 14400)
            
            # Для красоты выводим время в чат "Общение"
            wait_time_str = str(timedelta(seconds=wait_seconds)).split('.')[0] # Убираем миллисекунды
            hours_only = wait_seconds // 3600
            minutes_remain = (wait_seconds % 3600) // 60
            
            chat_channel = discord.utils.get(self.bot.get_all_channels(), name="💬・общение")
            
            if chat_channel:
                embed_hint = discord.Embed(
                    title="🔮 Предсказание Оракула",
                    description=f"Звезды говорят, что следующий **Случайный Ивент** произойдет примерно через:\n⏳ **{hours_only} ч. {minutes_remain} мин.**",
                    color=discord.Color.purple()
                )
                await chat_channel.send(embed=embed_hint)

            # 2. Ждем указанное время
            print(f"[Events] Следующий ивент через {wait_seconds} секунд.")
            await asyncio.sleep(wait_seconds)

            # 3. ЗАПУСК ИВЕНТА
            event_channel = discord.utils.get(self.bot.get_all_channels(), name="🎉・ивенты") or \
                            discord.utils.get(self.bot.get_all_channels(), name="🎉-ивенты")

            if event_channel:
                # Настройки ивента
                required_people = random.randint(1, 10) # 1-10 человек
                reward_coins = random.randint(20, 100)  # Случайная награда
                
                embed = discord.Embed(
                    title="🎁 СЛУЧАЙНЫЙ ДРОП!",
                    description=(
                        f"Появился сундук с сокровищами!\n"
                        f"Нужно собрать **{required_people}** человек(а), чтобы открыть его.\n\n"
                        f"💰 Награда каждому: **{reward_coins} монет**"
                    ),
                    color=discord.Color.gold()
                )
                embed.set_image(url="https://media.tenor.com/J3i5eC5T458AAAAC/treasure-chest.gif") # Гифка сундука
                
                view = EventView(required_people, reward_coins, event_channel)
                await event_channel.send(embed=embed, view=view)
            else:
                print("[!] Ошибка: Канал '🎉・ивенты' не найден!")

    # --- КОМАНДА ДЛЯ АДМИНА (ТЕСТ) ---
    @commands.command(name="testevent")
    @commands.has_permissions(administrator=True)
    async def force_event(self, ctx):
        """Принудительно запускает ивент прямо сейчас (для проверки)."""
        event_channel = discord.utils.get(ctx.guild.text_channels, name="🎉・ивенты") or \
                        discord.utils.get(ctx.guild.text_channels, name="🎉-ивенты")
        
        if not event_channel:
            return await ctx.send("❌ Канал ивентов не найден.")

        required_people = random.randint(1, 10)
        reward_coins = random.randint(20, 100)

        embed = discord.Embed(
            title="⚡ ТЕСТОВЫЙ ИВЕНТ",
            description=f"Нужно кликов: **{required_people}**\nНаграда: **{reward_coins}**",
            color=discord.Color.orange()
        )
        await event_channel.send(embed=embed, view=EventView(required_people, reward_coins, event_channel))
        await ctx.send("✅ Тестовый ивент запущен!")

async def setup(bot):
    await bot.add_cog(RandomEvents(bot))