"""State transitions and binary-search comparison for Number Guessing Lab."""

DIFFICULTIES = {
    "easy": {"label": "Easy", "attempts": 12},
    "medium": {"label": "Medium", "attempts": 8},
    "hard": {"label": "Hard", "attempts": 5},
}


def new_game(difficulty: str, secret: int) -> dict:
    return {
        "difficulty": difficulty, "secret": secret,
        "max_attempts": DIFFICULTIES[difficulty]["attempts"], "guesses": [],
        "low": 0, "high": 100, "finished": False, "won": False,
    }


def submit_guess(game: dict, guess: int) -> tuple[dict, str]:
    if game["finished"]:
        return game, "This round is already finished."
    if not game["low"] <= guess <= game["high"]:
        return game, f"Guess between {game['low']} and {game['high']}."
    game = {**game, "guesses": [*game["guesses"], guess]}
    if guess == game["secret"]:
        game.update(finished=True, won=True)
        return game, f"Correct — {guess} was the number."
    if guess < game["secret"]:
        game["low"] = guess + 1
        message = f"{guess} is too low."
    else:
        game["high"] = guess - 1
        message = f"{guess} is too high."
    if len(game["guesses"]) >= game["max_attempts"]:
        game["finished"] = True
        message = f"No attempts remain. The number was {game['secret']}."
    return game, message


def binary_search_steps(low: int, high: int, target: int) -> list[dict]:
    steps = []
    while low <= high:
        midpoint = (low + high) // 2
        steps.append({"low": low, "high": high, "guess": midpoint})
        if midpoint == target:
            break
        if midpoint < target:
            low = midpoint + 1
        else:
            high = midpoint - 1
    return steps
