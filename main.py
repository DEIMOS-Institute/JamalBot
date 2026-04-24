import asyncio
import signal
import discord
from discord.ext import commands, tasks
import re
import time
import random
import os
from config import (
    DISCORD_TOKEN, GUILD_ID, IGNORED_ROLES, BOOSTER_ROLES,
    AUTO_SAVE_INTERVAL, INACTIVITY_THRESHOLD, PREFIX, DATA_DIR
)
from data import load_player_data, save_player_data, get_player_data, schedule_save, start_backup_loop, stop_backup_loop, calculate_earnings
from constants import LOOT_ITEMS, HARD_R_REPLIES, SOFT_A_REPLIES, HOODS, QUOTES, RANDOM_ROASTS, ROAST_CATEGORIES, KILL_MESSAGES
from views import ChickenView
from commands import (
    EconomyCommands, FunCommands, CrimeCommands, GamesCommands,
    HustleGroup, JamalGroup, HoodGroup, ProfileCommands,
    SocialCommands, UtilityCommands, JoseGroup, BountyCommands, HitCommands,
    StreetCredCommands
)
from views import EventView

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Inactivity tracking
last_message_time = time.time()
inactivity_questions = [
    "Yo, the chat dead. Who got the best fried chicken in the hood?",
    "Aye, quick poll: Hennessy or Crown Royal?",
    "If you could claim any turf right now, where you posting up?",
    "What's the wildest thing you seen on the block?",
    "Who you think run the streets? Shikyo or TK?",
    "Be honest: you ever snitched on someone?",
]

class JamalBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.wisdom_counter = 0
        self.next_wisdom = random.randint(30, 50)
        self.interaction_counter = 0
        self.next_interaction = random.randint(50, 100)
        self.bounties = {}  # Global bounty storage

    async def setup_hook(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        await asyncio.to_thread(load_player_data)
        self.auto_save_loop.start()
        self.inactivity_check_loop.start()
        self.server_event_loop.start()
        guild = discord.Object(id=GUILD_ID)

        # Top-level commands (flattened from groups)
        for cls in [EconomyCommands, FunCommands, CrimeCommands, GamesCommands, SocialCommands, UtilityCommands]:
            instance = cls()
            for attr_name in dir(instance):
                attr = getattr(instance, attr_name)
                if isinstance(attr, app_commands.Command):
                    self.tree.add_command(attr)

        # Group commands
        self.tree.add_command(HustleGroup())
        self.tree.add_command(JamalGroup())
        self.tree.add_command(HoodGroup())
        self.tree.add_command(ProfileCommands())
        self.tree.add_command(JoseGroup())
        self.tree.add_command(BountyCommands())
        self.tree.add_command(HitCommands())
        self.tree.add_command(StreetCredCommands())

        await self.tree.sync(guild=guild)
        print("✅ Slash commands synced!")

    @tasks.loop(seconds=AUTO_SAVE_INTERVAL)
    async def auto_save_loop(self):
        await save_player_data(True)

    @tasks.loop(minutes=1)
    async def inactivity_check_loop(self):
        global last_message_time
        if time.time() - last_message_time > INACTIVITY_THRESHOLD * 60:
            channel = self.get_channel(1445307822689620090)  # Replace with your general chat ID
            if channel:
                question = random.choice(inactivity_questions)
                await channel.send(f"💬 **Chat dead for {INACTIVITY_THRESHOLD} mins...** {question}")
            last_message_time = time.time()  # Reset to avoid spam

    @tasks.loop(minutes=30)
    async def server_event_loop(self):
        if random.random() < 0.1:  # 10% chance every 30 min
            channel = self.get_channel(1445307822689620090)  # General chat
            if channel:
                event_type = random.choice(["block_party", "drive_by"])
                if event_type == "block_party":
                    embed = discord.Embed(title="🎉 BLOCK PARTY!", description="The hood is throwing a block party! Answer trivia questions for loot!", color=0x00ff00)
                    embed.add_field(name="Question", value="What does 'no cap' mean?", inline=False)
                    embed.add_field(name="Options", value="1. No hat\n2. No lie\n3. No money", inline=False)
                    view = EventView("block_party", {"answer": 2})
                    await channel.send(embed=embed, view=view)
                elif event_type == "drive_by":
                    embed = discord.Embed(title="🚗 DRIVE-BY HUNT!", description="Opps are lurking! Spot the intruder in the emoji sequence!", color=0xff0000)
                    sequence = "🚗💥🔫" + "".join(random.choice(["🚗", "🏠", "👤"]) for _ in range(5)) + "👹"
                    embed.add_field(name="Sequence", value=sequence, inline=False)
                    embed.add_field(name="Task", value="Click the button when you see the opp (👹)!", inline=False)
                    view = EventView("drive_by", {"sequence": sequence})
                    await channel.send(embed=embed, view=view)

    @server_event_loop.before_loop
    async def before_event_loop(self):
        await self.wait_until_ready()

    async def on_ready(self):
        print(f"🔥 Jamal is online as {self.user}")
        await self.change_presence(activity=discord.Game(name="/Shikyo | j!help"))
        start_backup_loop()

bot = JamalBot()

# Helper function to check if user has booster/N-word immunity
def has_nword_pass(user_id: int) -> bool:
    data = get_player_data(user_id)
    return "hard_r_pass" in data.get("purchased_services", [])

def is_booster(member: discord.Member) -> bool:
    return any(role.id in BOOSTER_ROLES for role in member.roles)

@bot.event
async def on_message(message: discord.Message):
    global last_message_time
    last_message_time = time.time()

    if message.author.bot:
        return

    # Prefix commands
    if message.content.startswith(PREFIX):
        await handle_prefix_command(message)
        return

    # N-word detection with booster/pass immunity
    if re.search(r"\bnigg[ae]r?\b", message.content, re.IGNORECASE):
        member = message.guild.get_member(message.author.id) if message.guild else None
        if member and (is_booster(member) or has_nword_pass(message.author.id)):
            # Boosters/pass holders are immune
            return

        data = get_player_data(message.author.id)
        data["roastsReceived"] += 1

        if re.search(r"\bnigger\b", message.content, re.IGNORECASE):
            roast = random.choice(HARD_R_REPLIES)
            await message.reply(f"{roast}\n\n⚠️ **HEAT +20** - The 12 are watching you now!")
            data["heat"] = min(data["heat"] + 20, 100)
        elif re.search(r"\bnigga\b", message.content, re.IGNORECASE):
            roast = random.choice(SOFT_A_REPLIES)
            await message.reply(f"{roast}\n\n⚠️ **HEAT +10** - You're attracting attention!")
            data["heat"] = min(data["heat"] + 10, 100)

        schedule_save()

        if data["heat"] >= 80 and random.random() > 0.7:
            await asyncio.sleep(3)
            loss = int(data["bread"] * 0.3)
            data["bread"] = max(0, data["bread"] - loss)
            data["heat"] = int(data["heat"] * 0.5)
            schedule_save()
            await message.channel.send(
                f"🚔 **POLICE RAID!** <@{message.author.id}>, the 12 just hit your trap house! You lost {loss} bread!"
            )
        return

    # Random events
    bot.wisdom_counter += 1
    if bot.wisdom_counter >= bot.next_wisdom:
        bot.wisdom_counter = 0
        bot.next_wisdom = random.randint(30, 50)

    bot.interaction_counter += 1
    if bot.interaction_counter >= bot.next_interaction:
        bot.interaction_counter = 0
        bot.next_interaction = random.randint(50, 100)
        data = get_player_data(message.author.id)
        event = random.random()

        if event < 0.3:
            item = random.choice(LOOT_ITEMS)
            data["inventory"].append(item)
            schedule_save()
            await message.channel.send(f"🎁 **RANDOM EVENT:** Jamal blessed <@{message.author.id}> with {item}! Added to your inventory.")
        elif event < 0.6:
            if data["inventory"]:
                stolen = random.choice(data["inventory"])
                data["inventory"].remove(stolen)
                schedule_save()
                await message.channel.send(f"😈 **RANDOM EVENT:** Jamal stole <@{message.author.id}>'s {stolen}! Better watch your stuff!")
            else:
                await message.channel.send(f"🤡 **RANDOM EVENT:** Jamal tried to rob <@{message.author.id}> but you're broke as hell!")
        elif event < 0.8:
            if data["heat"] > 50:
                fine = int(data["bread"] * 0.2)
                data["bread"] = max(0, data["bread"] - fine)
                data["heat"] = max(0, data["heat"] - 30)
                schedule_save()
                await message.channel.send(f"🚓 **POLICE CHECKPOINT:** <@{message.author.id}> got stopped by the 12! Paid {fine} bread in fines. Heat -30")
            else:
                await message.channel.send(f"✅ **POLICE CHECKPOINT:** <@{message.author.id}> slid through clean. Your heat level is low enough ({data['heat']}%).")
        else:
            win = random.random() > 0.5
            if win:
                winnings = random.randint(100, 600)
                data["bread"] += winnings
                data["streetCred"] += 10
                schedule_save()
                await message.channel.send(f"🥊 **STREET FIGHT:** <@{message.author.id}> won the fight! +{winnings} bread, +10 street cred!")
            else:
                loss = int(data["bread"] * 0.1)
                data["bread"] = max(0, data["bread"] - loss)
                schedule_save()
                await message.channel.send(f"😵 **STREET FIGHT:** <@{message.author.id}> got knocked out! Lost {loss} bread.")

        if random.random() < 0.2:
            view = ChickenView()
            await message.channel.send(
                f"🍗 **FRIED CHICKEN ALERT!** Jamal just snatched <@{message.author.id}>'s bucket of fried chicken! Click the button to give him another one before he gets mad!",
                view=view
            )

        if data["hood"]["name"] and random.random() < 0.1:
            hood_name = data["hood"]["name"]
            if hood_name == 'southside':
                data["bread"] += 50
                await message.channel.send(f"🏚️ **HOOD EVENT:** An old lady from Southside gave you some homemade cookies. +50 bread.")
            elif hood_name == 'northside':
                data["bread"] += 100
                await message.channel.send(f"🏙️ **HOOD EVENT:** A businessman slipped you a tip. +100 bread.")
            elif hood_name == 'eastside':
                data["bread"] += 75
                await message.channel.send(f"🏭 **HOOD EVENT:** Found some scrap metal to sell. +75 bread.")
            elif hood_name == 'westside':
                data["bread"] += 80
                await message.channel.send(f"🏡 **HOOD EVENT:** Your neighbor paid you to watch their house. +80 bread.")
            elif hood_name == 'downtown':
                data["bread"] += 200
                await message.channel.send(f"🏢 **HOOD EVENT:** A lobbyist gave you a 'consultation fee'. +200 bread.")
            schedule_save()

async def handle_prefix_command(message: discord.Message):
    content = message.content[len(PREFIX):].strip().lower()
    args = content.split()
    if not args:
        return

    cmd = args[0]
    data = get_player_data(message.author.id)

    # Basic prefix commands for quick access
    if cmd == "daily":
        now = int(time.time() * 1000)
        cooldown = 24 * 60 * 60 * 1000
        last = data["streak"].get("lastDailyClaim", data.get("lastDaily", 0))
        if now - last > cooldown * 2:
            data["streak"]["daily"] = 0
        elif now - last < cooldown:
            remaining = cooldown - (now - last)
            hours = remaining // (60 * 60 * 1000)
            await message.channel.send(f"Chill! Wait {hours}h.")
            return
        data["streak"]["daily"] += 1
        data["streak"]["lastDailyClaim"] = now
        data["lastDaily"] = now
        streak_bonus = min(data["streak"]["daily"], 7) * 50
        base = 500
        total = int(base * data["multiplier"]) + streak_bonus
        data["bread"] += total
        schedule_save()
        await message.channel.send(f"💰 +{total} bread! Streak: {data['streak']['daily']} days.")

    elif cmd == "bread":
        await message.channel.send(f"🍞 You have **{data['bread']}** bread.")

    elif cmd == "roast" and message.mentions:
        target = message.mentions[0]
        roast_text = random.choice(RANDOM_ROASTS)
        await message.channel.send(f"🔥 <@{target.id}> {roast_text}")

    elif cmd == "help":
        await message.channel.send("Use `/help` for all commands or `j!daily`, `j!bread`, `j!roast @user`.")

    elif cmd == "shikyo":
        await message.channel.send("👑 Shikyo is the plug. Check `/shop` for premium services.")

    elif cmd == "twerk":
        responses = [
            "Jamal starts throwing it back in the middle of the chat! 🍑💨",
            "Jamal twerks so hard the whole server shakes! 🥵",
            "Jamal drops it low... real low. Too low. Now his back hurts.",
            "Jamal's twerking skills are unmatched. The opps are jealous.",
        ]
        await message.channel.send(random.choice(responses))

    elif cmd == "steal":
        if len(args) < 2 or not message.mentions:
            await message.channel.send("Usage: j!steal @user [item]")
            return
        user = message.mentions[0]
        item = args[2] if len(args) > 2 else random.choice(LOOT_ITEMS)
        await message.channel.send(f"Jamal popped out the cut and stole <@{user.id}>'s **{item}**! NO CAP!")

    # Jamal talking/interaction (responds to mentions or keywords)
    elif "jamal" in message.content.lower() or bot.user.mentioned_in(message):
        responses = [
            "Yo wassup?",
            "I'm counting bread, what you need?",
            "You good cuz?",
            "The block is hot today.",
            "Shikyo said keep grinding.",
            random.choice(QUOTES),
        ]
        await message.channel.send(random.choice(responses))

@bot.event
async def on_interaction(interaction: discord.Interaction):
    # Button interactions are handled by the views themselves
    pass

async def graceful_shutdown():
    print("🔄 Saving data before shutdown...")
    bot.auto_save_loop.cancel()
    bot.inactivity_check_loop.cancel()
    await stop_backup_loop()
    await save_player_data(True)
    print("✅ Data saved. Goodbye!")
    await bot.close()

async def main():
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(graceful_shutdown()))

    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())