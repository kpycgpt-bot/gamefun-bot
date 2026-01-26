import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from database import db
from utils import EmbedBuilder
from config import Config
import logging
import os

logger = logging.getLogger('DiscordBot.Tickets')

class TicketLauncher(discord.ui.View):
    """Кнопка для создания тикета"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📩 Создать тикет", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Создает новый тикет"""
        guild = interaction.guild
        member = interaction.user
        
        # Проверяем, нет ли уже открытого тикета
        category_id = db.get_config("ticket_category_id", cast_type=int)
        if category_id:
            category = guild.get_channel(category_id)
            if category:
                for channel in category.text_channels:
                    if channel.topic and str(member.id) in channel.topic:
                        embed = EmbedBuilder.warning(
                            "Тикет уже открыт",
                            f"У тебя уже есть открытый тикет: {channel.mention}"
                        )
                        return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Получаем категорию для тикетов
            if not category_id:
                embed = EmbedBuilder.error(
                    "Ошибка конфигурации",
                    "Система тикетов не настроена. Администратор должен выполнить `!setupserver`"
                )
                return await interaction.followup.send(embed=embed, ephemeral=True)
            
            category = guild.get_channel(category_id)
            if not category:
                embed = EmbedBuilder.error(
                    "Ошибка",
                    "Категория для тикетов была удалена. Обратись к администратору."
                )
                return await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Создаем канал тикета
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_messages=True
                )
            }
            
            # Даем доступ модераторам/админам
            for role in guild.roles:
                if role.permissions.manage_messages or role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True
                    )
            
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{member.name}",
                category=category,
                topic=str(member.id),
                overwrites=overwrites,
                reason=f"Тикет создан пользователем {member}"
            )
            
            # Отправляем приветственное сообщение
            embed = discord.Embed(
                title="🎫 Тикет создан!",
                description=f"Привет, {member.mention}!\n\n"
                           "Опиши свою проблему или вопрос. Администрация ответит как можно скорее.\n\n"
                           "**Для закрытия тикета** нажми кнопку ниже.",
                color=Config.COLOR_INFO
            )
            embed.set_footer(text=f"Тикет #{ticket_channel.id}")
            
            await ticket_channel.send(
                content=member.mention,
                embed=embed,
                view=TicketControls()
            )
            
            # Уведомляем пользователя
            success_embed = EmbedBuilder.success(
                "Тикет создан!",
                f"Твой тикет: {ticket_channel.mention}"
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
            # Логируем в канал логов
            log_id = db.get_config("log_channel_id", cast_type=int)
            if log_id:
                log_channel = guild.get_channel(log_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="🎫 Новый тикет",
                        color=Config.COLOR_INFO
                    )
                    log_embed.add_field(name="Создатель", value=member.mention, inline=True)
                    log_embed.add_field(name="Канал", value=ticket_channel.mention, inline=True)
                    log_embed.timestamp = datetime.utcnow()
                    await log_channel.send(embed=log_embed)
            
            logger.info(f"Создан тикет {ticket_channel.id} пользователем {member}")
            
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                "Недостаточно прав",
                "У бота нет прав для создания канала. Обратись к администратору."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка создания тикета: {e}", exc_info=True)
            embed = EmbedBuilder.error(
                "Ошибка",
                f"Не удалось создать тикет: {str(e)}"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class TicketControls(discord.ui.View):
    """Кнопки управления тикетом"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🔒 Закрыть тикет", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Закрывает тикет"""
        channel = interaction.channel
        
        # Проверяем, что это канал тикета
        if not channel.category or not channel.topic:
            embed = EmbedBuilder.error("Ошибка", "Это не канал тикета")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Проверяем права (создатель или модератор)
        is_creator = str(interaction.user.id) == channel.topic
        is_moderator = interaction.user.guild_permissions.manage_messages
        
        if not (is_creator or is_moderator):
            embed = EmbedBuilder.error(
                "Отказано",
                "Только создатель тикета или модератор может закрыть его"
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.defer()
        
        try:
            # Создаем транскрипт
            embed = discord.Embed(
                title="🔒 Тикет закрывается...",
                description="Создаю транскрипт переписки...",
                color=Config.COLOR_WARNING
            )
            await channel.send(embed=embed)
            
            # Сохраняем историю сообщений
            transcript = []
            async for message in channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%d.%m.%Y %H:%M:%S")
                content = message.content or "[Вложения/Embed]"
                transcript.append(f"[{timestamp}] {message.author}: {content}")
            
            # Создаем файл транскрипта
            filename = f"transcript_{channel.id}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"ТРАНСКРИПТ ТИКЕТА: {channel.name}\n")
                f.write(f"СОЗДАН: {channel.created_at.strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"ЗАКРЫТ: {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"ЗАКРЫЛ: {interaction.user}\n")
                f.write("=" * 50 + "\n\n")
                f.write("\n".join(transcript))
            
            # Отправляем в логи
            log_id = db.get_config("log_channel_id", cast_type=int)
            if log_id:
                log_channel = interaction.guild.get_channel(log_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="📕 Тикет закрыт",
                        color=Config.COLOR_ERROR
                    )
                    log_embed.add_field(name="Тикет", value=channel.name, inline=True)
                    log_embed.add_field(name="Закрыл", value=interaction.user.mention, inline=True)
                    
                    # Пытаемся определить создателя
                    try:
                        creator_id = int(channel.topic)
                        creator = interaction.guild.get_member(creator_id)
                        if creator:
                            log_embed.add_field(name="Создатель", value=creator.mention, inline=True)
                    except:
                        pass
                    
                    log_embed.timestamp = datetime.utcnow()
                    
                    try:
                        file = discord.File(filename)
                        await log_channel.send(embed=log_embed, file=file)
                    except:
                        await log_channel.send(embed=log_embed)
            
            # Удаляем файл
            try:
                os.remove(filename)
            except:
                pass
            
            # Уведомляем о закрытии
            close_embed = EmbedBuilder.success(
                "Тикет закрыт",
                "Канал будет удален через 5 секунд..."
            )
            await channel.send(embed=close_embed)
            
            # Удаляем канал
            await asyncio.sleep(5)
            await channel.delete(reason=f"Тикет закрыт пользователем {interaction.user}")
            
            logger.info(f"Тикет {channel.id} закрыт пользователем {interaction.user}")
            
        except Exception as e:
            logger.error(f"Ошибка закрытия тикета: {e}", exc_info=True)
            error_embed = EmbedBuilder.error(
                "Ошибка",
                f"Не удалось закрыть тикет: {str(e)}"
            )
            await channel.send(embed=error_embed)

class Tickets(commands.Cog):
    """Система тикетов поддержки"""
    
    def __init__(self, bot):
        self.bot = bot
        # Регистрируем persistent views
        self.bot.add_view(TicketLauncher())
        self.bot.add_view(TicketControls())
        logger.info("✅ Tickets инициализирован")
    
    @commands.command(name='ticketpanel', aliases=['тикетпанель'])
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx):
        """
        🎫 Создать панель тикетов
        
        Отправляет сообщение с кнопкой для создания тикетов
        
        Требуемые права: Administrator
        """
        # Удаляем команду
        try:
            await ctx.message.delete()
        except:
            pass
        
        embed = discord.Embed(
            title="🎫 СЛУЖБА ПОДДЕРЖКИ",
            description="**Нужна помощь? Нашёл баг? Хочешь пожаловаться?**\n\n"
                       "Нажми кнопку ниже, чтобы создать приватный тикет!\n"
                       "Администрация ответит как можно скорее.\n\n"
                       "**Правила:**\n"
                       "• Один тикет = одна проблема\n"
                       "• Будь вежлив и конкретен\n"
                       "• Не спамь тикетами\n"
                       "• Закрывай тикет после решения проблемы",
            color=Config.COLOR_INFO
        )
        embed.set_footer(text="Нажми кнопку ниже ↓")
        
        await ctx.send(embed=embed, view=TicketLauncher())
        logger.info(f"{ctx.author} создал панель тикетов")
    
    @commands.command(name='addticket', aliases=['добавитьвтикет'])
    @commands.has_permissions(manage_messages=True)
    async def add_to_ticket(self, ctx, member: discord.Member):
        """
        ➕ Добавить пользователя в тикет
        
        Использование:
        !addticket @user - добавить в текущий тикет
        
        Требуемые права: Manage Messages
        """
        channel = ctx.channel
        
        # Проверяем, что это тикет
        category_id = db.get_config("ticket_category_id", cast_type=int)
        if not category_id or channel.category_id != category_id:
            embed = EmbedBuilder.error("Ошибка", "Эта команда работает только в тикетах")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            await channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
            
            embed = EmbedBuilder.success(
                "Пользователь добавлен",
                f"{member.mention} добавлен в тикет"
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} добавил {member} в тикет {channel.id}")
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Ошибка", "Недостаточно прав для изменения канала")
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='removeticket', aliases=['удалитьизтикета'])
    @commands.has_permissions(manage_messages=True)
    async def remove_from_ticket(self, ctx, member: discord.Member):
        """
        ➖ Удалить пользователя из тикета
        
        Использование:
        !removeticket @user - удалить из текущего тикета
        
        Требуемые права: Manage Messages
        """
        channel = ctx.channel
        
        # Проверяем, что это тикет
        category_id = db.get_config("ticket_category_id", cast_type=int)
        if not category_id or channel.category_id != category_id:
            embed = EmbedBuilder.error("Ошибка", "Эта команда работает только в тикетах")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Проверяем, что это не создатель
        if channel.topic and str(member.id) == channel.topic:
            embed = EmbedBuilder.error("Ошибка", "Нельзя удалить создателя тикета")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            await channel.set_permissions(member, overwrite=None)
            
            embed = EmbedBuilder.success(
                "Пользователь удален",
                f"{member.mention} удален из тикета"
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} удалил {member} из тикета {channel.id}")
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Ошибка", "Недостаточно прав для изменения канала")
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(Tickets(bot))
