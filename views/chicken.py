import discord
import random


class ChickenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Give Chicken", style=discord.ButtonStyle.primary)
    async def give_chicken(self, interaction: discord.Interaction, button: discord.ui.Button):
        if random.random() < 0.3:
            await interaction.response.edit_message(
                content='Jamal: "ALRIGHT CUZ, WE STRAIGHT FOR NOW. DON\'T LET ME CATCH YOU SLIPPING AGAIN."',
                view=None
            )
        else:
            responses = [
                'Jamal: "ONLY ONE BUCKET? YOU THINK I\'M SOME KIND OF BUM? GIVE ME ANOTHER ONE."',
                'Jamal: "THIS CHICKEN DRY AS HELL. GIVE ME MORE BEFORE I GET TRIGGERED."',
                'Jamal: "MY COUSIN NEED SOME TOO. PASS ANOTHER BUCKET."',
                'Jamal: "KEEP \'EM COMING. I\'M HUNGRY FOR REAL."'
            ]
            await interaction.response.edit_message(content=random.choice(responses), view=self)