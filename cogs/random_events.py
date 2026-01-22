import discord
from discord.ext import commands
import asyncio
import random
import json
from datetime import timedelta
from database import db

# --- ВЕЧНАЯ КНОПКА СУНДУКА ---
class PersistentChestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Никогда не отключается

    @discord.ui.button(label="🖐️ Участвовать", style=discord.ButtonStyle.success, emoji="💰", custom_id="chest_join_btn")
    async def join_chest(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Ищем этот сундук в базе данных
        event_data = db.get_event(interaction.message.id)
        
        if not event_data:
            # Если в базе нет записи = сундук старый или уже открыт
            button.disabled = True
            button.label = "❌ Ивент завершен"
            await interaction.response.edit_message(view=self)
            return await interaction.followup.send("Этот сундук уже пуст или истек!", ephemeral=True)

        # Распаковываем данные
        # (message_id, channel_id, reward, required, users_json)
        msg_id, ch_id, reward, required, users_json = event_data
        users_list = json.loads(users_json) # Превращаем текст "[]" обратно в список Python

        # 2. Проверка участника
        if interaction.user.id in users_list:
            return await interaction.response.send_message("❌ Ты уже записан!", ephemeral=True)

        # 3. Добавляем
        users_list.append(interaction.user.id)
        db.update_event_users(msg_id, users_list) # Сохраняем в базу

        current = len(users_list)
        
        # 4. Проверяем финиш
        if current >= required:
            # РАЗДАЧА НАГРАД
            for uid in users_list:
                db.add_coins(uid, reward)
            
            # Удаляем из базы (он больше не активен)
            db.delete_event(msg_id)
            
            # Обновляем сообщение
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = "✅ СУНДУК ОТКРЫТ!"
            embed.description = f"🎉 **{current}** счастливчиков получили по **{reward}** монет!"
            
            # Отключаем кнопку
            button.disabled = True
            button.label = f"💰 Открыто ({current}/{required})"
            await interaction.response.edit_message(embed=embed, view=self)
            
            await interaction.channel.send(f"🎉 Сундук открыт! Все участники получили по {reward} монет!")
        
        else:
            # ПРОДОЛЖАЕМ СБОР
            remaining = required - current
            button.label = f"🖐️ Участвовать ({current}/{required})"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ Ты в деле! Осталось собрать: {remaining}", ephemeral=True)


class RandomEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_loop_task = None
        # 🔥 Регистрируем вечную кнопку при старте!
        self.bot.add_view(PersistentChestView())

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.event_loop_task:
            self.event_loop_task = self.bot.loop.create_task(self.event_loop())

    async def event_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Ждем 1-3 часа
            wait_seconds = random.randint(3600, 10800)
            print(f"[Events] Next drop in {wait_seconds}s")
            await asyncio.sleep(wait_seconds)

            # Запускаем
            await self.spawn_random_chest()

    async def spawn_random_chest(self, channel=None):
        if not channel:
            channel = discord.utils.get(self.bot.get_all_channels(), name="🎉・ивенты") or \
                      discord.utils.get(self.bot.get_all_channels(), name="🎉-ивенты")
        
        if not channel: return print("❌ Нет канала для ивентов")

        required = random.randint(2, 6)
        reward = random.randint(50, 150)

        embed = discord.Embed(
            title="🎁 СЛУЧАЙНЫЙ СУНДУК",
            description=f"Нужно собрать **{required}** человек!\nНаграда: **{reward} монет**",
            color=discord.Color.gold()
        )
        embed.set_image(url="https://media.tenor.com/J3i5eC5T458AAAAC/treasure-chest.gif")

        # Отправляем сообщение
        msg = await channel.send(embed=embed, view=PersistentChestView())

        # 🔥 СОХРАНЯЕМ В БАЗУ
        db.create_event(msg.id, channel.id, reward, required)

    # Тестовая команда
    @commands.command(name="testevent")
    @commands.has_permissions(administrator=True)
    async def force_event(self, ctx):
        await ctx.message.delete()
        await self.spawn_random_chest(ctx.channel)

async def setup(bot):
    await bot.add_cog(RandomEvents(bot))