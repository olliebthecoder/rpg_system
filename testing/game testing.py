import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure tests work whether run from repository root or tests/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from character import Character
from enemy import generate_enemy


class CharacterTests(unittest.TestCase):
    def test_defend_and_end_defend_only_applies_once(self):
        hero = Character("hero", 100, 10, 20, 20, 10, 10)

        hero.defend()
        defended_value = hero.defense
        hero.defend()  # should not stack

        self.assertEqual(defended_value, hero.defense)

        hero.end_defend()
        self.assertEqual(10, hero.defense)

    def test_attack_does_not_reduce_health_below_zero(self):
        attacker = Character("attacker", 100, 999, 10, 999, 0, 0)
        target = Character("target", 50, 1, 1, 1, 0, 0)

        with patch("random.randint", return_value=100):  # no dodge, no crit
            attacker.attack(target)

        self.assertEqual(0, target.health)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                hero = Character("savehero", 120, 30, 40, 50, 15, 20)
                hero.level = 4
                hero.xp = 90
                hero.xp_to_next = 150
                hero.health = 75

                hero.save()

                loaded = Character("savehero", 1, 1, 1, 1, 1, 1)
                loaded.load()

                self.assertEqual(hero.level, loaded.level)
                self.assertEqual(hero.xp, loaded.xp)
                self.assertEqual(hero.xp_to_next, loaded.xp_to_next)
                self.assertEqual(hero.max_health, loaded.max_health)
                self.assertEqual(hero.health, loaded.health)
                self.assertEqual(hero.attack_power, loaded.attack_power)
                self.assertEqual(hero.speed, loaded.speed)
                self.assertEqual(hero.attack_speed, loaded.attack_speed)
                self.assertEqual(hero.defense, loaded.defense)
            finally:
                os.chdir(cwd)


class EnemyGenerationTests(unittest.TestCase):
    def test_level_5_enemy_is_boss(self):
        player = Character("p", 100, 10, 10, 10, 10, 10)
        player.level = 5

        with patch("random.choice", return_value="Tank"):
            enemy = generate_enemy(player)

        self.assertIn("BOSS", enemy.name)
        expected_health = int((150 + (5 * 25)) * 1.3)
        expected_attack = int((15 + (5 * 3)) * 1.5)

        self.assertEqual(expected_health, enemy.health)
        self.assertEqual(expected_attack, enemy.attack_power)


if __name__ == "__main__":
    unittest.main()
