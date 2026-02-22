import random

from enemy import generate_enemy
from player import choose_character


def get_valid_action() -> str:
    """Prompt until the player enters a valid action."""
    while True:
        action = input("Do you want to 1.attack, 2.defend, or 3.use item? \n").strip()
        if action in {"1", "2", "3", "4"}:
            return action
        print("Invalid action. Enter 1, 2, or 3.")


def resolve_player_action(player, target, action: str) -> None:
    if action == "1":
        player.attack(target)
    elif action == "2":
        player.defend()
    elif action == "3":
        player.show_inventory()
        choice = input("Enter item name to use: ")
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
    print(f"Welcome to the shop! You have {player.gold} gold.")
    print("1) Health Potion (10 gold) - heals 25% when used")
    print("2) Defense Potion (15 gold) - +defend when used")
    print("3) View Inventory")
    print("4) Exit Shop")

    buy = input("> ")
    while buy != "4":
        if buy == "1":
            if player.gold >= 10:
                player.gold -= 10
                player.add_item("Health Potion", 1)
            else:
                print("Not enough gold!")
        elif buy == "2":
            if player.gold >= 15:
                player.gold -= 15
                player.add_item("Defense Potion", 1)
            else:
                print("Not enough gold!")
        elif buy == "3":
            player.show_inventory()
        elif buy == "4":
            print("Thanks for visiting the shop!")
            break
        else:
            print("Invalid choice!")
        buy = input("> ")


def main() -> None:
    player = choose_character()
    player.load()
    enemy = generate_enemy(player)
    player.reset_health()
    while player.alive():
        enemy = generate_enemy(player)
        run_battle(player, enemy)
        finish_battle(player, enemy)
        shop(player)
        player.save()


if __name__ == "__main__":
    main()
1
