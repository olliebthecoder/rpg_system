from character import Character
from enemy import generate_enemy, enemy_archetypes
import random
from player import choose_character

# picks player character
player = choose_character()
# loads in the charcter
player.load()
# generates the enemy
enemy = generate_enemy(player)
player.reset_health()

# Combat loop

if player.speed > enemy.speed:
    first = player
    second = enemy
elif enemy.speed > player.speed:
    first = enemy
    second = player
else:
    first = random.choice([player, enemy])
    second = player if first == enemy else enemy

action = input("Do you want to 1.attack, 2.defend, or 3.heal? ")

while player.alive() and enemy.alive():
    if action == "1":
        player.attack(second)
    elif action == "2":
        player.defend()
    elif action == "3":
        player.heal()

    if enemy.alive():
        enemy.attack(player)

    returned_action = input("Do you want to 1.attack, 2.defend, or 3.heal? ")
    if returned_action in ["1", "2", "3"]:
        action = returned_action

    if enemy.health == 0:
        print(f"player wins!!\n")
        player.gain_xp(50)
    else:
        print("enemy wins!!")

player.save()
