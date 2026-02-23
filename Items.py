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
        rarity="Common",
    ),
    "Steel Sword": Item(
        name="Steel Sword",
        item_type="weapon",
        bonuses={"attack": 10},
        price=200,
        description="A sharp steel blade. +10 attack.",
        rarity="Uncommon",
    ),
    "Legendary Blade": Item(
        name="Legendary Blade",
        item_type="weapon",
        bonuses={"attack": 20},
        price=500,
        description="A legendary weapon of immense power. +20 attack.",
        rarity="Legendary",
    ),
    "Flame Sword": Item(
        name="Flame Sword",
        item_type="weapon",
        bonuses={"attack": 15},
        price=400,
        description="A sword imbued with flames. +15 attack. 20% chance to burn enemy.",
        special={
            "type": "burn",
            "chance": 20,  # 20% chance
            "damage": 5,  # burn damage
        },
        rarity="Epic",
    ),
    "Shadow Dagger": Item(
        name="Shadow Dagger",
        item_type="weapon",
        bonuses={"attack": 8, "speed": 5},
        price=250,
        description="A lightweight dagger. +8 attack, +5 speed. 15% bonus crit chance.",
        special={"type": "crit_bonus", "value": 15},  # +15% crit chance
        rarity="Rare",
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
