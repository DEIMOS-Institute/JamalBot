import discord
from ..data import get_player_data, schedule_save

class StoryView(discord.ui.View):
    def __init__(self, user_id: int, stage: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.stage = stage

    @discord.ui.button(label="Hide Stash", style=discord.ButtonStyle.primary)
    async def hide_stash(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This ain't your story.", ephemeral=True)
            return
        data = get_player_data(self.user_id)
        data["story_progress"]["loyalty_path"] = "loyal"
        schedule_save()
        await interaction.response.edit_message(content="📖 **Choice Made:** You hid the stash. The 12 left empty-handed. You stayed loyal to the hood.", view=None)

    @discord.ui.button(label="Confront Them", style=discord.ButtonStyle.danger)
    async def confront(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This ain't your story.", ephemeral=True)
            return
        data = get_player_data(self.user_id)
        data["story_progress"]["loyalty_path"] = "fight"
        schedule_save()
        await interaction.response.edit_message(content="📖 **Choice Made:** You confronted the 12. Shots fired, but you held your ground. The hood calls you a legend.", view=None)

    @discord.ui.button(label="Snitch", style=discord.ButtonStyle.secondary)
    async def snitch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This ain't your story.", ephemeral=True)
            return
        data = get_player_data(self.user_id)
        data["story_progress"]["loyalty_path"] = "snitch"
        schedule_save()
        await interaction.response.edit_message(content="📖 **Choice Made:** You snitched on the neighbor. The 12 left, but the hood knows. Loyalty broken.", view=None)