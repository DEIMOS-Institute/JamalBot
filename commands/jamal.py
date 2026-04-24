import discord
from discord import app_commands
import time
import random
from ..data import get_player_data, schedule_save
from ..constants import LOOT_ITEMS, QUOTES, STEAL_ITEMS, HOODS

class JamalGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="jamal", description="Jamal interaction")

    @app_commands.command(name="give")
    @app_commands.describe(user="Who to give to")
    async def give(self, interaction: discord.Interaction, user: discord.Member):
        item = random.choice(LOOT_ITEMS)
        await interaction.response.send_message(f"Jamal handed <@{user.id}> a **{item}**. \"Here, you broke ass nigga.\"")

    @app_commands.command(name="lick")
    @app_commands.describe(user="Who to lick")
    async def lick(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("You tryna lick yourself? That's nasty behavior, bro.", ephemeral=True)
            return

        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        lick_cooldown = 30 * 60 * 1000

        if data["lastLick"] and now - data["lastLick"] < lick_cooldown:
            remaining = int((lick_cooldown - (now - data["lastLick"])) / 60000)
            await interaction.response.send_message(f"Slow down! Your tongue needs a break. Wait {remaining} more minutes.", ephemeral=True)
            return

        data["lastLick"] = now
        attacker_data = get_player_data(interaction.user.id)
        target_data = get_player_data(user.id)
        target_pocket = target_data["bread"]

        if target_pocket <= 0:
            await interaction.response.send_message("This person is flat broke. You can't lick what ain't there.", ephemeral=True)
            return

        roll = random.random()
        if roll < 0.3:
            fine = int(attacker_data["bread"] * 0.15)
            attacker_data["bread"] = max(0, attacker_data["bread"] - fine)
            schedule_save()
            await interaction.response.send_message(f" **CAUGHT LACKING!** <@{user.id}> caught you tryna lick 'em and slapped you silly! Yo ass dropped **{fine}** bread running away.")
        elif roll < 0.6:
            portion = int(target_pocket * (random.random() * 0.3 + 0.1))
            target_data["bread"] -= portion
            attacker_data["bread"] += portion
            schedule_save()
            await interaction.response.send_message(f"👅 **LICKED!** You managed to snatch a decent portion of bread from <@{user.id}>'s pockets. You got **{portion}** bread!")
        elif roll < 0.9:
            portion = int(target_pocket * (random.random() * 0.4 + 0.4))
            target_data["bread"] -= portion
            attacker_data["bread"] += portion
            schedule_save()
            await interaction.response.send_message(f"💰 **FAT LICK!** You cleaned out most of <@{user.id}>'s pockets! You snatched **{portion}** bread!")
        else:
            stolen = target_pocket
            target_data["bread"] = 0
            attacker_data["bread"] += stolen
            schedule_save()
            await interaction.response.send_message(f"💎 **ULTIMATE LICK!** You caught <@{user.id}> completely off guard and took **EVERYTHING** in their pockets! **{stolen}** bread is now yours!")

    @app_commands.command(name="say")
    async def say(self, interaction: discord.Interaction):
        await interaction.response.send_message(random.choice(QUOTES))

    @app_commands.command(name="stash")
    @app_commands.describe(amount="Amount to stash")
    async def stash(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        if data["bread"] < amount:
            await interaction.response.send_message("You ain't even got that much bread in your pockets, fool.", ephemeral=True)
            return

        total_capacity = 5000 + data.get("stashCapacity", 0)
        if data["hood"]["name"] == 'eastside':
            total_capacity = int(total_capacity * HOODS["eastside"]["perks"]["modifiers"]["stashCapacity"])

        current_stashed = data.get("stashedBread", 0)
        if current_stashed + amount > total_capacity:
            await interaction.response.send_message(f"Your stash house is full NIGGUH! Max capacity is **{total_capacity}** bread. Buy some **Safe Boxes** from the `/shop` to increase it!", ephemeral=True)
            return

        data["bread"] -= amount
        data["stashedBread"] = current_stashed + amount
        schedule_save()
        await interaction.response.send_message(f"🏠 You stashed **{amount}** bread in your crib. It's safe from licks now! Total stashed: **{data['stashedBread']}**/**{total_capacity}**")

    @app_commands.command(name="unstash")
    @app_commands.describe(amount="Amount to unstash")
    async def unstash(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        current_stashed = data.get("stashedBread", 0)
        if current_stashed < amount:
            await interaction.response.send_message("You don't even have that much stashed, stop capping.", ephemeral=True)
            return

        data["stashedBread"] -= amount
        data["bread"] += amount
        schedule_save()
        await interaction.response.send_message(f"💰 You pulled **{amount}** bread out of your stash and put it in your pockets. Careful out there!")

    @app_commands.command(name="rap")
    async def rap(self, interaction: discord.Interaction):
        verses = [
            "Came from the mud, now the fit all clean",
            "Late nights grinding, chasing big dreams",
            "Bread on my mind, no time for beef",
            "From the block to the court, elite feet",
            "Rain on the pavement, still I shine",
            "Clock keep ticking, money on time",
            "Hood lessons taught me how to move",
            "Silent with it, nothing to prove",
        ]
        await interaction.response.send_message(random.choice(verses))

    @app_commands.command(name="steal")
    @app_commands.describe(user="Who to steal from", item="What to steal (optional)")
    async def steal(self, interaction: discord.Interaction, user: discord.Member, item: str | None = None):
        if item is None:
            item = random.choice(STEAL_ITEMS)
        await interaction.response.send_message(f"Jamal popped out the cut and stole <@{user.id}>'s **{item}**! NO CAP!")

    @app_commands.command(name="dice")
    @app_commands.describe(bet="Amount to bet")
    async def dice(self, interaction: discord.Interaction, bet: int = 50):
        data = get_player_data(interaction.user.id)
        if data["bread"] < bet:
            await interaction.response.send_message(f"You don't have enough bread! You have {data['bread']}, need {bet}.", ephemeral=True)
            return

        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2
        winnings = 0

        if total in (7, 11):
            result = "🎲 NATURAL! You won!"
            winnings = bet * 2
            data["bread"] += winnings
            data["streetCred"] += 3
        elif total in (2, 3, 12):
            result = "💀 CRAPS! Yo ass lost!"
            data["bread"] -= bet
        else:
            point = total
            new_roll = random.randint(2, 12)
            while new_roll not in (7, point):
                new_roll = random.randint(2, 12)
            if new_roll == point:
                result = f"🎯 Hit your point ({point})! You win!"
                winnings = int(bet * 1.5)
                data["bread"] += winnings
                data["streetCred"] += 2
            else:
                result = "😭 Seven out! You lose!"
                data["bread"] -= bet

        schedule_save()
        embed = discord.Embed(
            title="🎰 STREET CRAPS",
            description=f"**Roll:** {die1} + {die2} = **{total}**\n\n{result}",
            color=0x00ff00 if winnings > 0 else 0xff0000
        )
        embed.add_field(name="Bet", value=f"{bet} bread", inline=True)
        embed.add_field(name="Result", value=f"+{winnings} bread" if winnings > 0 else f"-{bet} bread", inline=True)
        embed.add_field(name="New Balance", value=f"{data['bread']} bread", inline=True)
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="share")
    @app_commands.describe(user="Who to share with", amount="Amount of bread to share")
    async def share(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't share bread with yourself, schizo ahh!", ephemeral=True)
            return

        data = get_player_data(interaction.user.id)
        target_data = get_player_data(user.id)

        if data["bread"] < amount:
            await interaction.response.send_message(f"You don't have enough bread, BROKIE! You have {data['bread']}, need {amount}.", ephemeral=True)
            return

        data["bread"] -= amount
        target_data["bread"] += amount
        schedule_save()

        embed = discord.Embed(
            title="💰 BREAD SHARED",
            description=f"<@{interaction.user.id}> shared {amount} bread with <@{user.id}>!",
            color=0x00ff00
        )
        embed.add_field(name="From", value=f"<@{interaction.user.id}>", inline=True)
        embed.add_field(name="To", value=f"<@{user.id}>", inline=True)
        embed.add_field(name="Amount", value=f"{amount} bread", inline=True)
        embed.set_footer(text="Real recognize real!")
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="block")
    async def block(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        heat = data["heat"]
        if heat < 30:
            msg = "The block is quiet right now. Good time to move."
        elif heat < 60:
            msg = "Block is warm. Keep your eyes open."
        elif heat < 90:
            msg = "Block is hot! The 12 is lurking."
        else:
            msg = "BLOCK IS ON FIRE! Get low or get caught!"
        await interaction.response.send_message(msg)

    @app_commands.command(name="drip")
    async def drip(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        drip_level = data.get("dripLevel", 1)
        await interaction.response.send_message(f"💎 Your current drip level is **{drip_level}**. Buy chains, grillz, and watches to increase it!")

    @app_commands.command(name="smoke")
    async def smoke(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        if data.get("lastSmoke") and now - data["lastSmoke"] < 60 * 60 * 1000:
            await interaction.response.send_message("You're still high from the last one.", ephemeral=True)
            return
        data["smokeCount"] = data.get("smokeCount", 0) + 1
        data["lastSmoke"] = now
        schedule_save()
        responses = [
            "Jamal passes the blunt. You take a hit and feel relaxed.",
            "Jamal sparks one up and starts talking about life. Deep.",
            "You smoke with Jamal and forget all your problems.",
            "Jamal: 'This za za got me zonin'. I'm good cuz.'",
        ]
        await interaction.response.send_message(f"{random.choice(responses)}\n💨 You've smoked **{data['smokeCount']}** times total.")