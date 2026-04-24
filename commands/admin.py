import discord
from discord import app_commands
from ..data import get_player_data, player_data, schedule_save
from ..config import JOSE_ID

class JoseGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="jose", description="🔒 Developer commands (Jose only)")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != JOSE_ID:
            await interaction.response.send_message("🚫 **ACCESS DENIED:** Only Jose can use these commands!", ephemeral=True)
            return False
        return True

    @app_commands.command(name="give_bread")
    @app_commands.describe(user="User to give bread to", amount="Amount of bread")
    async def give_bread(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        target_data = get_player_data(user.id)
        target_data["bread"] += amount
        schedule_save()
        await interaction.response.send_message(f"✅ Gave **{amount}** bread to <@{user.id}>.", ephemeral=True)

    @app_commands.command(name="give_item")
    @app_commands.describe(user="User to give item to", item="Item name", quantity="Quantity (default: 1)")
    async def give_item(self, interaction: discord.Interaction, user: discord.Member, item: str, quantity: int = 1):
        target_data = get_player_data(user.id)
        if "inventory" not in target_data:
            target_data["inventory"] = []
        for _ in range(quantity):
            target_data["inventory"].append(item)
        schedule_save()
        await interaction.response.send_message(f"✅ Gave **{quantity}x {item}** to <@{user.id}>.", ephemeral=True)

    @app_commands.command(name="wipe")
    @app_commands.describe(user="User to wipe")
    async def wipe(self, interaction: discord.Interaction, user: discord.Member):
        if user.id in player_data:
            del player_data[user.id]
        schedule_save()
        await interaction.response.send_message(f"✅ Wiped data for <@{user.id}>.", ephemeral=True)

    @app_commands.command(name="set_multiplier")
    @app_commands.describe(user="User to modify", value="Multiplier value")
    async def set_multiplier(self, interaction: discord.Interaction, user: discord.Member, value: float):
        target_data = get_player_data(user.id)
        target_data["multiplier"] = value
        schedule_save()
        await interaction.response.send_message(f"✅ Set multiplier to {value}x for <@{user.id}>.", ephemeral=True)

    @app_commands.command(name="set_heat")
    @app_commands.describe(user="User to modify", value="Heat value (0-100)")
    async def set_heat(self, interaction: discord.Interaction, user: discord.Member, value: int):
        target_data = get_player_data(user.id)
        target_data["heat"] = max(0, min(100, value))
        schedule_save()
        await interaction.response.send_message(f"✅ Set heat to {value} for <@{user.id}>.", ephemeral=True)

    @app_commands.command(name="set_cred")
    @app_commands.describe(user="User to modify", value="Street cred value")
    async def set_cred(self, interaction: discord.Interaction, user: discord.Member, value: int):
        target_data = get_player_data(user.id)
        target_data["streetCred"] = value
        schedule_save()
        await interaction.response.send_message(f"✅ Set street cred to {value} for <@{user.id}>.", ephemeral=True)

    @app_commands.command(name="reset_cooldowns")
    @app_commands.describe(user="User to reset")
    async def reset_cooldowns(self, interaction: discord.Interaction, user: discord.Member):
        target_data = get_player_data(user.id)
        cooldown_fields = ["lastDaily", "lastWork", "lastRob", "lastLick", "lastScavenge", "lastHustle", "lastMonthly"]
        for field in cooldown_fields:
            target_data[field] = 0
        schedule_save()
        await interaction.response.send_message(f"✅ Reset cooldowns for <@{user.id}>.", ephemeral=True)

    @app_commands.command(name="inspect")
    @app_commands.describe(user="User to inspect")
    async def inspect(self, interaction: discord.Interaction, user: discord.Member):
        data = get_player_data(user.id)
        embed = discord.Embed(title=f"Data for {user.name}", color=0x9c27b0)
        embed.add_field(name="Bread", value=data["bread"], inline=True)
        embed.add_field(name="Street Cred", value=data["streetCred"], inline=True)
        embed.add_field(name="Heat", value=data["heat"], inline=True)
        embed.add_field(name="Multiplier", value=f"{data['multiplier']}x", inline=True)
        embed.add_field(name="Safe Balance", value=data.get("safeBalance", 0), inline=True)
        embed.add_field(name="Loan", value=data.get("loanAmount", 0), inline=True)
        embed.add_field(name="Inventory", value=f"{len(data.get('inventory', []))} items", inline=True)
        hood_name = data["hood"].get("name")
        embed.add_field(name="Hood", value=HOODS[hood_name]["fullName"] if hood_name else "None", inline=True)
        await interaction.response.send_message(embeds=[embed], ephemeral=True)

    @app_commands.command(name="global_bonus")
    @app_commands.describe(amount="Amount per user")
    async def global_bonus(self, interaction: discord.Interaction, amount: int):
        count = 0
        for uid, data in player_data.items():
            data["bread"] += amount
            count += 1
        schedule_save()
        await interaction.response.send_message(f"✅ Gave **{amount}** bread to **{count}** users.", ephemeral=True)

    @app_commands.command(name="save_data")
    async def save_data(self, interaction: discord.Interaction):
        from ..data import save_player_data
        await save_player_data(True)
        await interaction.response.send_message("✅ Data saved.", ephemeral=True)