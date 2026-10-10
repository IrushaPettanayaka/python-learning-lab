"""Dice rolling, simulation, and exact probability calculations."""

import random
from collections import Counter


def theoretical_distribution(number_of_dice: int, sides: int) -> dict[int, float]:
    counts = {0: 1}
    for _ in range(number_of_dice):
        next_counts = Counter()
        for current_total, ways in counts.items():
            for face in range(1, sides + 1):
                next_counts[current_total + face] += ways
        counts = dict(next_counts)
    outcomes = sides ** number_of_dice
    return {total: ways / outcomes for total, ways in sorted(counts.items())}


def roll_dice(number_of_dice: int, sides: int) -> dict:
    rolls = [random.randint(1, sides) for _ in range(number_of_dice)]
    return {"mode": "roll", "rolls": rolls, "total": sum(rolls)}


def simulate_dice(number_of_dice: int, sides: int, simulations: int) -> dict:
    frequencies = Counter(
        sum(random.randint(1, sides) for _ in range(number_of_dice))
        for _ in range(simulations)
    )
    theoretical = theoretical_distribution(number_of_dice, sides)
    rows = []
    for total, probability in theoretical.items():
        experimental = frequencies[total] / simulations
        rows.append({
            "total": total, "frequency": frequencies[total],
            "experimental": experimental, "theoretical": probability,
            "difference": experimental - probability,
        })
    mean = sum(row["total"] * row["frequency"] for row in rows) / simulations
    most_common = max(rows, key=lambda row: row["frequency"])["total"]
    max_frequency = max(row["frequency"] for row in rows) or 1
    for row in rows:
        row["bar"] = round(row["frequency"] / max_frequency * 100, 2)
    return {
        "mode": "simulation", "rows": rows, "mean": mean,
        "most_common": most_common, "simulations": simulations,
        "number_of_dice": number_of_dice, "sides": sides,
    }
