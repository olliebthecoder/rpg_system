import random
import json
from item_Database import ITEM_DATABASE


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

        # Leveling stats
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100

        self.gold = 0
        # inventory: map item name -> quantity
        self.inventory = {}

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
        }

        with open(f"{self.name}_save.json", "w") as file:
            json.dump(data, file)

        print(f"💾 {self.name} has been saved!")

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
            with open(f"{self.name}_save.json", "r") as file:
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
            self.crit_chance = data.get("crit_chance", self.crit_chance)

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
        key = item_name.title()

        if self.inventory.get(key, 0) <= 0:
            print(f"No {key} in inventory.")
            return

        item_data = ITEM_DATABASE.get(key)
        if not item_data:
            print(f"{key} does nothing.")
            return

        if item_data["type"] == "consumable":
            self.remove_item(key, 1)

            if item_data["effect"] == "heal":
                heal_amount = int(self.max_health * item_data["value"])
                self.health = min(self.max_health, self.health + heal_amount)
                print(f"{self.name} healed for {heal_amount} HP!")

            elif item_data["effect"] == "defend":
                self.defend()

        else:
            print(f"{key} can't be used right now.")

    def show_inventory(self) -> None:
        if not self.inventory:
            print("Inventory is empty.")
            return
        print("Inventory:")
        for item, qty in self.inventory.items():
            print(f"- {item}: {qty}")

    def defend(self):
        if self.is_defending:
            print(f"{self.name} is already defending.")
            return

        self.defense += 10
        self.is_defending = True
        print(
            f"{self.name} is defending! Defense increased to {self.defense} for this turn."
        )

    def end_defend(self):
        if not self.is_defending:
            return

        self.defense -= 10
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
