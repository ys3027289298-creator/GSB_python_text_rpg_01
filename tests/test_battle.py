import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.battle import Battle, BattleState
from classes.game import Person
from classes.inventory import Item
from classes.magic import Spell


def make_person(name="Hero", hp=100, mp=50, atk=20, df=5, magic=None, items=None):
    return Person(name, hp, mp, atk, df, magic or [], items or [])


def entry(item, quantity):
    return {"item": item, "quantity": quantity}


class FakeRng:
    """Deterministic stand-in for random.Random used by Battle."""

    def __init__(self, rolls=(), ints=()):
        self._rolls = list(rolls)
        self._ints = list(ints)
        self.roll_calls = 0

    def random(self):
        self.roll_calls += 1
        return self._rolls.pop(0)

    def randrange(self, low, high=None):
        if high is None:
            high = low
            low = 0
        return self._ints.pop(0) % (high - low) + low


class SimultaneousDeathTest(unittest.TestCase):
    def test_both_sides_die_in_settlement_is_lost(self):
        player = make_person("Hero", hp=10)
        enemy = make_person("Imp", hp=10)
        battle = Battle([player], [enemy], rng=FakeRng(ints=[0]))

        player.take_damage(10)
        enemy.take_damage(10)

        state = battle.settle()
        self.assertIs(state, BattleState.LOST)
        self.assertTrue(battle.over)

    def test_killing_last_enemy_then_enemies_do_not_act(self):
        player = make_person("Hero", hp=100, atk=999, df=0)
        enemy = make_person("Imp", hp=10, atk=50, df=0)
        battle = Battle([player], [enemy], rng=FakeRng(ints=[0]))

        result = battle.attack(player, enemy)
        self.assertTrue(result.killed is enemy)
        self.assertIs(battle.state, BattleState.WON)

        acted = battle.enemy_take_turn(enemy)
        self.assertFalse(acted)
        self.assertEqual(player.hp, 100)
        battle.end_player_phase()
        self.assertIs(battle.state, BattleState.WON)

    def test_last_enemy_dying_after_last_player_is_lost(self):
        player = make_person("Hero", hp=1)
        enemy = make_person("Imp", hp=1)
        battle = Battle([player], [enemy], rng=FakeRng(ints=[0]))
        player.take_damage(1)
        enemy.take_damage(1)
        self.assertIs(battle.settle(), BattleState.LOST)


class FleeTest(unittest.TestCase):
    def _battle(self, rolls):
        player = make_person("Hero", hp=100)
        enemy = make_person("Imp", hp=100)
        return Battle([player], [enemy], rng=FakeRng(rolls=rolls, ints=[0]))

    def test_consecutive_flee_fail_then_success(self):
        battle = self._battle([0.9, 0.1])
        player, enemy = battle.players[0], battle.enemies[0]

        first = battle.flee(player)
        self.assertFalse(first.fled)
        self.assertIs(battle.state, BattleState.PLAYER_TURN)
        self.assertFalse(battle.over)

        second = battle.flee(player)
        self.assertTrue(second.fled)
        self.assertIs(battle.state, BattleState.FLED)
        self.assertTrue(battle.over)
        self.assertEqual(player.hp, 100)

    def test_no_actions_after_flee(self):
        battle = self._battle([0.0])
        battle.flee(battle.players[0])
        result = battle.attack(battle.players[0], battle.enemies[0])
        self.assertFalse(result)
        self.assertEqual(battle.enemies[0].hp, 100)


class EmptyInventoryTest(unittest.TestCase):
    def test_empty_backpack(self):
        player = make_person("Hero")
        enemy = make_person("Imp")
        battle = Battle([player], [enemy])

        self.assertFalse(battle.use_item(player, None))
        self.assertFalse(battle.use_item(player, entry(Item("Potion", "potion", "", 50), 1)))
        self.assertEqual(player.items, [])
        self.assertEqual(player.hp, 100)

    def test_zero_and_negative_quantity_never_consumed(self):
        potion = Item("Potion", "potion", "Heals 50 HP", 50)
        zero = entry(potion, 0)
        negative = entry(potion, -3)
        player = make_person("Hero", hp=10, items=[zero, negative])
        battle = Battle([player], [make_person("Imp")])

        self.assertEqual(battle.use_item(player, zero).message, "None left...")
        self.assertEqual(zero["quantity"], 0)
        self.assertEqual(battle.use_item(player, negative).message, "None left...")
        self.assertEqual(negative["quantity"], -3)
        self.assertFalse(battle.over)

    def test_potion_at_full_hp_is_not_drunk(self):
        potion = Item("Potion", "potion", "Heals 50 HP", 50)
        stack = entry(potion, 2)
        player = make_person("Hero", hp=100, items=[stack])
        battle = Battle([player], [make_person("Imp")])

        result = battle.use_item(player, stack)
        self.assertFalse(result)
        self.assertEqual(stack["quantity"], 2)
        self.assertEqual(player.hp, 100)


class NegativeAttributesTest(unittest.TestCase):
    def test_negative_stats_are_clamped(self):
        hero = make_person("Hero", hp=-10, mp=-5, atk=-100, df=-100)
        self.assertEqual(hero.maxhp, 1)
        self.assertEqual(hero.hp, 0)
        self.assertEqual(hero.maxmp, 0)
        self.assertEqual(hero.mp, 0)
        self.assertEqual(hero.get_atk(), 0)
        self.assertEqual(hero.get_df(), 0)

    def test_negative_equipment_bonus_cannot_make_stats_negative(self):
        curse_weapon = Item("Rusty Sword", "weapon", "weak", -999)
        curse_armor = Item("Paper Armor", "armor", "weak", -999)
        hero = make_person("Hero", atk=10, df=10,
                           items=[entry(curse_weapon, 1), entry(curse_armor, 1)])
        battle = Battle([hero], [make_person("Imp")])

        battle.equip(hero, hero.items[0])
        self.assertEqual(hero.get_atk(), 0)
        battle.equip(hero, hero.items[0])
        self.assertEqual(hero.get_df(), 0)

    def test_damage_and_heal_ignore_negative_amounts(self):
        hero = make_person("Hero", hp=50)
        hero.take_damage(-999)
        self.assertEqual(hero.hp, 50)
        hero.heal(-999)
        self.assertEqual(hero.hp, 50)

    def test_high_defense_turns_damage_to_zero_not_healing(self):
        hero = make_person("Hero", hp=100, atk=10, df=1000)
        enemy = make_person("Imp", hp=100, atk=500)
        battle = Battle([hero], [enemy], rng=FakeRng(ints=[0, 0]))

        result = battle.attack(enemy, hero)
        self.assertEqual(result.meta["damage"], 0)
        self.assertEqual(hero.hp, 100)
        result = battle.attack(hero, enemy)
        self.assertEqual(result.meta["damage"], 0)
        self.assertEqual(enemy.hp, 100)

    def test_negative_spell_cost_and_power(self):
        spell = Spell("Weird", -5, -20, "black")
        self.assertEqual(spell.cost, 0)
        self.assertEqual(spell.dmg, 0)
        self.assertGreaterEqual(spell.generate_damage(random.Random(0)), 0)


class HpBoundsInvariantTest(unittest.TestCase):
    def assert_bounds(self, battle):
        for person in battle.players + battle.enemies:
            self.assertGreaterEqual(person.hp, 0)
            self.assertLessEqual(person.hp, person.maxhp)
            self.assertGreaterEqual(person.mp, 0)
            self.assertLessEqual(person.mp, person.maxmp)

    def test_bounds_after_every_settlement_in_random_battles(self):
        rng = random.Random(1234)
        fire = Spell("Fire", 10, 40, "black")
        cure = Spell("Cure", 8, 30, "white")
        potion = Item("Potion", "potion", "Heals 30 HP", 30)
        grenade = Item("Grenade", "attack", "Deals 60 damage", 60)
        mega = Item("MegaElixer", "elixer", "party restore", 9999)
        sword = Item("Sword", "weapon", "+atk", 15)
        curse = Item("Curse", "weapon", "-atk", -40)

        for battle_index in range(300):
            players = []
            for n in range(rng.randrange(1, 4)):
                stats = rng.choice([
                    (rng.randrange(1, 200), rng.randrange(0, 60),
                     rng.randrange(0, 60), rng.randrange(0, 40)),
                    (-rng.randrange(0, 50), -5, -5, -5),
                ])
                players.append(Person("P%d" % n, *stats,
                                      magic=[fire, cure],
                                      items=[entry(potion, rng.randrange(0, 4)),
                                             entry(grenade, rng.randrange(0, 2)),
                                             entry(mega, rng.randrange(0, 2)),
                                             entry(sword, rng.randrange(0, 2)),
                                             entry(curse, rng.randrange(0, 2))]))
            enemies = [Person("E%d" % n,
                              rng.randrange(1, 200), rng.randrange(0, 60),
                              rng.randrange(0, 60), rng.randrange(0, 60),
                              [fire, cure], [])
                       for n in range(rng.randrange(1, 4))]
            battle = Battle(players, enemies, rng=rng)

            rounds = 0
            while not battle.over and rounds < 30:
                rounds += 1
                for actor in list(battle.alive_players()):
                    if battle.over:
                        break
                    choice = rng.randrange(0, 6)
                    if choice == 0 and battle.alive_enemies():
                        battle.attack(actor, rng.choice(battle.alive_enemies()))
                    elif choice == 1:
                        battle.cast(actor, fire,
                                    rng.choice(battle.alive_enemies()) if battle.alive_enemies() else None)
                    elif choice == 2:
                        battle.cast(actor, cure)
                    elif choice == 3:
                        stacks = [e for e in actor.items if e["item"].type == "potion"]
                        if stacks:
                            battle.use_item(actor, rng.choice(stacks))
                        else:
                            battle.use_item(actor, None)
                    elif choice == 4:
                        gear = [e for e in actor.items if e["item"].type == "weapon"]
                        if gear:
                            battle.equip(actor, rng.choice(gear))
                    else:
                        battle.flee(actor)
                    self.assert_bounds(battle)

                if not battle.over:
                    battle.end_player_phase()
                    self.assert_bounds(battle)

            self.assertIn(battle.state, (BattleState.WON, BattleState.LOST, BattleState.FLED))
            self.assert_bounds(battle)


class RegressionTest(unittest.TestCase):
    def test_mega_elixer_does_not_revive_dead(self):
        mega = Item("MegaElixer", "elixer", "party", 9999)
        alive = make_person("Alive", hp=10, mp=0, items=[entry(mega, 1)])
        dead = make_person("Dead", hp=10)
        dead.take_damage(10)
        battle = Battle([alive, dead], [make_person("Imp")])

        battle.use_item(alive, alive.items[0])
        self.assertEqual(alive.hp, alive.maxhp)
        self.assertEqual(dead.hp, 0)
        self.assertFalse(dead.is_alive())

    def test_enemy_ai_with_no_castable_spell_attacks(self):
        costly = Spell("Meteor", 9999, 60, "black")
        enemy = make_person("Magus", hp=100, mp=0, atk=30, df=0, magic=[costly])
        player = make_person("Hero", hp=100, df=0)
        battle = Battle([player], [enemy], rng=FakeRng(ints=[0, 0]))

        result = battle.enemy_take_turn(enemy)
        self.assertTrue(result)
        self.assertIsNone(result.spell)
        self.assertLess(player.hp, 100)
        self.assertEqual(enemy.mp, 0)

    def test_enemy_phase_stops_immediately_on_loss(self):
        imp1 = make_person("Imp1", hp=100, atk=999)
        imp2 = make_person("Imp2", hp=100, atk=999)
        player = make_person("Hero", hp=1, df=0)
        battle = Battle([player], [imp1, imp2], rng=FakeRng(ints=[0, 0, 0]))

        battle.end_player_phase()
        self.assertIs(battle.state, BattleState.LOST)
        self.assertEqual(player.hp, 0)

    def test_mp_never_negative_after_failed_cast_path(self):
        fire = Spell("Fire", 40, 50, "black")
        hero = make_person("Hero", mp=10, magic=[fire])
        battle = Battle([hero], [make_person("Imp")])
        result = battle.cast(hero, fire, battle.enemies[0])
        self.assertFalse(result)
        self.assertEqual(hero.mp, 10)


if __name__ == "__main__":
    unittest.main()
