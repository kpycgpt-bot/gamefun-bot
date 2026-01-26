import discord
from discord.ext import commands
import asyncio
import os
import sys
from database import db
from config import Config
from utils import EmbedBuilder
import logging

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DiscordBot')

class DiscordBot(commands.Bot):
    """Основной класс бота с расширенным функционалом"""
    
    def __init__(self):
        # Настройка intents
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None,  # Отключаем стандартную команду help
            case_insensitive=True  # Команды не зависят от регистра
        )
        
        self.logger = logger
    
    async def setup_hook(self):
        """Вызывается при запуске бота для инициализации"""
        try:
            # Подключаемся к базе данных
            await db.connect()
            
            # Загружаем все cogs из папки cogs
            await self.load_cogs()
            
            logger.info("✅ Setup завершен успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка в setup_hook: {e}")
            raise
    
    async def load_cogs(self):
        """Загружает все коги из папки cogs"""
        cogs_dir = "cogs"
        
        if not os.path.exists(cogs_dir):
            logger.warning(f"⚠️ Папка {cogs_dir} не найдена, создаю...")
            os.makedirs(cogs_dir)
            return
        
        loaded = 0
        failed = 0
        
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f"✅ Загружен cog: {filename}")
                    loaded += 1
                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки {filename}: {e}")
                    failed += 1
        
        logger.info(f"📦 Загружено {loaded} cogs, ошибок: {failed}")
    
    async def on_ready(self):
        """Вызывается когда бот готов к работе"""
        logger.info("="*50)
        logger.info(f"✅ Бот запущен как {self.user.name} (ID: {self.user.id})")
        logger.info(f"📊 Подключен к {len(self.guilds)} серверам")
        logger.info(f"👥 Обслуживает {sum(g.member_count for g in self.guilds)} пользователей")
        logger.info(f"🔧 Версия discord.py: {discord.__version__}")
        logger.info("="*50)
        
        # Устанавливаем статус
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{Config.PREFIX}help | {len(self.guilds)} серверов"
            ),
            status=discord.Status.online
        )
    
    async def on_command_error(self, ctx, error):
        """Глобальный обработчик ошибок команд"""
        # Игнорируем ошибки, которые уже обработаны
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Получаем оригинальную ошибку
        error = getattr(error, 'original', error)
        
        # Команда не найдена - игнорируем
        if isinstance(error, commands.CommandNotFound):
            return
        
        # Недостаточно прав
        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = EmbedBuilder.error(
                "Недостаточно прав",
                f"Требуемые права: `{perms}`"
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Команда на кулдауне
        elif isinstance(error, commands.CommandOnCooldown):
            embed = EmbedBuilder.warning(
                "Команда на кулдауне",
                f"Попробуй снова через {error.retry_after:.1f}с"
            )
            await ctx.send(embed=embed, delete_after=5)
        
        # Не хватает аргументов
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = EmbedBuilder.error(
                "Неверное использование команды",
                f"Отсутствует аргумент: `{error.param.name}`\n\n"
                f"Используй: `{Config.PREFIX}help {ctx.command.name}`"
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Неверный аргумент
        elif isinstance(error, commands.BadArgument):
            embed = EmbedBuilder.error(
                "Неверный аргумент",
                f"{str(error)}\n\n"
                f"Используй: `{Config.PREFIX}help {ctx.command.name}`"
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Участник не найден
        elif isinstance(error, commands.MemberNotFound):
            embed = EmbedBuilder.error(
                "Участник не найден",
                f"Не могу найти участника: `{error.argument}`"
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Канал не найден
        elif isinstance(error, commands.ChannelNotFound):
            embed = EmbedBuilder.error(
                "Канал не найден",
                f"Не могу найти канал: `{error.argument}`"
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Роль не найдена
        elif isinstance(error, commands.RoleNotFound):
            embed = EmbedBuilder.error(
                "Роль не найдена",
                f"Не могу найти роль: `{error.argument}`"
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Discord API ошибки
        elif isinstance(error, discord.Forbidden):
            embed = EmbedBuilder.error(
                "Недостаточно прав у бота",
                "У меня нет прав для выполнения этого действия.\n"
                "Проверь мои права на сервере."
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, discord.HTTPException):
            embed = EmbedBuilder.error(
                "Ошибка Discord API",
                f"Произошла ошибка при обращении к Discord.\n"
                f"Код: {error.status}"
            )
            await ctx.send(embed=embed, delete_after=10)
            logger.error(f"Discord HTTPException: {error}")
        
        # Неизвестная ошибка
        else:
            embed = EmbedBuilder.error(
                "Произошла ошибка",
                f"```{str(error)[:200]}```\n"
                "Ошибка записана в логи."
            )
            await ctx.send(embed=embed, delete_after=15)
            
            # Логируем полную ошибку
            logger.error(f"Необработанная ошибка в команде {ctx.command}:", exc_info=error)
    
    async def on_guild_join(self, guild):
        """Вызывается когда бот присоединяется к серверу"""
        logger.info(f"➕ Присоединился к серверу: {guild.name} (ID: {guild.id})")
        
        # Обновляем статус
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{Config.PREFIX}help | {len(self.guilds)} серверов"
            )
        )
        
        # Отправляем приветственное сообщение в первый доступный канал
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(
                    title="👋 Привет! Спасибо что добавили меня!",
                    description=f"Я многофункциональный бот для управления сервером.\n\n"
                                f"**Для начала работы:**\n"
                                f"• Используй `{Config.PREFIX}setupserver` для настройки\n"
                                f"• Посмотри все команды: `{Config.PREFIX}help`\n\n"
                                f"Если нужна помощь, используй `{Config.PREFIX}support`",
                    color=Config.COLOR_INFO
                )
                embed.set_footer(text=f"Префикс команд: {Config.PREFIX}")
                await channel.send(embed=embed)
                break
    
    async def on_guild_remove(self, guild):
        """Вызывается когда бот покидает сервер"""
        logger.info(f"➖ Покинул сервер: {guild.name} (ID: {guild.id})")
        
        # Обновляем статус
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{Config.PREFIX}help | {len(self.guilds)} серверов"
            )
        )
    
    async def close(self):
        """Корректное завершение работы бота"""
        logger.info("🔄 Закрываю соединения...")
        await db.close()
        await super().close()
        logger.info("✅ Бот остановлен")

async def main():
    """Главная функция запуска бота"""
    # Проверяем конфигурацию
    if not Config.validate():
        logger.error("❌ Конфигурация невалидна. Остановка.")
        sys.exit(1)
    
    # Создаем и запускаем бота
    bot = DiscordBot()
    
    try:
        async with bot:
            await bot.start(Config.TOKEN)
    except KeyboardInterrupt:
        logger.info("⌨️ Получен сигнал остановки")
    except discord.LoginFailure:
        logger.error("❌ Ошибка авторизации. Проверь токен в .env файле")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
