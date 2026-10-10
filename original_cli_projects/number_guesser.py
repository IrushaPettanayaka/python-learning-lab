# Guess the number game
import random

num_of_guesses = 0
secret_number = random.randint(0, 100)
print("Welcome to the number guessing game!")

while True:
    difficulty = input("Choose a difficulty level (easy, medium, hard): ").lower()
    if difficulty == "easy":
        max_guesses = 12
        break
    elif difficulty == "medium":
        max_guesses = 8
        break
    elif difficulty == "hard":
        max_guesses = 5
        break
    else:
        print("Invalid difficulty level. Please choose easy, medium, or hard.")

print(f"You have {max_guesses} guesses.")
while True:
    try:
        guess = int(input("Guess a number between 0 and 100: "))
    except ValueError:
        print("Please enter a valid number.")
        continue
    if guess < 0 or guess > 100:
        print("Please enter a number between 0 and 100.")
        continue
    num_of_guesses += 1
    difference = abs(secret_number - guess)
    if guess == secret_number:
        print(f"Congratulations! You've guessed the number {secret_number} in {num_of_guesses} attempts.")
        break
    if num_of_guesses >= max_guesses:
        print(f"You've reached the maximum number of guesses. The secret number was {secret_number}.")
        break
    if difference <= 10:
        print(f"{guess} is very close! Try again.")
    elif difference <= 20:
        print(f"{guess} is close! Try again.")
    elif guess < secret_number:
        print(f"{guess} is too low! Try again.")
    else:
        print(f"{guess} is too high! Try again.")
    print(f"Guesses remaining: {max_guesses - num_of_guesses}")
