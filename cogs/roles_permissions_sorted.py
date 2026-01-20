import discord
from discord.ext import commands
import asyncio
import config # Импортируем конфиг для доступа к LOG_CHANNEL

# Список ролей остается без изменений
GAMEFUN_ROLES = [
    {
        "name": "🔱 Верховный Архонт GameFun",
        "color": 0xFFB800,
        "permissions": discord.Permissions(administrator=True),
    },
    {
        "name": "🔥 Архонт Пламени",
        "color": 0xD47E00,
        "permissions": discord.Permissions(
            manage_guild=True, manage_roles=True, manage_channels=True,
            manage_messages=True, view_audit_log=True, kick_members=True, ban_members=True,
        )
    },
    {
        "name": "🛡️ Страж Огненных Путей",
        "color": 0xC0392B,
        "permissions": discord.Permissions(
            manage_messages=True, read_message_history=True, mute_members=True,
            moderate_members=True, move_members=True, kick_members=True,
        )
    },
    {
        "name": "🧭 Хранитель Реалма",
        "color": 0x1ABC9C,
        "permissions": discord.Permissions(
            read_message_history=True, moderate_members=True, send_messages=True,
            speak=True, connect=True,
        )
    },
    ("✨ Искра Начала", 0xF8C471),
    ("🔥 Огненная Ступень", 0xE67E22),
    ("🌪️ Пепельный Шторм", 0xD35400),
    ("🔥👑 Архонт Пламени+", 0xFF6F00),
    ("🗡️ Герой Меча (RPG)", 0x8E44AD),
    ("🎒 Странник Миров (MMO)", 0x27AE60),
    ("♟️ Тактик Реалма (RTS)", 0x34495E),
    ("⚡ Воин Арены (MOBA)", 0x2980B9),
    ("🎯 Меткий Стрелок (Shooter)", 0x2C3E50),
    ("🃏 Мастер Колоды (CCG)", 0x7D3C98),
    ("🦘 Прыгучий Платформер", 0xAF601A),
    ("🧱 Созидатель Реалма", 0xF39C12),
    ("🎥 Голос Миров (Streamer)", 0x9B59B6),
    ("🖌️ Ткач Контента", 0xE74C3C),
    ("🏆🔥 Легенда Архонтов", 0xFF4500),
    ("💎 Окрылённый Поддерживатель", 0x00E5FF),
    ("🥇 Избранный Реалма", 0xFFD700),
]

class RolePermissionsSorted(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetroles(self, ctx):
        """Полностью удаляет и пересоздает все роли GameFun с логированием."""
        guild = ctx.guild
        
        role_names = []
        for item in GAMEFUN_ROLES:
            role_names.append(item["name"] if isinstance(item, dict) else item[0])

        total_steps = len(role_names) * 2
        estimated_seconds = int(total_steps * 1.2)
        
        await ctx.send(f"🧨 **Запущена перезагрузка ролей.**\n"
                       f"Ориентировочное время: **~{estimated_seconds // 60} мин. {estimated_seconds % 60} сек.**")

        # --- ЭТАП 1: УДАЛЕНИЕ ---
        deleted_count = 0
        status_msg = await ctx.send("🗑️ Шаг 1/2: Удаление ролей...")
        
        for name in role_names:
            role = discord.utils.get(guild.roles, name=name)
            if role:
                try:
                    await role.delete(reason=f"Reset by {ctx.author}")
                    deleted_count += 1
                    await asyncio.sleep(0.5) 
                except:
                    continue

        await status_msg.edit(content=f"✅ Удалено: {deleted_count}. Перехожу к созданию...")

        # --- ЭТАП 2: СОЗДАНИЕ И СОРТИРОВКА ---
        created_roles = []
        for item in GAMEFUN_ROLES:
            if isinstance(item, dict):
                name, color, perms = item["name"], item["color"], item["permissions"]
            else:
                name, color = item
                perms = discord.Permissions.none()

            try:
                role = await guild.create_role(
                    name=name, color=discord.Color(color), 
                    permissions=perms, reason=f"Reset by {ctx.author}"
                )
                created_roles.append(role)
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Ошибка создания {name}: {e}")

        # Сортировка
        bot_role = guild.get_member(self.bot.user.id).top_role
        base_position = bot_role.position - 1

        for i, role in enumerate(reversed(created_roles)):
            new_pos = max(1, base_position - i)
            try:
                await role.edit(position=new_pos)
            except:
                continue

        # --- ЭТАП 3: ЛОГИРОВАНИЕ ---
        log_channel = self.bot.get_channel(config.LOG_CHANNEL)
        if log_channel:
            log_embed = discord.Embed(
                title="🔄 Рестарт иерархии ролей",
                description=f"Администратор {ctx.author.mention} выполнил полную перезагрузку ролей GameFun.",
                color=0x2ECC71 # Зеленый цвет успеха
            )
            log_embed.add_field(name="Удалено старых", value=f"**{deleted_count}**", inline=True)
            log_embed.add_field(name="Создано новых", value=f"**{len(created_roles)}**", inline=True)
            log_embed.set_footer(text=f"ID Администратора: {ctx.author.id}")
            log_embed.set_timestamp()
            
            await log_channel.send(embed=log_embed)

        await ctx.send(f"🎯 **Готово!** Все роли воссозданы. Отчет отправлен в {log_channel.mention if log_channel else 'канал логов'}.")

async def setup(bot):
    await bot.add_cog(RolePermissionsSorted(bot))