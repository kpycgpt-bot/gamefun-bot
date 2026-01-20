import discord
from discord.ext import commands

class RolesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # --- ЛОГИКА ВЫДАЧИ ---
    async def toggle_role(self, interaction, role_name):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            return await interaction.response.send_message(f"❌ Роль '{role_name}' не найдена! Проверь настройки сервера.", ephemeral=True)
        
        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(f"🗑️ Роль **{role_name}** убрана.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Роль **{role_name}** выдана!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ У бота нет прав (подними роль бота выше роли игры!).", ephemeral=True)

    # --- КНОПКИ ---
    
    @discord.ui.button(label="RPG", emoji="🗡️", style=discord.ButtonStyle.primary, custom_id="btn_rpg")
    async def rpg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "🗡️ Герой Меча (RPG)")

    @discord.ui.button(label="MMO", emoji="🎒", style=discord.ButtonStyle.success, custom_id="btn_mmo")
    async def mmo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "🎒 Странник Миров (MMO)")

    @discord.ui.button(label="Shooter", emoji="🎯", style=discord.ButtonStyle.primary, custom_id="btn_shooter")
    async def shooter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "🎯 Меткий Стрелок (Shooter)")

    @discord.ui.button(label="MOBA", emoji="⚡", style=discord.ButtonStyle.danger, custom_id="btn_moba")
    async def moba_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "⚡ Воин Арены (MOBA)")

    @discord.ui.button(label="RTS", emoji="♟️", style=discord.ButtonStyle.secondary, custom_id="btn_rts")
    async def rts_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "♟️ Тактик Реалма (RTS)")

    @discord.ui.button(label="CCG (Карты)", emoji="🃏", style=discord.ButtonStyle.secondary, custom_id="btn_ccg")
    async def ccg_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "🃏 Мастер Колоды (CCG)")
    
    @discord.ui.button(label="Sandbox", emoji="🧱", style=discord.ButtonStyle.primary, custom_id="btn_sandbox")
    async def sandbox_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "🧱 Созидатель Реалма")

class RolesPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rolespanel")
    @commands.has_permissions(administrator=True)
    async def send_roles_panel(self, ctx):
        embed = discord.Embed(
            title="🎭 ВЫБОР ИГРОВЫХ ИНТЕРЕСОВ",
            description="Нажми на кнопку, чтобы открыть доступ к категории!\nПовторное нажатие уберет роль.",
            color=0x9B59B6
        )
        await ctx.send(embed=embed, view=RolesView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(RolesPanel(bot))