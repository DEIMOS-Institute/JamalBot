import discord
from discord import app_commands
import time
import random
from typing import Optional
from ..data import get_player_data, schedule_save
from ..utils import create_deck, hand_total, hand_to_string, create_ttt_board
from ..views import TTTView, BlackjackView, BetView

tic_tac_toe_games = {}
blackjack_games = {}

class GamesCommands:
    def __init__(self):
        pass

    @app_commands.command(name="tictactoe")
    @app_commands.describe(opponent="Play against a friend (or leave empty for bot)", bet="Bet amount")
    async def tictactoe(self, interaction: discord.Interaction, opponent: Optional[discord.Member] = None, bet: Optional[int] = None):
        player1_data = get_player_data(interaction.user.id)

        if opponent:
            if opponent.id == interaction.user.id:
                await interaction.response.send_message("You can't play against yourself!", ephemeral=True)
                return
            player2_data = get_player_data(opponent.id)
            if bet:
                if bet < 10:
                    await interaction.response.send_message("Minimum bet 10 bread.", ephemeral=True)
                    return
                if player1_data["bread"] < bet or player2_data["bread"] < bet:
                    await interaction.response.send_message("Someone doesn't have enough bread.", ephemeral=True)
                    return
        else:
            opponent = interaction.client.user
            if bet:
                if bet < 10:
                    await interaction.response.send_message("Minimum bet 10 bread.", ephemeral=True)
                    return
                if player1_data["bread"] < bet:
                    await interaction.response.send_message("You don't have enough bread.", ephemeral=True)
                    return

        game_id = f"{interaction.user.id}-{opponent.id}-{int(time.time()*1000)}"
        game = {
            "player1": interaction.user.id,
            "player2": opponent.id,
            "is_bot": opponent.bot,
            "board": create_ttt_board(),
            "turn": interaction.user.id,
            "bet": bet
        }
        tic_tac_toe_games[game_id] = game

        embed = discord.Embed(
            title="🎮 Tic-Tac-Toe",
            description=f"<@{interaction.user.id}> (X) vs {'Bot' if opponent.bot else f'<@{opponent.id}>'} (O)\n\nCurrent turn: <@{interaction.user.id}>",
            color=0x00ff00
        )
        view = TTTView(game_id, game)
        await interaction.response.send_message(embeds=[embed], view=view)

    @app_commands.command(name="rps")
    @app_commands.describe(choice="Rock, Paper, or Scissors", bet="Amount to bet")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock 🪨", value="rock"),
        app_commands.Choice(name="Paper 📄", value="paper"),
        app_commands.Choice(name="Scissors ✂️", value="scissors")
    ])
    async def rps(self, interaction: discord.Interaction, choice: str, bet: int = 0):
        data = get_player_data(interaction.user.id)
        if bet > 0 and data["bread"] < bet:
            await interaction.response.send_message("Not enough bread.", ephemeral=True)
            return

        bot_choice = random.choice(["rock", "paper", "scissors"])
        result = None
        if choice == bot_choice:
            result = "tie"
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "win"
        else:
            result = "lose"

        msg = f"You chose **{choice}**, Jamal chose **{bot_choice}**.\n"
        if result == "tie":
            msg += "It's a tie!"
        elif result == "win":
            winnings = bet * 2 if bet > 0 else 0
            data["bread"] += winnings
            msg += f"You win! +{winnings} bread!"
        else:
            data["bread"] -= bet
            msg += f"You lose! -{bet} bread!"
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="roll")
    @app_commands.describe(sides="Number of sides (default 6)")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        result = random.randint(1, max(2, sides))
        await interaction.response.send_message(f"🎲 You rolled a **{result}**!")

    @app_commands.command(name="roulette")
    @app_commands.describe(bet="Amount to bet", color="Red or Black")
    @app_commands.choices(color=[
        app_commands.Choice(name="Red 🔴", value="red"),
        app_commands.Choice(name="Black ⚫", value="black")
    ])
    async def roulette(self, interaction: discord.Interaction, bet: int, color: str):
        data = get_player_data(interaction.user.id)
        if bet < 10:
            return await interaction.response.send_message("Minimum bet 10 bread.", ephemeral=True)
        if data["bread"] < bet:
            return await interaction.response.send_message("Not enough bread.", ephemeral=True)

        result = random.choices(["red", "black", "green"], weights=[18/38, 18/38, 2/38])[0]
        if result == color:
            winnings = bet * 2
            data["bread"] += winnings
            msg = f"🟢 **{result.upper()}!** You win {winnings} bread!"
        elif result == "green":
            data["bread"] -= bet
            msg = f"💚 **GREEN 0/00!** House wins, you lose {bet} bread."
        else:
            data["bread"] -= bet
            msg = f"🔴 Lost! It was {result}. You lose {bet} bread."
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="blackjack")
    @app_commands.describe(bet="Bet amount", opponent="Opponent (leave empty to play against dealer)")
    async def blackjack(self, interaction: discord.Interaction, bet: int, opponent: Optional[discord.Member] = None):
        player_data = get_player_data(interaction.user.id)
        if bet < 10:
            await interaction.response.send_message("Minimum bet is 10 bread.", ephemeral=True)
            return
        if player_data["bread"] < bet:
            await interaction.response.send_message(f"You don't have enough bread! You have {player_data['bread']}, need {bet}.", ephemeral=True)
            return

        if opponent is None:
            deck = create_deck()
            player_hand = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]
            game_id = f"{interaction.user.id}-{int(time.time()*1000)}"
            game = {
                "id": game_id,
                "player1": interaction.user,
                "player1Data": player_data,
                "opponent": 'dealer',
                "bet": bet,
                "deck": deck,
                "playerHand": player_hand,
                "dealerHand": dealer_hand,
                "status": 'active'
            }
            blackjack_games[game_id] = game
            player_total = hand_total(player_hand)
            embed = discord.Embed(
                title="♠️ Blackjack vs Dealer",
                description=f"Your hand: {hand_to_string(player_hand)} ({player_total})\nDealer shows: {hand_to_string([dealer_hand[0]])}",
                color=0x00ff00
            )
            view = BlackjackView(game_id, game)
            await interaction.response.send_message(embeds=[embed], view=view)
        else:
            if opponent.id == interaction.user.id:
                await interaction.response.send_message("You can't play against yourself!", ephemeral=True)
                return
            opponent_data = get_player_data(opponent.id)
            if opponent_data["bread"] < bet:
                await interaction.response.send_message(f"<@{opponent.id}> doesn't have enough bread!", ephemeral=True)
                return

            game_id = f"{interaction.user.id}-{opponent.id}-{int(time.time()*1000)}"
            deck = create_deck()
            player1_hand = [deck.pop(), deck.pop()]
            player2_hand = [deck.pop(), deck.pop()]
            game = {
                "id": game_id,
                "player1": interaction.user,
                "player1Data": player_data,
                "player2": opponent,
                "player2Data": opponent_data,
                "opponent": 'player',
                "bet": bet,
                "deck": deck,
                "player1Hand": player1_hand,
                "player2Hand": player2_hand,
                "currentPlayer": interaction.user.id,
                "status": 'active'
            }
            blackjack_games[game_id] = game
            total = hand_total(player1_hand)
            embed = discord.Embed(
                title="♠️ Blackjack – Player vs Player",
                description=f"<@{interaction.user.id}>'s turn\nYour hand: {hand_to_string(player1_hand)} ({total})",
                color=0x00ff00
            )
            view = BlackjackView(game_id, game)
            await interaction.response.send_message(embeds=[embed], view=view)

    @app_commands.command(name="coinflip")
    @app_commands.describe(bet="Amount to bet", choice="Heads or Tails")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: str):
        data = get_player_data(interaction.user.id)
        if bet < 10:
            await interaction.response.send_message("Minimum bet 10 bread.", ephemeral=True)
            return
        if data["bread"] < bet:
            await interaction.response.send_message("Not enough bread.", ephemeral=True)
            return

        result = random.choice(["heads", "tails"])
        if choice == result:
            data["bread"] += bet
            msg = f"🪙 It's **{result}**! You win {bet} bread!"
        else:
            data["bread"] -= bet
            msg = f"🪙 It's **{result}**! You lose {bet} bread."
        schedule_save()
        await interaction.response.send_message(msg)

    @app_commands.command(name="wyr")
    async def wyr(self, interaction: discord.Interaction):
        options = [
            ("Have unlimited bread but no friends", "Have many friends but be broke"),
            ("Fight 100 duck-sized horses", "Fight 1 horse-sized duck"),
            ("Always speak in rhymes", "Never be able to lie"),
        ]
        a, b = random.choice(options)
        await interaction.response.send_message(f"🤔 **Would You Rather:**\n🅰️ {a}\n**OR**\n🅱️ {b}")

    @app_commands.command(name="iq")
    async def iq(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        iq = random.randint(60, 140)
        await interaction.response.send_message(f"🧠 {target.display_name}'s IQ is **{iq}**.")

    @app_commands.command(name="howgay")
    async def howgay(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        percent = random.randint(0, 100)
        await interaction.response.send_message(f"🏳️‍🌈 {target.display_name} is **{percent}%** gay.")

    @app_commands.command(name="pp")
    async def pp(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        length = random.randint(1, 20)
        bar = "=" * length
        await interaction.response.send_message(f"🍆 {target.display_name}'s PP: 8{bar}D ({length} inches)")

    @app_commands.command(name="bitches")
    async def bitches(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target = user or interaction.user
        data = get_player_data(target.id)
        if user:
            count = random.randint(0, 20)
            await interaction.response.send_message(f"👯 {target.display_name} has pulled **{count}** bitches.")
        else:
            data["bitches"] = data.get("bitches", 0) + random.randint(0, 2)
            schedule_save()
            await interaction.response.send_message(f"👯 You've pulled **{data['bitches']}** bitches total!")

    @app_commands.command(name="horse")
    @app_commands.describe(bet="Amount to bet", horse="Horse number 1-6")
    async def horse(self, interaction: discord.Interaction, bet: int, horse: int):
        if horse < 1 or horse > 6:
            return await interaction.response.send_message("Choose horse 1-6.", ephemeral=True)
        data = get_player_data(interaction.user.id)
        if data["bread"] < bet:
            return await interaction.response.send_message("Not enough bread.", ephemeral=True)
        winner = random.randint(1, 6)
        if winner == horse:
            winnings = bet * 5
            data["bread"] += winnings
            await interaction.response.send_message(f"🏇 Horse {horse} wins! You earned {winnings} bread!")
        else:
            data["bread"] -= bet
            await interaction.response.send_message(f"🏇 Horse {winner} won. You lost {bet} bread.")
        schedule_save()

    @app_commands.command(name="bet")
    @app_commands.describe(user="Opponent", amount="Bet amount")
    async def bet_command(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        challenger_data = get_player_data(interaction.user.id)
        target_data = get_player_data(user.id)

        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't bet against yourself!", ephemeral=True)
            return
        if challenger_data["bread"] < amount:
            await interaction.response.send_message("You don't have enough bread!", ephemeral=True)
            return
        if target_data["bread"] < amount:
            await interaction.response.send_message("They don't have enough bread!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🤝 BET CHALLENGE",
            description=f"<@{interaction.user.id}> challenged <@{user.id}> to a coin flip for **{amount}** bread!\n\n<@{user.id}>, accept or decline below.",
            color=0x00ffff
        )
        view = BetView(interaction.user.id, user.id, amount)
        await interaction.response.send_message(embeds=[embed], view=view)