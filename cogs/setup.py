import discord
from discord.ext import commands
from database import db
from utils import EmbedBuilder
from config import Config
import logging

logger = logging.getLogger('DiscordBot.Setup')

class Setup(commands.Cog):
    """Модуль первоначальной настройки сервера"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ Setup инициализирован")
    
    @commands.command(name='setupserver', aliases=['настройка'])
    @commands.has_permissions(administrator=True)
    async def setup_server(self, ctx):
        """
        🔧 Первоначальная настройка бота на сервере
        
        Создает все необходимые каналы и категории:
        - Категория для тикетов
        - Категория для голосовых каналов  
        - Канал-триггер для создания войсов
        - Канал для логов
        - Канал приветствий
        
        Требуемые права: Administrator
        """
        guild = ctx.guild
        
        msg = await ctx.send(embed=EmbedBuilder.info(
            "🔧 Настройка сервера",
            "Начинаю создание каналов и категорий...\nЭто может занять некоторое время."
        ))
        
        try:
            # --- КАТЕГОРИЯ ДЛЯ ТИКЕТОВ ---
            ticket_category = discord.utils.get(guild.categories, name=Config.TICKET_CATEGORY_NAME)
            if not ticket_category:
                ticket_category = await guild.create_category(
                    Config.TICKET_CATEGORY_NAME,
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(view_channel=False),
                        guild.me: discord.PermissionOverwrite(view_channel=True)
                    },
                    reason="Настройка бота - категория для тикетов"
                )
                logger.info(f"Создана категория тикетов: {ticket_category.id}")
            
            await db.set_config("ticket_category_id", ticket_category.id)
            
            # --- КАТЕГОРИЯ ДЛЯ ГОЛОСОВЫХ КАНАЛОВ ---
            voice_category = discord.utils.get(guild.categories, name=Config.VOICE_CATEGORY_NAME)
            if not voice_category:
                voice_category = await guild.create_category(
                    Config.VOICE_CATEGORY_NAME,
                    reason="Настройка бота - категория для голосовых каналов"
                )
                logger.info(f"Создана категория войсов: {voice_category.id}")
            
            await db.set_config("voice_category_id", voice_category.id)
            
            # --- КАНАЛ-ТРИГГЕР ДЛЯ СОЗДАНИЯ ВОЙСОВ ---
            trigger_channel = discord.utils.get(voice_category.voice_channels, name="➕ Создать комнату")
            if not trigger_channel:
                trigger_channel = await guild.create_voice_channel(
                    "➕ Создать комнату",
                    category=voice_category,
                    reason="Настройка бота - триггер для голосовых каналов"
                )
                logger.info(f"Создан канал-триггер: {trigger_channel.id}")
            
            await db.set_config("voice_trigger_id", trigger_channel.id)
            
            # --- КАНАЛ ДЛЯ ЛОГОВ ---
            log_channel = discord.utils.get(guild.text_channels, name="📝-логи")
            if not log_channel:
                log_channel = await guild.create_text_channel(
                    "📝-логи",
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(
                            read_messages=False,
                            send_messages=False
                        ),
                        guild.me: discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True
                        )
                    },
                    reason="Настройка бота - канал для логов"
                )
                logger.info(f"Создан канал логов: {log_channel.id}")
            
            await db.set_config("log_channel_id", log_channel.id)
            
            # --- КАНАЛ ПРИВЕТСТВИЙ ---
            welcome_channel = discord.utils.get(guild.text_channels, name="👋-приветствия")
            if not welcome_channel:
                welcome_channel = await guild.create_text_channel(
                    "👋-приветствия",
                    reason="Настройка бота - канал приветствий"
                )
                logger.info(f"Создан канал приветствий: {welcome_channel.id}")
            
            await db.set_config("welcome_channel_id", welcome_channel.id)
            
            # --- УСПЕШНОЕ ЗАВЕРШЕНИЕ ---
            embed = discord.Embed(
                title="✅ Настройка завершена!",
                description="Все каналы и категории созданы и настроены.",
                color=Config.COLOR_SUCCESS
            )
            
            embed.add_field(
                name="📋 Созданные элементы",
                value=f"• {ticket_category.mention} - категория для тикетов\n"
                     f"• {voice_category.mention} - категория для войсов\n"
                     f"• {trigger_channel.mention} - канал создания комнат\n"
                     f"• {log_channel.mention} - канал логов\n"
                     f"• {welcome_channel.mention} - канал приветствий",
                inline=False
            )
            
            embed.add_field(
                name="📝 Следующие шаги",
                value=f"1. Используй `{Config.PREFIX}ticketpanel` для создания панели тикетов\n"
                     f"2. Используй `{Config.PREFIX}voicepanel` для инструкций по войсам\n"
                     f"3. Настрой права доступа к каналам при необходимости",
                inline=False
            )
            
            embed.set_footer(text=f"Используй {Config.PREFIX}config для просмотра настроек")
            
            await msg.edit(embed=embed)
            logger.info(f"{ctx.author} завершил настройку сервера {guild.name}")
            
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                "❌ Недостаточно прав",
                "У меня нет прав для создания каналов.\n"
                "Дай мне права **Administrator** или:\n"
                "• Manage Channels\n"
                "• Manage Roles"
            )
            await msg.edit(embed=embed)
            logger.error(f"Ошибка прав при настройке сервера {guild.name}")
            
        except Exception as e:
            embed = EmbedBuilder.error(
                "❌ Ошибка настройки",
                f"Произошла ошибка: {str(e)}\n\n"
                "Проверь права бота и попробуй снова."
            )
            await msg.edit(embed=embed)
            logger.error(f"Ошибка при настройке сервера {guild.name}: {e}", exc_info=True)
    
    @commands.command(name='config', aliases=['конфиг', 'настройки'])
    @commands.has_permissions(administrator=True)
    async def show_config(self, ctx):
        """
        ⚙️ Показать текущую конфигурацию бота
        
        Отображает все настроенные каналы и категории
        
        Требуемые права: Administrator
        """
        guild = ctx.guild
        
        embed = discord.Embed(
            title="⚙️ Конфигурация бота",
            description=f"Текущие настройки для **{guild.name}**",
            color=Config.COLOR_INFO
        )
        
        # Получаем все настройки из БД
        configs = {
            "ticket_category_id": "📋 Категория тикетов",
            "voice_category_id": "🔊 Категория войсов",
            "voice_trigger_id": "➕ Триггер создания войсов",
            "log_channel_id": "📝 Канал логов",
            "welcome_channel_id": "👋 Канал приветствий"
        }
        
        for key, label in configs.items():
            channel_id = db.get_config(key, cast_type=int)
            
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    value = f"{channel.mention} (`{channel_id}`)"
                    status = "✅"
                else:
                    value = f"⚠️ Канал удален (`{channel_id}`)"
                    status = "⚠️"
            else:
                value = "❌ Не настроено"
                status = "❌"
            
            embed.add_field(
                name=f"{status} {label}",
                value=value,
                inline=False
            )
        
        # Дополнительная информация
        embed.add_field(
            name="📊 Статистика",
            value=f"• Префикс команд: `{Config.PREFIX}`\n"
                 f"• XP за сообщение: `{Config.XP_PER_MESSAGE}`\n"
                 f"• Монет за сообщение: `{Config.COINS_PER_MESSAGE}`\n"
                 f"• Максимум варнов: `{Config.MAX_WARNS}`",
            inline=False
        )
        
        embed.set_footer(text=f"Используй {Config.PREFIX}setupserver для настройки")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='setlog', aliases=['логи'])
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """
        📝 Установить канал для логов
        
        Использование:
        !setlog #логи
        
        Требуемые права: Administrator
        """
        await db.set_config("log_channel_id", channel.id)
        
        embed = EmbedBuilder.success(
            "📝 Канал логов установлен",
            f"Все логи модерации будут отправляться в {channel.mention}"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} установил канал логов: {channel.id}")
    
    @commands.command(name='setwelcome', aliases=['приветствия'])
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel):
        """
        👋 Установить канал приветствий
        
        Использование:
        !setwelcome #приветствия
        
        Требуемые права: Administrator
        """
        await db.set_config("welcome_channel_id", channel.id)
        
        embed = EmbedBuilder.success(
            "👋 Канал приветствий установлен",
            f"Новые участники будут приветствоваться в {channel.mention}"
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} установил канал приветствий: {channel.id}")
    
    @commands.command(name='resetconfig', aliases=['сброс'])
    @commands.has_permissions(administrator=True)
    async def reset_config(self, ctx):
        """
        🗑️ Сбросить всю конфигурацию бота
        
        ⚠️ Это удалит все настройки!
        
        Требуемые права: Administrator
        """
        from utils import confirm_action
        
        confirmed = await confirm_action(
            ctx,
            "🗑️ Сбросить конфигурацию?",
            "Это удалит все настройки бота на сервере.\n"
            "Каналы НЕ будут удалены, только настройки."
        )
        
        if not confirmed:
            return
        
        # Удаляем все настройки
        configs_to_delete = [
            "ticket_category_id",
            "voice_category_id",
            "voice_trigger_id",
            "log_channel_id",
            "welcome_channel_id"
        ]
        
        for key in configs_to_delete:
            await db.delete_config(key)
        
        embed = EmbedBuilder.success(
            "✅ Конфигурация сброшена",
            f"Все настройки удалены.\n\n"
            f"Используй `{Config.PREFIX}setupserver` для повторной настройки."
        )
        
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} сбросил конфигурацию на сервере {ctx.guild.name}")

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Setup(bot))
