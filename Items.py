class Item:
    def __init__(
        self,
        name,
        item_type,
        bonuses=None,
        price=0,
        description="",
        effect=None,
        value=0,
        special=None,
        rarity="Common",
    ):
        self.name = name
        self.type = item_type
        self.bonuses = bonuses if bonuses else {}  # For equipment
        self.price = price
        self.description = description
        self.effect = effect  # For consumables
        self.value = value  # Amount healed or defense buff
        self.special = special  # For unique item effects
        self.rarity = rarity

    def colored_name(self):
        reset = "\033[0m"
        colors = {
            "Common": "\033[37m",
            "Uncommon": "\033[32m",
            "Rare": "\033[34m",
            "Epic": "\033[35m",
            "Legendary": "\033[33m",
            "Mythic": "\033[31m",
        }
        color = colors.get(self.rarity, "\033[37m")
        return f"{color}{self.name}{reset}"

    def rarity_initial(self):
        mapping = {
            "Common": "C",
            "Uncommon": "U",
            "Rare": "R",
            "Epic": "E",
            "Legendary": "L",
            "Mythic": "M",
        }
        return mapping.get(self.rarity, (self.rarity[0] if self.rarity else "?"))

    def apply_effect(self, target):
        if self.effect == "heal":
            heal_amount = int(target.max_health * self.value)
            target.health = min(target.max_health, target.health + heal_amount)
            print(f"{target.name} healed for {heal_amount} HP!")
        elif self.effect == "defend":
            target.temp_defense_buff += self.value
            target.defense += self.value
            target.is_defending = True
            print(f"{target.name}'s defense increased by {self.value} for one turn.")
        elif self.effect == "speed":
            target.speed += self.value
            print(f"{target.name}'s speed increased by {self.value} for one turn!")
        elif self.effect == "heal_defend":
            heal_amount = int(target.max_health * self.value["heal"])
            target.health = min(target.max_health, target.health + heal_amount)
            target.temp_defense_buff += self.value["defend"]
            target.defense += self.value["defend"]
            target.is_defending = True
            print(
                f"{target.name} healed for {heal_amount} HP and defense increased by {self.value['defend']} for one turn."
            )


ITEM_DATABASE = {
    # ---- CONSUMABLES ----
    "Health Potion": Item(
        name="Health Potion",
        item_type="consumable",
        effect="heal",
        value=0.25,
        price=10,
        description="Heals 25% of your max health.",
        rarity="Common",
    ),
    "Defense Potion": Item(
        name="Defense Potion",
        item_type="consumable",
        effect="defend",
        value=10,
        price=15,
        description="Increases your defense by 10 for one turn.",
        rarity="Common",
    ),
    "Super Healing Potion": Item(
        name="Super Healing Potion",
        item_type="consumable",
        effect="heal",
        value=0.5,
        price=25,
        description="Heals 50% of your max health.",
        rarity="Rare",
    ),
    "Super Defense Potion": Item(
        name="Super Defense Potion",
        item_type="consumable",
        effect="defend",
        value=20,
        price=30,
        description="Increases your defense by 20 for one turn.",
        rarity="Rare",
    ),
    "Elixir of Speed": Item(
        name="Elixir of Speed",
        item_type="consumable",
        effect="speed",
        value=5,
        price=40,
        description="Increases your speed by 5 for one turn.",
        rarity="Uncommon",
    ),
    "Mega Healing Potion": Item(
        name="Mega Healing Potion",
        item_type="consumable",
        effect="heal",
        value=0.75,
        price=75,
        description="Heals 75% of your max health.",
        rarity="Epic",
    ),
    "Rejuvenation Potion": Item(
        name="Rejuvenation Potion",
        item_type="consumable",
        effect="heal_defend",
        value={"heal": 0.5, "defend": 10},
        price=50,
        description="Heals 50% HP and increases defense by 10 for one turn.",
        rarity="Rare",
    ),
    # ---- WEAPONS ----
    "Iron Sword": Item(
        name="Iron Sword",
        item_type="weapon",
        bonuses={"attack": 5},
        price=100,
        description="A sturdy iron sword. +5 attack.",
        special={"crit_chance": 10, "crit_multiplier": 1.5},
        rarity="Common",
    ),
    "Steel Sword": Item(
        name="Steel Sword",
        item_type="weapon",
        bonuses={"attack": 10},
        price=200,
        description="A sharp steel blade. +10 attack.",
        special={"crit_chance": 10, "crit_multiplier": 1.5},
        rarity="Uncommon",
    ),
    "Legendary sword": Item(
        name="Legendary sword",
        item_type="weapon",
        bonuses={"attack": 20},
        price=500,
        description="A legendary weapon of immense power. +20 attack.",
        special={"crit_chance": 10, "crit_multiplier": 1.5},
        rarity="Legendary",
    ),
    "Flame Sword": Item(
        name="Flame Sword",
        item_type="weapon",
        bonuses={"attack": 15},
        price=700,
        description="A sword imbued with flames. +15 attack. 20% chance to burn enemy.",
        special={
            "type": "burn",
            "chance": 100,  # 100% chance
            "damage": 5,  # burn damage
            "duration": 3,  # burn duration in turns
            "crit_chance": 10,
            "crit_multiplier": 1.5,
        },
        rarity="Mythic",
    ),
    "Shadow Dagger": Item(
        name="Shadow Dagger",
        item_type="weapon",
        bonuses={"attack": 8, "speed": 5},
        price=650,
        description="A lightweight dagger. +8 attack, +5 speed. poison.",
        special={
            "type": "poison",
            "chance": 100,
            "damage": 3,
            "duration": 5,  # poison duration in turns
            "crit_chance": 20,
            "crit_multiplier": 2.0,
        },
        rarity="Mythic",
    ),
    "Ice Sword": Item(
        name="Ice Sword",
        item_type="weapon",
        bonuses={"attack": 12},
        price=800,
        description="A sword imbued with ice. +12 attack, slows down opponent .",
        special={
            "type": "freeze",
            "chance": 100,
            "damage": 4,
            "duration": 2,  # freeze duration in turns
            "crit_chance": 10,
            "crit_multiplier": 1.5,
        },
        rarity="Mythic",
    ),
    "Lightning Hammer": Item(
        name="Lightning Hammer",
        item_type="weapon",
        bonuses={"attack": 18, "speed": 5},
        price=900,
        description="A hammer imbued with lightning. +18 attack, +5 speed.",
        special={
            "type": "lightning",
            "chance": 100,
            "damage": 0,
            "duration": 2,  # lightning duration in turns
            "crit_chance": 5,
            "crit_multiplier": 2.5,
        },
        rarity="Mythic",
    ),
    "Titan Hammer": Item(
        name="Titan Hammer",
        item_type="weapon",
        bonuses={"attack": 25, "speed": -5},
        price=1200,
        description="A massive hammer, unmatched in power. +25 attack, -5 speed.",
        special={
            "type": "Armor Break",
            "chance": 100,
            "damage": 0,
            "duration": 2,  # Armor Break duration in turns
            "crit_chance": 5,
            "crit_multiplier": 2.5,
        },
        rarity="Mythic",
    ),
    "Draining Axe": Item(
        name="Draining Axe",
        item_type="weapon",
        bonuses={"attack": 12, "Bleed": 5},
        price=750,
        description="An axe that drains health from enemies. +12 attack, deals 20% of damage as bleed.",
        special={
            "type": "Bleed",
            "chance": 100,
            "damage": lambda final_damage: int(
                final_damage * 0.2
            ),  # Bleed damage is 20% of final damage
            "duration": 2,  # Bleed duration in turns
            "crit_chance": 10,
            "crit_multiplier": 1.5,
        },
        rarity="Mythic",
    ),
    "Weakening Rapier": Item(
        name="Weakening Rapier",
        item_type="weapon",
        bonuses={"attack": 10, "speed": 10},
        price=850,
        description="A rapier that weakens enemies. +10 attack, +10 speed, reduces enemy attack and defense by 20% for the rest of the battle.",
        special={
            "type": "Weaken",
            "chance": 100,
            "attack_pct": 0.2,
            "defense_pct": 0.2,
            "duration": -1,  # Weaken is permanent until removed
            "crit_chance": 15,
            "crit_multiplier": 1.8,
        },
        rarity="Mythic",
    ),
    "test_sword": Item(
        name="Test Sword",
        item_type="weapon",
        bonuses={"attack": 5},
        price=0,
        description="A sword for testing. +5 attack.",
        special={"crit_chance": 10, "crit_multiplier": 1.5},
        rarity="Common",
    ),
    "test_axe": Item(
        name="Test Axe",
        item_type="weapon",
        bonuses={"attack": 6, "speed": -4, "attack_speed": -4},
        price=0,
        description="An axe for testing. +6 attack.",
        special={"crit_chance": 10, "crit_multiplier": 1.5},
        rarity="Common",
    ),
    "test_rapier": Item(
        name="Test Rapier",
        item_type="weapon",
        bonuses={"attack": 4, "speed": 6, "attack_speed": 6},
        price=0,
        description="A rapier for testing. +4 attack, +5 speed.",
        special={"crit_chance": 15, "crit_multiplier": 1.8},
        rarity="Common",
    ),
    "test_hammer": Item(
        name="Test Hammer",
        item_type="weapon",
        bonuses={"attack": 7, "speed": -6, "attack_speed": -6},
        price=0,
        description="A hammer for testing. +7 attack.",
        special={"crit_chance": 5, "crit_multiplier": 2.5},
        rarity="Common",
    ),
    "test_dagger": Item(
        name="Test Dagger",
        item_type="weapon",
        bonuses={"attack": 3, "speed": 10, "attack_speed": 10},
        price=0,
        description="A dagger for testing. +3 attack.",
        special={
            "type": "poison",
            "chance": 60,
            "damage": 5,
            "duration": 2,  # Poison duration in turns
            "crit_chance": 20,
            "crit_multiplier": 2.0,
        },
        rarity="Common",
    ),
    # ---- ARMOR ----
    "Iron Armor": Item(
        name="Iron Armor",
        item_type="armor",
        bonuses={"defense": 8},
        price=150,
        description="Heavy iron plating for protection. +8 defense.",
        rarity="Common",
    ),
    "Steel Armor": Item(
        name="Steel Armor",
        item_type="armor",
        bonuses={"defense": 15},
        price=300,
        description="Reinforced steel armor. +15 defense.",
        rarity="Uncommon",
    ),
    "Dragon Scale Armor": Item(
        name="Dragon Scale Armor",
        item_type="armor",
        bonuses={"defense": 25},
        price=600,
        description="Armor forged from dragon scales. +25 defense.",
        rarity="Legendary",
    ),
    "Mage Robes": Item(
        name="Mage Robes",
        item_type="armor",
        bonuses={"defense": 10, "speed": 5},
        price=200,
        description="Light robes that protect and allow agility. +10 defense, +5 speed.",
        rarity="Rare",
    ),
    "Titan Armor": Item(
        name="Titan Armor",
        item_type="armor",
        bonuses={"defense": 40, "speed": -5},
        price=800,
        description="Extremely heavy armor, unmatched protection. +40 defense, -5 speed.",
        rarity="Mythic",
    ),
}
