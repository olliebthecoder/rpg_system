import random

from enemy import generate_enemy
from player import choose_character


def get_valid_action() -> str:
    """Prompt until the player enters a valid action."""
    while True:
        action = input("Do you want to 1.attack, 2.defend, or 3.heal? ").strip()
        if action in {"1", "2", "3"}:
            return action
        print("Invalid action. Enter 1, 2, or 3.")


def resolve_player_action(player, target, action: str) -> None:
    if action == "1":
        player.attack(target)
    elif action == "2":
        player.defend()
    elif action == "3":
        player.heal()


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
        print("player wins!!\n")
        player.gain_xp(50)
        player.gain_gold(20)
    else:
        print("enemy wins!!")


def shop(player) -> None:
    print(f"Welcome to the shop! You have {player.gold} gold.")
    print("1) Health Potion (10 gold) - Heals 25% of your max health")
    print("2) Defense Potion (15 gold) - Increases defense by 10 for one turn")
    print("3) Exit Shop")

    buy = input("> ")
    while buy != "3":
        if buy == "1":
            if player.gold >= 10:
                player.gold -= 10
                player.heal()
            else:
                print("Not enough gold!")
        elif buy == "2":
            if player.gold >= 15:
                player.gold -= 15
                player.defend()
            else:
                print("Not enough gold!")
        elif buy == "3":
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

    run_battle(player, enemy)
    finish_battle(player, enemy)
    shop(player)
    player.save()


if __name__ == "__main__":
    main()
