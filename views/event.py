import discord
import random
from ..data import get_player_data, schedule_save
from ..constants import COLLECTIBLES

class EventView(discord.ui.View):
    def __init__(self, event_type: str, data: dict):
        super().__init__(timeout=600)  # 10 min
        self.event_type = event_type
        self.data = data
        self.participants = set()

    @discord.ui.button(label="Answer 1", style=discord.ButtonStyle.primary)
    async def answer1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, 1)

    @discord.ui.button(label="Answer 2", style=discord.ButtonStyle.primary)
    async def answer2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, 2)

    @discord.ui.button(label="Answer 3", style=discord.ButtonStyle.primary)
    async def answer3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, 3)

    @discord.ui.button(label="Spot Opp", style=discord.ButtonStyle.danger)
    async def spot_opp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.event_type != "drive_by":
            return
        if interaction.user.id in self.participants:
            await interaction.response.send_message("Already participated!", ephemeral=True)
            return
        self.participants.add(interaction.user.id)
        # Simple: random reward
        data = get_player_data(interaction.user.id)
        loot = random.randint(100, 500)
        data["bread"] += loot
        # Chance for collectible
        if random.random() < 0.2:
            coll_id = random.choice(list(COLLECTIBLES.keys()))
            data["collectibles"].append({"id": coll_id, "rarity": COLLECTIBLES[coll_id]["rarity"]})
            schedule_save()
            await interaction.response.send_message(f"🎁 You spotted the opp! +{loot} bread and a rare {COLLECTIBLES[coll_id]['name']}!", ephemeral=True)
        else:
            schedule_save()
            await interaction.response.send_message(f"🎁 You spotted the opp! +{loot} bread!", ephemeral=True)

    async def handle_answer(self, interaction: discord.Interaction, answer: int):
        if self.event_type != "block_party":
            return
        if interaction.user.id in self.participants:
            await interaction.response.send_message("Already participated!", ephemeral=True)
            return
        self.participants.add(interaction.user.id)
        correct = self.data.get("answer", 2)
        data = get_player_data(interaction.user.id)
        if answer == correct:
            loot = random.randint(200, 1000)
            data["bread"] += loot
            # Chance for collectible
            if random.random() < 0.3:
                coll_id = random.choice(list(COLLECTIBLES.keys()))
                data["collectibles"].append({"id": coll_id, "rarity": COLLECTIBLES[coll_id]["rarity"]})
                schedule_save()
                await interaction.response.send_message(f"✅ Correct! +{loot} bread and {COLLECTIBLES[coll_id]['name']}!", ephemeral=True)
            else:
                schedule_save()
                await interaction.response.send_message(f"✅ Correct! +{loot} bread!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Wrong! Better luck next time.", ephemeral=True)