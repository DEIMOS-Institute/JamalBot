import discord
from discord import app_commands
import random
from ..data import get_player_data, schedule_save
from ..constants import ROAST_CATEGORIES, RANDOM_ROASTS, KILL_MESSAGES, QUOTES
from ..views import StoryView

class FunCommands:
    def __init__(self):
        super().__init__(name="fun", description="Fun and entertainment commands")

    @app_commands.command(name="roast")
    @app_commands.describe(target="Who needs to be roasted?", category="Type of roast")
    @app_commands.choices(category=[
        app_commands.Choice(name="🔥 Appearance", value="appearance"),
        app_commands.Choice(name="🧠 Intelligence", value="intelligence"),
        app_commands.Choice(name="👤 Personality", value="personality"),
        app_commands.Choice(name="🏙️ Hood", value="hood"),
        app_commands.Choice(name="💀 Savage", value="savage"),
        app_commands.Choice(name="🎲 Random", value="random")
    ])
    async def roast(self, interaction: discord.Interaction, target: discord.Member, category: str = "random"):
        if category == "random" or category not in ROAST_CATEGORIES:
            roast = random.choice(RANDOM_ROASTS)
        else:
            roast = random.choice(ROAST_CATEGORIES[category])
        data = get_player_data(interaction.user.id)
        target_data = get_player_data(target.id)
        data["roastsGiven"] += 1
        target_data["roastsReceived"] += 1
        schedule_save()
        await interaction.response.send_message(f"🔥 **Roasting <@{target.id}>:** {roast}")

    @app_commands.command(name="slap")
    @app_commands.describe(user="Who needs a reality check")
    async def slap(self, interaction: discord.Interaction, user: discord.Member):
        responses = [
            f"Jamal reached across the screen and slapped the taste out of <@{user.id}>'s mouth!",
            f"<@{interaction.user.id}> hit <@{user.id}> with a backhand so hard they saw their ancestors.",
            f"Jamal: \"KEEP MY NAME OUT YOUR MOUTH!\" *SLAPS <@{user.id}>*",
            f"The whole chat heard that slap on <@{user.id}>. Embarrassing."
        ]
        await interaction.response.send_message(random.choice(responses))

    @app_commands.command(name="twerk")
    async def twerk(self, interaction: discord.Interaction):
        responses = [
            "Jamal starts throwing it back in the middle of the chat! 🍑💨",
            "Jamal twerks so hard the whole server shakes! 🥵",
            "Jamal drops it low... real low. Too low. Now his back hurts.",
            "Jamal's twerking skills are unmatched. The opps are jealous.",
        ]
        await interaction.response.send_message(random.choice(responses))

    @app_commands.command(name="sniff")
    async def sniff(self, interaction: discord.Interaction):
        smells = [
            "It smells like broke in here.",
            "I smell zaza...",
            "I smell 12 nearby...",
            "It smells like straight snitch in this chat.",
            "I smell fresh bread!",
            "Someone's been smoking that loud pack.",
            "Smells like opps are lurking.",
            "It smells like victory... or is that just my cologne?",
        ]
        await interaction.response.send_message(f"👃 Jamal takes a deep sniff...\n\n**\"{random.choice(smells)}\"**")

    @app_commands.command(name="fish")
    @app_commands.describe(amount="Bet amount")
    async def fish(self, interaction: discord.Interaction, amount: int):
        data = get_player_data(interaction.user.id)
        if amount < 10:
            await interaction.response.send_message("Minimum bet is 10 bread.", ephemeral=True)
            return
        if data["bread"] < amount:
            await interaction.response.send_message("You don't have enough bread!", ephemeral=True)
            return
        if random.random() < 0.4:
            fish_value = amount * 2
            data["bread"] += fish_value
            schedule_save()
            await interaction.response.send_message(f"🐟 You cast your line and caught a big fish! You gained **{fish_value}** bread!")
        else:
            data["bread"] -= amount
            schedule_save()
            await interaction.response.send_message(f"🐟 You fished all day and caught nothing... Lost **{amount}** bread.")

    @app_commands.command(name="kill")
    @app_commands.describe(user="Who to kill")
    async def kill(self, interaction: discord.Interaction, user: discord.Member):
        death_msg = random.choice(KILL_MESSAGES)
        await interaction.response.send_message(f"🔪 **{interaction.user.name}** killed **{user.name}** – {death_msg}")

    @app_commands.command(name="8ball")
    @app_commands.describe(question="Your question")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Yes", "No", "Maybe", "Hell nah", "For sure", "Keep dreaming",
            "Jamal says yes", "Try again later", "Ask the opps", "On folks grave, yes",
            "In your dreams", "The 12 say no", "Hell yeah", "Absolutely not",
        ]
        await interaction.response.send_message(f"🎱 **8-Ball:** {random.choice(responses)}")

    @app_commands.command(name="dab")
    @app_commands.describe(user="Who to dab on (optional)")
    async def dab(self, interaction: discord.Interaction, user: discord.Member | None = None):
        if user:
            await interaction.response.send_message(f"💃 <@{interaction.user.id}> just dabbed on <@{user.id}>! Get rekt!")
        else:
            await interaction.response.send_message(f"💃 <@{interaction.user.id}> dabbed on the haters!")

    @app_commands.command(name="yeet")
    @app_commands.describe(thing="What to yeet")
    async def yeet(self, interaction: discord.Interaction, thing: str):
        responses = [
            f"🚀 **YEET!** {thing} went flying into the sun!",
            f"💨 <@{interaction.user.id}> yeeted {thing} into oblivion!",
            f"🤾‍♂️ {thing} got yeeted so hard it landed in 3012.",
            f"🎯 {thing} was yeeted perfectly into the trash can.",
        ]
        await interaction.response.send_message(random.choice(responses))

    @app_commands.command(name="mock")
    @app_commands.describe(text="Text to mock")
    async def mock(self, interaction: discord.Interaction, text: str):
        mocked = "".join(c.lower() if i % 2 == 0 else c.upper() for i, c in enumerate(text))
        await interaction.response.send_message(f"😤 **MOCKING:** {mocked}")

    @app_commands.command(name="fact")
    async def fact(self, interaction: discord.Interaction):
        facts = [
            "A group of flamingos is called a 'flamboyance'.",
            "Octopuses have three hearts.",
            "Bananas are berries, but strawberries aren't.",
            "Honey never spoils. Archaeologists found 3000-year-old honey still edible!",
            "A day on Venus is longer than a year on Venus.",
            "Wombat poop is cube-shaped.",
            "The shortest war in history was between Britain and Zanzibar in 1896 – it lasted 38 minutes.",
            "Cows have best friends and get stressed when separated.",
            "The Eiffel Tower can be 15 cm taller during summer.",
            "There's a species of jellyfish that is biologically immortal.",
        ]
        await interaction.response.send_message(f"📚 **FUN FACT:** {random.choice(facts)}")

    @app_commands.command(name="joke")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "How does a penguin build its house? Igloos it together!",
            "Why don't skeletons fight each other? They don't have the guts.",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't you give Elsa a balloon? Because she will let it go!",
            "What do you call a fish wearing a bowtie? So-fish-ticated!",
        ]
        await interaction.response.send_message(f"😂 **JOKE:** {random.choice(jokes)}")

    @app_commands.command(name="pun")
    async def pun(self, interaction: discord.Interaction):
        puns = [
            "I used to be a baker, but I couldn't make enough dough.",
            "I'm reading a book on anti-gravity. It's impossible to put down!",
            "I don't trust stairs. They're always up to something.",
            "What do you call a cheese that's not yours? Nacho cheese!",
            "I would tell you a construction pun, but I'm still working on it.",
            "I have a fear of speed bumps. I'm slowly getting over it.",
            "I used to play piano by ear, but now I use my hands.",
            "I'm on a seafood diet. I see food and I eat it.",
        ]
        await interaction.response.send_message(f"🥁 **PUN:** {random.choice(puns)}")

    @app_commands.command(name="quote")
    async def quote(self, interaction: discord.Interaction):
        await interaction.response.send_message(random.choice(QUOTES))

    @app_commands.command(name="story")
    async def story(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        progress = data.get("story_progress", {})

        # Simple branching story
        if "loyalty_path" not in progress:
            embed = discord.Embed(title="📖 Life Simulator", description="You wake up in the hood. The 12 just pulled up outside. What do you do?")
            embed.add_field(name="Option 1", value="Hide the stash and stay quiet.", inline=False)
            embed.add_field(name="Option 2", value="Grab your strap and confront them.", inline=False)
            embed.add_field(name="Option 3", value="Snitch on the neighbor to save yourself.", inline=False)
            view = StoryView(interaction.user.id, "start")
            await interaction.response.send_message(embed=embed, view=view)
        else:
            path = progress["loyalty_path"]
            if path == "loyal":
                ending = "You stayed loyal. The hood respects you. +500 street cred!"
                data["streetCred"] += 500
            elif path == "fight":
                ending = "You fought back. Got arrested but became a legend. +1000 respect!"
                data["respect"] += 1000
            else:
                ending = "You snitched. The hood turns on you. -200 street cred."
                data["streetCred"] = max(0, data["streetCred"] - 200)
            schedule_save()
            await interaction.response.send_message(f"📖 **Story Ending:** {ending}")