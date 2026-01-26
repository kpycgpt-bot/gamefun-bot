import discord
from discord.ext import commands
from typing import Optional, Union
from config import Config
import asyncio
from datetime import datetime

class EmbedBuilder:
    """Класс для создания красивых embed сообщений"""
    
    @staticmethod
    def success(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Создает embed для успешного действия"""
        embed = discord.Embed(
            title=f"{Config.EMOJI_SUCCESS} {title}",
            description=description,
            color=Config.COLOR_SUCCESS,
            **kwargs
        )
        embed.timestamp = datetime.utcnow()
        return embed
    
    @staticmethod
    def error(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Создает embed для ошибки"""
        embed = discord.Embed(
            title=f"{Config.EMOJI_ERROR} {title}",
            description=description,
            color=Config.COLOR_ERROR,
            **kwargs
        )
        embed.timestamp = datetime.utcnow()
        return embed
    
    @staticmethod
    def info(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Создает embed для информации"""
        embed = discord.Embed(
            title=f"{Config.EMOJI_INFO} {title}",
            description=description,
            color=Config.COLOR_INFO,
            **kwargs
        )
        embed.timestamp = datetime.utcnow()
        return embed
    
    @staticmethod
    def warning(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Создает embed для предупреждения"""
        embed = discord.Embed(
            title=f"{Config.EMOJI_WARNING} {title}",
            description=description,
            color=Config.COLOR_WARNING,
            **kwargs
        )
        embed.timestamp = datetime.utcnow()
        return embed

class Checks:
    """Кастомные проверки для команд"""
    
    @staticmethod
    def is_admin():
        """Проверяет, является ли пользователь администратором"""
        async def predicate(ctx):
            return ctx.author.guild_permissions.administrator
        return commands.check(predicate)
    
    @staticmethod
    def is_moderator():
        """Проверяет, является ли пользователь модератором"""
        async def predicate(ctx):
            return ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
        return commands.check(predicate)
    
    @staticmethod
    def is_owner():
        """Проверяет, является ли пользователь владельцем бота"""
        async def predicate(ctx):
            return ctx.author.id == Config.OWNER_ID
        return commands.check(predicate)

class Paginator:
    """Класс для создания пагинации в embed сообщениях"""
    
    def __init__(self, ctx, pages: list, timeout: int = 60):
        self.ctx = ctx
        self.pages = pages
        self.timeout = timeout
        self.current = 0
        self.message: Optional[discord.Message] = None
    
    async def start(self):
        """Запускает пагинатор"""
        if not self.pages:
            await self.ctx.send(embed=EmbedBuilder.error("Ошибка", "Нет данных для отображения"))
            return
        
        self.message = await self.ctx.send(embed=self.pages[0], view=PaginatorView(self))
    
    def get_page(self, page: int) -> discord.Embed:
        """Получает страницу по номеру"""
        return self.pages[page % len(self.pages)]
    
    async def update_page(self, page: int):
        """Обновляет текущую страницу"""
        self.current = page % len(self.pages)
        await self.message.edit(embed=self.get_page(self.current), view=PaginatorView(self))

class PaginatorView(discord.ui.View):
    """View с кнопками для пагинатора"""
    
    def __init__(self, paginator: Paginator):
        super().__init__(timeout=paginator.timeout)
        self.paginator = paginator
        
        # Отключаем кнопки если только одна страница
        if len(paginator.pages) == 1:
            for item in self.children:
                item.disabled = True
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка предыдущей страницы"""
        if interaction.user.id != self.paginator.ctx.author.id:
            await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
            return
        
        new_page = self.paginator.current - 1
        if new_page < 0:
            new_page = len(self.paginator.pages) - 1
        
        await self.paginator.update_page(new_page)
        await interaction.response.defer()
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка следующей страницы"""
        if interaction.user.id != self.paginator.ctx.author.id:
            await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
            return
        
        new_page = self.paginator.current + 1
        if new_page >= len(self.paginator.pages):
            new_page = 0
        
        await self.paginator.update_page(new_page)
        await interaction.response.defer()
    
    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка закрытия"""
        if interaction.user.id != self.paginator.ctx.author.id:
            await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
            return
        
        await self.paginator.message.delete()
        self.stop()

class ConfirmView(discord.ui.View):
    """View для подтверждения действий"""
    
    def __init__(self, ctx, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.value: Optional[bool] = None
    
    @discord.ui.button(label="✅ Подтвердить", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка подтверждения"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
            return
        
        self.value = True
        self.stop()
        await interaction.response.send_message("✅ Подтверждено!", ephemeral=True)
    
    @discord.ui.button(label="❌ Отмена", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка отмены"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
            return
        
        self.value = False
        self.stop()
        await interaction.response.send_message("❌ Отменено!", ephemeral=True)

async def send_temporary_message(
    channel: Union[discord.TextChannel, discord.User],
    content: str = None,
    embed: discord.Embed = None,
    delete_after: int = 10
):
    """Отправляет временное сообщение, которое удалится через N секунд"""
    message = await channel.send(content=content, embed=embed)
    await asyncio.sleep(delete_after)
    try:
        await message.delete()
    except discord.NotFound:
        pass

async def confirm_action(ctx, title: str, description: str, timeout: int = 30) -> bool:
    """
    Запрашивает подтверждение действия у пользователя
    Возвращает True если подтвердил, False если отменил или таймаут
    """
    embed = EmbedBuilder.warning(title, description)
    view = ConfirmView(ctx, timeout=timeout)
    
    message = await ctx.send(embed=embed, view=view)
    await view.wait()
    
    try:
        await message.delete()
    except:
        pass
    
    return view.value if view.value is not None else False

def format_seconds(seconds: int) -> str:
    """Форматирует секунды в читаемый формат (1д 2ч 3м 4с)"""
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}м")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}с")
    
    return " ".join(parts)

def format_number(number: int) -> str:
    """Форматирует число с разделителями (1000 -> 1,000)"""
    return "{:,}".format(number).replace(",", " ")

def get_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """
    Создает прогресс-бар в виде строки
    Пример: [████████░░] 80%
    """
    if maximum == 0:
        return f"[{'░' * length}] 0%"
    
    percentage = min(current / maximum, 1.0)
    filled = int(length * percentage)
    empty = length - filled
    
    bar = "█" * filled + "░" * empty
    percent = int(percentage * 100)
    
    return f"[{bar}] {percent}%"

class CooldownManager:
    """Менеджер кулдаунов для предотвращения спама"""
    
    def __init__(self):
        self.cooldowns = {}
    
    def is_on_cooldown(self, user_id: int, action: str) -> bool:
        """Проверяет, находится ли действие на кулдауне"""
        key = f"{user_id}_{action}"
        if key in self.cooldowns:
            return datetime.utcnow() < self.cooldowns[key]
        return False
    
    def set_cooldown(self, user_id: int, action: str, seconds: int):
        """Устанавливает кулдаун на действие"""
        from datetime import timedelta
        key = f"{user_id}_{action}"
        self.cooldowns[key] = datetime.utcnow() + timedelta(seconds=seconds)
    
    def get_remaining(self, user_id: int, action: str) -> int:
        """Получает оставшееся время кулдауна в секундах"""
        key = f"{user_id}_{action}"
        if key in self.cooldowns:
            remaining = (self.cooldowns[key] - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
        return 0
    
    def clear_cooldown(self, user_id: int, action: str):
        """Очищает кулдаун"""
        key = f"{user_id}_{action}"
        if key in self.cooldowns:
            del self.cooldowns[key]

# Глобальный менеджер кулдаунов
cooldown_manager = CooldownManager()
