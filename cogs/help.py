import discord
from discord.ext import commands
from utils import Paginator, EmbedBuilder
from config import Config
import logging

logger = logging.getLogger('DiscordBot.Help')

class Help(commands.Cog):
    """Система помощи и информации"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ Help инициализирован")
    
    @commands.command(name='help', aliases=['помощь', 'commands', 'команды'])
    async def help_command(self, ctx, *, category: str = None):
        """
        📚 Показать список команд
        
        Использование:
        !help - все категории
        !help economy - команды экономики
        !help moderation - команды модерации
        """
        if category:
            await self.show_category_help(ctx, category.lower())
        else:
            await self.show_main_help(ctx)
    
    async def show_main_help(self, ctx):
        """Показывает главное меню помощи"""
        embed = discord.Embed(
            title="📚 Помощь по командам",
            description=f"Префикс команд: `{Config.PREFIX}`\n\n"
                       "Выбери категорию для подробной информации:",
            color=Config.COLOR_INFO
        )
        
        # Получаем все коги
        categories = {
            "🎮 Экономика": ("economy", "balance, daily, work, shop, inventory"),
            "👮 Модерация": ("moderation", "warn, kick, ban, clear"),
            "🔊 Голосовые": ("voice", "lock, unlock, limit, rename, claim"),
            "⚙️ Настройка": ("setup", "setupserver, config, setlog, setwelcome"),
            "ℹ️ Информация": ("info", "help, ping, info, serverinfo")
        }
        
        for name, (key, commands_list) in categories.items():
            embed.add_field(
                name=name,
                value=f"Команды: `{commands_list}`\n"
                     f"Подробнее: `{Config.PREFIX}help {key}`",
                inline=False
            )
        
        embed.add_field(
            name="🔗 Полезные ссылки",
            value=f"• [Документация](https://github.com)\n"
                 f"• [Сервер поддержки](https://discord.gg)\n"
                 f"• [Пожертвования](https://boosty.to)",
            inline=False
        )
        
        embed.set_footer(
            text=f"Используй {Config.PREFIX}help <категория> для подробностей",
            icon_url=self.bot.user.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    async def show_category_help(self, ctx, category: str):
        """Показывает помощь по конкретной категории"""
        
        categories_data = {
            "economy": {
                "title": "🎮 Команды экономики",
                "commands": {
                    "balance": "Посмотреть свой баланс",
                    "daily": "Получить ежедневную награду (100-500 монет)",
                    "work": "Поработать за монеты (50-150 монет)",
                    "shop": "Открыть магазин предметов",
                    "buy <предмет>": "Купить предмет из магазина",
                    "inventory": "Посмотреть свой инвентарь",
                    "give <@user> <сумма>": "Передать монеты другому игроку",
                    "top": "Топ игроков по уровню",
                    "coinflip <ставка>": "Орел или решка (удвой или потеряй)"
                }
            },
            "moderation": {
                "title": "👮 Команды модерации",
                "commands": {
                    "warn <@user> [причина]": "Выдать предупреждение",
                    "warns [@user]": "Посмотреть предупреждения",
                    "clearwarns <@user>": "Очистить все варны (админ)",
                    "kick <@user> [причина]": "Кикнуть пользователя",
                    "ban <@user> [причина]": "Забанить пользователя",
                    "unban <ID> [причина]": "Разбанить пользователя",
                    "clear <количество>": "Очистить сообщения (1-100)",
                    "slowmode <секунды>": "Установить медленный режим"
                }
            },
            "voice": {
                "title": "🔊 Команды для голосовых каналов",
                "commands": {
                    "lock": "Закрыть свою комнату",
                    "unlock": "Открыть свою комнату",
                    "limit <число>": "Установить лимит пользователей (0 = без лимита)",
                    "rename <название>": "Переименовать свою комнату",
                    "claim": "Забрать владение комнатой (если владелец вышел)",
                    "voicepanel": "Показать панель управления (админ)"
                }
            },
            "setup": {
                "title": "⚙️ Команды настройки",
                "commands": {
                    "setupserver": "Первоначальная настройка бота (админ)",
                    "config": "Показать текущую конфигурацию (админ)",
                    "setlog <#канал>": "Установить канал логов (админ)",
                    "setwelcome <#канал>": "Установить канал приветствий (админ)",
                    "resetconfig": "Сбросить всю конфигурацию (админ)",
                    "ticketpanel": "Создать панель тикетов (админ)"
                }
            },
            "info": {
                "title": "ℹ️ Информационные команды",
                "commands": {
                    "help [категория]": "Показать помощь",
                    "ping": "Проверить задержку бота",
                    "info": "Информация о боте",
                    "serverinfo": "Информация о сервере",
                    "userinfo [@user]": "Информация о пользователе"
                }
            }
        }
        
        if category not in categories_data:
            embed = EmbedBuilder.error(
                "Категория не найдена",
                f"Доступные категории: `economy`, `moderation`, `voice`, `setup`, `info`\n\n"
                f"Используй `{Config.PREFIX}help` для списка всех категорий"
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        data = categories_data[category]
        
        embed = discord.Embed(
            title=data["title"],
            description=f"Префикс: `{Config.PREFIX}`",
            color=Config.COLOR_INFO
        )
        
        for command, description in data["commands"].items():
            embed.add_field(
                name=f"`{Config.PREFIX}{command}`",
                value=description,
                inline=False
            )
        
        embed.set_footer(
            text=f"Пример: {Config.PREFIX}{list(data['commands'].keys())[0]}",
            icon_url=self.bot.user.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping', aliases=['пинг'])
    async def ping(self, ctx):
        """
        🏓 Проверить задержку бота
        
        Показывает время отклика бота и API Discord
        """
        # Задержка WebSocket
        ws_latency = round(self.bot.latency * 1000)
        
        # Создаем сообщение для измерения задержки
        embed = EmbedBuilder.info("🏓 Понг!", "Измеряю задержку...")
        msg = await ctx.send(embed=embed)
        
        # Задержка API
        api_latency = round((msg.created_at - ctx.message.created_at).total_seconds() * 1000)
        
        # Обновляем embed
        embed = discord.Embed(
            title="🏓 Понг!",
            color=Config.COLOR_SUCCESS if ws_latency < 100 else Config.COLOR_WARNING
        )
        
        embed.add_field(
            name="📡 WebSocket",
            value=f"`{ws_latency}ms`",
            inline=True
        )
        
        embed.add_field(
            name="🔌 API",
            value=f"`{api_latency}ms`",
            inline=True
        )
        
        # Статус задержки
        if ws_latency < 100:
            status = "🟢 Отлично"
        elif ws_latency < 200:
            status = "🟡 Нормально"
        else:
            status = "🔴 Высокая задержка"
        
        embed.add_field(
            name="📊 Статус",
            value=status,
            inline=True
        )
        
        await msg.edit(embed=embed)
    
    @commands.command(name='info', aliases=['about', 'информация'])
    async def bot_info(self, ctx):
        """
        🤖 Информация о боте
        
        Показывает статистику и информацию о боте
        """
        embed = discord.Embed(
            title=f"🤖 {self.bot.user.name}",
            description="Многофункциональный Discord бот",
            color=Config.COLOR_INFO
        )
        
        # Статистика
        total_members = sum(g.member_count for g in self.bot.guilds)
        total_commands = len(self.bot.commands)
        
        embed.add_field(
            name="📊 Статистика",
            value=f"• Серверов: **{len(self.bot.guilds)}**\n"
                 f"• Пользователей: **{total_members:,}**\n"
                 f"• Команд: **{total_commands}**",
            inline=True
        )
        
        # Версии
        import discord as discord_lib
        embed.add_field(
            name="🔧 Технологии",
            value=f"• Python 3.8+\n"
                 f"• discord.py {discord_lib.__version__}\n"
                 f"• SQLite 3",
            inline=True
        )
        
        # Ссылки
        embed.add_field(
            name="🔗 Ссылки",
            value=f"[Документация](https://github.com) • "
                 f"[Поддержка](https://discord.gg) • "
                 f"[GitHub](https://github.com)",
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=f"Запрошено {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='serverinfo', aliases=['сервер'])
    async def server_info(self, ctx):
        """
        🏠 Информация о сервере
        
        Показывает детальную информацию о текущем сервере
        """
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🏠 {guild.name}",
            description=guild.description or "Описание не установлено",
            color=Config.COLOR_INFO
        )
        
        # Владелец
        embed.add_field(
            name="👑 Владелец",
            value=guild.owner.mention,
            inline=True
        )
        
        # Дата создания
        created = guild.created_at.strftime("%d.%m.%Y")
        embed.add_field(
            name="📅 Создан",
            value=created,
            inline=True
        )
        
        # ID
        embed.add_field(
            name="🆔 ID",
            value=f"`{guild.id}`",
            inline=True
        )
        
        # Участники
        bot_count = len([m for m in guild.members if m.bot])
        human_count = guild.member_count - bot_count
        
        embed.add_field(
            name="👥 Участники",
            value=f"Всего: **{guild.member_count}**\n"
                 f"Люди: **{human_count}**\n"
                 f"Боты: **{bot_count}**",
            inline=True
        )
        
        # Каналы
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="📺 Каналы",
            value=f"Категорий: **{categories}**\n"
                 f"Текстовых: **{text_channels}**\n"
                 f"Голосовых: **{voice_channels}**",
            inline=True
        )
        
        # Роли
        embed.add_field(
            name="🎭 Роли",
            value=f"**{len(guild.roles)}** ролей",
            inline=True
        )
        
        # Уровень верификации
        verification_levels = {
            discord.VerificationLevel.none: "Нет",
            discord.VerificationLevel.low: "Низкий",
            discord.VerificationLevel.medium: "Средний",
            discord.VerificationLevel.high: "Высокий",
            discord.VerificationLevel.highest: "Максимальный"
        }
        
        embed.add_field(
            name="🔒 Верификация",
            value=verification_levels.get(guild.verification_level, "Неизвестно"),
            inline=True
        )
        
        # Буст
        if guild.premium_tier > 0:
            embed.add_field(
                name="💎 Буст",
                value=f"Уровень: **{guild.premium_tier}**\n"
                     f"Бустов: **{guild.premium_subscription_count}**",
                inline=True
            )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='userinfo', aliases=['user', 'юзер'])
    async def user_info(self, ctx, member: discord.Member = None):
        """
        👤 Информация о пользователе
        
        Использование:
        !userinfo - твоя информация
        !userinfo @user - информация о другом пользователе
        """
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color
        )
        
        # Основная информация
        embed.add_field(
            name="🏷️ Имя",
            value=f"{member.name}#{member.discriminator}",
            inline=True
        )
        
        embed.add_field(
            name="🆔 ID",
            value=f"`{member.id}`",
            inline=True
        )
        
        embed.add_field(
            name="🤖 Бот",
            value="Да" if member.bot else "Нет",
            inline=True
        )
        
        # Даты
        created = member.created_at.strftime("%d.%m.%Y")
        joined = member.joined_at.strftime("%d.%m.%Y") if member.joined_at else "Неизвестно"
        
        embed.add_field(
            name="📅 Аккаунт создан",
            value=created,
            inline=True
        )
        
        embed.add_field(
            name="📥 Присоединился",
            value=joined,
            inline=True
        )
        
        # Роли
        roles = [role.mention for role in member.roles[1:]]  # Исключаем @everyone
        roles_text = ", ".join(roles) if roles else "Нет ролей"
        
        if len(roles_text) > 1024:
            roles_text = f"{len(roles)} ролей"
        
        embed.add_field(
            name=f"🎭 Роли ({len(roles)})",
            value=roles_text,
            inline=False
        )
        
        # Статус экономики
        user_data = await db.get_user(member.id)
        embed.add_field(
            name="💰 Экономика",
            value=f"Уровень: **{user_data['level']}**\n"
                 f"XP: **{user_data['xp']:,}**\n"
                 f"Монеты: **{user_data['coins']:,}** {Config.EMOJI_COIN}",
            inline=True
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Help(bot))
