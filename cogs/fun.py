import discord
from discord.ext import commands
import random
import json
from discord import Guild, app_commands
import re

class fun(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print("fun.py is ready!")
    
    @commands.hybrid_command(name="8ball", description="Ask the magic 8‑ball a question")
    async def ball(self, ctx, *, question):
        with open("8ball.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(f"{ctx.author} asks {question}:\n{response}")
    @ball.error
    async def ball_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Am I supposed to tell the air's fortune?")

    @commands.hybrid_command(name="roast", description="Roast a specific or random user")
    async def roast(self, ctx, user: discord.Member = None):
        if user is None:
            user = random.choice(ctx.guild.members)

        with open("roasts.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response.format(user=user.mention))

    @commands.hybrid_command(name="say", description="Jamal says anything you want him to")
    async def say(self, ctx, *, prompt):

    # Check if @everyone or @here or a role mention is part of the question
        if "@everyone" in prompt or "@here" in prompt or re.search(r"<@&\d+>", prompt):
            await ctx.send("I can't rate mentions like `@everyone`, `@here`, or roles.")
            return

        await ctx.send(f"{prompt}")

    @commands.hybrid_command(name="drip", description="Jamal rates your hood drip")
    async def drip(self, ctx):
        with open("drip.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response)

    @commands.hybrid_command(name="bail", description="Bail Jamal out of jail")
    async def bail(self, ctx):
        with open("bail.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response)

    @commands.hybrid_command(name="sniff", description="Sniff the chat to see if something is fishy")
    async def sniff(self, ctx):
        with open("sniff.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response)

    @commands.hybrid_command(name="twerk", description="Jamal shows off his moves")
    async def twerk(self, ctx):
        with open("twerk.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response)

    @commands.hybrid_command(name="fact", description="Get a random fun fact about the hood")
    async def fact(self, ctx):
        with open("fact.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="pun", description="Get a terrible pun")
    async def pun(self, ctx):
        with open("puns.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="joke", description="Tell a random black dad joke")
    async def joke(self, ctx):
        with open("joke.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="rap", description="Jamal drops a fire verse")
    async def rap(self, ctx):
        with open("rap.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="kill", description="Hire Jamal to slime someone out for you.")
    async def kill(self, ctx, user: discord.Member = None):
        if user is None:
            user = random.choice(ctx.guild.members)

        with open("kill.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response.format(user=user.mention))

    @commands.hybrid_command(name="yeet", description="Tell a random black dad joke")
    async def yeet(self, ctx, user: discord.Member = None):
        if user is None:
            user = random.choice(ctx.guild.members)

        with open("yeet.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response.format(user=user.mention))

    @commands.hybrid_command(name="stimulus", description="Check if your stimulus check hit")
    async def stimulus(self, ctx):
        with open("stimulus.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="chill", description="Chill in the cut with Jamal")
    async def chill(self, ctx):
        with open("chill.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="spin", description="Jamal spins the block for you")
    async def spin(self, ctx):
        with open("spin.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="opps", description="Check for opps in the area")
    async def opps(self, ctx):
        with open("opps.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)
    
    @commands.hybrid_command(name="trap", description="Jamal puts you to work in the trap")
    async def trap(self, ctx):
        with open("trap.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="court", description="Jamal goes to court for his charges")
    async def court(self, ctx):
        with open("court.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="smoke", description="Jamal sparks one up with you")
    async def smoke(self, ctx):
        with open("smoke.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="block", description="Check how hot the block is")
    async def block(self, ctx):
        with open("block.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="bando", description="Visit the abandoned house with Jamal")
    async def bando(self, ctx):
        with open("bando.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="lean", description="Jamal pours up a double cup")
    async def lean(self, ctx):
        with open("lean.txt", "r") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses)

            await ctx.send(response)

    @commands.hybrid_command(name="slap", description="Slap someone for talking crazy")
    async def slap(self, ctx, user: discord.Member = None):
        if user is None:
            user = random.choice(ctx.guild.members)

        with open("slap.txt", "r", encoding="utf-8") as f:
            random_responses = f.readlines()
            response = random.choice(random_responses).strip()

        await ctx.send(response.format(user=user.mention))


async def setup(client):
    await client.add_cog(fun(client))