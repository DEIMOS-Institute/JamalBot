import discord
from discord import app_commands
import time
import random
from ..data import get_player_data, schedule_save
from ..utils import get_street_rank
from ..constants import HOODS

class HustleGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="hustle", description="Various street hustles")

    @app_commands.command(name="work")
    async def hustle_work(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        rank = get_street_rank(data["bread"], data["streetCred"])
        car_bonus = 0.8 if "car" in data.get("inventory", []) else 1.0
        final_cd_mult = rank["cdMult"] * car_bonus
        now = int(time.time() * 1000)
        work_cooldown = int((15 * 60 * 1000) * final_cd_mult)

        if data["lastWork"] and now - data["lastWork"] < work_cooldown:
            remaining = int((work_cooldown - (now - data["lastWork"])) / 60000)
            await interaction.response.send_message(f"[{rank['name']}] Clocked out. Wait {remaining} mins.", ephemeral=True)
            return

        data["lastWork"] = now
        pay = random.randint(150, 350)
        if data["hood"]["name"] == 'eastside':
            pay = int(pay * HOODS["eastside"]["perks"]["modifiers"]["hustleWorkEarnings"])
        data["bread"] += pay
        schedule_save()
        await interaction.response.send_message(f"💼 **[{rank['name']}]** You did some legal street work and earned **{pay}** bread.")

    @app_commands.command(name="random")
    async def hustle_random(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        rank = get_street_rank(data["bread"], data["streetCred"])
        car_bonus = 0.8 if "car" in data.get("inventory", []) else 1.0
        final_cd_mult = rank["cdMult"] * car_bonus
        now = int(time.time() * 1000)
        hustle_cooldown = int((30 * 60 * 1000) * final_cd_mult)

        if data["lastHustle"] and now - data["lastHustle"] < hustle_cooldown:
            remaining = int((hustle_cooldown - (now - data["lastHustle"])) / 60000)
            await interaction.response.send_message(f"[{rank['name']}] Wait {remaining} minutes.", ephemeral=True)
            return

        data["lastHustle"] = now
        hustles = [
            {"m": "Flipped some kicks for **{p}** bread.", "min": 200, "max": 600},
            {"m": "Helped move boxes for **{p}** bread.", "min": 100, "max": 400},
            {"m": "Fixed a screen for **{p}** bread.", "min": 300, "max": 700},
            {"m": "Sold some lemonade for **{p}** bread.", "min": 50, "max": 200},
        ]
        h = random.choice(hustles)
        p = random.randint(h["min"], h["max"])
        data["bread"] += p
        schedule_save()
        await interaction.response.send_message(f"💰 **[{rank['name']}]** {h['m'].replace('{p}', str(p))}")

    @app_commands.command(name="corner")
    async def hustle_corner(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        rank = get_street_rank(data["bread"], data["streetCred"])

        if random.random() < 0.35:
            loss = int(data["bread"] * 0.15)
            data["bread"] = max(0, data["bread"] - loss)
            schedule_save()
            await interaction.response.send_message(f"🚨 **[{rank['name']}]** The corner got hot! You lost **{loss}** bread escaping the ops.")
        else:
            p = random.randint(600, 1800)
            data["bread"] += p
            schedule_save()
            await interaction.response.send_message(f"📍 **[{rank['name']}]** You posted up on the corner and made **{p}** bread.")

    @app_commands.command(name="freestyle")
    async def hustle_freestyle(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        rank = get_street_rank(data["bread"], data["streetCred"])
        p = random.randint(150, 650)
        data["bread"] += p
        data["streetCred"] += 2
        schedule_save()
        await interaction.response.send_message(f"🎤 **[{rank['name']}]** Fire verse! The crowd threw you **{p}** bread and +2 street cred!")

    @app_commands.command(name="pickpocket")
    async def hustle_pickpocket(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        rank = get_street_rank(data["bread"], data["streetCred"])

        if random.random() < 0.55:
            fine = 400
            data["bread"] = max(0, data["bread"] - fine)
            schedule_save()
            await interaction.response.send_message(f"🕵️ **[{rank['name']}]** Caught! You lost **{fine}** bread in legal fees.")
        else:
            p = random.randint(300, 1100)
            data["bread"] += p
            schedule_save()
            await interaction.response.send_message(f"🕵️ **[{rank['name']}]** Snatched **{p}** bread! Slick move.")

    @app_commands.command(name="hijack")
    async def hustle_hijack(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        rank = get_street_rank(data["bread"], data["streetCred"])

        if random.random() < 0.8:
            fine = 2000
            data["bread"] = max(0, data["bread"] - fine)
            schedule_save()
            await interaction.response.send_message(f"🚓 **[{rank['name']}]** Busted hijacking! Lost **{fine}** bread in the chase.")
        else:
            p = random.randint(4000, 13000)
            data["bread"] += p
            schedule_save()
            await interaction.response.send_message(f"🏎️ **[{rank['name']}]** BIG SCORE! Sold the hijacked whip for **{p}** bread!")