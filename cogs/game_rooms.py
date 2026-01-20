import discord
from discord.ext import commands
import asyncio

# --- 1. МЕНЮ ДЛЯ ДОБАВЛЕНИЯ ---
class AddUserSelectView(discord.ui.View):
    def __init__(self, channel):
        super().__init__(timeout=60)
        self.channel = channel

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="🔍 Выбери друга для добавления...", min_values=1, max_values=1)
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        member = select.values[0]
        # Выдаем права: Видеть канал + Писать сообщения
        await self.channel.set_permissions(member, view_channel=True, send_messages=True)
        await interaction.response.edit_message(content=f"✅ **{member.display_name}** добавлен в базу!", view=None)

# --- 2. МЕНЮ ДЛЯ КИКА (НОВОЕ) ---
class KickUserSelectView(discord.ui.View):
    def __init__(self, channel):
        super().__init__(timeout=60)
        self.channel = channel

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="🚫 Выбери, кого выгнать...", min_values=1, max_values=1)
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        member = select.values[0]
        
        # Защита от выстрела себе в ногу (нельзя кикнуть самого себя)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Нельзя выгнать самого себя!", ephemeral=True)

        # Снимаем права (overwrite=None удаляет настройки для юзера)
        await self.channel.set_permissions(member, overwrite=None)
        await interaction.response.edit_message(content=f"👋 **{member.display_name}** удален из комнаты.", view=None)

# --- 3. МОДАЛКА ТОЛЬКО ДЛЯ ПЕРЕИМЕНОВАНИЯ ---
class RenameTextRoomModal(discord.ui.Modal, title="Переименовать комнату"):
    name_input = discord.ui.TextInput(
        label="Новое название",
        placeholder="Например: Секретный бункер",
        min_length=2,
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):
        new_name = f"🔒┃{self.name_input.value}"
        await interaction.channel.edit(name=new_name)
        await interaction.response.send_message(f"✅ Комната переименована в **{new_name}**", ephemeral=True)

# --- 4. ГЛАВНЫЙ ПУЛЬТ УПРАВЛЕНИЯ ---
class RoomControlsView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Проверка: нажимать может только владелец или админ
        if interaction.user.id != self.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Вы не владелец этой комнаты!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Добавить", emoji="➕", style=discord.ButtonStyle.blurple, row=0)
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Открываем меню добавления
        view = AddUserSelectView(interaction.channel)
        await interaction.response.send_message("👇 **Выберите, кого добавить:**", view=view, ephemeral=True)

    @discord.ui.button(label="Кикнуть", emoji="🚫", style=discord.ButtonStyle.gray, row=0)
    async def kick_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Открываем меню кика
        view = KickUserSelectView(interaction.channel)
        await interaction.response.send_message("👇 **Выберите, кого выгнать:**", view=view, ephemeral=True)

    @discord.ui.button(label="Переименовать", emoji="✏️", style=discord.ButtonStyle.secondary, row=1)
    async def rename_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameTextRoomModal())

    @discord.ui.button(label="Удалить комнату", emoji="🗑️", style=discord.ButtonStyle.red, row=1)
    async def delete_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🧨 Комната будет уничтожена через 3 секунды...", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.channel.delete()

# --- 5. КНОПКА СОЗДАНИЯ (ЗЕЛЕНАЯ) ---
class CreateTextRoomButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Создать текстовую базу",
            emoji="📝",
            style=discord.ButtonStyle.green,
            custom_id="create_text_room"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        
        category = discord.utils.get(guild.categories, name="🎮 Игровые Миры")
        if not category:
            category = await guild.create_category("🎮 Игровые Миры")

        # Права при создании: только бот и создатель
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
        }

        channel_name = f"🔒┃база-{user.display_name}"
        channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)

        await interaction.response.send_message(f"✅ Комната создана: {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title=f"База данных: {user.display_name}",
            description="**Управление доступом:**\nИспользуй кнопки ниже, чтобы добавить или выгнать друзей.",
            color=0x2ECC71
        )
        await channel.send(f"{user.mention}, твоя комната готова!", embed=embed, view=RoomControlsView(user.id))

class GameRoomView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreateTextRoomButton())

class GameRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def textpanel(self, ctx):
        embed = discord.Embed(
            title="🔒 Приватные Текстовые Комнаты",
            description="Нажми кнопку ниже, чтобы создать свой личный закрытый чат.",
            color=0x2ECC71
        )
        await ctx.send(embed=embed, view=GameRoomView())

async def setup(bot):
    await bot.add_cog(GameRooms(bot))