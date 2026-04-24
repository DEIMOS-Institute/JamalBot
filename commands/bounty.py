import discord
from discord import app_commands
import random
import time
from ..data import get_player_data, schedule_save
from ..constants import LOOT_ITEMS

class BountyCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="bounty", description="Bounty and hit contract system")

    @app_commands.command(name="set")
    @app_commands.describe(user="Target to place bounty on", amount="Bounty amount (min 50,000)")
    async def set_bounty(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't place a bounty on yourself!", ephemeral=True)
            return

        if amount < 50000:
            await interaction.response.send_message("Minimum bounty is 50,000 bread!", ephemeral=True)
            return

        data = get_player_data(interaction.user.id)
        if data["bread"] < amount:
            await interaction.response.send_message(f"You don't have enough bread! You have {data['bread']:,}.", ephemeral=True)
            return

        # Check if bounty already exists on this target
        existing_bounties = data.get("bounties_set", [])
        for bounty in existing_bounties:
            if bounty["target_id"] == user.id and bounty["status"] == "active":
                await interaction.response.send_message("You already have an active bounty on this person!", ephemeral=True)
                return

        # Deduct bread and create bounty
        data["bread"] -= amount
        bounty_id = f"{interaction.user.id}_{user.id}_{int(time.time())}"

        bounty = {
            "id": bounty_id,
            "target_id": user.id,
            "issuer_id": interaction.user.id,
            "amount": amount,
            "claimed_by": None,
            "status": "active",
            "created_at": int(time.time()),
            "expires_at": int(time.time()) + (7 * 24 * 60 * 60),  # 7 days
        }

        if "bounties_set" not in data:
            data["bounties_set"] = []
        data["bounties_set"].append(bounty)

        # Add to global bounties
        global_bounties = interaction.client.bounties
        global_bounties[bounty_id] = bounty

        schedule_save()

        await interaction.response.send_message(
            f"💰 **BOUNTY PLACED!**\n"
            f"Target: <@{user.id}>\n"
            f"Amount: {amount:,} bread\n"
            f"Expires: <t:{bounty['expires_at']}:R>\n\n"
            f"Anyone can claim this bounty by using `/hit claim {bounty_id}`"
        )

    @app_commands.command(name="list")
    async def list_bounties(self, interaction: discord.Interaction):
        global_bounties = interaction.client.bounties
        active_bounties = [b for b in global_bounties.values() if b["status"] == "active"]

        if not active_bounties:
            await interaction.response.send_message("No active bounties right now. Be the first to place one!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎯 ACTIVE BOUNTIES",
            description="Use `/hit claim <bounty_id>` to accept a contract",
            color=0xff0000
        )

        for bounty in active_bounties[:10]:  # Show top 10
            target_name = f"<@{bounty['target_id']}>"
            issuer_name = f"<@{bounty['issuer_id']}>"
            embed.add_field(
                name=f"ID: {bounty['id'][:16]}...",
                value=f"Target: {target_name}\nReward: {bounty['amount']:,} bread\nIssuer: {issuer_name}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="withdraw")
    @app_commands.describe(bounty_id="Bounty ID to cancel")
    async def withdraw_bounty(self, interaction: discord.Interaction, bounty_id: str):
        data = get_player_data(interaction.user.id)
        bounties_set = data.get("bounties_set", [])

        for bounty in bounties_set:
            if bounty["id"] == bounty_id and bounty["status"] == "active":
                if bounty["claimed_by"] is not None:
                    await interaction.response.send_message("Can't withdraw a claimed bounty!", ephemeral=True)
                    return

                # Refund the bounty
                data["bread"] += bounty["amount"]
                bounty["status"] = "cancelled"

                # Remove from global bounties
                if bounty_id in interaction.client.bounties:
                    del interaction.client.bounties[bounty_id]

                schedule_save()
                await interaction.response.send_message(f"✅ Bounty withdrawn. {bounty['amount']:,} bread refunded.")
                return

        await interaction.response.send_message("Bounty not found or already claimed!", ephemeral=True)

class HitCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="hit", description="Hit contract execution")

    @app_commands.command(name="claim")
    @app_commands.describe(bounty_id="Bounty ID to claim")
    async def claim_hit(self, interaction: discord.Interaction, bounty_id: str):
        global_bounties = interaction.client.bounties

        if bounty_id not in global_bounties:
            await interaction.response.send_message("Bounty not found!", ephemeral=True)
            return

        bounty = global_bounties[bounty_id]
        if bounty["status"] != "active":
            await interaction.response.send_message("This bounty is no longer available!", ephemeral=True)
            return

        if bounty["claimed_by"] is not None:
            await interaction.response.send_message("This bounty has already been claimed!", ephemeral=True)
            return

        # Check if user is trying to claim their own bounty
        if bounty["issuer_id"] == interaction.user.id:
            await interaction.response.send_message("You can't claim your own bounty!", ephemeral=True)
            return

        # Check if user is the target
        if bounty["target_id"] == interaction.user.id:
            await interaction.response.send_message("You can't claim a bounty on yourself!", ephemeral=True)
            return

        # Claim the bounty
        bounty["claimed_by"] = interaction.user.id
        bounty["status"] = "claimed"
        bounty["claimed_at"] = int(time.time())

        # Add to claimer's active hits
        data = get_player_data(interaction.user.id)
        if "active_hits" not in data:
            data["active_hits"] = []
        data["active_hits"].append(bounty_id)

        schedule_save()

        await interaction.response.send_message(
            f"🔫 **HIT ACCEPTED!**\n"
            f"Target: <@{bounty['target_id']}>\n"
            f"Reward: {bounty['amount']:,} bread\n\n"
            f"Complete the hit with `/hit complete {bounty_id}`\n"
            f"⚠️ **WARNING:** Failed hits cost you 10% of the bounty amount!"
        )

    @app_commands.command(name="complete")
    @app_commands.describe(bounty_id="Bounty ID to complete", proof="Optional proof of completion")
    async def complete_hit(self, interaction: discord.Interaction, bounty_id: str, proof: str = None):
        global_bounties = interaction.client.bounties
        data = get_player_data(interaction.user.id)

        if bounty_id not in global_bounties:
            await interaction.response.send_message("Bounty not found!", ephemeral=True)
            return

        bounty = global_bounties[bounty_id]
        if bounty["claimed_by"] != interaction.user.id:
            await interaction.response.send_message("This isn't your hit to complete!", ephemeral=True)
            return

        if bounty["status"] != "claimed":
            await interaction.response.send_message("This bounty isn't in claimed status!", ephemeral=True)
            return

        # Simulate hit success (70% success rate)
        success = random.random() < 0.7

        if success:
            # Successful hit - get reward
            reward = bounty["amount"]
            data["bread"] += reward
            data["streetCred"] += 25

            bounty["status"] = "completed"
            bounty["completed_at"] = int(time.time())

            # Remove from active hits
            if bounty_id in data.get("active_hits", []):
                data["active_hits"].remove(bounty_id)

            schedule_save()

            await interaction.response.send_message(
                f"🎯 **HIT SUCCESSFUL!**\n"
                f"Target: <@{bounty['target_id']}>\n"
                f"Reward: +{reward:,} bread\n"
                f"Street Cred: +25\n\n"
                f"The streets will remember this... 🕵️"
            )
        else:
            # Failed hit - penalty
            penalty = int(bounty["amount"] * 0.1)
            data["bread"] = max(0, data["bread"] - penalty)
            data["heat"] = min(100, data["heat"] + 15)

            bounty["status"] = "failed"
            bounty["failed_at"] = int(time.time())

            # Remove from active hits
            if bounty_id in data.get("active_hits", []):
                data["active_hits"].remove(bounty_id)

            schedule_save()

            await interaction.response.send_message(
                f"💥 **HIT FAILED!**\n"
                f"Target: <@{bounty['target_id']}>\n"
                f"Penalty: -{penalty:,} bread\n"
                f"Heat: +15%\n\n"
                f"Better luck next time, soldier... 👮"
            )

    @app_commands.command(name="active")
    async def active_hits(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        active_hits = data.get("active_hits", [])

        if not active_hits:
            await interaction.response.send_message("You have no active hits. Claim one with `/hit claim <bounty_id>`", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎯 YOUR ACTIVE HITS",
            description="Complete these contracts for rewards!",
            color=0xffa500
        )

        global_bounties = interaction.client.bounties
        for bounty_id in active_hits:
            if bounty_id in global_bounties:
                bounty = global_bounties[bounty_id]
                embed.add_field(
                    name=f"ID: {bounty_id[:16]}...",
                    value=f"Target: <@{bounty['target_id']}>\nReward: {bounty['amount']:,} bread",
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)