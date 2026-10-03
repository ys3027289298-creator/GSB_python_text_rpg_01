import random
import unittest

from classes.game import Person
from classes.magic import Spell
from classes.inventory import Item
from classes.equipment import Equipment
from classes.battle import Battle, BattleState


def make_fighters():
    player = Person("Hero", 1000, 100, 100, 10, [], [])
    enemy = Person("Foe", 1000, 100, 100, 10, [], [])
    return player, enemy


class SimultaneousDeathTest(unittest.TestCase):
    def test_both_sides_dead_is_terminal_defeat(self):
        player, enemy = make_fighters()
        battle = Battle([player], [enemy])
        player.take_damage(99999)
        enemy.take_damage(99999)
        state = battle.settle()
        self.assertEqual(state, BattleState.DEFEAT)
        self.assertTrue(battle.is_over)

    def test_no_step_after_mutual_death(self):
        player, enemy = make_fighters()
        battle = Battle([player], [enemy])
        player.take_damage(99999)
        enemy.take_damage(99999)
        battle.settle()
        # Battle is over: every further action must be a no-op.
        self.assertIsNone(battle.attack(player, enemy))
        self.assertFalse(battle.flee(player))
        self.assertFalse(battle.use_item(player, {"item": Item("P", "potion", "", 50), "quantity": 3}))
        self.assertEqual(battle.state, BattleState.DEFEAT)

    def test_killing_last_enemy_ends_battle_immediately(self):
        player, enemy = make_fighters()
        enemy.hp = 1
        battle = Battle([player], [enemy])
        battle.attack(player, enemy)
        # Settlement happens right after the action, before any enemy phase.
        self.assertEqual(battle.state, BattleState.VICTORY)

    def test_killing_last_player_ends_battle_immediately(self):
        player, enemy = make_fighters()
        player.hp = 1
        battle = Battle([player], [enemy])
        battle.attack(enemy, player)
        self.assertEqual(battle.state, BattleState.DEFEAT)


class FleeTest(unittest.TestCase):
    def test_consecutive_flee_attempts(self):
        player, enemy = make_fighters()
        rng = random.Random(1234)
        battle = Battle([player], [enemy], rng=rng, flee_chance=0.5)

        results = [battle.flee(player) for _ in range(20)]
        # Failed attempts leave the battle running and do not end it.
        self.assertIn(False, results)
        self.assertIn(True, results)
        first_success = results.index(True)
        for result in results[:first_success]:
            self.assertFalse(result)
        self.assertEqual(battle.state, BattleState.FLED)
        self.assertTrue(battle.is_over)

    def test_always_failing_flee_keeps_battle_running(self):
        player, enemy = make_fighters()
        battle = Battle([player], [enemy], rng=random.Random(0), flee_chance=0.0)
        for _ in range(10):
            self.assertFalse(battle.flee(player))
            self.assertFalse(battle.is_over)

    def test_no_actions_after_successful_flee(self):
        player, enemy = make_fighters()
        battle = Battle([player], [enemy], flee_chance=1.0)
        self.assertTrue(battle.flee(player))
        self.assertIsNone(battle.attack(player, enemy))
        self.assertEqual(enemy.get_hp(), enemy.get_max_hp())


class EmptyInventoryTest(unittest.TestCase):
    def test_use_item_with_empty_inventory(self):
        player, enemy = make_fighters()
        player.items = []
        battle = Battle([player], [enemy])
        self.assertFalse(battle.use_item(player, None))
        self.assertEqual(player.get_hp(), player.get_max_hp())

    def test_use_item_with_zero_quantity(self):
        player, enemy = make_fighters()
        player.take_damage(100)
        entry = {"item": Item("Potion", "potion", "Heals 50 HP", 50), "quantity": 0}
        battle = Battle([player], [enemy])
        self.assertFalse(battle.use_item(player, entry))
        self.assertEqual(entry["quantity"], 0)  # never goes negative
        self.assertEqual(player.get_hp(), player.get_max_hp() - 100)

    def test_repeated_potion_until_empty(self):
        player, enemy = make_fighters()
        player.take_damage(500)
        entry = {"item": Item("Potion", "potion", "Heals 50 HP", 50), "quantity": 2}
        battle = Battle([player], [enemy])
        self.assertTrue(battle.use_item(player, entry))
        self.assertTrue(battle.use_item(player, entry))
        self.assertFalse(battle.use_item(player, entry))
        self.assertEqual(entry["quantity"], 0)

    def test_potion_not_wasted_at_full_hp(self):
        player, enemy = make_fighters()
        entry = {"item": Item("Potion", "potion", "Heals 50 HP", 50), "quantity": 1}
        battle = Battle([player], [enemy])
        self.assertFalse(battle.use_item(player, entry))
        self.assertEqual(entry["quantity"], 1)
        self.assertEqual(player.get_hp(), player.get_max_hp())


class NegativeAttributeTest(unittest.TestCase):
    def test_negative_constructor_attributes(self):
        person = Person("Neg", -100, -50, -30, -20, [], [])
        self.assertEqual(person.get_max_hp(), 0)
        self.assertEqual(person.get_hp(), 0)
        self.assertEqual(person.get_mp(), 0)
        self.assertFalse(person.is_alive())

    def test_negative_damage_and_healing_are_noops(self):
        person = Person("P", 100, 100, 100, 10, [], [])
        person.take_damage(-50)
        self.assertEqual(person.get_hp(), 100)  # cannot heal via negative damage
        person.take_damage(60)
        person.heal(-30)
        self.assertEqual(person.get_hp(), 40)  # cannot be hurt via negative heal

    def test_negative_attack_still_resolves(self):
        player = Person("Weak", 100, 100, -5000, 0, [], [])
        enemy, _ = make_fighters()
        battle = Battle([player], [enemy])
        dmg = battle.attack(player, enemy)
        self.assertGreaterEqual(dmg, 0)
        self.assertGreaterEqual(enemy.get_hp(), 0)

    def test_negative_defense_is_safe(self):
        player, enemy = make_fighters()
        enemy.df = -100
        battle = Battle([player], [enemy])
        dmg = battle.attack(player, enemy)
        self.assertGreaterEqual(dmg, 0)
        self.assertGreaterEqual(enemy.get_hp(), 0)

    def test_mp_never_goes_negative(self):
        person = Person("P", 100, 10, 100, 10, [], [])
        person.reduce_mp(999)
        self.assertEqual(person.get_mp(), 0)

    def test_zero_defense_takes_full_damage(self):
        player, enemy = make_fighters()
        enemy.df = 0
        battle = Battle([player], [enemy], rng=random.Random(0))
        dmg = battle.attack(player, enemy)
        self.assertGreater(dmg, 0)
        self.assertEqual(enemy.get_hp(), enemy.get_max_hp() - dmg)


class EquipmentTest(unittest.TestCase):
    def test_switching_equipment_does_not_stack(self):
        person = Person("P", 1000, 100, 100, 10, [], [])
        sword_a = Equipment("A", "weapon", "", atk=50)
        sword_b = Equipment("B", "weapon", "", atk=20)
        battle = Battle([person], [Person("E", 100, 100, 100, 10, [], [])])

        battle.equip(person, sword_a)
        self.assertEqual(person.atkl, 100 + 50 - 10)
        battle.equip(person, sword_b)  # switch: only B applies
        self.assertEqual(person.atkl, 100 + 20 - 10)
        person.unequip("weapon")
        self.assertEqual(person.atkl, 100 - 10)

    def test_equipment_maxhp_change_clamps_hp(self):
        person = Person("P", 1000, 100, 100, 10, [], [])
        mail = Equipment("Mail", "armor", "", maxhp=-600)
        battle = Battle([person], [Person("E", 100, 100, 100, 10, [], [])])
        battle.equip(person, mail)
        self.assertEqual(person.get_max_hp(), 400)
        self.assertLessEqual(person.get_hp(), person.get_max_hp())
        person.unequip("armor")
        self.assertEqual(person.get_max_hp(), 1000)


class HpBoundsInvariantTest(unittest.TestCase):
    """After every single settlement, every combatant must satisfy
    0 <= hp <= maxhp and 0 <= mp <= maxmp, whatever happened."""

    def assert_bounds(self, battle):
        for combatant in battle.combatants:
            self.assertGreaterEqual(combatant.get_hp(), 0, combatant.name)
            self.assertLessEqual(combatant.get_hp(), combatant.get_max_hp(), combatant.name)
            self.assertGreaterEqual(combatant.get_mp(), 0, combatant.name)
            self.assertLessEqual(combatant.get_mp(), combatant.get_max_mp(), combatant.name)

    def test_invariant_holds_across_random_battles(self):
        spells = [Spell("Fire", 25, 600, "black"), Spell("Cure", 25, 620, "white")]
        sword = Equipment("Sword", "weapon", "", atk=30)

        for seed in range(100):
            rng = random.Random(seed)
            players = [Person("P%d" % n, rng.randint(1, 3000), rng.randint(0, 200),
                              rng.randint(-50, 400), rng.randint(-20, 300),
                              spells, [{"item": Item("Potion", "potion", "", 50), "quantity": 3}])
                       for n in range(3)]
            enemies = [Person("E%d" % n, rng.randint(1, 3000), rng.randint(0, 200),
                              rng.randint(-50, 400), rng.randint(-20, 300), spells, [])
                       for n in range(3)]
            battle = Battle(players, enemies, rng=rng, flee_chance=0.2)
            self.assert_bounds(battle)

            steps = 0
            while not battle.is_over and steps < 500:
                steps += 1
                actor = rng.choice(battle.combatants)
                side = players if actor in players else enemies
                foes = battle.living_enemies() if actor in players else battle.living_players()
                action = rng.randrange(6)
                if action == 0 and foes:
                    battle.attack(actor, rng.choice(foes))
                elif action == 1:
                    battle.cast_spell(actor, rng.choice(spells),
                                      rng.choice(foes) if foes else None)
                elif action == 2 and actor.items:
                    entry = rng.choice(actor.items)
                    target = rng.choice(foes) if foes else None
                    battle.use_item(actor, entry, target=target, party=side)
                elif action == 3:
                    battle.equip(actor, sword)
                elif action == 4:
                    battle.flee(actor)
                else:
                    actor.take_damage(rng.randint(-100, 500))
                    actor.heal(rng.randint(-100, 500))
                    battle.settle()
                self.assert_bounds(battle)

            self.assertTrue(battle.is_over, "battle %d never terminated" % seed)
            self.assert_bounds(battle)


if __name__ == "__main__":
    unittest.main()
