import random
from enum import Enum, auto


class BattleState(Enum):
    """States of the battle state machine.

    PLAYER_PHASE / ENEMY_PHASE: battle is running.
    VICTORY / DEFEAT / FLED: terminal states; once reached, every
    further action is a no-op so nothing can proceed after the end.
    """
    PLAYER_PHASE = auto()
    ENEMY_PHASE = auto()
    VICTORY = auto()
    DEFEAT = auto()
    FLED = auto()


TERMINAL_STATES = (BattleState.VICTORY, BattleState.DEFEAT, BattleState.FLED)


class Battle:
    """Reusable FF-style turn-based battle resolution state machine.

    Every mutation goes through an action method, and every action ends
    with settle(), which clamps all combatants' HP/MP into [0, max] and
    evaluates the end conditions exactly once, in a fixed order:

    1. both sides wiped out in the same resolution -> DEFEAT
    2. no living enemies  -> VICTORY
    3. no living players  -> DEFEAT
    """

    def __init__(self, players, enemies, rng=None, flee_chance=0.5):
        self.players = list(players)
        self.enemies = list(enemies)
        self.rng = rng if rng is not None else random.Random()
        self.flee_chance = flee_chance
        self.state = BattleState.PLAYER_PHASE
        self.settle()

    @property
    def is_over(self):
        return self.state in TERMINAL_STATES

    @property
    def combatants(self):
        return self.players + self.enemies

    def living_players(self):
        return [p for p in self.players if p.is_alive()]

    def living_enemies(self):
        return [e for e in self.enemies if e.is_alive()]

    def settle(self):
        """Clamp resources, then evaluate end conditions. Returns state."""
        if self.is_over:
            return self.state
        for combatant in self.combatants:
            combatant.clamp_stats()
        if not self.living_enemies() and not self.living_players():
            self.state = BattleState.DEFEAT
        elif not self.living_enemies():
            self.state = BattleState.VICTORY
        elif not self.living_players():
            self.state = BattleState.DEFEAT
        return self.state

    def attack(self, attacker, target):
        """Physical attack; defense reduces damage, df=0 is safe."""
        if self.is_over or target is None:
            return None
        raw = attacker.generate_damage()
        dmg = max(1, raw - max(0, target.df) // 2)
        target.take_damage(dmg)
        self.settle()
        return dmg

    def cast_spell(self, caster, spell, target=None):
        """Cast a spell. Returns the amount healed/dealt, or None."""
        if self.is_over:
            return None
        if spell.cost > caster.get_mp():
            return None
        caster.reduce_mp(spell.cost)
        amount = max(0, spell.generate_damage())
        if spell.type == "white":
            caster.heal(amount)
        else:
            if target is None:
                return None
            target.take_damage(amount)
        self.settle()
        return amount

    def use_item(self, user, entry, target=None, party=None):
        """Use one inventory entry {"item": Item, "quantity": n}.

        Never drives quantity below 0 and never wastes a potion on a
        combatant who is already at full HP. Returns True if consumed.
        """
        if self.is_over:
            return False
        if entry is None or entry.get("quantity", 0) <= 0:
            return False
        item = entry["item"]

        if item.type == "potion":
            if user.get_hp() >= user.get_max_hp():
                return False
            entry["quantity"] -= 1
            user.heal(item.prop)
        elif item.type == "elixer":
            entry["quantity"] -= 1
            if item.name == "MegaElixer":
                for member in (party if party is not None else [user]):
                    member.full_restore()
            else:
                user.full_restore()
        elif item.type == "attack":
            if target is None:
                return False
            entry["quantity"] -= 1
            target.take_damage(max(0, item.prop))
        else:
            return False

        self.settle()
        return True

    def equip(self, person, equipment):
        """Switch equipment; stats are recomputed from base, never stacked."""
        if self.is_over or equipment is None:
            return False
        person.equip(equipment)
        self.settle()
        return True

    def flee(self, person):
        """Attempt to flee. A failed attempt leaves the battle running."""
        if self.is_over:
            return False
        if self.rng.random() < self.flee_chance:
            self.state = BattleState.FLED
            return True
        return False
