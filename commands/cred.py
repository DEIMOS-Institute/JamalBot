import discord
from discord import app_commands
import random
from ..data import get_player_data, schedule_save
from ..constants import LOOT_ITEMS

class StreetCredCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="cred", description="Street cred utilities and spending")

    @app_commands.command(name="status")
    async def cred_status(self, interaction: discord.Interaction):
        """Check your street cred level and available perks"""
        data = get_player_data(interaction.user.id)
        cred = data["streetCred"]

        # Calculate cred tier
        if cred >= 500:
            tier = "🏆 LEGENDARY"
            perks = "• 50% reduced crime heat\n• Access to exclusive events\n• Automatic respect boost"
        elif cred >= 250:
            tier = "💎 ELITE"
            perks = "• 25% reduced crime heat\n• Priority in queues\n• Better loot drops"
        elif cred >= 100:
            tier = "🔥 VETERAN"
            perks = "• 15% reduced crime heat\n• Access to veteran shops\n• Street cred multiplier"
        elif cred >= 50:
            tier = "⭐ RESPECTED"
            perks = "• 10% reduced crime heat\n• Basic perks unlocked"
        else:
            tier = "🆕 ROOKIE"
            perks = "• No special perks yet\n• Keep grinding!"

        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Street Cred",
            color=0xffd700
        )
        embed.add_field(name="Current Cred", value=f"**{cred}** ⭐", inline=True)
        embed.add_field(name="Tier", value=tier, inline=True)
        embed.add_field(name="Perks", value=perks, inline=False)

        if data.get("cred_multiplier", 1.0) > 1.0:
            embed.add_field(name="Cred Multiplier", value=f"**{data['cred_multiplier']}x** earnings", inline=True)

        if data.get("vip_pass", False):
            embed.add_field(name="VIP Status", value="✅ Active", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="boost")
    @app_commands.describe(type="Type of boost to purchase")
    @app_commands.choices(type=[
        app_commands.Choice(name="🎲 Crime Success (+10% for 1 hour)", value="crime_success"),
        app_commands.Choice(name="💰 Earnings Multiplier (1.5x for 30 min)", value="earnings_boost"),
        app_commands.Choice(name="🛡️ Heat Reduction (-25 heat)", value="heat_reduction"),
        app_commands.Choice(name="🎯 Lucky Charm (Better loot odds)", value="lucky_charm"),
    ])
    async def cred_boost(self, interaction: discord.Interaction, type: str):
        """Spend street cred for temporary boosts"""
        data = get_player_data(interaction.user.id)
        cred_costs = {
            "crime_success": 25,
            "earnings_boost": 50,
            "heat_reduction": 30,
            "lucky_charm": 20,
        }

        cost = cred_costs[type]
        if data["streetCred"] < cost:
            await interaction.response.send_message(f"You need **{cost}** street cred for this boost! You have {data['streetCred']}.", ephemeral=True)
            return

        # Apply the boost
        if type == "crime_success":
            data["active_boosts"] = data.get("active_boosts", {})
            data["active_boosts"]["crime_success"] = {
                "expires": int(__import__("time").time()) + 3600,  # 1 hour
                "multiplier": 1.1
            }
            effect = "10% crime success boost for 1 hour"
        elif type == "earnings_boost":
            data["active_boosts"] = data.get("active_boosts", {})
            data["active_boosts"]["earnings"] = {
                "expires": int(__import__("time").time()) + 1800,  # 30 min
                "multiplier": 1.5
            }
            effect = "1.5x earnings multiplier for 30 minutes"
        elif type == "heat_reduction":
            data["heat"] = max(0, data["heat"] - 25)
            effect = "Reduced heat by 25 points"
        elif type == "lucky_charm":
            data["active_boosts"] = data.get("active_boosts", {})
            data["active_boosts"]["lucky"] = {
                "expires": int(__import__("time").time()) + 3600,  # 1 hour
                "active": True
            }
            effect = "Better loot odds for 1 hour"

        data["streetCred"] -= cost
        schedule_save()

        await interaction.response.send_message(f"✅ **Street Cred Boost Activated!**\nSpent {cost} ⭐ for: {effect}")

    @app_commands.command(name="intimidate")
    @app_commands.describe(user="Player to intimidate")
    async def intimidate(self, interaction: discord.Interaction, user: discord.Member):
        """Use street cred to intimidate another player (reduces their earnings temporarily)"""
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't intimidate yourself!", ephemeral=True)
            return

        data = get_player_data(interaction.user.id)
        target_data = get_player_data(user.id)

        cred_cost = 40
        if data["streetCred"] < cred_cost:
            await interaction.response.send_message(f"You need **{cred_cost}** street cred to intimidate! You have {data['streetCred']}.", ephemeral=True)
            return

        # Success chance based on cred difference
        cred_diff = data["streetCred"] - target_data["streetCred"]
        success_chance = min(0.9, max(0.3, 0.5 + (cred_diff * 0.01)))

        if random.random() < success_chance:
            # Success - reduce target's earnings for 1 hour
            target_data["active_debuffs"] = target_data.get("active_debuffs", {})
            target_data["active_debuffs"]["intimidated"] = {
                "expires": int(__import__("time").time()) + 3600,
                "earnings_penalty": 0.7  # 30% reduction
            }

            data["streetCred"] -= cred_cost
            schedule_save()

            await interaction.response.send_message(
                f"😈 **INTIMIDATION SUCCESSFUL!**\n"
                f"You scared <@{user.id}> straight! Their earnings are reduced by 30% for 1 hour.\n"
                f"Spent {cred_cost} ⭐ street cred."
            )
        else:
            # Failure - lose some cred
            penalty = cred_cost // 2
            data["streetCred"] = max(0, data["streetCred"] - penalty)
            schedule_save()

            await interaction.response.send_message(
                f"💪 **INTIMIDATION FAILED!**\n"
                f"<@{user.id}> wasn't fazed by your street cred. You lost {penalty} ⭐."
            )

    @app_commands.command(name="respect")
    @app_commands.describe(user="Player to show respect to")
    async def show_respect(self, interaction: discord.Interaction, user: discord.Member):
        """Give street cred to another player as a sign of respect"""
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't give respect to yourself!", ephemeral=True)
            return

        data = get_player_data(interaction.user.id)
        target_data = get_player_data(user.id)

        cred_amount = 10
        if data["streetCred"] < cred_amount:
            await interaction.response.send_message(f"You need **{cred_amount}** street cred to show respect! You have {data['streetCred']}.", ephemeral=True)
            return

        data["streetCred"] -= cred_amount
        target_data["streetCred"] += cred_amount
        target_data["respect"] = target_data.get("respect", 50) + 5

        schedule_save()

        await interaction.response.send_message(
            f"🙏 **RESPECT PAID!**\n"
            f"You showed respect to <@{user.id}> and gave them {cred_amount} ⭐ street cred.\n"
            f"Their respect level increased!"
        )