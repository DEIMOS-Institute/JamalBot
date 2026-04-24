import discord
from discord import app_commands
import random
import time
from ..data import get_player_data, schedule_save
from ..constants import RANDOM_ROASTS

class SocialCommands:
    def __init__(self):
        pass

    @app_commands.command(name="beef")
    @app_commands.describe(user="Who to start beef with")
    async def beef(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't beef with yourself.", ephemeral=True)
            return
        data = get_player_data(interaction.user.id)
        if user.id in data.get("beefs", []):
            await interaction.response.send_message("You're already beefing with them!", ephemeral=True)
            return
        data["beefs"].append(user.id)
        schedule_save()
        await interaction.response.send_message(f"🥩 <@{interaction.user.id}> is now beefing with <@{user.id}>! Watch your back.")

    @app_commands.command(name="squash")
    @app_commands.describe(user="Who to end beef with")
    async def squash(self, interaction: discord.Interaction, user: discord.Member):
        data = get_player_data(interaction.user.id)
        if user.id not in data.get("beefs", []):
            await interaction.response.send_message("You ain't beefing with them.", ephemeral=True)
            return
        data["beefs"].remove(user.id)
        schedule_save()
        await interaction.response.send_message(f"🤝 <@{interaction.user.id}> squashed beef with <@{user.id}>. Peace out.")

    @app_commands.command(name="diss")
    @app_commands.describe(user="Who to diss")
    async def diss(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't diss yourself.", ephemeral=True)
            return
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        if data.get("lastDiss") and now - data["lastDiss"] < 60 * 60 * 1000:
            await interaction.response.send_message("You just dropped a diss. Wait a bit.", ephemeral=True)
            return
        diss = random.choice(RANDOM_ROASTS)
        data["lastDiss"] = now
        schedule_save()
        await interaction.response.send_message(f"🎤 <@{interaction.user.id}> drops a diss on <@{user.id}>: **{diss}**")

    @app_commands.command(name="slide")
    @app_commands.describe(user="Who to slide into DMs of")
    async def slide(self, interaction: discord.Interaction, user: discord.Member):
        responses = [
            f"<@{interaction.user.id}> slides into <@{user.id}>'s DMs... and gets left on read. 😔",
            f"<@{interaction.user.id}> slides in smooth. <@{user.id}> responds! 😏",
            f"<@{interaction.user.id}> tries to slide but trips. Embarrassing.",
        ]
        await interaction.response.send_message(random.choice(responses))

    @app_commands.command(name="opp")
    @app_commands.describe(user="Call someone an opp")
    async def opp(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(f"🔫 <@{interaction.user.id}> just called <@{user.id}> an OPP! On sight!")

    @app_commands.command(name="snitch")
    @app_commands.describe(user="Report a user (joke)")
    async def snitch(self, interaction: discord.Interaction, user: discord.Member):
        responses = [
            f"📞 <@{interaction.user.id}> snitched on <@{user.id}>! The 12 are on their way!",
            f"🐀 <@{interaction.user.id}> is a RAT! Everybody run!",
            f"<@{interaction.user.id}> tried to snitch but the line was busy.",
        ]
        await interaction.response.send_message(random.choice(responses))

    @app_commands.command(name="court")
    @app_commands.describe(user="Take someone to hood court")
    async def court(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't take yourself to court.", ephemeral=True)
            return
        await interaction.response.send_message(f"⚖️ <@{interaction.user.id}> is taking <@{user.id}> to HOOD COURT! The jury will decide their fate.")

    @app_commands.command(name="gucci")
    async def gucci(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        data["dripLevel"] = data.get("dripLevel", 1) + 1
        schedule_save()
        await interaction.response.send_message(f"👔 <@{interaction.user.id}> put on that Gucci fit! Drip level +1 (now {data['dripLevel']})")

    @app_commands.command(name="icedout")
    async def icedout(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        drip = data.get("dripLevel", 1)
        if drip >= 5:
            await interaction.response.send_message(f"💎❄️ <@{interaction.user.id}> is ICED OUT! Drip level {drip}!")
        else:
            await interaction.response.send_message(f"<@{interaction.user.id}> is trying to be iced out but needs more drip (current: {drip})")