import discord
import random
from ..data import get_player_data, schedule_save

class BetView(discord.ui.View):
    def __init__(self, challenger_id: int, target_id: int, amount: int):
        super().__init__(timeout=60)
        self.challenger_id = challenger_id
        self.target_id = target_id
        self.amount = amount

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            await interaction.response.send_message("This ain't your bet.", ephemeral=True)
            return

        challenger_data = get_player_data(self.challenger_id)
        target_data = get_player_data(self.target_id)

        if challenger_data["bread"] < self.amount or target_data["bread"] < self.amount:
            await interaction.response.edit_message(content="Someone ain't got the bread no more. Bet cancelled.", view=None)
            return

        win = random.random() > 0.5
        if win:
            challenger_data["bread"] += self.amount
            target_data["bread"] -= self.amount
            content = f"🎰 <@{self.challenger_id}> won the flip and snatched **{self.amount}** bread from <@{self.target_id}>!"
        else:
            challenger_data["bread"] -= self.amount
            target_data["bread"] += self.amount
            content = f"🎰 <@{self.target_id}> won the flip and snatched **{self.amount}** bread from <@{self.challenger_id}>!"
        schedule_save()
        await interaction.response.edit_message(content=content, view=None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            await interaction.response.send_message("This ain't your bet.", ephemeral=True)
            return
        await interaction.response.edit_message(content="Bet declined. Pussy.", view=None)