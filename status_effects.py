# status_effects.py
"""
Status effect system for RPG. Easily extensible for new effects.
"""
import random


class StatusEffect:
    def __init__(self, name, duration, damage=0, source=None, **kwargs):
        self.name = name
        self.duration = duration
        self.damage = damage
        self.source = source
        self.extra = kwargs  # For custom effect data

    def apply(self, target):
        """Apply effect to target each turn. Override for custom logic."""
        if self.damage:
            target.health -= self.damage
            print(
                f"{target.name} suffers {self.damage} {self.name} damage! ({target.health} HP left)"
            )
        # Add more logic for other effects here

    def on_apply(self, target):
        """Called when effect is first applied. Override for custom logic."""
        pass

    def on_expire(self, target):
        """Called when effect expires. Override for custom logic."""
        pass

    def tick(self, target):
        self.apply(target)
        self.duration -= 1
        if self.duration <= 0:
            self.on_expire(target)
            return False  # Remove effect
        return True  # Keep effect


# Registry for all status effects
STATUS_EFFECTS = {}


def register_status_effect(name, effect_class):
    STATUS_EFFECTS[name.lower()] = effect_class


def create_status_effect(name, **kwargs):
    cls = STATUS_EFFECTS.get(name.lower())
    if cls:
        return cls(**kwargs)
    raise ValueError(f"Unknown status effect: {name}")


# Example: Burn effect
class Burn(StatusEffect):
    def __init__(self, duration, damage, source=None):
        super().__init__("Burn", duration, damage, source)

    def on_apply(self, target):
        print(f"{target.name} is burned!")

    def on_expire(self, target):
        print(f"{target.name} is no longer burned.")


class Poison(StatusEffect):
    def __init__(self, duration, damage, source=None):
        super().__init__("Poison", duration, damage, source)

    def on_apply(self, target):
        print(f"{target.name} is poisoned!")

    def on_expire(self, target):
        print(f"{target.name} is no longer poisoned.")


register_status_effect("burn", Burn)
register_status_effect("poison", Poison)

# Add more effects by subclassing StatusEffect and registering them.
# Example:
# class Poison(StatusEffect): ...
# register_status_effect("poison", Poison)
