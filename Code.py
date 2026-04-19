import discord
from discord.ext import commands, tasks
from itertools import cycle
from dotenv import load_dotenv
import os
import asyncio
import json

load_dotenv()

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

def get_server_prefix(bot, message):
    prefixes = load_prefixes()
    if message.guild is None:
        return DEFAULT_PREFIX
    return prefixes.get(str(message.guild.id), DEFAULT_PREFIX)

bot_status = cycle(["/shikyo", "/shikyo"])

intents = discord.Intents.all()
client = commands.Bot(command_prefix=get_server_prefix, intents=intents)

@tasks.loop(hours=2)
async def change_status():
    await client.change_presence(activity=discord.Game(next(bot_status)))

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    try:
        await client.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Slash sync failed: {e}")

    if not change_status.is_running():
        change_status.start()

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
        await ctx.send("You do not have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"Command error: {error}")

async def load():
    if not os.path.isdir("./cogs"):
        print("No cogs folder found, skipping cog load.")
        return

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")

async def main():
    token = os.getenv("DISCORD_TOKEN")

    print("Starting bot...")
    print("TOKEN FOUND:", bool(token))
    print("TOKEN LENGTH:", len(token.strip()) if token else 0)

    if not token:
        raise ValueError("DISCORD_TOKEN was not found in environment or .env file.")

    async with client:
        await load()
        await client.start(token.strip())

asyncio.run(main())