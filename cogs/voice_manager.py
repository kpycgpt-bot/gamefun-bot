import discord
from discord.ext import commands
import config
import asyncio

class VoiceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_owners = {} # {channel_id: user_id}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 1. Логика создания (Join to Create)
        if after.channel and after.channel.id == config.VOICE_TRIGGER_CHANNEL:
            category = member.guild.get_channel(config.VOICE_CATEGORY_ID)
            
            # Создаем канал
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(connect=True),
                member: discord.PermissionOverwrite(connect=True, move_members=True, manage_channels=True)
            }
            
            new_channel = await member.guild.create_voice_channel(
                name=f"🔊┃{member.display_name}",
                category=category,
                overwrites=overwrites
            )
            
            # Запоминаем владельца
            self.voice_owners[new_channel.id] = member.id
            
            # Перекидываем
            await member.move_to(new_channel)

        # 2. Удаление пустых
        if before.channel and before.channel.category_id == config.VOICE_CATEGORY_ID:
            if before.channel.id != config.VOICE_TRIGGER_CHANNEL:
                if len(before.channel.members) == 0:
                    await asyncio.sleep(5) # Ждем 5 сек
                    if len(before.channel.members) == 0:
                        try:
                            await before.channel.delete()
                            if before.channel.id in self.voice_owners:
                                del self.voice_owners[before.channel.id]
                        except: pass

    # --- КОМАНДЫ УПРАВЛЕНИЯ ГОЛОСОМ ---

    @commands.command()
    async def lock(self, ctx):
        """Закрывает твою голосовую комнату."""
        if not ctx.author.voice:
            return await ctx.send("❌ Ты не в войсе.")
        
        channel = ctx.author.voice.channel
        
        # Проверка владельца (по словарю или правам)
        is_owner = self.voice_owners.get(channel.id) == ctx.author.id or channel.permissions_for(ctx.author).manage_channels
        
        if is_owner:
            await channel.set_permissions(ctx.guild.default_role, connect=False)
            await ctx.send(f"🔒 Комната **{channel.name}** закрыта для всех.")
        else:
            await ctx.send("❌ Это не твоя комната.")

    @commands.command()
    async def unlock(self, ctx):
        """Открывает твою голосовую комнату."""
        if not ctx.author.voice: return
        channel = ctx.author.voice.channel
        
        is_owner = self.voice_owners.get(channel.id) == ctx.author.id or channel.permissions_for(ctx.author).manage_channels
        
        if is_owner:
            await channel.set_permissions(ctx.guild.default_role, connect=True)
            await ctx.send(f"🔓 Комната **{channel.name}** открыта.")
        else:
            await ctx.send("❌ Это не твоя комната.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def voicepanel(self, ctx):
        """Инструкция по голосу (опционально)"""
        embed = discord.Embed(
            title="🔊 Голосовая система",
            description="Зайди в канал **➕ Создать комнату**, чтобы получить личный войс.\n\n"
                        "**Команды управления:**\n"
                        "`!lock` — закрыть комнату\n"
                        "`!unlock` — открыть комнату",
            color=0x3498DB
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VoiceManager(bot))