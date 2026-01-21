import discord
from discord.ext import commands

# Настройка кнопок и ролей
# Формат: "custom_id": {"name": "Имя Роли", "emoji": "Эмодзи", "style": ЦветКнопки}
ROLES_CONFIG = {
    "role_rpg":     {"name": "RPG",     "emoji": "🗡️", "style": discord.ButtonStyle.primary},
    "role_mmo":     {"name": "MMO",     "emoji": "🛡️", "style": discord.ButtonStyle.success},
    "role_shooter": {"name": "Shooter", "emoji": "🎯", "style": discord.ButtonStyle.primary},
    "role_moba":    {"name": "MOBA",    "emoji": "⚡", "style": discord.ButtonStyle.danger},
    "role_rts":     {"name": "RTS",     "emoji": "🏰", "style": discord.ButtonStyle.secondary},
}

class RoleButton(discord.ui.Button):
    def __init__(self, role_key, data):
        super().__init__(
            style=data["style"],
            label=data["name"],
            emoji=data["emoji"],
            custom_id=role_key, # ВАЖНО: ID кнопки должен быть постоянным
            row=0 if list(ROLES_CONFIG.keys()).index(role_key) < 3 else 1 # Красивая расстановка
        )
        self.role_name = data["name"]

    async def callback(self, interaction: discord.Interaction):
        # Эта функция срабатывает при нажатии
        role = discord.utils.get(interaction.guild.roles, name=self.role_name)
        
        if not role:
            return await interaction.response.send_message(f"❌ Админ забыл создать роль **{self.role_name}**!", ephemeral=True)

        user = interaction.user
        if role in user.roles:
            await user.remove_roles(role)
            await interaction.response.send_message(f"❌ Роль **{self.role_name}** убрана.", ephemeral=True)
        else:
            await user.add_roles(role)
            await interaction.response.send_message(f"✅ Роль **{self.role_name}** выдана!", ephemeral=True)

class RolesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # ВАЖНО: timeout=None делает кнопки вечными
        # Создаем кнопки из конфига
        for key, data in ROLES_CONFIG.items():
            self.add_item(RoleButton(key, data))

class RolesPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 🔥 САМОЕ ГЛАВНОЕ: Регистрируем кнопки при запуске бота
        # Без этого после перезагрузки кнопки перестанут работать
        self.bot.add_view(RolesView())

    @commands.command(name="rolemenu")
    @commands.has_permissions(administrator=True)
    async def send_panel(self, ctx):
        """Отправляет панель выбора ролей."""
        await ctx.message.delete()
        
        embed = discord.Embed(
            title="🎭 ВЫБОР ИГРОВЫХ ИНТЕРЕСОВ",
            description="Нажми на кнопку, чтобы получить доступ к категории!\nПовторное нажатие уберет роль.",
            color=discord.Color.dark_theme()
        )
        # Отправляем сообщение с нашей вечной View
        await ctx.send(embed=embed, view=RolesView())

async def setup(bot):
    await bot.add_cog(RolesPanel(bot))