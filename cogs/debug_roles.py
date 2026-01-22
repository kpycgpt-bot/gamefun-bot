import discord
from discord.ext import commands

class DebugRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def checkroles(self, ctx):
        """Выводит точные названия всех ролей для настройки."""
        text = "📋 **ТОЧНЫЕ НАЗВАНИЯ РОЛЕЙ (Скопируй в код):**\n\n"
        
        for role in ctx.guild.roles:
            if role.name == "@everyone": continue
            # Форматируем готовый код для копирования
            text += f'`"role_name": "{role.name}",`\n'

        # Разбиваем, если слишком длинное
        if len(text) > 2000:
            part1 = text[:1900]
            part2 = text[1900:]
            await ctx.send(part1)
            await ctx.send(part2)
        else:
            await ctx.send(text)

async def setup(bot):
    await bot.add_cog(DebugRoles(bot))