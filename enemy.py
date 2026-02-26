import random

from character import Character
from Items import ITEM_DATABASE
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


def _choose_enemy_armor(level: int, is_boss: bool):
    """Return an armor key or None based on enemy level."""
    spawn_chance = min(0.2 + (level * 0.03), 0.8)
    if is_boss:
        spawn_chance = min(spawn_chance + 0.2, 0.95)

    if random.random() > spawn_chance:
        return None

    if level < 4:
        choices = ["Iron Armor"]
    elif level < 8:
        choices = ["Iron Armor", "Steel Armor", "Mage Robes"]
    elif level < 12:
        choices = ["Steel Armor", "Mage Robes", "Dragon Scale Armor"]
    else:
        choices = ["Steel Armor", "Mage Robes", "Dragon Scale Armor", "Titan Armor"]

    valid = [
        key
        for key in choices
        if key in ITEM_DATABASE and ITEM_DATABASE[key].type == "armor"
    ]
    if not valid:
        return None
    return random.choice(valid)


def _choose_enemy_weapon(level: int, is_boss: bool):
    """Return a weapon key or None based on enemy level."""
    spawn_chance = min(0.25 + (level * 0.035), 0.85)
    if is_boss:
        spawn_chance = min(spawn_chance + 0.1, 0.95)

    if random.random() > spawn_chance:
        return None

    if level < 4:
        choices = ["Iron Sword", "Steel Sword", "Shadow Dagger"]
    elif level < 8:
        choices = [
            "Steel Sword",
            "Shadow Dagger",
            "Draining Axe",
            "Weakening Rapier",
            "Lightning Hammer",
        ]
    elif level < 12:
        choices = [
            "Flame Sword",
            "Ice sword",
            "Lightning Hammer",
            "Titan Hammer",
            "Weakening Rapier",
            "Draining Axe",
        ]
    else:
        choices = [
            "Legendary sword",
            "Flame Sword",
            "Ice sword",
            "Lightning Hammer",
            "Titan Hammer",
            "Weakening Rapier",
            "Draining Axe",
        ]

    valid = [
        key
        for key in choices
        if key in ITEM_DATABASE and ITEM_DATABASE[key].type == "weapon"
    ]
    if not valid:
        return None
    return random.choice(valid)


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

    # Randomly equip gear based on level (higher levels = better/more likely gear).
    weapon_key = _choose_enemy_weapon(level, is_boss)
    armor_key = _choose_enemy_armor(level, is_boss)
    if weapon_key:
        enemy.equipped_weapon = weapon_key
    if armor_key:
        enemy.equipped_armor = armor_key

    # Recalculate once after setting equipment.
    if weapon_key or armor_key:
        enemy._recalc_equipped_bonuses()

    # Attach drops to enemy for use in finish_battle
    enemy.drops = get_enemy_drops(archetype_name, is_boss)
    return enemy
