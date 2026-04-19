import discord
from discord.ext import commands
import random
import json
from discord import app_commands

class mod(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print("hustle.py is ready!")

    


async def setup(client):
    await client.add_cog(mod(client))