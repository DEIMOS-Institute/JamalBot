import discord
from discord import app_commands
import time
import random
from ..data import get_player_data, schedule_save
from ..utils import get_street_rank
from ..constants import HOODS, LOOT_ITEMS

class CrimeCommands:
    def __init__(self):
        super().__init__(name="crime", description="Criminal activities")

    @app_commands.command(name="crime")
    async def crime(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        if data.get("lastCrime") and now - data["lastCrime"] < 30 * 60 * 1000:
            remaining = (30 * 60 * 1000 - (now - data["lastCrime"])) // 60000
            await interaction.response.send_message(f"Cooldown: {remaining} mins.", ephemeral=True)
            return

        outcomes = [
            {"text": "You tried to rob a store but the clerk had a gun. You lost 200 bread.", "loss": 200},
            {"text": "You sold fake watches and got caught. Paid 150 bread fine.", "loss": 150},
            {"text": "You helped move some packages and got paid 300 bread!", "gain": 300},
            {"text": "You ran a small scam and made 250 bread.", "gain": 250},
            {"text": "The cops raided your spot. You lost 400 bread.", "loss": 400},
            {"text": "You found an unlocked car and took the cash inside. +350 bread.", "gain": 350},
        ]
        outcome = random.choice(outcomes)
        if "gain" in outcome:
            data["bread"] += outcome["gain"]
            msg = f"💀 **CRIME:** {outcome['text']} You now have **{data['bread']}** bread."
        else:
            data["bread"] = max(0, data["bread"] - outcome["loss"])
            msg = f"💀 **CRIME:** {outcome['text']} You now have **{data['bread']}** bread."
        data["lastCrime"] = now
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="rob")
    @app_commands.describe(user="Who to rob")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        data = get_player_data(interaction.user.id)
        target_data = get_player_data(user.id)

        if user.id == interaction.user.id:
            await interaction.response.send_message("Robbing yourself? That's just sad.", ephemeral=True)
            return

        now = int(time.time() * 1000)
        rank = get_street_rank(data["bread"], data["streetCred"])
        rob_cooldown = int(3600000 * rank["cdMult"])

        if data["lastRob"] and now - data["lastRob"] < rob_cooldown:
            remaining = int((rob_cooldown - (now - data["lastRob"])) / 60000)
            await interaction.response.send_message(f"The heat is too high. Wait {remaining} minutes.", ephemeral=True)
            return

        if target_data["bread"] < 100:
            await interaction.response.send_message("They're too broke to rob.", ephemeral=True)
            return

        success_chance = 0.45
        if "weapon" in data.get("inventory", []):
            success_chance += 0.15
        if data["hood"]["name"] == 'eastside':
            success_chance += 0.05

        success = random.random() < success_chance
        data["lastRob"] = now

        if success:
            stolen = int(target_data["bread"] * (random.random() * 0.3 + 0.2))
            target_data["bread"] -= stolen
            data["bread"] += stolen
            schedule_save()
            await interaction.response.send_message(f"🥷 **[{rank['name']}] SUCCESS!** You robbed **{stolen}** bread from <@{user.id}>!")
        else:
            caught_chance = 0.5
            if "mask" in data.get("inventory", []):
                caught_chance -= 0.2

            if random.random() < caught_chance:
                if "jail_card" in data.get("inventory", []):
                    data["inventory"].remove("jail_card")
                    schedule_save()
                    await interaction.response.send_message(f"🚔 **[{rank['name']}]** The feds almost had you, but you used your **Bail Bond** to walk free!")
                else:
                    fine = int(data["bread"] * 0.2)
                    data["bread"] = max(0, data["bread"] - fine)
                    schedule_save()
                    await interaction.response.send_message(f"🚔 **[{rank['name']}] CAUGHT!** You got bagged and paid **{fine}** bread in fines.")
            else:
                await interaction.response.send_message(f"🏃 **[{rank['name']}]** You failed the robbery but managed to lose the feds.")

    @app_commands.command(name="drill")
    @app_commands.describe(amount="Optional gear-up cost")
    async def drill(self, interaction: discord.Interaction, amount: int = 0):
        data = get_player_data(interaction.user.id)
        if amount > 0 and data["bread"] < amount:
            await interaction.response.send_message("You can't afford to gear up for a drill.", ephemeral=True)
            return

        now = int(time.time() * 1000)
        if data.get("lastDrill") and now - data["lastDrill"] < 4 * 60 * 60 * 1000:
            remaining = (4 * 60 * 60 * 1000 - (now - data["lastDrill"])) // 60000
            await interaction.response.send_message(f"Wait {remaining} mins.", ephemeral=True)
            return

        if random.random() > 0.9:
            reward = amount * 6 if amount > 0 else 2500
            data["bread"] += reward
            data["drillsCompleted"] += 1
            await interaction.response.send_message(f"🔫 **DRILL SUCCESS!** You caught them slipping and hit a major score! You got **{reward}** bread!")
        else:
            loss = amount if amount > 0 else 750
            data["bread"] = max(0, data["bread"] - loss)
            await interaction.response.send_message(f"🚔 **DRILL FAILED.** The ops were ready for you. You lost **{loss}** bread escaping.")
        data["lastDrill"] = now
        schedule_save()

    @app_commands.command(name="scavenge")
    async def scavenge(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        scav_cooldown = 2 * 60 * 60 * 1000

        if data["lastScavenge"] and now - data["lastScavenge"] < scav_cooldown:
            remaining = int((scav_cooldown - (now - data["lastScavenge"])) / 60000)
            await interaction.response.send_message(f"The block is dry. Check back in {remaining} minutes.", ephemeral=True)
            return

        data["lastScavenge"] = now
        found = random.randint(50, 350) if random.random() > 0.5 else 0
        if found > 0:
            data["bread"] += found
            msg = f"🗑️ You scavenged the back alleys and found **{found}** pieces of bread!"
            if data["hood"]["name"] == 'southside' and random.random() < HOODS["southside"]["perks"]["modifiers"]["scavengeBonusChance"]:
                extra_item = random.choice(LOOT_ITEMS)
                data["inventory"].append(extra_item)
                msg += f" You also found a **{extra_item}**!"
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("🗑️ You looked everywhere but the block is completely empty. Tough luck.")
        schedule_save()

    @app_commands.command(name="trap")
    async def trap(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        cooldown = 2 * 60 * 60 * 1000
        if data.get("lastTrap") and now - data["lastTrap"] < cooldown:
            remaining = (cooldown - (now - data["lastTrap"])) // 60000
            await interaction.response.send_message(f"Trap is cooling down. Wait {remaining} mins.", ephemeral=True)
            return

        raid_chance = data["heat"] / 200
        if random.random() < raid_chance:
            loss = int(data["bread"] * 0.25)
            data["bread"] = max(0, data["bread"] - loss)
            data["heat"] = min(100, data["heat"] + 10)
            msg = f"🚔 **RAIDED!** The 12 shut down your trap. Lost {loss} bread."
        else:
            profit = random.randint(400, 1200) * data["trapHouseLevel"]
            data["bread"] += profit
            data["heat"] = min(100, data["heat"] + 5)
            msg = f"💰 You served fiends all night. Earned **{profit}** bread."
        data["lastTrap"] = now
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="stickup")
    @app_commands.describe(user="Who to rob")
    async def stickup(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("Can't rob yourself.", ephemeral=True)
            return
        data = get_player_data(interaction.user.id)
        target = get_player_data(user.id)
        now = int(time.time() * 1000)
        cooldown = 4 * 60 * 60 * 1000
        if data.get("lastStickup") and now - data["lastStickup"] < cooldown:
            remaining = (cooldown - (now - data["lastStickup"])) // 60000
            await interaction.response.send_message(f"Cooldown: {remaining} mins.", ephemeral=True)
            return
        if target["bread"] < 200:
            await interaction.response.send_message("They're too broke.", ephemeral=True)
            return

        success_chance = 0.4
        if "weapon" in data["inventory"]:
            success_chance += 0.15
        if "mask" in data["inventory"]:
            success_chance += 0.1

        if random.random() < success_chance:
            stolen = int(target["bread"] * random.uniform(0.2, 0.4))
            target["bread"] -= stolen
            data["bread"] += stolen
            data["heat"] = min(100, data["heat"] + 15)
            msg = f"🔫 Stickup successful! Stole **{stolen}** bread from <@{user.id}>."
        else:
            if random.random() < 0.5:
                fine = int(data["bread"] * 0.3) + 500
                data["bread"] = max(0, data["bread"] - fine)
                msg = f"🚔 **CAUGHT!** You got booked. Lost {fine} bread in bail."
            else:
                data["heat"] = min(100, data["heat"] + 20)
                msg = "You failed the stickup but escaped."
        data["lastStickup"] = now
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="finesse")
    async def finesse(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        success = random.random() < 0.5
        if success:
            earned = random.randint(200, 800)
            data["bread"] += earned
            data["streetCred"] += 5
            msg = f"🤝 You finessed an NPC for **{earned}** bread!"
        else:
            data["bread"] = max(0, data["bread"] - 100)
            msg = "The NPC wasn't having it. You lost 100 bread."
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="shoplift")
    async def shoplift(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if random.random() < 0.6:
            earned = random.randint(100, 500)
            data["bread"] += earned
            data["heat"] = min(100, data["heat"] + 10)
            msg = f"🛒 You swiped **{earned}** bread worth of goods!"
        else:
            data["heat"] = min(100, data["heat"] + 20)
            msg = "🚨 You got caught shoplifting! Heat increased."
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="grow")
    async def grow(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        seeds = data["inventory"].count("weed_seed")
        if seeds < 1:
            await interaction.response.send_message("You need weed seeds!", ephemeral=True)
            return
        data["inventory"].remove("weed_seed")
        data["growOp"]["plants"] += 1
        data["growOp"]["plantedAt"] = int(time.time() * 1000)
        schedule_save()
        await interaction.response.send_message(f"🌿 You planted a weed plant. It'll be ready in 12 hours!")

    @app_commands.command(name="harvest")
    async def harvest(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if data["growOp"]["plants"] <= 0:
            await interaction.response.send_message("No plants to harvest.", ephemeral=True)
            return
        now = int(time.time() * 1000)
        if now - data["growOp"]["plantedAt"] < 12 * 60 * 60 * 1000:
            await interaction.response.send_message("Plants aren't ready yet.", ephemeral=True)
            return
        harvested = data["growOp"]["plants"] * random.randint(5, 10)
        data["drugs"]["weed"] = data["drugs"].get("weed", 0) + harvested
        data["growOp"]["plants"] = 0
        schedule_save()
        await interaction.response.send_message(f"🌿 Harvested **{harvested}** weed!")

    @app_commands.command(name="sellweed")
    @app_commands.describe(amount="Amount to sell")
    async def sellweed(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        if data["drugs"].get("weed", 0) < amount:
            await interaction.response.send_message("You don't have that much weed.", ephemeral=True)
            return
        price = 50 * amount
        data["drugs"]["weed"] -= amount
        data["bread"] += price
        schedule_save()
        await interaction.response.send_message(f"💰 Sold {amount} weed for **{price}** bread.")