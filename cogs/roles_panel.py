import discord
from discord.ext import commands
from utils import EmbedBuilder
from config import Config
import logging

logger = logging.getLogger('DiscordBot.RolesPanel')

class RoleButton(discord.ui.Button):
    """Кнопка для получения/удаления роли"""
    
    def __init__(self, role: discord.Role):
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_{role.id}"
        )
        self.role = role
    
    async def callback(self, interaction: discord.Interaction):
        """Выдает или убирает роль"""
        member = interaction.user
        
        if self.role in member.roles:
            # Убираем роль
            try:
                await member.remove_roles(self.role, reason="Панель ролей")
                embed = EmbedBuilder.success(
                    "Роль убрана",
                    f"Ты больше не {self.role.mention}"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(f"{member} убрал роль {self.role}")
            except discord.Forbidden:
                embed = EmbedBuilder.error(
                    "Ошибка",
                    "У бота нет прав для управления этой ролью"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            # Выдаем роль
            try:
                await member.add_roles(self.role, reason="Панель ролей")
                embed = EmbedBuilder.success(
                    "Роль получена!",
                    f"Теперь ты {self.role.mention}"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(f"{member} получил роль {self.role}")
            except discord.Forbidden:
                embed = EmbedBuilder.error(
                    "Ошибка",
                    "У бота нет прав для управления этой ролью"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

class RoleSelectView(discord.ui.View):
    """View с кнопками ролей"""
    
    def __init__(self, roles: list):
        super().__init__(timeout=None)
        
        # Добавляем кнопки для каждой роли (максимум 25)
        for role in roles[:25]:
            self.add_item(RoleButton(role))

class RolesPanel(commands.Cog):
    """Панель выбора ролей"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ RolesPanel инициализирован")
    
    @commands.command(name='rolepanel', aliases=['панельролей'])
    @commands.has_permissions(manage_roles=True)
    async def role_panel(self, ctx, category: str = None):
        """
        🎭 Создать панель выбора ролей
        
        Использование:
        !rolepanel игры - роли с категорией "игры"
        !rolepanel уведомления - роли для уведомлений
        
        Создай роли с префиксом в названии, например:
        • [Игра] Minecraft
        • [Игра] CS:GO
        • [Уведомление] Новости
        
        Требуемые права: Manage Roles
        """
        if not category:
            embed = EmbedBuilder.error(
                "Укажи категорию",
                f"Использование: `{Config.PREFIX}rolepanel <категория>`\n\n"
                "Пример: `!rolepanel игры`"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        # Ищем роли с категорией
        category_lower = category.lower()
        matching_roles = []
        
        for role in ctx.guild.roles:
            role_name_lower = role.name.lower()
            # Ищем роли с [категория] или категория в названии
            if f"[{category_lower}]" in role_name_lower or category_lower in role_name_lower:
                # Проверяем что роль ниже роли бота
                if role < ctx.guild.me.top_role and not role.is_default():
                    matching_roles.append(role)
        
        if not matching_roles:
            embed = EmbedBuilder.error(
                "Роли не найдены",
                f"Не найдено ролей с категорией `{category}`\n\n"
                f"Создай роли с названием:\n"
                f"• `[{category}] Название`\n"
                f"• `{category} Название`"
            )
            return await ctx.send(embed=embed, delete_after=15)
        
        if len(matching_roles) > 25:
            embed = EmbedBuilder.warning(
                "Слишком много ролей",
                f"Найдено {len(matching_roles)} ролей, но панель поддерживает максимум 25.\n"
                "Будут добавлены первые 25."
            )
            await ctx.send(embed=embed, delete_after=10)
            matching_roles = matching_roles[:25]
        
        # Удаляем команду
        try:
            await ctx.message.delete()
        except:
            pass
        
        # Создаем панель
        embed = discord.Embed(
            title=f"🎭 Роли: {category.title()}",
            description="**Выбери роли, которые тебе нужны!**\n\n"
                       "Нажми на кнопку, чтобы получить или убрать роль.\n"
                       "Ты можешь выбрать несколько ролей.",
            color=Config.COLOR_INFO
        )
        
        # Список ролей
        roles_list = "\n".join([f"• {role.mention}" for role in matching_roles])
        embed.add_field(name="📋 Доступные роли", value=roles_list, inline=False)
        
        embed.set_footer(text="Нажми на кнопку ниже для получения роли")
        
        view = RoleSelectView(matching_roles)
        await ctx.send(embed=embed, view=view)
        
        logger.info(f"{ctx.author} создал панель ролей: {category} ({len(matching_roles)} ролей)")
    
    @commands.command(name='createroles', aliases=['создатьроли'])
    @commands.has_permissions(manage_roles=True)
    async def create_roles(self, ctx, category: str, *role_names):
        """
        ➕ Быстро создать роли для панели
        
        Использование:
        !createroles игры Minecraft "CS:GO" Dota2
        
        Создаст роли:
        • [игры] Minecraft
        • [игры] CS:GO
        • [игры] Dota2
        
        Требуемые права: Manage Roles
        """
        if not role_names:
            embed = EmbedBuilder.error(
                "Укажи названия ролей",
                f"Использование: `{Config.PREFIX}createroles <категория> <роль1> <роль2> ...`\n\n"
                "Пример: `!createroles игры Minecraft \"CS:GO\" Dota2`"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        # Создаем роли
        created = []
        failed = []
        
        for role_name in role_names:
            full_name = f"[{category}] {role_name}"
            
            try:
                role = await ctx.guild.create_role(
                    name=full_name,
                    color=discord.Color.random(),
                    mentionable=False,
                    reason=f"Создано через панель ролей: {ctx.author}"
                )
                created.append(role)
                logger.info(f"Создана роль {full_name}")
            except discord.Forbidden:
                failed.append(role_name)
            except Exception as e:
                logger.error(f"Ошибка создания роли {full_name}: {e}")
                failed.append(role_name)
        
        # Результат
        embed = discord.Embed(
            title="➕ Создание ролей",
            color=Config.COLOR_SUCCESS if not failed else Config.COLOR_WARNING
        )
        
        if created:
            roles_text = "\n".join([f"• {role.mention}" for role in created])
            embed.add_field(
                name=f"✅ Создано ({len(created)})",
                value=roles_text,
                inline=False
            )
        
        if failed:
            failed_text = "\n".join([f"• {name}" for name in failed])
            embed.add_field(
                name=f"❌ Не удалось ({len(failed)})",
                value=failed_text,
                inline=False
            )
        
        embed.add_field(
            name="📝 Следующий шаг",
            value=f"Используй `{Config.PREFIX}rolepanel {category}` для создания панели",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rolelist', aliases=['списокролей'])
    @commands.has_permissions(manage_roles=True)
    async def role_list(self, ctx, category: str = None):
        """
        📋 Показать роли по категории
        
        Использование:
        !rolelist игры - роли категории "игры"
        !rolelist - все роли сервера
        
        Требуемые права: Manage Roles
        """
        if category:
            # Фильтруем по категории
            category_lower = category.lower()
            roles = [
                role for role in ctx.guild.roles
                if (f"[{category_lower}]" in role.name.lower() or category_lower in role.name.lower())
                and not role.is_default()
            ]
            
            if not roles:
                embed = EmbedBuilder.error(
                    "Роли не найдены",
                    f"Нет ролей с категорией `{category}`"
                )
                return await ctx.send(embed=embed, delete_after=10)
            
            title = f"📋 Роли: {category.title()}"
        else:
            # Все роли (кроме @everyone и управляемых ботом)
            roles = [
                role for role in ctx.guild.roles
                if not role.is_default() and not role.managed
            ]
            title = "📋 Все роли сервера"
        
        embed = discord.Embed(
            title=title,
            description=f"Найдено {len(roles)} ролей",
            color=Config.COLOR_INFO
        )
        
        # Группируем по 10 ролей в поле
        for i in range(0, len(roles), 10):
            chunk = roles[i:i+10]
            roles_text = "\n".join([
                f"• {role.mention} ({len([m for m in ctx.guild.members if role in m.roles])} чел.)"
                for role in chunk
            ])
            
            embed.add_field(
                name=f"Роли {i+1}-{min(i+10, len(roles))}",
                value=roles_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='deleterole', aliases=['удалитьроль'])
    @commands.has_permissions(manage_roles=True)
    async def delete_role(self, ctx, role: discord.Role):
        """
        🗑️ Удалить роль
        
        Использование:
        !deleterole @роль
        
        Требуемые права: Manage Roles
        """
        from utils import confirm_action
        
        # Проверяем что роль можно удалить
        if role >= ctx.guild.me.top_role:
            embed = EmbedBuilder.error(
                "Ошибка",
                "Эта роль выше моей роли. Я не могу её удалить."
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        if role.managed:
            embed = EmbedBuilder.error(
                "Ошибка",
                "Это интеграционная роль. Её нельзя удалить."
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        # Подтверждение
        members_with_role = len([m for m in ctx.guild.members if role in m.roles])
        
        confirmed = await confirm_action(
            ctx,
            f"Удалить роль {role.name}?",
            f"У **{members_with_role}** участников есть эта роль.\n"
            "Они её потеряют."
        )
        
        if not confirmed:
            return
        
        try:
            await role.delete(reason=f"Удалена {ctx.author}")
            embed = EmbedBuilder.success(
                "Роль удалена",
                f"Роль **{role.name}** успешно удалена"
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} удалил роль {role.name}")
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                "Ошибка",
                "У меня нет прав для удаления этой роли"
            )
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='rolecolor', aliases=['цветроли'])
    @commands.has_permissions(manage_roles=True)
    async def role_color(self, ctx, role: discord.Role, color: str):
        """
        🎨 Изменить цвет роли
        
        Использование:
        !rolecolor @роль #FF5733
        !rolecolor @роль red
        !rolecolor @роль random
        
        Требуемые права: Manage Roles
        """
        if role >= ctx.guild.me.top_role:
            embed = EmbedBuilder.error(
                "Ошибка",
                "Эта роль выше моей роли"
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            # Определяем цвет
            if color.lower() == 'random':
                new_color = discord.Color.random()
            elif color.startswith('#'):
                new_color = discord.Color(int(color[1:], 16))
            else:
                # Предустановленные цвета
                colors = {
                    'red': discord.Color.red(),
                    'blue': discord.Color.blue(),
                    'green': discord.Color.green(),
                    'yellow': discord.Color.yellow(),
                    'purple': discord.Color.purple(),
                    'orange': discord.Color.orange(),
                    'pink': discord.Color.pink(),
                }
                new_color = colors.get(color.lower(), discord.Color.default())
            
            await role.edit(color=new_color, reason=f"Цвет изменен {ctx.author}")
            
            embed = discord.Embed(
                title="🎨 Цвет изменен",
                description=f"Роль {role.mention} теперь этого цвета",
                color=new_color
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} изменил цвет роли {role.name}")
            
        except ValueError:
            embed = EmbedBuilder.error(
                "Неверный цвет",
                "Используй HEX (#FF5733) или название (red, blue, green...)"
            )
            await ctx.send(embed=embed, delete_after=5)
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                "Ошибка",
                "У меня нет прав для изменения этой роли"
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(RolesPanel(bot))
    
    # Восстанавливаем persistent views для существующих панелей
    # (Если бот перезапустился, кнопки снова будут работать)
    for guild in bot.guilds:
        # Здесь можно добавить логику загрузки сохраненных панелей из БД
        pass
