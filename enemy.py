import random

from character import Character
from loot.drops import get_enemy_drops


enemy_archetypes = {
    "Tank": {
        "health": 150,
        "attack": 15,
        "speed": 10,
        "attack_speed": 15,
        "defense": 35,
        "crit_chance": 30,
    },
    "Assassin": {
        "health": 80,
        "attack": 20,
        "speed": 60,
        "attack_speed": 50,
        "defense": 10,
        "crit_chance": 60,
    },
    "Bruiser": {
        "health": 120,
        "attack": 15,
        "speed": 30,
        "attack_speed": 30,
        "defense": 20,
        "crit_chance": 20,
    },
    "Glass Cannon": {
        "health": 70,
        "attack": 25,
        "speed": 35,
        "attack_speed": 40,
        "defense": 5,
        "crit_chance": 15,
    },
}


def generate_enemy(player):
    archetype_name = random.choice(list(enemy_archetypes.keys()))
    base = enemy_archetypes[archetype_name]

    level = player.level

    # Scale stats exactly with player level
    health = base["health"] + (player.level * 25)
    attack = base["attack"] + (player.level * 3)
    speed = base["speed"] + (player.level * 3)
    attack_speed = base["attack_speed"] + (player.level * 3)
    defense = base["defense"] + (player.level * 2)
    crit_chance = base["crit_chance"]

    name = f"Level {level} {archetype_name}"

    # Boss every 5 levels
    is_boss = False
    if level % 5 == 0:
        name = f"🔥 BOSS {archetype_name}"
        health = int(health * 1.5)
        attack = int(attack * 1.5)
        is_boss = True

    enemy = Character(name, health, attack, speed, attack_speed, defense, crit_chance)

    # Attach drops to enemy for use in finish_battle
    enemy.drops = get_enemy_drops(archetype_name, is_boss)
    return enemy
