import random

# Drop tables for each archetype
drops_table = {
    "Tank": [
        ("Iron Armor", 0.15),
        ("Health Potion", 0.3),
        ("Defense Potion", 0.2),
    ],
    "Assassin": [
        ("Shadow Dagger", 0.1),
        ("Elixir of Speed", 0.25),
        ("Health Potion", 0.2),
    ],
    "Bruiser": [
        ("Iron Sword", 0.15),
        ("Super Healing Potion", 0.15),
        ("Defense Potion", 0.2),
    ],
    "Glass Cannon": [
        ("Super Healing Potion", 0.2),
        ("Mega Healing Potion", 0.05),
        ("Iron Sword", 0.1),
    ],
}

boss_drops = [
    ("Legendary Blade", 0.08),
    ("Dragon Scale Armor", 0.08),
    ("Flame Sword", 0.12),
    ("Titan Armor", 0.05),
    ("Mega Healing Potion", 0.2),
]


def get_enemy_drops(archetype, is_boss):
    if is_boss:
        return boss_drops + drops_table.get(archetype, [])
    else:
        return drops_table.get(archetype, [])


def roll_drops(drops):
    """Given a list of (item, chance), return a list of dropped item names."""
    dropped = []
    for item, chance in drops:
        if random.random() < chance:
            dropped.append(item)
    return dropped
