import discord

class BlackjackView(discord.ui.View):
    def __init__(self, game_id: str, game: dict):
        super().__init__(timeout=300)
        self.game_id = game_id
        self.game = game

        hit_btn = discord.ui.Button(label="Hit", style=discord.ButtonStyle.primary, custom_id=f"bj_{game_id}_hit")
        hit_btn.callback = self.create_callback("hit")
        self.add_item(hit_btn)

        stand_btn = discord.ui.Button(label="Stand", style=discord.ButtonStyle.secondary, custom_id=f"bj_{game_id}_stand")
        stand_btn.callback = self.create_callback("stand")
        self.add_item(stand_btn)

        quit_btn = discord.ui.Button(label="Quit", style=discord.ButtonStyle.danger, custom_id=f"bj_{game_id}_quit")
        quit_btn.callback = self.create_callback("quit")
        self.add_item(quit_btn)

    def create_callback(self, action: str):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
        return callback