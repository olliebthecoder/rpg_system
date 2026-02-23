import random

from enemy import generate_enemy
from player import choose_character
from item_Database import ITEM_DATABASE


def get_valid_action() -> str:
    """Prompt until the player enters a valid action."""
    while True:
        action = input(
            "Do you want to 1.attack, 2.defend, 3.use item, or 4.save and quit? \n"
        ).strip()
        if action in {"1", "2", "3", "4"}:
            return action
        print("Invalid action. Enter 1, 2, 3, or 4.")


def resolve_player_action(player, target, action: str) -> None:
    if action == "1":
        player.attack(target)
    elif action == "2":
        player.defend()
    elif action == "3":
        player.show_inventory()
        choice = input("Enter item name to use: ")
    elif action == "4":
        player.save()
        print("Game saved. Exiting...")
        exit()
        if choice:
            player.use_item(choice)


def choose_turn_order(player, enemy):
    if player.speed > enemy.speed:
        return player, enemy
    if enemy.speed > player.speed:
        return enemy, player
    first = random.choice([player, enemy])
    second = enemy if first == player else player
    return first, second


def run_battle(player, enemy) -> None:
    while player.alive() and enemy.alive():
        first, second = choose_turn_order(player, enemy)

        # First actor's turn
        if first == player:
            player.end_defend()
            action = get_valid_action()
            resolve_player_action(player, enemy, action)
        else:
            enemy.attack(player)

        if not player.alive() or not enemy.alive():
            break

        # Second actor's turn
        if second == player:
            player.end_defend()
            action = get_valid_action()
            resolve_player_action(player, enemy, action)
        else:
            enemy.attack(player)


def finish_battle(player, enemy) -> None:
    if enemy.health == 0:
        # Detect bosses by name (enemy names for bosses include 'BOSS')
        is_boss = "BOSS" in enemy.name.upper()

        if is_boss:
            xp_reward = 200
            gold_reward = 100
            print("🔥 Boss defeated! Massive rewards! 🔥")
        else:
            xp_reward = 50
            gold_reward = 20

        print("player wins!!\n")
        player.gain_xp(xp_reward)
        player.gain_gold(gold_reward)
    else:
        print("enemy wins!!")


def shop(player) -> None:
    while True:
        print(f"\nWelcome to the shop! You have {player.gold} gold.\n")

        items = list(ITEM_DATABASE.keys())

        # Display items dynamically
        for i, item in enumerate(items, start=1):
            price = ITEM_DATABASE[item]["price"]
            desc = ITEM_DATABASE[item]["description"]
            print(f"{i}) {item} ({price} gold) - {desc}")

        print(f"{len(items)+1}) View Inventory")
        print(f"{len(items)+2}) Exit Shop")

        choice = input("> ")

        # Exit
        if choice == str(len(items) + 2):
            print("Thanks for visiting the shop!")
            break

        # View Inventory
        if choice == str(len(items) + 1):
            player.show_inventory()
            continue

        # Buy Item
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(items):
                item_name = items[index]
                price = ITEM_DATABASE[item_name]["price"]

                if player.gold >= price:
                    player.gold -= price
                    player.add_item(item_name, 1)
                    print(f"Bought {item_name}! You have {player.gold} gold left.")
                else:
                    print("Not enough gold!")
            else:
                print("Invalid choice!")
        else:
            print("Invalid choice!")


def main() -> None:
    player = choose_character()
    player.load()
    enemy = generate_enemy(player)
    player.reset_health()
    while player.alive():
        player.reset_health()
        enemy = generate_enemy(player)
        run_battle(player, enemy)
        finish_battle(player, enemy)
        shop(player)
        player.save()


if __name__ == "__main__":
    main()
