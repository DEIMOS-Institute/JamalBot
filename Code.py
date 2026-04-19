#  +---+    _   _______ _      _      __   _______ _   _______  _____ _____ _     ______ 
#  |   |   | | / /_   _| |    | |     \ \ / /  _  | | | | ___ \/  ___|  ___| |    |  ___|
#  O   |   | |/ /  | | | |    | |      \ V /| | | | | | | |_/ /\ `--.| |__ | |    | |_   
# /|\  |   |    \  | | | |    | |       \ / | | | | | | |    /  `--. \  __|| |    |  _|
# / \  |   | |\  \_| |_| |____| |____   | | \ \_/ / |_| | |\ \ /\__/ / |___| |____| |
#      |   \_| \_/\___/\_____/\_____/   \_/  \___/ \___/\_| \_|\____/\____/\_____/\_|    

import random
import discord
from discord.ext import commands, tasks
from itertools import cycle
import os
import asyncio
import json

def get_server_prefix(client, message):
    with open("cogs/JsonFiles/prefixes.json", "r") as f:
        prefix = json.load(f)

        return prefix[str(message.guild.id)]

bot_status = cycle(["/shikyo", "/shikyo"])

@tasks.loop(hours=2)
async def change_status():
    await client.change_presence(activity=discord.Game(next(bot_status)))

client = commands.Bot(command_prefix=get_server_prefix, intents=discord.Intents.all())

client.remove_command("help")

@client.event
async def on_ready():
    await client.tree.sync()
    print("Bot is successfully connected to Discord!")
    change_status.start()

@client.event
async def on_guild_join(guild):
    with open("cogs/JsonFiles/prefixes.json", "r") as f:
        prefix = json.load(f)

    prefix[str(guild.id)] = "s?" # Prefix used to trigger the bot. Adjust as needed

    with open("cogs/JsonFiles/prefixes.json", "w") as f:
        json.dump(prefix, f, indent=4)

@client.event
async def on_guild_remove(guild):
    with open("cogs/JsonFiles/prefixes.json", "r") as f:
        prefix = json.load(f)

    prefix.pop[str(guild.id)]

@client.command()
async def setprefix(ctx, *, newprefix: str):
    with open("cogs/JsonFiles/prefixes.json", "r") as f:
        prefix = json.load(f)

    prefix[str(ctx.guild.id)] = newprefix

    with open("cogs/JsonFiles/prefixes.json", "w") as f:
        json.dump(prefix, f, indent=4)

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Error: You do not have permission to execute this command.")

async def main():
    async with client:
        await load()
        await client.start("j's token")

asyncio.run(main())

