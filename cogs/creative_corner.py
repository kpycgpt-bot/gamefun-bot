import discord
from discord.ext import commands
import config  # Берем настройки из конфига

class CreativeCorner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Проверяем, совпадает ли имя канала или его ID с настройками
        is_creative_name = message.channel.name in config.CREATIVE_CHANNELS_NAMES
        is_creative_id = message.channel.id in config.CREATIVE_CHANNELS_IDS
        
        if is_creative_name or is_creative_id:
            if message.attachments or "http" in message.content:
                try:
                    await message.add_reaction("❤️")
                    await message.add_reaction("🔥")
                    await message.add_reaction("⭐")
                except discord.Forbidden:
                    pass 
                except Exception as e:
                    print(f"[Creative] Ошибка реакции: {e}")

async def setup(bot):
    await bot.add_cog(CreativeCorner(bot))