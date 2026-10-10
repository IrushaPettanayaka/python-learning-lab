import random

while True:
    choice = input("Roll the dice? (y/n): ").lower()
    if choice == "y":
        num_dice = int(input("How many dice would you like to roll? "))
        dice = [random.randint(1, 6) for _ in range(num_dice)]
        print(f"({', '.join(map(str, dice))})")
    elif choice == "n":
        print("Thanks for playing!")
        break
    else:
        print("Invalid choice!")
