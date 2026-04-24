import discord
from discord import app_commands
import time
from typing import Optional
from ..data import get_player_data, player_data, schedule_save
from ..utils import get_street_rank
from ..constants import HOODS

class ProfileCommands:
    pass

    @app_commands.command(name="profile")
    @app_commands.describe(user="User to view")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        data = get_player_data(target.id)
        rank = get_street_rank(data["bread"], data["streetCred"])

        embed = discord.Embed(
            title=f"{target.display_name}'s Hood Profile",
            color=0x00ff00
        )
        embed.add_field(name="💰 Bread", value=f"{data['bread']:,}", inline=True)
        embed.add_field(name="⭐ Street Cred", value=data["streetCred"], inline=True)
        embed.add_field(name="🏆 Rank", value=rank["name"], inline=True)
        embed.add_field(name="🔥 Heat", value=f"{data['heat']}%", inline=True)
        embed.add_field(name="📈 Rep", value=data.get("rep", 0), inline=True)
        embed.add_field(name="👑 Crew", value=data.get("crew", "None"), inline=True)
        embed.add_field(name="🏚️ Hood", value=HOODS[data["hood"]["name"]]["fullName"] if data["hood"]["name"] else "None", inline=True)
        embed.add_field(name="💨 Smoke Count", value=data.get("smokeCount", 0), inline=True)
        embed.add_field(name="💎 Drip Level", value=data.get("dripLevel", 1), inline=True)
        embed.add_field(name="🏠 Turf", value=data.get("turf", "None"), inline=True)

        badges = ", ".join(data.get("badges", [])) or "None"
        embed.add_field(name="🏅 Badges", value=badges, inline=False)

        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="rep")
    @app_commands.describe(user="User to view")
    async def rep(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        data = get_player_data(target.id)
        await interaction.response.send_message(f"📈 {target.display_name} has **{data.get('rep', 0)}** reputation.")

    @app_commands.command(name="repgive")
    @app_commands.describe(user="User to give rep to")
    async def repgive(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("Can't rep yourself.", ephemeral=True)
            return

        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        if data.get("lastRepGiven") and now - data["lastRepGiven"] < 24 * 60 * 60 * 1000:
            await interaction.response.send_message("You can only give rep once per day.", ephemeral=True)
            return

        target_data = get_player_data(user.id)
        target_data["rep"] = target_data.get("rep", 0) + 1
        data["lastRepGiven"] = now
        schedule_save()
        await interaction.response.send_message(f"✅ Gave +1 rep to <@{user.id}>!")

    @app_commands.command(name="rich")
    async def rich(self, interaction: discord.Interaction):
        sorted_players = sorted(player_data.items(), key=lambda x: x[1]["bread"] + x[1].get("safeBalance", 0), reverse=True)[:10]
        if not sorted_players:
            await interaction.response.send_message("No players yet.")
            return
        embed = discord.Embed(title="💰 Richest in the Hood", color=0xffd700)
        description = "\n".join(
            f"{i+1}. <@{uid}> — **{data['bread'] + data.get('safeBalance', 0):,}** total bread"
            for i, (uid, data) in enumerate(sorted_players)
        )
        embed.description = description
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="guide")
    async def guide(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏚️ Hood Survival Guide (For These White Kids)",
            description="Welcome to the block. Here's how to not get clowned:",
            color=0x8B4513
        )
        embed.add_field(name="1. Get Your Bread Up", value="Use `/daily`, `/hustle work`, and `/crime` to earn bread.", inline=False)
        embed.add_field(name="2. Watch Your Heat", value="Too much heat and the 12 will raid you. Keep it low.", inline=False)
        embed.add_field(name="3. Join a Hood", value="Use `/hood pick` to rep a set. Each hood got different perks.", inline=False)
        embed.add_field(name="4. Invest and Save", value="Use `/safe` to protect your bread. `/invest` to grow it.", inline=False)
        embed.add_field(name="5. Don't Get Caught Slippin'", value="Always check `/jamal block` before moving weight.", inline=False)
        embed.add_field(name="6. Respect the Plug", value="Shikyo got premium services. Check `/shop`.", inline=False)
        embed.add_field(name="7. TK? Who's That?", value="That one dude... you know. He run things around here.", inline=False)
        embed.set_footer(text="Stay dangerous, cuz.")
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="badges")
    @app_commands.describe(user="User to view")
    async def badges(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        data = get_player_data(target.id)
        badges = data.get("badges", [])
        if not badges:
            await interaction.response.send_message(f"{target.display_name} has no badges yet.")
        else:
            await interaction.response.send_message(f"🏅 {target.display_name}'s Badges: {', '.join(badges)}")

    @app_commands.command(name="stats")
    async def stats(self, interaction: discord.Interaction):
        total_players = len(player_data)
        total_bread = sum(d["bread"] for d in player_data.values())
        total_smokes = sum(d.get("smokeCount", 0) for d in player_data.values())
        total_roasts = sum(d.get("roastsGiven", 0) for d in player_data.values())

        embed = discord.Embed(title="📊 Hood Stats", color=0x00ff00)
        embed.add_field(name="Total Players", value=total_players, inline=True)
        embed.add_field(name="Total Bread", value=f"{total_bread:,}", inline=True)
        embed.add_field(name="Total Smokes", value=total_smokes, inline=True)
        embed.add_field(name="Roasts Thrown", value=total_roasts, inline=True)
        await interaction.response.send_message(embeds=[embed])