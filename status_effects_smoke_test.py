from character import Character
import character as character_module
from Items import ITEM_DATABASE


def make_char(name: str) -> Character:
    return Character(
        name=name,
        health=200,
        attack_power=20,
        speed=20,
        attack_speed=50,
        defense=0,
        crit_chance=0,
    )


def equip_weapon(user: Character, weapon_name: str) -> None:
    user.equipped_weapon = weapon_name
    user._recalc_equipped_bonuses()


def tick_n(target: Character, turns: int) -> None:
    for _ in range(turns):
        target.process_status_effects()


def assert_single_status(target: Character, status_type: str) -> dict:
    matches = [s for s in target.status_effects if s.get("type") == status_type]
    assert len(matches) == 1, f"Expected one {status_type} effect, got {len(matches)}."
    return matches[0]


def main() -> None:
    original_randint = character_module.random.randint
    original_random = character_module.random.random

    # Deterministic battle checks:
    # - randint=100 means no dodge (dodge max 70), no crit (unless 100%), and 100% proc chances pass.
    # - random()=1.0 means freeze skip roll never triggers.
    character_module.random.randint = lambda _a, _b: 100
    character_module.random.random = lambda: 1.0

    try:
        # Burn
        attacker = make_char("Burner")
        target = make_char("TargetBurn")
        equip_weapon(attacker, "Flame Sword")
        attacker.attack(target)
        burn = assert_single_status(target, "burn")
        burn_duration = ITEM_DATABASE["Flame Sword"].special["duration"]
        burn_damage = ITEM_DATABASE["Flame Sword"].special["damage"]
        hp_before = target.health
        tick_n(target, burn_duration)
        assert target.health == hp_before - (burn_damage * burn_duration), "Burn damage tick total mismatch."
        assert not any(s.get("type") == "burn" for s in target.status_effects), "Burn should expire."

        # Poison
        attacker = make_char("Poisoner")
        target = make_char("TargetPoison")
        equip_weapon(attacker, "Shadow Dagger")
        attacker.attack(target)
        poison = assert_single_status(target, "poison")
        poison_duration = ITEM_DATABASE["Shadow Dagger"].special["duration"]
        poison_damage = ITEM_DATABASE["Shadow Dagger"].special["damage"]
        hp_before = target.health
        tick_n(target, poison_duration)
        assert target.health == hp_before - (poison_damage * poison_duration), "Poison damage tick total mismatch."
        assert not any(s.get("type") == "poison" for s in target.status_effects), "Poison should expire."

        # Bleed should not duplicate
        attacker = make_char("Bleeder")
        target = make_char("TargetBleed")
        equip_weapon(attacker, "Draining Axe")
        attacker.attack(target)
        attacker.attack(target)
        bleed_count = sum(1 for s in target.status_effects if s.get("type") == "Bleed")
        assert bleed_count == 1, f"Bleed duplicated unexpectedly: {bleed_count}."

        # Freeze should restore speed/attack_speed on expiry
        attacker = make_char("Freezer")
        target = make_char("TargetFreeze")
        base_speed = target.speed
        base_attack_speed = target.attack_speed
        equip_weapon(attacker, "Ice Scythe")
        attacker.attack(target)
        freeze = assert_single_status(target, "freeze")
        assert target.speed == base_speed - 10, "Freeze speed penalty not applied."
        assert target.attack_speed == base_attack_speed - 10, "Freeze attack_speed penalty not applied."
        tick_n(target, freeze["duration"])
        assert target.speed == base_speed, "Freeze speed penalty did not restore."
        assert target.attack_speed == base_attack_speed, "Freeze attack_speed penalty did not restore."
        assert not any(s.get("type") == "freeze" for s in target.status_effects), "Freeze should expire."

        # Armor break should restore defense on expiry
        attacker = make_char("Breaker")
        target = make_char("TargetArmor")
        target.defense = 30
        original_def = target.defense
        equip_weapon(attacker, "Titan Hammer")
        attacker.attack(target)
        armor_break = assert_single_status(target, "armor break")
        assert target.defense == int(original_def * 0.5), "Armor break did not halve defense."
        tick_n(target, armor_break["duration"])
        assert target.defense == original_def, "Armor break did not restore defense."
        assert not any(s.get("type") == "armor break" for s in target.status_effects), "Armor break should expire."

        # Weaken should apply once (20% less attack + defense) and remain active with negative duration
        attacker = make_char("Weakener")
        target = make_char("TargetWeaken")
        target.defense = 20
        equip_weapon(attacker, "Weakening Rapier")
        attacker.attack(target)
        weaken = assert_single_status(target, "Weaken")
        start_atk = target.attack_power
        start_def = target.defense
        target.process_status_effects()  # first application
        first_atk = target.attack_power
        first_def = target.defense
        target.process_status_effects()  # should not apply reduction a second time
        assert target.attack_power == first_atk, "Weaken reapplied attack reduction."
        assert target.defense == first_def, "Weaken reapplied defense reduction."
        assert target.attack_power < start_atk and target.defense < start_def, "Weaken did not apply reduction."
        expected_atk = start_atk - int(start_atk * 0.2)
        expected_def = start_def - int(start_def * 0.2)
        assert first_atk == expected_atk, f"Weaken attack reduction mismatch: expected {expected_atk}, got {first_atk}."
        assert first_def == expected_def, f"Weaken defense reduction mismatch: expected {expected_def}, got {first_def}."
        assert any(s.get("type") == "Weaken" for s in target.status_effects), "Weaken should remain active with negative duration."

        # Lightning should amplify exactly one next hit, then clear
        applier = make_char("LightningApplier")
        attacker = make_char("LightningFollowup")
        target = make_char("TargetLightning")
        attacker.attack_power = 20
        target.defense = 0
        equip_weapon(applier, "Lightning Hammer")
        applier.attack(target)
        assert_single_status(target, "lightning")
        hp_before = target.health
        attacker.attack(target)
        assert target.health == hp_before - 25, "Lightning bonus damage expected to be 25% (20 -> 25)."
        assert not any(s.get("type") == "lightning" for s in target.status_effects), "Lightning should be consumed after one hit."

        print("All status effect smoke tests passed.")
    finally:
        character_module.random.randint = original_randint
        character_module.random.random = original_random


if __name__ == "__main__":
    main()
