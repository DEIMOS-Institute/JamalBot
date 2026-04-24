import discord
from discord import app_commands
from ..utils import niggifier

class UtilityCommands:
    def __init__(self):
        pass

    @app_commands.command(name="niggifier")
    @app_commands.describe(text="The text to transform")
    async def niggifier_cmd(self, interaction: discord.Interaction, text: str):
        result = niggifier(text)
        await interaction.response.send_message(result or "Error")

    @app_commands.command(name="fetchuser")
    @app_commands.describe(userid="The User ID")
    async def fetchuser(self, interaction: discord.Interaction, userid: str):
        try:
            user = await interaction.client.fetch_user(int(userid))
            embed = discord.Embed(title="User Information", color=0x00ff00)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="Username", value=user.name, inline=True)
            embed.add_field(name="User ID", value=user.id, inline=True)
            embed.add_field(name="Bot", value="Yes" if user.bot else "No", inline=True)
            embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d"), inline=True)
            await interaction.response.send_message(embeds=[embed])
        except Exception:
            await interaction.response.send_message("Could not find a user with that ID.", ephemeral=True)

    @app_commands.command(name="help")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🆘 Jamal Bot Help",
            description="Here's all the commands you need to survive the hood:",
            color=0x00ff00
        )
        embed.add_field(name="💰 Economy", value="`/daily` `/weekly` `/monthly` `/shop` `/buy` `/sell` `/inventory` `/safe` `/loan` `/invest` `/leaderboard`", inline=False)
        embed.add_field(name="🎮 Games", value="`/games tictactoe` `/games blackjack` `/games rps` `/games roulette` `/games coinflip` `/games horse` `/games bet`", inline=False)
        embed.add_field(name="🔫 Crime", value="`/crime crime` `/crime rob` `/crime drill` `/crime trap` `/crime stickup` `/crime grow` `/crime sellweed`", inline=False)
        embed.add_field(name="💼 Hustle", value="`/hustle work` `/hustle random` `/hustle corner` `/hustle freestyle`", inline=False)
        embed.add_field(name="👤 Jamal", value="`/jamal give` `/jamal lick` `/jamal stash` `/jamal dice` `/jamal smoke` `/jamal drip`", inline=False)
        embed.add_field(name="🏙️ Hood", value="`/hood pick` `/hood info` `/hood turf` `/hood leaderboard`", inline=False)
        embed.add_field(name="📊 Profile", value="`/profile profile` `/profile rep` `/profile guide` `/profile rich`", inline=False)
        embed.add_field(name="🎭 Social", value="`/social beef` `/social diss` `/social court` `/social gucci`", inline=False)
        embed.add_field(name="🎉 Fun", value="`/fun roast` `/fun 8ball` `/fun kill` `/fun joke`", inline=False)
        embed.add_field(name="🛠️ Utility", value="`/utility niggifier` `/utility help`", inline=False)
        embed.set_footer(text="Prefix commands: j!help, j!daily, j!roast @user, etc.")
        await interaction.response.send_message(embeds=[embed])