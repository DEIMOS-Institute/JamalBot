import discord
from discord import app_commands
import time
from ..data import get_player_data, player_data, schedule_save
from ..constants import HOODS

class HoodGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="hood", description="🏙️ Hood system – rep your turf")

    @app_commands.command(name="pick")
    @app_commands.describe(hood="The hood you want to rep")
    @app_commands.choices(hood=[
        app_commands.Choice(name="🏚️ Southside – The Bottom", value="southside"),
        app_commands.Choice(name="🏙️ Northside – Uptown", value="northside"),
        app_commands.Choice(name="🏭 Eastside – The Industrial", value="eastside"),
        app_commands.Choice(name="🏡 Westside – The Suburbs", value="westside"),
        app_commands.Choice(name="🏢 Downtown – The Core", value="downtown"),
    ])
    async def pick(self, interaction: discord.Interaction, hood: str):
        data = get_player_data(interaction.user.id)
        if data["hood"]["name"]:
            await interaction.response.send_message(
                f"You're already repping **{HOODS[data['hood']['name']]['fullName']}**. If you want to switch, use `/hood change` (costs 1,000,000 bread).",
                ephemeral=True
            )
            return

        data["hood"]["name"] = hood
        data["hood"]["joined"] = int(time.time() * 1000)
        data["hood"]["loyalty"] = 0
        data["hood"]["lastLoyaltyUpdate"] = int(time.time() * 1000)
        schedule_save()

        hood_info = HOODS[hood]
        embed = discord.Embed(
            title=f"{hood_info['emoji']} Welcome to {hood_info['fullName']}",
            description=hood_info["story"],
            color=hood_info["color"]
        )
        embed.add_field(name="🔥 Hood Perks", value=hood_info["perks"]["description"])
        embed.set_footer(text="Represent! You can never change for free.")
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="info")
    async def info(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if not data["hood"]["name"]:
            await interaction.response.send_message("You haven't picked a hood yet! Use `/hood pick` to choose.", ephemeral=True)
            return

        hood_info = HOODS[data["hood"]["name"]]
        embed = discord.Embed(
            title=f"{hood_info['emoji']} {hood_info['fullName']}",
            description=hood_info["story"],
            color=hood_info["color"]
        )
        embed.add_field(name="🔥 Your Perks", value=hood_info["perks"]["description"])
        embed.add_field(name="📊 Loyalty", value=f"Level {data['hood']['loyalty'] // 100} ({data['hood']['loyalty']} points)")
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="stats")
    async def stats(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if not data["hood"]["name"]:
            await interaction.response.send_message("You haven't picked a hood yet!", ephemeral=True)
            return

        hood_info = HOODS[data["hood"]["name"]]
        loyalty_level = data["hood"]["loyalty"] // 100
        progress = data["hood"]["loyalty"] % 100
        bar = "▓" * (progress // 10) + "░" * (10 - progress // 10)

        embed = discord.Embed(
            title=f"{hood_info['emoji']} Your Hood Stats",
            color=hood_info["color"]
        )
        embed.add_field(name="Hood", value=hood_info["fullName"], inline=True)
        embed.add_field(name="Loyalty Level", value=str(loyalty_level), inline=True)
        embed.add_field(name="Progress to Next", value=f"{bar} {progress}/100", inline=False)
        embed.add_field(name="Loyalty Points", value=str(data["hood"]["loyalty"]), inline=True)
        days_repped = (int(time.time() * 1000) - data["hood"]["joined"]) // 86400000
        embed.add_field(name="Days Repped", value=str(days_repped), inline=True)
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="change")
    async def change(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if not data["hood"]["name"]:
            await interaction.response.send_message("You haven't even picked a hood yet! Use `/hood pick` first.", ephemeral=True)
            return

        cost = 1_000_000
        if data["bread"] < cost:
            await interaction.response.send_message(f"You need **{cost:,}** bread to switch hoods.", ephemeral=True)
            return

        data["bread"] -= cost
        data["hood"] = {"name": None, "joined": 0, "loyalty": 0, "lastLoyaltyUpdate": 0}
        schedule_save()
        await interaction.response.send_message(f"💰 You paid **{cost:,}** bread and are now hoodless. Use `/hood pick` to choose a new turf.", ephemeral=True)

    @app_commands.command(name="loyalty")
    async def loyalty(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if not data["hood"]["name"]:
            await interaction.response.send_message("You haven't picked a hood yet!", ephemeral=True)
            return

        hood_info = HOODS[data["hood"]["name"]]
        loyalty_level = data["hood"]["loyalty"] // 100
        embed = discord.Embed(
            title=f"{hood_info['emoji']} Loyalty Level {loyalty_level}",
            description="Loyalty unlocks perks:",
            color=hood_info["color"]
        )
        embed.add_field(name="Level 0", value="Base perks", inline=False)
        embed.add_field(name="Level 1 (100 pts)", value="Unlock hood‑only shop item", inline=False)
        embed.add_field(name="Level 2 (300 pts)", value="Hood title (e.g., 'Southside Legend')", inline=False)
        embed.add_field(name="Level 3 (1000 pts)", value="Permanent hood‑wide buff for all members", inline=False)
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        hood_totals = {
            "southside": {"count": 0, "wealth": 0},
            "northside": {"count": 0, "wealth": 0},
            "eastside": {"count": 0, "wealth": 0},
            "westside": {"count": 0, "wealth": 0},
            "downtown": {"count": 0, "wealth": 0},
        }
        for uid, data in player_data.items():
            hood_name = data["hood"].get("name")
            if hood_name and hood_name in hood_totals:
                hood_totals[hood_name]["count"] += 1
                hood_totals[hood_name]["wealth"] += data["bread"] + data.get("stashedBread", 0) + data.get("safeBalance", 0)

        sorted_hoods = sorted(
            [(name, stats) for name, stats in hood_totals.items() if stats["count"] > 0],
            key=lambda x: x[1]["wealth"],
            reverse=True
        )
        if not sorted_hoods:
            await interaction.response.send_message("No hoods have members yet.")
            return

        embed = discord.Embed(title="🏆 Hood Leaderboard", color=0xffd700)
        description = "\n".join(
            f"{i+1}. {HOODS[name]['emoji']} **{HOODS[name]['name']}** — {stats['count']} members — **{stats['wealth']:,}** total wealth"
            for i, (name, stats) in enumerate(sorted_hoods)
        )
        embed.description = description
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="turf")
    async def turf(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if not data["hood"]["name"]:
            await interaction.response.send_message("You need a hood first!", ephemeral=True)
            return
        if data["turf"]:
            await interaction.response.send_message(f"You already claim **{data['turf']}**.", ephemeral=True)
            return
        cost = 10000
        if data["bread"] < cost:
            await interaction.response.send_message(f"You need {cost} bread.", ephemeral=True)
            return
        data["bread"] -= cost
        data["turf"] = f"{data['hood']['name']} Block"
        data["turfIncome"] = 100
        schedule_save()
        await interaction.response.send_message(f"🏠 You claimed **{data['turf']}**! Passive income: {data['turfIncome']}/day.")