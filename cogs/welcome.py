import discord
from discord.ext import commands
import config

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Получаем канал приветствий по ID из конфига
        channel = member.guild.get_channel(config.WELCOME_CHANNEL)
        
        # Ищем каналы правил и ролей по имени для ссылок
        rules_channel = discord.utils.get(member.guild.text_channels, name="📜-rules")
        roles_channel = discord.utils.get(member.guild.text_channels, name="🎭-choose-your-interest")
        
        # Формируем ссылки (если каналы найдены)
        rules_link = rules_channel.mention if rules_channel else "#правила"
        roles_link = roles_channel.mention if roles_channel else "#выбор-ролей"

        if channel:
            embed = discord.Embed(
                title=f"👋 Добро пожаловать, {member.display_name}!",
                description=(
                    f"Рады видеть тебя в **{member.guild.name}**!\n\n"
                    f"📍 Сначала загляни в {rules_link}, чтобы знать правила.\n"
                    f"🎭 А затем выбери игры в {roles_link}."
                ),
                color=discord.Color.blue()
            )
            
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            
            embed.set_footer(text=f"Теперь нас {member.guild.member_count}!")
            
            await channel.send(content=member.mention, embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))