import random
from typing import List, Optional

def create_deck() -> List[dict]:
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [{"rank": r, "suit": s} for s in suits for r in ranks]
    random.shuffle(deck)
    return deck

def card_value(card: dict) -> int:
    if card['rank'] in 'JQK':
        return 10
    if card['rank'] == 'A':
        return 11
    return int(card['rank'])

def hand_total(hand: List[dict]) -> int:
    total = 0
    aces = 0
    for card in hand:
        if card['rank'] == 'A':
            aces += 1
        total += card_value(card)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

def hand_to_string(hand: List[dict]) -> str:
    return ' '.join(f"{c['rank']}{c['suit']}" for c in hand)

def create_ttt_board() -> List[str]:
    return [' '] * 9

def check_ttt_winner(board: List[str]) -> Optional[str]:
    win_patterns = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in win_patterns:
        if board[a] != ' ' and board[a] == board[b] == board[c]:
            return board[a]
    if all(cell != ' ' for cell in board):
        return 'tie'
    return None