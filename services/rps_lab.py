"""Explainable Rock Paper Scissors rules and adaptive opponent."""

import random
from collections import Counter


CHOICES = {
    "rock": {"label": "Rock", "symbol": "●"},
    "paper": {"label": "Paper", "symbol": "▰"},
    "scissors": {"label": "Scissors", "symbol": "✕"},
}
COUNTER = {"rock": "paper", "paper": "scissors", "scissors": "rock"}


def determine_winner(player: str, opponent: str) -> str:
    if player == opponent:
        return "draw"
    return "win" if COUNTER[opponent] == player else "loss"


def predict_next_choice(history: list[str]) -> str | None:
    if not history:
        return None
    if len(history) >= 2:
        latest = history[-1]
        following = [history[index + 1] for index in range(len(history) - 1)
                     if history[index] == latest]
        if following:
            return Counter(following).most_common(1)[0][0]
    return Counter(history).most_common(1)[0][0]


def choose_opponent_move(mode: str, history: list[str], chooser=random.choice):
    if mode == "adaptive":
        prediction = predict_next_choice(history)
        if prediction:
            return COUNTER[prediction], prediction
    return chooser(list(CHOICES)), None
