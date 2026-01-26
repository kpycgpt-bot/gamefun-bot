import discord
from discord.ext import commands
import asyncio
from database import db
from utils import EmbedBuilder, Checks
from config import Config
import logging

logger = logging.getLogger('DiscordBot.VoiceManager')

class VoiceManager(commands.Cog):
    """Система управления приватными голосовыми каналами"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ VoiceManager инициализирован")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Обрабатывает подключения/отключения от голосовых каналов"""
        try:
            # Получаем настройки из БД
            trigger_id = db.get_config("voice_trigger_id", cast_type=int)
            category_id = db.get_config("voice_category_id", cast_type=int)
            
            # Если система не настроена - выходим
            if not trigger_id or not category_id:
                return
            
            # --- СОЗДАНИЕ ПРИВАТНОГО КАНАЛА ---
            if after.channel and after.channel.id == trigger_id:
                await self._create_private_channel(member, category_id)
            
            # --- УДАЛЕНИЕ ПУСТОГО КАНАЛА ---
            if before.channel and before.channel.category_id == category_id:
                await self._delete_empty_channel(before.channel, trigger_id)
        
        except Exception as e:
            logger.error(f"Ошибка в on_voice_state_update: {e}", exc_info=True)
    
    async def _create_private_channel(self, member: discord.Member, category_id: int):
        """Создает приватный голосовой канал для пользователя"""
        try:
            guild = member.guild
            category = guild.get_channel(category_id)
            
            if not category:
                logger.warning(f"Категория {category_id} не найдена")
                return
            
            # Проверяем, не создал ли пользователь уже канал
            existing_channels = await db.get_user_voice_channels(member.id)
            for channel_id in existing_channels:
                channel = guild.get_channel(channel_id)
                if channel and len(channel.members) > 0:
                    # У пользователя уже есть активный канал
                    try:
                        await member.move_to(channel)
                        return
                    except:
                        pass
            
            # Настройка прав доступа
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    connect=True,
                    view_channel=True
                ),
                member: discord.PermissionOverwrite(
                    connect=True,
                    move_members=True,
                    manage_channels=True,
                    mute_members=True,
                    deafen_members=True,
                    priority_speaker=True
                )
            }
            
            # Создаем канал
            new_channel = await guild.create_voice_channel(
                name=f"🔊┃{member.display_name}",
                category=category,
                overwrites=overwrites,
                user_limit=0,  # Без ограничений по умолчанию
                reason=f"Приватный канал для {member}"
            )
            
            # Сохраняем в БД
            await db.add_voice_channel(new_channel.id, member.id)
            
            # Перемещаем пользователя
            await member.move_to(new_channel)
            
            logger.info(f"Создан голосовой канал {new_channel.id} для {member} ({member.id})")
            
        except discord.Forbidden:
            logger.error(f"Нет прав для создания канала для {member}")
        except Exception as e:
            logger.error(f"Ошибка создания канала для {member}: {e}", exc_info=True)
    
    async def _delete_empty_channel(self, channel: discord.VoiceChannel, trigger_id: int):
        """Удаляет пустой приватный канал"""
        try:
            # Не трогаем канал-триггер
            if channel.id == trigger_id:
                return
            
            # Если канал не пуст - выходим
            if len(channel.members) > 0:
                return
            
            # Ждем 5 секунд (вдруг пользователь переподключается)
            await asyncio.sleep(5)
            
            # Проверяем еще раз
            channel = self.bot.get_channel(channel.id)
            if not channel:
                await db.remove_voice_channel(channel.id)
                return
            
            if len(channel.members) == 0:
                # Удаляем из БД
                await db.remove_voice_channel(channel.id)
                # Удаляем канал
                await channel.delete(reason="Приватный канал опустел")
                logger.info(f"Удален пустой голосовой канал {channel.id}")
        
        except discord.NotFound:
            # Канал уже удален
            await db.remove_voice_channel(channel.id)
        except discord.Forbidden:
            logger.error(f"Нет прав для удаления канала {channel.id}")
        except Exception as e:
            logger.error(f"Ошибка удаления канала: {e}", exc_info=True)
    
    @commands.command(name='lock', aliases=['закрыть'])
    async def lock(self, ctx):
        """🔒 Закрыть твою голосовую комнату"""
        if not ctx.author.voice:
            embed = EmbedBuilder.error("Ошибка", "Ты не находишься в голосовом канале!")
            return await ctx.send(embed=embed, delete_after=5)
        
        channel = ctx.author.voice.channel
        owner_id = await db.get_voice_owner(channel.id)
        
        # Проверяем права (владелец или админ)
        is_admin = ctx.author.guild_permissions.administrator
        
        if owner_id != ctx.author.id and not is_admin:
            embed = EmbedBuilder.error("Отказано", "Это не твоя комната!")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                connect=False,
                reason=f"Заблокирован {ctx.author}"
            )
            embed = EmbedBuilder.success(
                "Комната заблокирована",
                f"🔒 **{channel.name}** закрыта для всех"
            )
            await ctx.send(embed=embed, delete_after=10)
            logger.info(f"{ctx.author} заблокировал канал {channel.id}")
        except discord.Forbidden:
            embed = EmbedBuilder.error("Ошибка", "У меня нет прав для изменения канала")
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='unlock', aliases=['открыть'])
    async def unlock(self, ctx):
        """🔓 Открыть твою голосовую комнату"""
        if not ctx.author.voice:
            embed = EmbedBuilder.error("Ошибка", "Ты не находишься в голосовом канале!")
            return await ctx.send(embed=embed, delete_after=5)
        
        channel = ctx.author.voice.channel
        owner_id = await db.get_voice_owner(channel.id)
        
        is_admin = ctx.author.guild_permissions.administrator
        
        if owner_id != ctx.author.id and not is_admin:
            embed = EmbedBuilder.error("Отказано", "Это не твоя комната!")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                connect=True,
                reason=f"Разблокирован {ctx.author}"
            )
            embed = EmbedBuilder.success(
                "Комната разблокирована",
                f"🔓 **{channel.name}** открыта для всех"
            )
            await ctx.send(embed=embed, delete_after=10)
            logger.info(f"{ctx.author} разблокировал канал {channel.id}")
        except discord.Forbidden:
            embed = EmbedBuilder.error("Ошибка", "У меня нет прав для изменения канала")
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='limit', aliases=['лимит'])
    async def limit(self, ctx, limit: int = 0):
        """
        👥 Установить лимит пользователей в комнате
        
        Использование:
        !limit 5 - установить лимит 5 человек
        !limit 0 - убрать лимит
        """
        if not ctx.author.voice:
            embed = EmbedBuilder.error("Ошибка", "Ты не находишься в голосовом канале!")
            return await ctx.send(embed=embed, delete_after=5)
        
        channel = ctx.author.voice.channel
        owner_id = await db.get_voice_owner(channel.id)
        
        is_admin = ctx.author.guild_permissions.administrator
        
        if owner_id != ctx.author.id and not is_admin:
            embed = EmbedBuilder.error("Отказано", "Это не твоя комната!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if limit < 0 or limit > 99:
            embed = EmbedBuilder.error("Ошибка", "Лимит должен быть от 0 до 99!")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            await channel.edit(user_limit=limit, reason=f"Изменен лимит {ctx.author}")
            
            if limit == 0:
                text = "♾️ Лимит пользователей снят"
            else:
                text = f"👥 Лимит установлен: **{limit}** человек"
            
            embed = EmbedBuilder.success("Лимит изменен", text)
            await ctx.send(embed=embed, delete_after=10)
            logger.info(f"{ctx.author} установил лимит {limit} для канала {channel.id}")
        except discord.Forbidden:
            embed = EmbedBuilder.error("Ошибка", "У меня нет прав для изменения канала")
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='rename', aliases=['переименовать'])
    async def rename(self, ctx, *, name: str):
        """
        ✏️ Переименовать твою голосовую комнату
        
        Использование:
        !rename Новое название
        """
        if not ctx.author.voice:
            embed = EmbedBuilder.error("Ошибка", "Ты не находишься в голосовом канале!")
            return await ctx.send(embed=embed, delete_after=5)
        
        channel = ctx.author.voice.channel
        owner_id = await db.get_voice_owner(channel.id)
        
        is_admin = ctx.author.guild_permissions.administrator
        
        if owner_id != ctx.author.id and not is_admin:
            embed = EmbedBuilder.error("Отказано", "Это не твоя комната!")
            return await ctx.send(embed=embed, delete_after=5)
        
        if len(name) > 100:
            embed = EmbedBuilder.error("Ошибка", "Название слишком длинное (макс. 100 символов)")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            await channel.edit(name=name, reason=f"Переименован {ctx.author}")
            embed = EmbedBuilder.success(
                "Комната переименована",
                f"✏️ Новое название: **{name}**"
            )
            await ctx.send(embed=embed, delete_after=10)
            logger.info(f"{ctx.author} переименовал канал {channel.id} в '{name}'")
        except discord.Forbidden:
            embed = EmbedBuilder.error("Ошибка", "У меня нет прав для изменения канала")
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='claim', aliases=['забрать'])
    async def claim(self, ctx):
        """👑 Забрать владение комнатой, если владелец вышел"""
        if not ctx.author.voice:
            embed = EmbedBuilder.error("Ошибка", "Ты не находишься в голосовом канале!")
            return await ctx.send(embed=embed, delete_after=5)
        
        channel = ctx.author.voice.channel
        owner_id = await db.get_voice_owner(channel.id)
        
        if not owner_id:
            embed = EmbedBuilder.error("Ошибка", "Это не приватная комната!")
            return await ctx.send(embed=embed, delete_after=5)
        
        # Проверяем, есть ли владелец в канале
        owner = ctx.guild.get_member(owner_id)
        if owner and owner in channel.members:
            embed = EmbedBuilder.error("Ошибка", f"Владелец {owner.mention} еще в канале!")
            return await ctx.send(embed=embed, delete_after=5)
        
        try:
            # Меняем владельца в БД
            await db.remove_voice_channel(channel.id)
            await db.add_voice_channel(channel.id, ctx.author.id)
            
            # Обновляем права
            await channel.set_permissions(
                ctx.author,
                connect=True,
                move_members=True,
                manage_channels=True,
                mute_members=True,
                deafen_members=True,
                priority_speaker=True
            )
            
            embed = EmbedBuilder.success(
                "Владение передано",
                f"👑 {ctx.author.mention} теперь владелец этой комнаты!"
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} забрал владение каналом {channel.id}")
        except discord.Forbidden:
            embed = EmbedBuilder.error("Ошибка", "У меня нет прав для изменения канала")
            await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name='voicepanel', aliases=['войспанель'])
    @commands.has_permissions(administrator=True)
    async def voicepanel(self, ctx):
        """📋 Показать панель управления голосовыми каналами"""
        embed = discord.Embed(
            title="🔊 Система приватных голосовых каналов",
            description="Зайди в канал **➕ Создать комнату**, чтобы получить свой приватный голосовой канал!",
            color=Config.COLOR_INFO
        )
        
        embed.add_field(
            name="📝 Команды управления",
            value=f"`{Config.PREFIX}lock` - закрыть комнату\n"
                  f"`{Config.PREFIX}unlock` - открыть комнату\n"
                  f"`{Config.PREFIX}limit <число>` - установить лимит\n"
                  f"`{Config.PREFIX}rename <название>` - переименовать\n"
                  f"`{Config.PREFIX}claim` - забрать владение (если владелец вышел)",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Информация",
            value="• Комната автоматически удаляется когда пустеет\n"
                  "• Владелец имеет полные права на управление\n"
                  "• Администраторы могут управлять любой комнатой",
            inline=False
        )
        
        embed.set_footer(text=f"Используй {Config.PREFIX}help для списка всех команд")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Регистрация кога"""
    await bot.add_cog(VoiceManager(bot))
