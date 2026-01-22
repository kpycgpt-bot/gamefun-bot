import discord
from discord.ext import commands
import asyncio
import random
import json
from database import db

class PersistentChestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Вечная кнопка

    @discord.ui.button(label="🖐️ Участвовать", style=discord.ButtonStyle.success, emoji="💰", custom_id="chest_join_btn")
    async def join_chest(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # 1. Проверяем базу данных
            event_data = db.get_event(interaction.message.id)
            
            if not event_data:
                button.disabled = True
                button.label = "❌ Истек"
                await interaction.response.edit_message(view=self)
                return await interaction.followup.send("⏳ Этот сундук уже пуст или истек!", ephemeral=True)

            # 2. Разбираем данные
            msg_id, ch_id, reward, required, users_json = event_data
            users_list = json.loads(users_json)

            # 3. Проверка
            if interaction.user.id in users_list:
                return await interaction.response.send_message("⚠️ Ты уже записан!", ephemeral=True)

            # 4. Добавляем участника
            users_list.append(interaction.user.id)
            db.update_event_users(msg_id, users_list)

            current = len(users_list)
            remaining = required - current

            # 5. Если собрали всех
            if current >= required:
                # Выдаем награды
                for uid in users_list:
                    db.add_coins(uid, reward)
                
                # Удаляем ивент
                db.delete_event(msg_id)
                
                # Обновляем вид
                embed = interaction.message.embeds[0]
                embed.color = discord.Color.green()
                embed.title = "✅ СУНДУК ОТКРЫТ!"
                embed.description = f"🎉 **{current}** участников получили по **{reward}** монет!"
                
                button.disabled = True
                button.label = f"💰 Открыто ({current}/{required})"
                await interaction.response.edit_message(embed=embed, view=self)
                await interaction.channel.send(f"🎉 **СУНДУК ОТКРЫТ!** Все получили по {reward} монет!")
            
            else:
                # Обновляем кнопку
                button.label = f"🖐️ Участвовать ({current}/{required})"
                await interaction.response.edit_message(view=self)
                await interaction.followup.send(f"✅ Ты записан! Нужно еще {remaining} чел.", ephemeral=True)
        
        except Exception as e:
            # 🔥 ВОТ ЭТО ПОКАЖЕТ ОШИБКУ 🔥
            print(f"[Chest Error] {e}")
            await interaction.response.send_message(f"❌ **Критическая ошибка:** `{e}`\nПокажи это админу!", ephemeral=True)

class RandomEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_loop_task = None
        # Регистрируем кнопку, чтобы не ломалась после рестарта
        self.bot.add_view(PersistentChestView())

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.event_loop_task:
            self.event_loop_task = self.bot.loop.create_task(self.event_loop())

    async def event_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            wait_seconds = random.randint(3600, 10800) # 1-3 часа
            await asyncio.sleep(wait_seconds)
            await self.spawn_random_chest()

    async def spawn_random_chest(self, channel=None):
        if not channel:
            channel = discord.utils.get(self.bot.get_all_channels(), name="🎉・ивенты") or \
                      discord.utils.get(self.bot.get_all_channels(), name="🎉-ивенты")
        
        if not channel: return

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
        
        # Сохраняем в базу (если тут ошибка, она вылезет в консоль)
        try:
            db.create_event(msg.id, channel.id, reward, required)
        except Exception as e:
            await channel.send(f"⚠️ Ошибка базы данных: `{e}`")

    @commands.command(name="testevent")
    @commands.has_permissions(administrator=True)
    async def force_event(self, ctx):
        await ctx.message.delete()
        await self.spawn_random_chest(ctx.channel)

async def setup(bot):
    await bot.add_cog(RandomEvents(bot))