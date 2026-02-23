import random
import json
import os
from Items import ITEM_DATABASE

# Directory where character save files are stored
SAVE_DIR = "player files"


class Character:
    def __init__(
        self,
        name,
        health,
        attack_power,
        speed,
        attack_speed,
        defense,
        crit_chance,
    ):
        self.name = name
        self.health = health
        self.max_health = health
        self.attack_power = attack_power
        self.speed = speed
        self.attack_speed = attack_speed
        self.defense = defense
        self.crit_chance = crit_chance

        self.is_defending = False
        # temporary defense buff applied by defend or items; removed by end_defend()
        self.temp_defense_buff = 0

        # Leveling stats
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100

        self.gold = 0
        # inventory: map item name -> quantity
        self.inventory = {}
        # equipped items: weapon and armor
        self.equipped_weapon = None
        self.equipped_armor = None
        # base stat bonuses from equipped items
        self.equipped_attack_bonus = 0
        self.equipped_defense_bonus = 0

    def save(self):
        data = {
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "max_health": self.max_health,
            "health": self.health,
            "attack_power": self.attack_power,
            "speed": self.speed,
            "attack_speed": self.attack_speed,
            "defense": self.defense,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipped_weapon": self.equipped_weapon,
            "equipped_armor": self.equipped_armor,
        }

        os.makedirs(SAVE_DIR, exist_ok=True)
        path = os.path.join(SAVE_DIR, f"{self.name}_save.json")
        with open(path, "w") as file:
            json.dump(data, file)

        print(f"💾 {self.name} has been saved to {path}!")

    def level_up(self):
        self.xp -= self.xp_to_next
        self.level += 1
        self.xp_to_next = int(self.xp_to_next * 1.5)

    def gain_gold(self, amount):
        self.gold += amount
        print(f"{self.name} gained {amount} gold! (Total Gold: {self.gold})")

    def gain_xp(self, amount):
        self.xp += amount
        print(f"{self.name} gained {amount} XP!\n")

        while self.xp >= self.xp_to_next:
            self.level_up()
            print(f"\n🔥 {self.name} LEVELLED UP to Level {self.level}! 🔥")
            # Increase stats
            self.max_health += 20
            self.health = self.max_health
            self.attack_power += 5
            self.speed += 3
            self.attack_speed += 3
            self.defense += 1

            print(f"Stats increased!")
            print(f"HP: {self.max_health}")
            print(f"ATK: {self.attack_power}")
            print(f"SPD: {self.speed}")
            print(f"ATK SPD: {self.attack_speed}")
            print(f"DEF: {self.defense}\n")

    def alive(self):
        return self.health > 0

    def reset_health(self):
        self.health = self.max_health

    def load(self):
        try:
            # prefer save inside SAVE_DIR, fall back to current directory
            path = os.path.join(SAVE_DIR, f"{self.name}_save.json")
            if not os.path.exists(path):
                path = f"{self.name}_save.json"

            with open(path, "r") as file:
                data = json.load(file)

            self.level = data.get("level", self.level)
            self.xp = data.get("xp", self.xp)
            self.xp_to_next = data.get("xp_to_next", self.xp_to_next)
            self.max_health = data.get("max_health", self.max_health)
            self.health = data.get("health", self.health)
            self.attack_power = data.get("attack_power", self.attack_power)
            self.speed = data.get("speed", self.speed)
            self.attack_speed = data.get("attack_speed", self.attack_speed)
            self.defense = data.get("defense", self.defense)
            self.gold = data.get("gold", self.gold)
            self.inventory = data.get("inventory", self.inventory)
            self.equipped_weapon = data.get("equipped_weapon", self.equipped_weapon)
            self.equipped_armor = data.get("equipped_armor", self.equipped_armor)
            self.crit_chance = data.get("crit_chance", self.crit_chance)

            # reapply equipment bonuses when loading
            self._recalc_equipped_bonuses()

            print(f"📂 {self.name} has been loaded!")

        except FileNotFoundError:
            print("No save file found.")

    def heal(self):
        heal = self.max_health * 0.25
        self.health += heal
        if self.health > self.max_health:
            self.health = self.max_health
        print(f"{self.name} healed for {heal} HP! (HP: {self.health})")

    def add_item(self, item_name: str, qty: int = 1):
        key = item_name.title()
        self.inventory[key] = self.inventory.get(key, 0) + qty
        print(f"{self.name} received {qty} x {key} (Total: {self.inventory[key]})")

    def remove_item(self, item_name: str, qty: int = 1) -> bool:
        key = item_name.title()
        count = self.inventory.get(key, 0)
        if count < qty:
            return False
        if count == qty:
            del self.inventory[key]
        else:
            self.inventory[key] = count - qty
        return True

    def use_item(self, item_name: str) -> None:
        name = item_name.strip()
        inventory_key = name.title()

        if self.inventory.get(inventory_key, 0) <= 0:
            print(f"No {inventory_key} in inventory.")
            return

        # Try tolerant lookups in ITEM_DATABASE: Title Case, lowercase, underscore form
        candidates = [inventory_key, name, name.lower(), name.lower().replace(" ", "_")]
        item_data = None
        for cand in candidates:
            if cand in ITEM_DATABASE:
                item_data = ITEM_DATABASE[cand]
                break

        if not item_data:
            print(f"{inventory_key} does nothing.")
            return

        # item_data is now an Item object with .type, .effect, .value attributes
        if item_data.type == "consumable":
            # remove from inventory (use inventory_key since inventory uses Title Case)
            self.remove_item(inventory_key, 1)

            effect = item_data.effect
            if effect == "heal":
                heal_amount = int(self.max_health * item_data.value)
                self.health = min(self.max_health, self.health + heal_amount)
                print(f"{self.name} healed for {heal_amount} HP!")

            elif effect == "defend":
                defense_buff = item_data.value
                # apply temporary defense buff tracked separately so end_defend() removes correctly
                self.temp_defense_buff += defense_buff
                self.defense += defense_buff
                self.is_defending = True
                print(
                    f"{self.name}'s defense increased by {defense_buff} for this turn."
                )
            else:
                print(f"{inventory_key} can't be used right now.")

    def show_inventory(self) -> None:
        if not self.inventory:
            print("Inventory is empty.")
            return
        print("Inventory:")
        for item, qty in self.inventory.items():
            print(f"- {item}: {qty}")
        print()
        print("Equipped Items:")
        print(f"- Weapon: {self.equipped_weapon if self.equipped_weapon else 'None'}")
        print(f"- Armor: {self.equipped_armor if self.equipped_armor else 'None'}")

    def equip_item(self, item_name: str) -> None:
        """Equip a weapon or armor from inventory."""
        name = item_name.strip()
        inventory_key = name.title()

        if self.inventory.get(inventory_key, 0) <= 0:
            print(f"No {inventory_key} in inventory.")
            return

        # Find the item in database
        candidates = [inventory_key, name, name.lower(), name.lower().replace(" ", "_")]
        item_data = None
        for cand in candidates:
            if cand in ITEM_DATABASE:
                item_data = ITEM_DATABASE[cand]
                inventory_key = cand  # Use the found key
                break

        if not item_data:
            print(f"{name} not found in database.")
            return

        # Equip based on item type
        if item_data.type == "weapon":
            self.equipped_weapon = inventory_key
            print(f"Equipped {inventory_key}!")
            self._recalc_equipped_bonuses()
        elif item_data.type == "armor":
            self.equipped_armor = inventory_key
            print(f"Equipped {inventory_key}!")
            self._recalc_equipped_bonuses()
        else:
            print(f"{inventory_key} cannot be equipped.")

    def unequip_item(self, slot: str) -> None:
        """Unequip weapon or armor."""
        slot = slot.lower().strip()
        if slot in ["weapon", "w"]:
            self.equipped_weapon = None
            print("Unequipped weapon.")
        elif slot in ["armor", "a"]:
            self.equipped_armor = None
            print("Unequipped armor.")
        else:
            print("Invalid slot. Use 'weapon' or 'armor'.")
        self._recalc_equipped_bonuses()

    def _recalc_equipped_bonuses(self) -> None:
        """Recalculate and apply attack/defense bonuses from equipped items."""
        # Reset bonuses
        self.attack_power -= self.equipped_attack_bonus
        self.defense -= self.equipped_defense_bonus
        self.equipped_attack_bonus = 0
        self.equipped_defense_bonus = 0

        # Apply weapon bonuses
        if self.equipped_weapon and self.equipped_weapon in ITEM_DATABASE:
            weapon = ITEM_DATABASE[self.equipped_weapon]
            if weapon.bonuses.get("attack"):
                self.equipped_attack_bonus = weapon.bonuses["attack"]
                self.attack_power += self.equipped_attack_bonus

        # Apply armor bonuses
        if self.equipped_armor and self.equipped_armor in ITEM_DATABASE:
            armor = ITEM_DATABASE[self.equipped_armor]
            if armor.bonuses.get("defense"):
                self.equipped_defense_bonus = armor.bonuses["defense"]
                self.defense += self.equipped_defense_bonus

    def defend(self):
        if self.is_defending:
            print(f"{self.name} is already defending.")
            return

        buff = 10
        self.temp_defense_buff = buff
        self.defense += buff
        self.is_defending = True
        print(
            f"{self.name} is defending! Defense increased to {self.defense} for this turn."
        )

    def end_defend(self):
        if not self.is_defending:
            return

        # remove whatever temporary defense buff was applied
        self.defense -= self.temp_defense_buff
        self.temp_defense_buff = 0
        self.is_defending = False
        print(f"{self.name} stopped defending. Defense back to {self.defense}.")

    def attack(self, other):

        if not self.alive() or not other.alive():
            return

        # Calculate dodge chance
        dodge_chance = other.speed - self.attack_speed

        # makes chance to dodge between 5% and 70%
        dodge_chance = max(5, min(70, dodge_chance))

        dodge_roll = random.randint(1, 100)

        if dodge_roll <= dodge_chance:
            print(f"{other.name} DODGED {self.name}'s attack! (Roll: {dodge_roll})\n")
            return

        damage = self.attack_power
        # ---- DEFENSE (Percentage Based) ----
        defense_percent = max(0, min(75, other.defense))

        final_damage = damage * (1 - defense_percent / 100)
        final_damage = int(final_damage)

        # ------ Critical hit formula ----------------

        crit_chance = self.crit_chance

        crit_roll = random.randint(1, 100)

        if crit_roll <= crit_chance:
            final_damage *= 2
            print("💥 CRITICAL HIT!")

            # This code applies damage
        other.health -= final_damage
        if other.health < 0:
            other.health = 0

        print(f"{self.name} hit {other.name} for {final_damage} damage!")
        print(f"{other.name} has {other.health} HP left.\n")
