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
    ):
        self.name = name
        self.type = item_type
        self.bonuses = bonuses if bonuses else {}  # For equipment
        self.price = price
        self.description = description
        self.effect = effect  # For consumables
        self.value = value  # Amount healed or defense buff

    def apply_effect(self, target):
        """Optional: define behavior for consumables here"""
        if self.effect == "heal":
            heal_amount = int(target.max_health * self.value)
            target.health = min(target.max_health, target.health + heal_amount)
            print(f"{target.name} healed for {heal_amount} HP!")
        elif self.effect == "defend":
            target.temp_defense_buff += self.value
            target.defense += self.value
            target.is_defending = True
            print(f"{target.name}'s defense increased by {self.value} for one turn.")


ITEM_DATABASE = {
    "Health Potion": Item(
        name="Health Potion",
        item_type="consumable",
        effect="heal",
        value=0.25,
        price=10,
        description="Heals 25% of your max health.",
    ),
    "Defense Potion": Item(
        name="Defense Potion",
        item_type="consumable",
        effect="defend",
        value=10,
        price=15,
        description="Increases your defense by 10 for one turn.",
    ),
    "Super Healing Potion": Item(
        name="Super Healing Potion",
        item_type="consumable",
        effect="heal",
        value=0.5,
        price=25,
        description="Heals 50% of your max health.",
    ),
    "Super Defense Potion": Item(
        name="Super Defense Potion",
        item_type="consumable",
        effect="defend",
        value=20,
        price=30,
        description="Increases your defense by 20 for one turn.",
    ),
    "Iron Sword": Item(
        name="Iron Sword",
        item_type="weapon",
        bonuses={"attack": 5},
        price=100,
        description="A sturdy iron sword. +5 attack.",
    ),
    "Steel Sword": Item(
        name="Steel Sword",
        item_type="weapon",
        bonuses={"attack": 10},
        price=200,
        description="A sharp steel blade. +10 attack.",
    ),
    "Legendary Blade": Item(
        name="Legendary Blade",
        item_type="weapon",
        bonuses={"attack": 20},
        price=500,
        description="A legendary weapon of immense power. +20 attack.",
    ),
    "Iron Armor": Item(
        name="Iron Armor",
        item_type="armor",
        bonuses={"defense": 8},
        price=150,
        description="Heavy iron plating for protection. +8 defense.",
    ),
    "Steel Armor": Item(
        name="Steel Armor",
        item_type="armor",
        bonuses={"defense": 15},
        price=300,
        description="Reinforced steel armor. +15 defense.",
    ),
    "Dragon Scale Armor": Item(
        name="Dragon Scale Armor",
        item_type="armor",
        bonuses={"defense": 25},
        price=600,
        description="Armor forged from dragon scales. +25 defense.",
    ),
}
