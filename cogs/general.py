from discord.ext import commands
import discord


class GFGeneral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gf_ping")
    async def gf_ping(self, ctx):
        """Проверяет ответ бота."""
        await ctx.send("GF Pong!")

    @commands.command(name="gf_testvoice")
    async def gf_testvoice(self, ctx):
        """Проверяет права бота в голосовом канале."""
        if ctx.author.voice is None:
            await ctx.send("Ты не находишься в голосовом канале.")
            return

        channel = ctx.author.voice.channel
        perms = channel.permissions_for(ctx.guild.me)

        await ctx.send(
            f"Права в канале **{channel.name}**:\n"
            f"Connect: {perms.connect}\n"
            f"Speak: {perms.speak}\n"
            f"View: {perms.view_channel}"
        )


async def setup(bot):
    await bot.add_cog(GFGeneral(bot))
