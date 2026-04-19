import asyncio
import discord
from discord.ext import commands
import random
import json
from discord import app_commands

class misc(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print("misc.py is ready!")

    @commands.command()
    async def test(self, ctx):
        bot_latency = round(self.client.latency * 1000)
        #if bot_latency > 1000:
            #response = f"I'm alive but slow! {bot_latency} ms."
        #else:
            #response = f"I'm alive! {bot_latency} ms."
        await ctx.send(f"I'm alive! {bot_latency} ms.")

async def setup(client):
    await client.add_cog(misc(client))