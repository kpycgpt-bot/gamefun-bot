import discord
from discord.ext import commands
import config
import asyncio

# --- СПИСОК РОЛЕЙ ---
ROLES_DB = [
    ("🔱 Верховный Архонт GameFun", 0xFFD700, "admin"),
    ("🔥 Архонт Пламени", 0xE67E22, "mod_high"),
    ("🛡️ Страж Огненных Путей", 0xE74C3C, "mod"),
    ("🗡️ Герой Меча (RPG)", 0x9B59B6, "game"),
    ("🎒 Странник Миров (MMO)", 0x2ECC71, "game"),
    ("♟️ Тактик Реалма (RTS)", 0x34495E, "game"),
    ("⚡ Воин Арены (MOBA)", 0x3498DB, "game"),
    ("🎯 Меткий Стрелок (Shooter)", 0x95A5A6, "game"),
    ("🃏 Мастер Колоды (CCG)", 0xD35400, "game"),
    ("🦘 Прыгучий Платформер", 0xF1C40F, "game"),
    ("🧱 Созидатель Реалма", 0x8E44AD, "game"),
    ("✨ Искра Начала", 0xF39C12, "rank"),
    ("🔥 Огненная Ступень", 0xD35400, "rank"),
    ("🌪️ Пепельный Шторм", 0xC0392B, "rank"),
    ("🔥👑 Архонт Пламени+", 0xFF0000, "rank"),
]

GAME_ROLES_MAP = {
    "⚔️・rpg-мир": "🗡️ Герой Меча (RPG)",
    "🎒・mmo-центр": "🎒 Странник Миров (MMO)",
    "♟️・rts-комната": "♟️ Тактик Реалма (RTS)",
    "⚡・moba-арена": "⚡ Воин Арены (MOBA)",
    "🎯・shooter-база": "🎯 Меткий Стрелок (Shooter)",
    "🃏・ccg-зал": "🃏 Мастер Колоды (CCG)",
    "🦘・platform-комната": "🦘 Прыгучий Платформер",
    "🧱・sandbox-ландшафт": "🧱 Созидатель Реалма"
}

ADMIN_ROLES = ["🔱 Верховный Архонт GameFun", "🔥 Архонт Пламени"]
MOD_ROLES = ["🛡️ Страж Огненных Путей"]

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def update_config_file(self, updates: dict):
        """Умное обновление конфига с защитой от кодировок (UTF-8 / CP1251)."""
        lines = []
        
        # 1. Читаем файл (пробуем разные кодировки)
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                # Если файл был сохранен в Windows-кодировке
                with open("config.py", "r", encoding="cp1251") as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"❌ Критическая ошибка чтения конфига: {e}")
                return

        # 2. Перезаписываем в UTF-8 (чтобы починить файл навсегда)
        try:
            with open("config.py", "w", encoding="utf-8") as f:
                for line in lines:
                    updated_line = False
                    for key, value in updates.items():
                        if line.strip().startswith(f"{key} ="):
                            f.write(f"{key} = {value}\n")
                            updated_line = True
                            break
                    if not updated_line:
                        f.write(line)
            print("✅ Config.py успешно обновлен!")
        except Exception as e:
            print(f"❌ Ошибка записи конфига: {e}")

    async def create_roles_safe(self, ctx, status_msg):
        guild = ctx.guild
        total = len(ROLES_DB)
        
        for i, (name, color_hex, r_type) in enumerate(ROLES_DB):
            if discord.utils.get(guild.roles, name=name):
                continue

            perms = discord.Permissions.general()
            if r_type == "admin": perms = discord.Permissions(administrator=True)
            elif r_type == "mod_high": perms = discord.Permissions(manage_guild=True, kick_members=True)
            elif r_type == "mod": perms = discord.Permissions(manage_messages=True)
            
            try:
                await guild.create_role(name=name, color=discord.Color(color_hex), permissions=perms)
                if i % 3 == 0:
                    await status_msg.edit(content=f"🎨 Создание ролей... ({i}/{total})")
                await asyncio.sleep(1.0)
            except Exception as e:
                print(f"Skip role {name}: {e}")

    async def create_category_safe(self, guild, name, channels, is_private=False, is_voice=False):
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=not is_private)}
        for r in ADMIN_ROLES + MOD_ROLES:
            role = discord.utils.get(guild.roles, name=r)
            if role: overwrites[role] = discord.PermissionOverwrite(view_channel=True)

        try:
            cat = await guild.create_category(name, overwrites=overwrites)
            await asyncio.sleep(2.0)
        except Exception as e:
            print(f"Category fail {name}: {e}")
            return None, {}

        created = {}
        for ch_name in channels:
            ch_over = overwrites.copy()
            
            if ch_name in GAME_ROLES_MAP:
                ch_over[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                role = discord.utils.get(guild.roles, name=GAME_ROLES_MAP[ch_name])
                if role: ch_over[role] = discord.PermissionOverwrite(view_channel=True)

            try:
                if is_voice:
                    ch = await guild.create_voice_channel(ch_name, category=cat, overwrites=ch_over)
                else:
                    ch = await guild.create_text_channel(ch_name, category=cat, overwrites=ch_over)
                created[ch_name] = ch
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"Channel fail {ch_name}: {e}")
        
        return cat, created

    @commands.command(name="resetserver")
    @commands.has_permissions(administrator=True)
    async def resetserver(self, ctx):
        await ctx.send("🧨 **Удаляю каналы (подожди 30 сек)...**")
        for ch in ctx.guild.channels:
            if ch != ctx.channel:
                try: 
                    await ch.delete()
                    await asyncio.sleep(0.5)
                except: pass
        
        self.update_config_file({"LOG_CHANNEL": 0, "VOICE_CATEGORY_ID": 0, "VOICE_TRIGGER_CHANNEL": 0})
        await ctx.send("🗑️ **Чисто.** Пиши `!setupserver`.")

    @commands.command(name="setupserver")
    @commands.has_permissions(administrator=True)
    async def setupserver(self, ctx):
        msg = await ctx.send("⏳ **Запуск безопасной установки (займет ~2-3 минуты)...**")
        
        # 1. Роли
        await self.create_roles_safe(ctx, msg)
        await msg.edit(content="🏗️ Роли готовы. Строим категории (0/10)...")

        config_updates = {}
        guild = ctx.guild

        # Структура
        structure = [
            ("📥 WELCOME.", ["👋-welcome", "📜-rules", "🎭-choose-your-interest", "📢-announcements"], False, False),
            ("💬 COMMUNITY LOUNGE", ["💬-общий-чат", "🤪-флудилка", "📷-наши-моменты", "🎧-музыка"], False, False),
            ("🎨 CREATIVE CORNER", ["🎨-творчество", "🎥-клипы"], False, False),
            ("🤖 AI & TOOLS", ["🤖-бот-помощник", "🛠️-репорты"], False, False),
            ("🛡️ STAFF", ["🛡️-staff", "🚨-reports", "📁-mod-log"], True, False),
            ("🎮 Игровые Миры", ["⚔️・rpg-мир", "🎒・mmo-центр", "🎯・shooter-база", "⚡・moba-арена"], False, False),
            ("🔊 Голосовые Реалма", ["🔊 ➕ Создать комнату", "🔊・общий", "🎤・стрим"], False, True),
            ("🛡️ Управление", ["🔱・админ-центр", "🔥・модерация"], True, False),
            ("🌍 Центр Реалма", ["💬・общение", "🎉・ивенты"], False, False),
            ("🛠️ СИСТЕМА", ["📜┃логи-сервера"], True, False)
        ]

        for i, (cat_name, channels, is_private, is_voice) in enumerate(structure):
            await msg.edit(content=f"🏗️ Строим раздел: **{cat_name}**... ({i+1}/{len(structure)})")
            
            cat, created_chans = await self.create_category_safe(guild, cat_name, channels, is_private, is_voice)
            
            if "👋-welcome" in created_chans: config_updates["WELCOME_CHANNEL"] = created_chans["👋-welcome"].id
            if "🔊 ➕ Создать комнату" in created_chans: 
                config_updates["VOICE_TRIGGER_CHANNEL"] = created_chans["🔊 ➕ Создать комнату"].id
                config_updates["VOICE_CATEGORY_ID"] = cat.id
            if "📜┃логи-сервера" in created_chans: config_updates["LOG_CHANNEL"] = created_chans["📜┃логи-сервера"].id

        self.update_config_file(config_updates)
        await msg.edit(content="✅ **ГОТОВО!** Все каналы созданы и конфиг обновлен.\n⚠️ **ПЕРЕЗАПУСТИ БОТА (Ctrl+C -> Start)!**")

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))