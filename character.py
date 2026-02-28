import random
import json
import os
from Items import ITEM_DATABASE

# Directory where character save files are stored
SAVE_DIR = "player files"


def _normalize_item_key(name: str) -> str:
    return " ".join(str(name or "").replace("_", " ").strip().lower().split())


def resolve_item_key(name: str):
    """Return canonical ITEM_DATABASE key for a user/save-provided item name."""
    if not name:
        return None
    if name in ITEM_DATABASE:
        return name
    target = _normalize_item_key(name)
    for key in ITEM_DATABASE.keys():
        if _normalize_item_key(key) == target:
            return key
    return None


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
        # status effects like burn/poison: list of dicts {type, damage, duration, source}
        self.status_effects = []

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
        self.equipped_speed_bonus = 0
        self.equipped_attack_speed_bonus = 0
        self.equipped_crit_bonus = 0
        self.temp_speed_buff = 0

        # Store base stats for correct saving/loading
        self.base_attack_power = attack_power
        self.base_defense = defense
        self.base_speed = speed
        self.base_attack_speed = attack_speed
        self.base_crit_chance = crit_chance

    def save(self):
        data = {
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "max_health": self.max_health,
            "health": self.health,
            # Save base stats, not boosted
            "attack_power": self.base_attack_power,
            "defense": self.base_defense,
            "base_speed": self.base_speed,
            "base_attack_speed": self.base_attack_speed,
            "speed": self.speed,
            "attack_speed": self.attack_speed,
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
            # Keep base stats in sync so save/load doesn't drop level-up gains.
            self.base_attack_power += 5
            self.base_defense += 0
            self.base_speed += 3
            self.base_attack_speed += 3

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
            loaded_inventory = data.get("inventory", self.inventory)
            # Canonicalize saved inventory keys to current ITEM_DATABASE keys.
            canonical_inventory = {}
            for raw_key, qty in loaded_inventory.items():
                key = resolve_item_key(raw_key) or raw_key
                canonical_inventory[key] = canonical_inventory.get(key, 0) + qty
            self.inventory = canonical_inventory
            self.equipped_weapon = resolve_item_key(
                data.get("equipped_weapon", self.equipped_weapon)
            )
            self.equipped_armor = resolve_item_key(
                data.get("equipped_armor", self.equipped_armor)
            )
            self.crit_chance = data.get("crit_chance", self.crit_chance)

            # Reset stats to base values from save file before applying equipment bonuses
            self.base_attack_power = data.get("attack_power", self.attack_power)
            self.base_defense = data.get("defense", self.defense)
            saved_speed = data.get("speed", self.speed)
            saved_attack_speed = data.get("attack_speed", self.attack_speed)

            # Backward compatibility: older saves don't have base_speed fields.
            speed_bonus_from_equipment = 0
            attack_speed_bonus_from_equipment = 0
            if self.equipped_weapon and self.equipped_weapon in ITEM_DATABASE:
                speed_bonus_from_equipment += ITEM_DATABASE[
                    self.equipped_weapon
                ].bonuses.get("speed", 0)
                attack_speed_bonus_from_equipment += ITEM_DATABASE[
                    self.equipped_weapon
                ].bonuses.get("attack_speed", 0)
            if self.equipped_armor and self.equipped_armor in ITEM_DATABASE:
                speed_bonus_from_equipment += ITEM_DATABASE[
                    self.equipped_armor
                ].bonuses.get("speed", 0)
                attack_speed_bonus_from_equipment += ITEM_DATABASE[
                    self.equipped_armor
                ].bonuses.get("attack_speed", 0)

            self.base_speed = data.get(
                "base_speed", saved_speed - speed_bonus_from_equipment
            )
            self.base_attack_speed = data.get(
                "base_attack_speed",
                saved_attack_speed - attack_speed_bonus_from_equipment,
            )
            self.attack_power = self.base_attack_power
            self.defense = self.base_defense
            self.speed = self.base_speed
            self.attack_speed = self.base_attack_speed
            self.equipped_attack_bonus = 0
            self.equipped_defense_bonus = 0
            self.equipped_speed_bonus = 0
            self.equipped_attack_speed_bonus = 0
            self.equipped_crit_bonus = 0

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
        key = resolve_item_key(item_name) or item_name.title()
        self.inventory[key] = self.inventory.get(key, 0) + qty
        print(f"{self.name} received {qty} x {key} (Total: {self.inventory[key]})")

    def remove_item(self, item_name: str, qty: int = 1) -> bool:
        key = resolve_item_key(item_name) or item_name.title()
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
        inventory_key = resolve_item_key(name) or name.title()

        if self.inventory.get(inventory_key, 0) <= 0:
            print(f"No {inventory_key} in inventory.")
            return

        item_db_key = resolve_item_key(name) or resolve_item_key(inventory_key)
        item_data = ITEM_DATABASE.get(item_db_key) if item_db_key else None

        if not item_data:
            print(f"{inventory_key} does nothing.")
            return

        # item_data is now an Item object with .type, .effect, .value attributes
        if item_data.type == "consumable":
            effect = item_data.effect
            if effect == "heal":
                self.remove_item(inventory_key, 1)
                heal_amount = int(self.max_health * item_data.value)
                self.health = min(self.max_health, self.health + heal_amount)
                print(f"{self.name} healed for {heal_amount} HP!")

            elif effect == "defend":
                self.remove_item(inventory_key, 1)
                defense_buff = item_data.value
                # apply temporary defense buff tracked separately so end_defend() removes correctly
                self.temp_defense_buff += defense_buff
                self.defense += defense_buff
                self.is_defending = True
                print(
                    f"{self.name}'s defense increased by {defense_buff} for this turn."
                )
            elif effect == "speed":
                self.remove_item(inventory_key, 1)
                speed_buff = item_data.value
                self.temp_speed_buff += speed_buff
                self.speed += speed_buff
                print(f"{self.name}'s speed increased by {speed_buff} for this turn.")
            elif effect == "heal_defend":
                self.remove_item(inventory_key, 1)
                heal_amount = int(self.max_health * item_data.value["heal"])
                defense_buff = item_data.value["defend"]
                self.health = min(self.max_health, self.health + heal_amount)
                self.temp_defense_buff += defense_buff
                self.defense += defense_buff
                self.is_defending = True
                print(
                    f"{self.name} healed for {heal_amount} HP and defense increased by {defense_buff} for this turn."
                )
            else:
                print(f"{inventory_key} can't be used right now.")

    def show_inventory(self) -> None:
        if not self.inventory:
            print("Inventory is empty.")
            return
        print("Inventory:")
        for item, qty in self.inventory.items():
            name_display = (
                ITEM_DATABASE[item].colored_name() if item in ITEM_DATABASE else item
            )
            initial = (
                f" ({ITEM_DATABASE[item].rarity[0]})" if item in ITEM_DATABASE else ""
            )
            print(f"- {name_display}{initial}: {qty}")
        print()
        print("Equipped Items:")
        weapon_display = (
            ITEM_DATABASE[self.equipped_weapon].colored_name()
            + f" ({ITEM_DATABASE[self.equipped_weapon].rarity[0]})"
            if self.equipped_weapon and self.equipped_weapon in ITEM_DATABASE
            else (self.equipped_weapon if self.equipped_weapon else "None")
        )
        armor_display = (
            ITEM_DATABASE[self.equipped_armor].colored_name()
            + f" ({ITEM_DATABASE[self.equipped_armor].rarity[0]})"
            if self.equipped_armor and self.equipped_armor in ITEM_DATABASE
            else (self.equipped_armor if self.equipped_armor else "None")
        )
        print(f"- Weapon: {weapon_display}")
        print(f"- Armor: {armor_display}")

    def equip_item(self, item_name: str) -> None:
        """Equip a weapon or armor from inventory."""
        name = item_name.strip()
        inventory_key = resolve_item_key(name) or name.title()

        if self.inventory.get(inventory_key, 0) <= 0:
            print(f"No {inventory_key} in inventory.")
            return

        # Find canonical key in database
        item_db_key = resolve_item_key(name) or resolve_item_key(inventory_key)
        item_data = ITEM_DATABASE.get(item_db_key) if item_db_key else None
        if item_db_key:
            inventory_key = item_db_key

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
        """Recalculate and apply attack/defense/speed bonuses from equipped items."""
        # Reset bonuses
        self.attack_power -= self.equipped_attack_bonus
        self.defense -= self.equipped_defense_bonus
        self.speed -= self.equipped_speed_bonus
        self.attack_speed -= self.equipped_attack_speed_bonus
        self.crit_chance -= self.equipped_crit_bonus
        self.equipped_attack_bonus = 0
        self.equipped_defense_bonus = 0
        self.equipped_speed_bonus = 0
        self.equipped_attack_speed_bonus = 0
        self.equipped_crit_bonus = 0

        # Apply weapon bonuses
        if self.equipped_weapon and self.equipped_weapon in ITEM_DATABASE:
            weapon = ITEM_DATABASE[self.equipped_weapon]
            if weapon.bonuses.get("attack"):
                self.equipped_attack_bonus = weapon.bonuses["attack"]
                self.attack_power += self.equipped_attack_bonus
            if weapon.bonuses.get("speed"):
                self.equipped_speed_bonus += weapon.bonuses["speed"]
                self.speed += weapon.bonuses["speed"]
            if weapon.bonuses.get("crit_chance"):
                self.equipped_crit_bonus += weapon.bonuses["crit_chance"]
                self.crit_chance += weapon.bonuses["crit_chance"]
            if weapon.bonuses.get("attack_speed"):
                self.equipped_attack_speed_bonus += weapon.bonuses["attack_speed"]
                self.attack_speed += weapon.bonuses["attack_speed"]

        # Apply armor bonuses
        if self.equipped_armor and self.equipped_armor in ITEM_DATABASE:
            armor = ITEM_DATABASE[self.equipped_armor]
            if armor.bonuses.get("defense"):
                self.equipped_defense_bonus = armor.bonuses["defense"]
                self.defense += self.equipped_defense_bonus
            if armor.bonuses.get("speed"):
                self.equipped_speed_bonus += armor.bonuses["speed"]
                self.speed += armor.bonuses["speed"]
            if armor.bonuses.get("attack_speed"):
                self.equipped_attack_speed_bonus += armor.bonuses["attack_speed"]
                self.attack_speed += armor.bonuses["attack_speed"]
            if armor.bonuses.get("crit_chance"):
                self.equipped_crit_bonus += armor.bonuses["crit_chance"]
                self.crit_chance += armor.bonuses["crit_chance"]

    def defend(self):
        if self.is_defending:
            print(f"{self.name} is already defending.")
            return

        buff = 10
        self.temp_defense_buff = buff
        self.defense += buff
        self.is_defending = True
        archetype = getattr(self, "archetype", "")
        if archetype == "Tank":
            print(f"{self.name} BRACES(defend)!")
        elif archetype == "Assassin":
            print(f"{self.name} hides(defend)!")
        elif archetype == "Bruiser":
            print(f"{self.name} protects themself.")
        else:
            print(
                f"{self.name} is defending! Defense increased to {self.defense} for this turn."
            )

    def end_defend(self):
        if self.is_defending:
            # remove whatever temporary defense buff was applied
            self.defense -= self.temp_defense_buff
            self.temp_defense_buff = 0
            self.is_defending = False
            print(f"{self.name} stopped defending. Defense back to {self.defense}.")

        if self.temp_speed_buff > 0:
            self.speed = max(0, self.speed - self.temp_speed_buff)
            self.temp_speed_buff = 0
            print(f"{self.name}'s speed boost wore off.")

    def process_status_effects(self):
        """Apply and tick down status effects like burn at the start of the character's turn."""
        if not self.status_effects:
            return

        remaining = []
        for eff in self.status_effects:
            etype = eff.get("type")
            dmg = eff.get("damage", 0)
            turns_left = eff.get("duration", 1)
            if etype == "Bleed":
                self.health -= dmg
                if self.health < 0:
                    self.health = 0
                print(
                    f"🩸 {self.name} takes {dmg} bleed damage! ({self.health} HP left) [{turns_left} turns left]"
                )
            if etype == "burn":
                self.health -= dmg
                if self.health < 0:
                    self.health = 0
                print(
                    f"🔥 {self.name} takes {dmg} burn damage! ({self.health} HP left) [{turns_left} turns left]"
                )
            elif etype == "poison":
                self.health -= dmg
                if self.health < 0:
                    self.health = 0
                print(
                    f"☠️ {self.name} takes {dmg} poison damage! ({self.health} HP left) [{turns_left} turns left]"
                )

            elif etype == "freeze":
                self.health -= dmg
                if self.health < 0:
                    self.health = 0
                print(
                    f"❄️ {self.name} takes {dmg} freeze damage! ({self.health} HP left) [{turns_left} turns left]"
                )
                # 50% chance to skip turn
                if random.random() < 0.5:
                    self.turn_skipped = True
                    print(f"{self.name} is slowed by freeze and may lose their turn!")
                # Restore temporary freeze slow when it expires.
                if turns_left == 1:
                    self.speed += eff.get("speed_penalty", 0)
                    self.attack_speed += eff.get("attack_speed_penalty", 0)

            elif etype == "armor break":
                # If this is the last turn, restore defense
                if turns_left == 1 and hasattr(self, "_original_defense"):
                    self.defense = self._original_defense
                    del self._original_defense
                    print(f"🛡️ {self.name}'s armor is restored!")

            elif etype == "Weaken":
                # Weaken reduces attack power and defense.
                if not eff.get("applied", False):
                    attack_pct = eff.get("attack_pct", 0.2)
                    defense_pct = eff.get("defense_pct", 0.2)
                    attack_reduction = int(self.attack_power * attack_pct)
                    defense_reduction = int(self.defense * defense_pct)
                    self.attack_power -= attack_reduction
                    self.defense = max(0, self.defense - defense_reduction)
                    eff["attack_reduction"] = attack_reduction
                    eff["defense_reduction"] = defense_reduction
                    eff["applied"] = True
                    print(
                        f"{self.name} is weakened! Attack reduced by {attack_reduction} and defense reduced by {defense_reduction}."
                    )
                elif turns_left == 1 and turns_left >= 0:
                    # If weaken has a finite duration, restore stats on expiry.
                    self.attack_power += eff.get("attack_reduction", 0)
                    self.defense += eff.get("defense_reduction", 0)
                    print(f"{self.name} is no longer weakened.")
            # ...existing code...

            # decrement duration
            if turns_left < 0:
                # Negative duration means permanent until battle reset/clear.
                remaining.append(eff)
            else:
                eff["duration"] = turns_left - 1
                if eff["duration"] > 0:
                    remaining.append(eff)

        self.status_effects = remaining

    def attack(self, other):

        if not self.alive() or not other.alive():
            return

        # Check for lightning status on target (take 25% more damage, then remove effect)
        lightning_bonus = 1.0
        for eff in list(other.status_effects):
            if eff.get("type") == "lightning" and eff.get("duration", 0) > 0:
                lightning_bonus = 1.25
                other.status_effects.remove(eff)  # Consume immediately after use
                print(f"⚡ {other.name} takes 25% more damage from lightning!")
                break

        # Calculate dodge chance
        dodge_chance = other.speed - self.attack_speed

        # makes chance to dodge between 5% and 70%
        dodge_chance = max(5, min(70, dodge_chance))

        dodge_roll = random.randint(1, 100)

        if dodge_roll <= dodge_chance:
            print(f"{other.name} DODGED {self.name}'s attack! (Roll: {dodge_roll})\n")
            return

        archetype = getattr(self, "archetype", "")
        if archetype == "Tank":
            print(f"{self.name} charges!")
        elif archetype == "Assassin":
            print(f"{self.name} strikes!")
        elif archetype == "Bruiser":
            print(f"{self.name} swings!")

        damage = self.attack_power
        if archetype == "Bruiser":
            hp_ratio = 1.0 if self.max_health <= 0 else (self.health / self.max_health)
            if hp_ratio <= 0.35:
                damage *= 1.2
        elif archetype == "Glass Cannon":
            damage *= 1.15
        # ---- DEFENSE (Percentage Based) ----
        defense_percent = max(0, min(75, other.defense))

        final_damage = damage * (1 - defense_percent / 100)
        final_damage = int(
            final_damage * lightning_bonus
        )  # Apply lightning bonus if applicable

        # ------ Critical hit formula ----------------

        crit_chance = self.crit_chance
        if archetype == "Assassin":
            crit_chance += 10
        crit_multiplier = 2.0

        # Weapon-level crit tuning:
        # - special["crit_chance"]: additive crit chance for this weapon
        # - special["crit_multiplier"]: crit damage multiplier for this weapon
        if self.equipped_weapon and self.equipped_weapon in ITEM_DATABASE:
            weapon = ITEM_DATABASE[self.equipped_weapon]
            special = getattr(weapon, "special", None) or {}
            crit_chance += special.get("crit_chance", 0)
            crit_multiplier = special.get("crit_multiplier", 2.0)

        crit_roll = random.randint(1, 100)

        if crit_roll <= crit_chance:
            final_damage = int(final_damage * crit_multiplier)
            print("💥 CRITICAL HIT!")

            # This code applies damage
        other_archetype = getattr(other, "archetype", "")
        if other_archetype == "Glass Cannon":
            final_damage = int(final_damage * 1.10)
        if other_archetype == "Tank" and getattr(other, "is_defending", False):
            # Extra mitigation for Tank while defending.
            final_damage = int(final_damage * 0.90)
        other.health -= final_damage
        if other.health < 0:
            other.health = 0

        # Special weapon effects (e.g., burn) -> apply as DOT status effect
        # ARMOR BREAK: halve defense for 1 turn, restore after effect expires
        try:
            if self.equipped_weapon and self.equipped_weapon in ITEM_DATABASE:
                weapon = ITEM_DATABASE[self.equipped_weapon]
                special = getattr(weapon, "special", None)
                # BLEED: applies a percent of this attack's final_damage as DOT
                if special and special.get("type") == "Bleed":
                    chance = special.get("chance", 0)
                    if random.randint(1, 100) <= chance:
                        bleed_percent = special.get("percent", 0.2)  # Default 20%
                        bleed_damage = int(final_damage * bleed_percent)
                        duration = special.get("duration", 3)
                        # Prevent duplicate bleed
                        if not any(
                            eff.get("type") == "Bleed" for eff in other.status_effects
                        ):
                            other.status_effects.append(
                                {
                                    "type": "Bleed",
                                    "damage": bleed_damage,
                                    "duration": duration,
                                    "source": self.name,
                                }
                            )
                            print(
                                f"🩸 {other.name} is bleeding! Will take {bleed_damage} damage for {duration} turns!"
                            )

                if special and special.get("type") == "burn":
                    chance = special.get("chance", 0)
                    if random.randint(1, 100) <= chance:
                        burn = special.get("damage", 0)
                        duration = special.get("duration", 3)
                        # Prevent duplicate burn
                        if not any(
                            eff.get("type") == "burn" for eff in other.status_effects
                        ):
                            other.status_effects.append(
                                {
                                    "type": "burn",
                                    "damage": burn,
                                    "duration": duration,
                                    "source": self.name,
                                }
                            )
                            print(
                                f"🔥 {other.name} was burned and will take {burn} damage for {duration} turns!"
                            )

                if special and special.get("type") == "poison":
                    chance = special.get("chance", 0)
                    if random.randint(1, 100) <= chance:
                        poison = special.get("damage", 0)
                        duration = special.get("duration", 3)
                        # Prevent duplicate poison
                        if not any(
                            eff.get("type") == "poison" for eff in other.status_effects
                        ):
                            other.status_effects.append(
                                {
                                    "type": "poison",
                                    "damage": poison,
                                    "duration": duration,
                                    "source": self.name,
                                }
                            )
                            print(
                                f"☠️ {other.name} was poisoned and will take {poison} damage for {duration} turns!"
                            )

                if special and special.get("type") == "lightning":
                    chance = special.get("chance", 0)
                    if random.randint(1, 100) <= chance:
                        duration = special.get("duration", 2)
                        # Prevent duplicate lightning
                        if not any(
                            eff.get("type") == "lightning"
                            for eff in other.status_effects
                        ):
                            other.status_effects.append(
                                {
                                    "type": "lightning",
                                    "duration": duration,
                                    "source": self.name,
                                }
                            )
                            print(
                                f"⚡ {other.name} is charged with lightning! Next attack will deal 25% more damage!"
                            )

                if special and special.get("type") == "freeze":
                    chance = special.get("chance", 0)
                    if random.randint(1, 100) <= chance:
                        freeze = special.get("damage", 0)
                        duration = special.get("duration", 3)
                        speed_penalty = 10
                        attack_speed_penalty = 10
                        # Prevent duplicate freeze
                        if not any(
                            eff.get("type") == "freeze" for eff in other.status_effects
                        ):
                            other.speed = max(0, other.speed - speed_penalty)
                            other.attack_speed = max(
                                0, other.attack_speed - attack_speed_penalty
                            )
                            other.status_effects.append(
                                {
                                    "type": "freeze",
                                    "damage": freeze,
                                    "duration": duration,
                                    "speed_penalty": speed_penalty,
                                    "attack_speed_penalty": attack_speed_penalty,
                                    "source": self.name,
                                }
                            )
                            print(
                                f"❄️ {other.name} was frozen and will take {freeze} damage for {duration} turns!"
                            )

                if special and special.get("type", "").lower() == "armor break":
                    chance = special.get("chance", 0)
                    if random.randint(1, 100) <= chance:
                        duration = special.get("duration", 1)
                        # Prevent duplicate Armor Break
                        if not any(
                            eff.get("type") == "armor break"
                            for eff in other.status_effects
                        ):
                            # Store original defense if not already stored
                            if not hasattr(other, "_original_defense"):
                                other._original_defense = other.defense
                            other.defense = max(0, int(other.defense * 0.5))
                            other.status_effects.append(
                                {
                                    "type": "armor break",
                                    "duration": duration,
                                    "source": self.name,
                                }
                            )
                            print(
                                f"🛡️ {other.name}'s armor is broken! Defense halved for {duration} turn!"
                            )

                if special and special.get("type") == "Weaken":
                    chance = special.get("chance", 0)
                    if random.randint(1, 100) <= chance:
                        duration = special.get(
                            "duration", -1
                        )  # Permanent until removed
                        attack_pct = special.get("attack_pct", 0.2)
                        defense_pct = special.get("defense_pct", 0.2)
                        # Prevent duplicate Weaken
                        if not any(
                            eff.get("type") == "Weaken" for eff in other.status_effects
                        ):
                            other.status_effects.append(
                                {
                                    "type": "Weaken",
                                    "duration": duration,
                                    "attack_pct": attack_pct,
                                    "defense_pct": defense_pct,
                                    "source": self.name,
                                }
                            )
                            print(
                                f"⚔️ {other.name} is weakened! They deal 20% less damage and lose 20% defense."
                            )
                # ...existing code...

        except Exception as err:
            print(f"Error applying weapon special effects: {err}")

        print(f"{self.name} hit {other.name} for {final_damage} damage!")
        print(f"{other.name} has {other.health} HP left.\n")
