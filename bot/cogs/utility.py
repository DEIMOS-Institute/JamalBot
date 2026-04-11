from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check the bot latency.")
    async def ping(self, ctx: commands.Context) -> None:
        """Respond with the bot latency."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.reply(f"Pong! `{latency_ms}ms`")

    @commands.hybrid_command(name="hello", description="Say hello to the bot.")
    async def hello(self, ctx: commands.Context) -> None:
        """Simple starter command."""
        await ctx.reply(f"Hey, {ctx.author.mention}.")

    @commands.hybrid_command(name="say", description="Make the bot repeat a message.")
    async def say(self, ctx: commands.Context, *, message: str) -> None:
        """Repeat a user-provided message."""
        await ctx.reply(message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Utility(bot))