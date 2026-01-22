import discord
from discord.ext import commands

# --- НАСТРОЙКИ ---
# Мы берем ТОЧНЫЕ названия из твоего списка.
# На кнопке пишем коротко (button_label), а ищем длинное (role_name).

ROLES_CONFIG = {
    "role_rpg": {
        "button_label": "RPG", 
        "role_name": "🗡️ Герой Меча (RPG)", 
        "emoji": "🗡️", 
        "style": discord.ButtonStyle.primary
    },
    "role_mmo": {
        "button_label": "MMO", 
        "role_name": "🎒 Странник Миров (MMO)", 
        "emoji": "🎒", 
        "style": discord.ButtonStyle.success
    },
    "role_shooter": {
        "button_label": "Shooter", 
        "role_name": "🎯 Меткий Стрелок (Shooter)", 
        "emoji": "🎯", 
        "style": discord.ButtonStyle.primary
    },
    "role_moba": {
        "button_label": "MOBA", 
        "role_name": "⚡ Воин Арены (MOBA)", 
        "emoji": "⚡", 
        "style": discord.ButtonStyle.danger
    },
    "role_rts": {
        "button_label": "RTS", 
        "role_name": "♟️ Тактик Реалма (RTS)", 
        "emoji": "♟️", 
        "style": discord.ButtonStyle.secondary
    },
    "role_ccg": {
        "button_label": "CCG (Карты)", 
        "role_name": "🃏 Мастер Колоды (CCG)", 
        "emoji": "🃏", 
        "style": discord.ButtonStyle.secondary
    },
    "role_platformer": {
        "button_label": "Platformer", 
        "role_name": "🦘 Прыгучий Платформер", 
        "emoji": "🦘", 
        "style": discord.ButtonStyle.secondary
    },
    "role_sandbox": {
        "button_label": "Sandbox", 
        "role_name": "🧱 Созидатель Реалма", 
        "emoji": "🧱", 
        "style": discord.ButtonStyle.primary
    }
}

class RoleButton(discord.ui.Button):
    def __init__(self, role_key, data):
        super().__init__(
            style=data["style"],
            label=data["button_label"],
            emoji=data["emoji"],
            custom_id=role_key,
            # Первые 4 кнопки в ряд 0, вторые 4 кнопки в ряд 1
            row=0 if list(ROLES_CONFIG.keys()).index(role_key) < 4 else 1 
        )
        self.role_to_give = data["role_name"]

    async def callback(self, interaction: discord.Interaction):
        # Ищем роль по ТОЧНОМУ названию
        role = discord.utils.get(interaction.guild.roles, name=self.role_to_give)
        
        if not role:
            return await interaction.response.send_message(
                f"❌ **ОШИБКА КОНФИГА:**\nЯ пытался найти роль `{self.role_to_give}`, но её нет на сервере.\nПроверь, не удалил ли ты её?", 
                ephemeral=True
            )

        user = interaction.user
        if role in user.roles:
            await user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Роль **{self.role_to_give}** убрана.", ephemeral=True)
        else:
            await user.add_roles(role)
            await interaction.response.send_message(f"✅ Роль **{self.role_to_give}** выдана!", ephemeral=True)

class RolesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Делаем кнопки вечными
        for key, data in ROLES_CONFIG.items():
            self.add_item(RoleButton(key, data))

class RolesPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 🔥 ВОССТАНАВЛИВАЕМ КНОПКИ ПРИ ЗАПУСКЕ 🔥
        self.bot.add_view(RolesView())

    @commands.command(name="rolemenu")
    @commands.has_permissions(administrator=True)
    async def send_panel(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(
            title="🎭 ВЫБОР ИГРОВЫХ ИНТЕРЕСОВ",
            description="Нажми на кнопку, чтобы открыть доступ к категории!\nПовторное нажатие уберет роль.",
            color=0x9B59B6
        )
        # Отправляем сообщение с кнопками
        await ctx.send(embed=embed, view=RolesView())

async def setup(bot):
    await bot.add_cog(RolesPanel(bot))