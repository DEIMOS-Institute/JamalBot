#  +---+    _   _______ _      _      __   _______ _   _______  _____ _____ _     ______ 
#  |   |   | | / /_   _| |    | |     \ \ / /  _  | | | | ___ \/  ___|  ___| |    |  ___|
#  O   |   | |/ /  | | | |    | |      \ V /| | | | | | | |_/ /\ `--.| |__ | |    | |_   
# /|\  |   |    \  | | | |    | |       \ / | | | | | | |    /  `--. \  __|| |    |  _|
# / \  |   | |\  \_| |_| |____| |____   | | \ \_/ / |_| | |\ \ /\__/ / |___| |____| |
#      |   \_| \_/\___/\_____/\_____/   \_/  \___/ \___/\_| \_|\____/\____/\_____/\_|    

import discord
from discord.ext import commands, tasks
from itertools import cycle
import os
import asyncio
import json

PREFIX_FILE = "cogs/JsonFiles/prefixes.json"
DEFAULT_PREFIX = "s?"

def load_prefixes():
    if not os.path.exists(PREFIX_FILE):
        os.makedirs(os.path.dirname(PREFIX_FILE), exist_ok=True)
        with open(PREFIX_FILE, "w") as f:
            json.dump({}, f, indent=4)
        return {}

    with open(PREFIX_FILE, "r") as f:
        return json.load(f)

def save_prefixes(prefixes):
    with open(PREFIX_FILE, "w") as f:
        json.dump(prefixes, f, indent=4)

def get_server_prefix(client, message):
    prefixes = load_prefixes()

    if message.guild is None:
        return DEFAULT_PREFIX

    return prefixes.get(str(message.guild.id), DEFAULT_PREFIX)

bot_status = cycle(["/shikyo", "/shikyo"])

intents = discord.Intents.all()
client = commands.Bot(command_prefix=get_server_prefix, intents=intents)

client.remove_command("help")

@tasks.loop(hours=2)
async def change_status():
    await client.change_presence(activity=discord.Game(next(bot_status)))

@client.event
async def on_ready():
    try:
        await client.tree.sync()
    except Exception as e:
        print(f"Slash command sync failed: {e}")

    if not change_status.is_running():
        change_status.start()

    print(f"Bot is successfully connected to Discord as {client.user}!")

@client.event
async def on_guild_join(guild):
    prefixes = load_prefixes()
    prefixes[str(guild.id)] = DEFAULT_PREFIX
    save_prefixes(prefixes)

@client.event
async def on_guild_remove(guild):
    prefixes = load_prefixes()
    prefixes.pop(str(guild.id), None)
    save_prefixes(prefixes)

@client.command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, *, newprefix: str):
    prefixes = load_prefixes()
    prefixes[str(ctx.guild.id)] = newprefix
    save_prefixes(prefixes)
    await ctx.send(f"Prefix updated to `{newprefix}`")

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Error: You do not have permission to execute this command.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"Unhandled command error: {error}")

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

async def main():
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        raise ValueError("No DISCORD_TOKEN found in environment variables.")

    async with client:
        await load()
        await client.start(token)

asyncio.run(main())