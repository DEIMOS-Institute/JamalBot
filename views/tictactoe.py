import discord

class TTTView(discord.ui.View):
    def __init__(self, game_id: str, game: dict):
        super().__init__(timeout=300)
        self.game_id = game_id
        self.game = game

        for i in range(9):
            row = i // 3
            cell = game["board"][i]
            disabled = cell != ' '
            style = (
                discord.ButtonStyle.primary if cell == 'X'
                else discord.ButtonStyle.success if cell == 'O'
                else discord.ButtonStyle.secondary
            )
            button = discord.ui.Button(
                label='⬜' if cell == ' ' else cell,
                style=style,
                custom_id=f"ttt_{game_id}_{i}",
                row=row,
                disabled=disabled
            )
            button.callback = self.create_callback(i)
            self.add_item(button)

        quit_btn = discord.ui.Button(
            label="🚪 Quit",
            style=discord.ButtonStyle.danger,
            custom_id=f"ttt_{game_id}_quit",
            row=3
        )
        quit_btn.callback = self.quit_callback
        self.add_item(quit_btn)

    def create_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
        return callback

    async def quit_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()