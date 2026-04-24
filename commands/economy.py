import discord
from discord import app_commands
import time
import random
from ..data import get_player_data, schedule_save, calculate_earnings
from ..constants import HOODS, SHOP_ITEMS, SHIKYO_SERVICES
from ..utils import get_street_rank
from ..views import ShopView

class EconomyCommands:
    def __init__(self):
        super().__init__(name="economy", description="Economy commands")

    @app_commands.command(name="bread")
    async def bread(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        await interaction.response.send_message(f"🍞 You currently have **{data['bread']}** pieces of bread and **{data['streetCred']}** street cred.")

    @app_commands.command(name="daily")
    async def daily(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        cooldown = 24 * 60 * 60 * 1000
        last = data["streak"].get("lastDailyClaim", data.get("lastDaily", 0))

        if now - last > cooldown * 2:
            data["streak"]["daily"] = 0
        elif now - last < cooldown:
            remaining = cooldown - (now - last)
            hours = remaining // (60 * 60 * 1000)
            await interaction.response.send_message(f"Chill out! You can claim more daily bread in {hours} hours.", ephemeral=True)
            return

        data["streak"]["daily"] += 1
        data["streak"]["lastDailyClaim"] = now
        data["lastDaily"] = now
        streak_bonus = min(data["streak"]["daily"], 7) * 50
        base = 500
        total = calculate_earnings(base + streak_bonus, interaction.user.id)
        data["bread"] += total

        # Hood loyalty update
        if data["hood"]["name"]:
            one_day = 86400000
            if not data["hood"]["lastLoyaltyUpdate"] or now - data["hood"]["lastLoyaltyUpdate"] > one_day:
                data["hood"]["loyalty"] += 1
                data["hood"]["lastLoyaltyUpdate"] = now

        schedule_save()
        await interaction.response.send_message(f"💰 Daily claimed! +{total} bread (streak: {data['streak']['daily']} days). Total: {data['bread']}")

    @app_commands.command(name="weekly")
    async def weekly(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        cooldown = 7 * 24 * 60 * 60 * 1000
        last = data["streak"].get("lastWeeklyClaim", 0)

        if now - last > cooldown * 2:
            data["streak"]["weekly"] = 0
        elif now - last < cooldown:
            remaining = cooldown - (now - last)
            days = remaining // (24 * 60 * 60 * 1000)
            await interaction.response.send_message(f"Wait {days} days.", ephemeral=True)
            return

        data["streak"]["weekly"] += 1
        data["streak"]["lastWeeklyClaim"] = now
        streak_bonus = min(data["streak"]["weekly"], 4) * 500
        base = 3500
        total = calculate_earnings(base + streak_bonus, interaction.user.id)
        data["bread"] += total
        schedule_save()
        await interaction.response.send_message(f"💰 Weekly claimed! +{total} bread (streak: {data['streak']['weekly']} weeks).")

    @app_commands.command(name="monthly")
    async def monthly(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if "monthly_command" not in data.get("inventory", []):
            await interaction.response.send_message("You need to buy the **Monthly Pass** from the shop first!", ephemeral=True)
            return

        now = int(time.time() * 1000)
        cooldown = 30 * 24 * 60 * 60 * 1000
        last = data["streak"].get("lastMonthlyClaim", data.get("lastMonthly", 0))

        if now - last > cooldown * 2:
            data["streak"]["monthly"] = 0
        elif now - last < cooldown:
            remaining = cooldown - (now - last)
            days = remaining // (24 * 60 * 60 * 1000)
            await interaction.response.send_message(f"Wait {days} days.", ephemeral=True)
            return

        data["streak"]["monthly"] += 1
        data["streak"]["lastMonthlyClaim"] = now
        data["lastMonthly"] = now
        streak_bonus = min(data["streak"]["monthly"], 3) * 2000
        base = 15000
        total = calculate_earnings(base + streak_bonus, interaction.user.id)
        data["bread"] += total
        schedule_save()
        await interaction.response.send_message(f"💰 Monthly claimed! +{total} bread (streak: {data['streak']['monthly']} months).")

    @app_commands.command(name="shop")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Jamal's Enhancement Shop",
            description="Get these to run the streets better! Use the dropdown to browse categories.",
            color=0xffff00
        )
        embed.add_field(name="🍞 Bread Magnet (magnet)", value="Permanent 1.5x multiplier - 1,000 bread", inline=True)
        embed.add_field(name="🔥 Industrial Oven (oven)", value="Permanent 2.0x multiplier - 5,000 bread", inline=True)
        embed.add_field(name="💎 Gold Kneader (kneader)", value="Permanent 3.0x multiplier - 15,000 bread", inline=True)
        embed.add_field(name="📦 Safe Box (safe_box)", value="Increase stash capacity - 2,500 bread", inline=True)
        embed.add_field(name="👑 Shikyo Services", value="Premium perks from the plug", inline=False)
        view = ShopView(interaction.user.id)
        await interaction.response.send_message(embeds=[embed], view=view)

    @app_commands.command(name="buy")
    @app_commands.describe(item="Item ID", quantity="Quantity (default: 1)")
    async def buy(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        data = get_player_data(interaction.user.id)
        if "inventory" not in data:
            data["inventory"] = []

        if item not in SHOP_ITEMS:
            await interaction.response.send_message("Jamal ain't selling that.", ephemeral=True)
            return

        item_data = SHOP_ITEMS[item]
        
        # Check street cred requirements for prestige items
        if "street_cred_req" in item_data:
            if data["streetCred"] < item_data["street_cred_req"]:
                await interaction.response.send_message(f"You need **{item_data['street_cred_req']}** street cred to buy this prestige item! You have {data['streetCred']}.", ephemeral=True)
                return
        
        total_cost = item_data["cost"] * quantity
        if data["hood"]["name"] == 'southside':
            total_cost = int(total_cost * HOODS["southside"]["perks"]["modifiers"]["shopDiscount"])

        if data["bread"] < total_cost:
            await interaction.response.send_message(f"You need **{total_cost}** bread for {quantity}x {item_data['name']}!", ephemeral=True)
            return

        data["bread"] -= total_cost

        if item_data["type"] == "multiplier":
            if quantity > 1:
                await interaction.response.send_message("Multipliers don't stack like that, just buy one.", ephemeral=True)
                return
            if data["multiplier"] * item_data["mult"] > 10:
                await interaction.response.send_message("Your multiplier is already too high!", ephemeral=True)
                return
            data["multiplier"] *= item_data["mult"]
        elif item_data["type"] == "capacity":
            data["stashCapacity"] = data.get("stashCapacity", 5000) + (item_data["amount"] * quantity)
        elif item_data["type"] == "special":
            if item == "pass":
                if quantity > 1:
                    await interaction.response.send_message("One pass is enough.", ephemeral=True)
                    return
                if "monthly_command" in data["inventory"]:
                    await interaction.response.send_message("You already got the pass.", ephemeral=True)
                    return
                data["inventory"].append("monthly_command")
        elif item_data["type"] == "prestige":
            if item == "respect_boost":
                data["respect"] = data.get("respect", 50) + 25
            elif item == "cred_multiplier":
                data["cred_multiplier"] = data.get("cred_multiplier", 1.0) * 1.25
            elif item == "hood_pass":
                data["vip_pass"] = True
            elif item == "legendary_chain":
                data["dripLevel"] = data.get("dripLevel", 1) + 50
        elif item_data["type"] in ["equipment", "consumable", "drip", "drug_seed"]:
            data["inventory"].extend([item] * quantity)
        elif item_data["type"] == "drug":
            drug_name = item.replace("_brick", "").replace("_", "")
            data["drugs"][drug_name] = data["drugs"].get(drug_name, 0) + quantity

        schedule_save()
        await interaction.response.send_message(f"✅ You bought **{quantity}x {item_data['name']}** for **{total_cost}** bread!")

    @app_commands.command(name="sell")
    @app_commands.describe(item="Item to sell", quantity="Quantity")
    async def sell(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        data = get_player_data(interaction.user.id)
        if item not in SHOP_ITEMS:
            await interaction.response.send_message("Can't sell that.", ephemeral=True)
            return

        item_data = SHOP_ITEMS[item]
        sell_price = int(item_data["cost"] * 0.5)

        if item_data["type"] in ["equipment", "consumable", "drip", "drug_seed"]:
            count = data["inventory"].count(item)
            if count < quantity:
                await interaction.response.send_message(f"You only have {count}.", ephemeral=True)
                return
            for _ in range(quantity):
                data["inventory"].remove(item)
        elif item_data["type"] == "drug":
            drug_name = item.replace("_brick", "").replace("_", "")
            if data["drugs"].get(drug_name, 0) < quantity:
                await interaction.response.send_message(f"Not enough {drug_name}.", ephemeral=True)
                return
            data["drugs"][drug_name] -= quantity
        else:
            await interaction.response.send_message("This item cannot be sold.", ephemeral=True)
            return

        total = sell_price * quantity
        data["bread"] += total
        schedule_save()
        await interaction.response.send_message(f"💰 Sold {quantity}x {item_data['name']} for {total} bread.")
    @app_commands.command(name="invest")
    @app_commands.describe(business="Business to invest in")
    @app_commands.choices(business=[
        app_commands.Choice(name="Trap House", value="trap_house"),
        app_commands.Choice(name="Corner Store", value="corner_store"),
        app_commands.Choice(name="Car Wash", value="car_wash"),
        app_commands.Choice(name="Barbershop", value="barbershop"),
    ])
    async def invest(self, interaction: discord.Interaction, business: str):
        from ..constants import BUSINESSES
        data = get_player_data(interaction.user.id)
        if business not in BUSINESSES:
            await interaction.response.send_message("Invalid business.", ephemeral=True)
            return

        biz_data = BUSINESSES[business]
        cost = biz_data["upgrade_cost"]
        if data["bread"] < cost:
            await interaction.response.send_message(f"You need {cost} bread to invest.", ephemeral=True)
            return

        if business not in data["investments"]:
            data["investments"][business] = {"level": 0, "last_collect": 0}

        inv = data["investments"][business]
        inv["level"] += 1
        data["bread"] -= cost
        schedule_save()
        await interaction.response.send_message(f"💼 Invested in **{biz_data['name']}**! Level {inv['level']}. Next collect in 1 hour.")

    @app_commands.command(name="collect")
    async def collect(self, interaction: discord.Interaction):
        from ..constants import BUSINESSES
        data = get_player_data(interaction.user.id)
        now = int(time.time())
        total_yield = 0
        collected = []

        for biz, inv in data["investments"].items():
            if biz in BUSINESSES:
                biz_data = BUSINESSES[biz]
                cooldown = 3600  # 1 hour
                if now - inv["last_collect"] >= cooldown:
                    yield_amount = biz_data["base_yield"] * inv["level"]
                    total_yield += yield_amount
                    inv["last_collect"] = now
                    collected.append(f"{biz_data['name']}: +{yield_amount}")

        if total_yield == 0:
            await interaction.response.send_message("Nothing to collect yet. Wait 1 hour.", ephemeral=True)
            return

        data["bread"] += total_yield
        schedule_save()
        await interaction.response.send_message(f"💰 Collected **{total_yield}** bread from investments!\n" + "\n".join(collected))

    @app_commands.command(name="blackmarket")
    async def blackmarket(self, interaction: discord.Interaction):
        from ..constants import BLACK_MARKET_ITEMS
        embed = discord.Embed(title="🕵️ Black Market", description="Illegal trades - high risk, high reward!", color=0x000000)
        for item in BLACK_MARKET_ITEMS:
            embed.add_field(name=item.replace("_", " ").title(), value=f"Risky item - sell for big bread!", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell_black")
    @app_commands.describe(item="Black market item to sell")
    async def sell_black(self, interaction: discord.Interaction, item: str):
        from ..constants import BLACK_MARKET_ITEMS
        data = get_player_data(interaction.user.id)
        if item not in BLACK_MARKET_ITEMS:
            await interaction.response.send_message("Not a black market item.", ephemeral=True)
            return

        if item not in data["black_market_items"]:
            await interaction.response.send_message("You don't have that item.", ephemeral=True)
            return

        # Risk: chance of getting caught
        if random.random() < 0.3:  # 30% chance
            data["heat"] += 20
            data["black_market_items"].remove(item)
            schedule_save()
            await interaction.response.send_message("🚔 Got caught selling illegal goods! Heat +20!")
            return

        payout = random.randint(500, 2000)
        data["bread"] += payout
        data["black_market_items"].remove(item)
        schedule_save()
        await interaction.response.send_message(f"💸 Sold **{item}** on the black market for **{payout}** bread!")

    @app_commands.command(name="collectibles")
    async def collectibles(self, interaction: discord.Interaction):
        from ..constants import COLLECTIBLES
        data = get_player_data(interaction.user.id)
        embed = discord.Embed(title="🛍️ Your Collectibles", color=0xffd700)
        if not data["collectibles"]:
            embed.description = "No collectibles yet. Hunt for them in events!"
        else:
            for coll in data["collectibles"]:
                coll_data = COLLECTIBLES.get(coll["id"], {})
                embed.add_field(name=f"{coll_data.get('name', coll['id'])} ({coll['rarity']})", value=coll_data.get('description', ''), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="trade_collectible")
    @app_commands.describe(target="User to trade with", collectible="Collectible ID", price="Bread price")
    async def trade_collectible(self, interaction: discord.Interaction, target: discord.Member, collectible: str, price: int):
        from ..constants import COLLECTIBLES
        data = get_player_data(interaction.user.id)
        target_data = get_player_data(target.id)

        if collectible not in [c["id"] for c in data["collectibles"]]:
            await interaction.response.send_message("You don't own that collectible.", ephemeral=True)
            return

        if target_data["bread"] < price:
            await interaction.response.send_message("Target doesn't have enough bread.", ephemeral=True)
            return

        # Remove from seller, add to buyer
        data["collectibles"] = [c for c in data["collectibles"] if c["id"] != collectible]
        target_data["collectibles"].append({"id": collectible, "rarity": COLLECTIBLES[collectible]["rarity"]})

        data["bread"] += price
        target_data["bread"] -= price
        schedule_save()
        await interaction.response.send_message(f"✅ Traded **{COLLECTIBLES[collectible]['name']}** to {target.mention} for **{price}** bread!")
    @app_commands.command(name="inventory")
    async def inventory(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        inv = data.get("inventory", [])
        drugs = data.get("drugs", {})
        lines = []
        if inv:
            counts = {}
            for i in inv:
                counts[i] = counts.get(i, 0) + 1
            lines.append("**Items:**")
            for k, v in counts.items():
                lines.append(f"  {v}x {SHOP_ITEMS.get(k, {}).get('name', k)}")
        if drugs:
            lines.append("**Drugs:**")
            for k, v in drugs.items():
                if v > 0:
                    lines.append(f"  {v}x {k.title()}")
        if not lines:
            lines.append("Your pockets are empty.")
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="safe")
    @app_commands.describe(amount="Amount to deposit (or 'all')", action="deposit or withdraw")
    @app_commands.choices(action=[
        app_commands.Choice(name="Deposit", value="deposit"),
        app_commands.Choice(name="Withdraw", value="withdraw")
    ])
    async def safe(self, interaction: discord.Interaction, amount: str, action: str):
        data = get_player_data(interaction.user.id)
        if amount.lower() == "all":
            amount_int = data["bread"] if action == "deposit" else data["safeBalance"]
        else:
            try:
                amount_int = int(amount)
            except:
                await interaction.response.send_message("Invalid amount.", ephemeral=True)
                return

        if action == "deposit":
            if data["bread"] < amount_int:
                await interaction.response.send_message("Not enough bread.", ephemeral=True)
                return
            if data["safeBalance"] + amount_int > data["safeCapacity"]:
                await interaction.response.send_message(f"Safe full (capacity {data['safeCapacity']}).", ephemeral=True)
                return
            data["bread"] -= amount_int
            data["safeBalance"] += amount_int
            msg = f"🔒 Deposited {amount_int} bread. Safe: {data['safeBalance']}/{data['safeCapacity']}"
        else:
            if data["safeBalance"] < amount_int:
                await interaction.response.send_message("Not enough in safe.", ephemeral=True)
                return
            data["safeBalance"] -= amount_int
            data["bread"] += amount_int
            msg = f"🔓 Withdrew {amount_int} bread. Safe: {data['safeBalance']}/{data['safeCapacity']}"
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="interest")
    async def interest(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        now = int(time.time() * 1000)
        cooldown = 24 * 60 * 60 * 1000
        last = data.get("lastInterest", 0)
        if now - last < cooldown:
            remaining = (cooldown - (now - last)) // (60 * 60 * 1000)
            await interaction.response.send_message(f"Interest can be claimed once per day. Wait {remaining}h.", ephemeral=True)
            return

        rate = 0.05
        if "watch" in data["inventory"]:
            rate += 0.02
        interest_earned = int(data["safeBalance"] * rate)
        data["safeBalance"] += interest_earned
        data["lastInterest"] = now
        schedule_save()
        await interaction.response.send_message(f"💰 Earned {interest_earned} bread interest! New safe balance: {data['safeBalance']}")

    @app_commands.command(name="loan")
    @app_commands.describe(amount="Amount to borrow")
    async def loan(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        if data["loanAmount"] > 0:
            await interaction.response.send_message(f"You already owe {data['loanAmount']} bread. Pay it back first.", ephemeral=True)
            return
        max_loan = 10000 * data["trapHouseLevel"]
        if amount > max_loan:
            await interaction.response.send_message(f"Max loan is {max_loan}.", ephemeral=True)
            return
        data["bread"] += amount
        data["loanAmount"] = int(amount * 1.2)
        data["loanDue"] = int(time.time() * 1000) + 7 * 24 * 60 * 60 * 1000
        schedule_save()
        await interaction.response.send_message(f"🏦 Borrowed {amount} bread. Pay back {data['loanAmount']} within 7 days!")

    @app_commands.command(name="payloan")
    async def payloan(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if data["loanAmount"] == 0:
            await interaction.response.send_message("You don't have a loan.", ephemeral=True)
            return
        if data["bread"] < data["loanAmount"]:
            await interaction.response.send_message(f"You need {data['loanAmount']} bread.", ephemeral=True)
            return
        data["bread"] -= data["loanAmount"]
        paid = data["loanAmount"]
        data["loanAmount"] = 0
        data["loanDue"] = 0
        schedule_save()
        await interaction.response.send_message(f"✅ Paid off loan of {paid} bread. You're debt free!")

    @app_commands.command(name="leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        from ..data import player_data
        sorted_players = sorted(player_data.items(), key=lambda x: x[1]["bread"], reverse=True)[:10]
        if not sorted_players:
            await interaction.response.send_message("No players yet.")
            return
        embed = discord.Embed(title="🏆 Bread Leaderboard", color=0xffd700)
        description = "\n".join(f"{i+1}. <@{uid}> — **{data['bread']}** bread" for i, (uid, data) in enumerate(sorted_players))
        embed.description = description
        await interaction.response.send_message(embeds=[embed])

    @app_commands.command(name="gamble")
    @app_commands.describe(amount="Amount to bet")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        if amount < 10:
            await interaction.response.send_message("Minimum bet is 10 bread.", ephemeral=True)
            return
        if data["bread"] < amount:
            await interaction.response.send_message("You're too broke for that bet.", ephemeral=True)
            return

        win_chance = 0.40
        lucky_charm_used = False
        if "lucky_charm" in data.get("inventory", []):
            win_chance = 0.46
            data["inventory"].remove("lucky_charm")
            lucky_charm_used = True
        if data["hood"]["name"] == 'northside':
            win_chance += HOODS["northside"]["perks"]["modifiers"]["gambleWinChance"]

        win = random.random() < win_chance
        if win:
            data["bread"] += amount
            msg = f"🎰 **WIN!** You doubled your bet and now have **{data['bread']}** bread!"
            if lucky_charm_used:
                msg += " 🍀 Your Lucky Charm did the trick!"
        else:
            data["bread"] -= amount
            msg = f"📉 **LOSS!** You lost **{amount}** bread. Better luck next time."
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="slots")
    @app_commands.describe(amount="Bet amount")
    async def slots(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        if amount < 10:
            await interaction.response.send_message("Minimum bet is 10 bread.", ephemeral=True)
            return
        if data["bread"] < amount:
            await interaction.response.send_message("You're too broke for these stakes.", ephemeral=True)
            return

        emojis = ["🍎", "🍊", "🍇", "💎", "🔔", "💀"]
        slot1, slot2, slot3 = random.choices(emojis, k=3)

        result_msg = f"[ {slot1} | {slot2} | {slot3} ]\n\n"
        if slot1 == slot2 == slot3 and slot1 != "💀":
            win = amount * 4
            data["bread"] += win
            result_msg += f"💎 **JACKPOT!** You won **{win}** bread!"
        elif (slot1 == slot2 or slot2 == slot3 or slot1 == slot3) and "💀" not in [slot1, slot2, slot3]:
            win = int(amount * 1.2)
            data["bread"] += win
            result_msg += f"✅ **MATCH!** You won **{win}** bread!"
        else:
            data["bread"] -= amount
            result_msg += f"💀 **BUST.** You lost **{amount}** bread."
        schedule_save()
        await interaction.response.send_message(result_msg)

    @app_commands.command(name="race")
    @app_commands.describe(amount="Entry fee")
    async def race(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        if amount < 10:
            await interaction.response.send_message("Minimum entry fee is 10 bread.", ephemeral=True)
            return
        if data["bread"] < amount:
            await interaction.response.send_message("You can't afford the entry fee.", ephemeral=True)
            return

        if random.random() > 0.9:
            winnings = amount * 4
            data["bread"] += winnings
            await interaction.response.send_message(f"🏎️💨 **SKRRRRR!** You gapped them ops and won the race! You took home **{winnings}** bread!")
        else:
            data["bread"] -= amount
            await interaction.response.send_message(f"🚔 **WEE-OOO!** The feds crashed the race and impounded your whip! You lost **{amount}** bread.")
        schedule_save()