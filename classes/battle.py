import random
from dataclasses import dataclass, field
from enum import Enum

from .inventory import Item


class BattleState(Enum):
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    WON = "won"
    LOST = "lost"
    FLED = "fled"


TERMINAL_STATES = {BattleState.WON, BattleState.LOST, BattleState.FLED}


@dataclass
class ActionResult:
    ok: bool
    message: str = ""
    killed: object = None
    healed: int = 0
    spell: object = None
    item: object = None
    fled: bool = False
    meta: dict = field(default_factory=dict)

    def __bool__(self):
        return self.ok


class Battle:
    """Reusable FF-style turn battle state machine.

    Transitions:
        PLAYER_TURN --all actors acted--> ENEMY_TURN
        any terminal side is dead --> WON / LOST
        successful flee --> FLED
    When both sides are wiped in the same settlement, LOST wins: a downed
    party cannot claim victory. Every action and phase ends in `settle`,
    and a terminal battle rejects further actions, so the world can never
    advance past a failure.
    """

    def __init__(self, players, enemies, rng=None, flee_chance=0.5):
        self.players = list(players)
        self.enemies = list(enemies)
        self.rng = rng or random.Random()
        self.flee_chance = flee_chance
        self.state = BattleState.PLAYER_TURN
        self.last_result = None

    @property
    def over(self):
        return self.state in TERMINAL_STATES

    def alive_players(self):
        return [person for person in self.players if person.is_alive()]

    def alive_enemies(self):
        return [person for person in self.enemies if person.is_alive()]

    def settle(self):
        if self.state not in TERMINAL_STATES:
            if not self.alive_players():
                self.state = BattleState.LOST
            elif not self.alive_enemies():
                self.state = BattleState.WON
        return self.state

    def _assert_actor(self, actor):
        if self.over:
            return ActionResult(False, "battle is already over")
        if not actor.is_alive():
            return ActionResult(False, actor.name + " cannot act while down")
        return None

    def _attack_damage(self, attacker, defender, rng=None):
        raw = attacker.generate_damage(rng)
        return max(0, raw - defender.get_df())

    def attack(self, attacker, target):
        blocked = self._assert_actor(actor=attacker)
        if blocked is not None:
            self.last_result = blocked
            return blocked
        dmg = self._attack_damage(attacker, target, self.rng)
        target.take_damage(dmg)
        result = ActionResult(True, "", killed=target if not target.is_alive() else None,
                              meta={"damage": dmg})
        self.last_result = result
        self.settle()
        return result

    def cast(self, caster, spell, target=None):
        blocked = self._assert_actor(actor=caster)
        if blocked is not None:
            self.last_result = blocked
            return blocked
        if spell is None:
            result = ActionResult(False, "no such spell")
            self.last_result = result
            return result
        if not caster.can_cast(spell):
            result = ActionResult(False, "Not enough MP", spell=spell)
            self.last_result = result
            return result

        caster.reduce_mp(spell.cost)
        if spell.type == "white":
            before = caster.hp
            magic_dmg = spell.generate_damage(self.rng)
            caster.heal(magic_dmg)
            result = ActionResult(True, "", healed=caster.hp - before, spell=spell,
                                  meta={"amount": magic_dmg})
        else:
            if target is None or not target.is_alive():
                caster.restore_mp(spell.cost)
                result = ActionResult(False, "no valid target", spell=spell)
                self.last_result = result
                return result
            magic_dmg = spell.generate_damage(self.rng)
            target.take_damage(magic_dmg)
            result = ActionResult(True, "", killed=target if not target.is_alive() else None,
                                  spell=spell, meta={"damage": magic_dmg})
        self.last_result = result
        self.settle()
        return result

    def use_item(self, user, entry, target=None):
        blocked = self._assert_actor(actor=user)
        if blocked is not None:
            self.last_result = blocked
            return blocked
        if entry is None or entry not in user.items:
            result = ActionResult(False, "no such item", item=entry)
            self.last_result = result
            return result
        item = entry["item"]
        if entry["quantity"] <= 0:
            result = ActionResult(False, "None left...", item=item)
            self.last_result = result
            return result

        if item.type == Item.POTION:
            if target is None:
                target = user
            before = target.hp
            target.heal(item.prop)
            healed = target.hp - before
            if healed <= 0:
                result = ActionResult(False, item.name + " had no effect", item=item)
                self.last_result = result
                return result
            entry["quantity"] -= 1
            result = ActionResult(True, "", healed=healed, item=item)
        elif item.type == Item.ELIXER:
            targets = self.players if item.name == "MegaElixer" else [user]
            if not any(person.is_alive() for person in targets):
                result = ActionResult(False, item.name + " had no effect", item=item)
                self.last_result = result
                return result
            entry["quantity"] -= 1
            for person in targets:
                if person.is_alive():
                    person.restore()
            result = ActionResult(True, "", item=item)
        elif item.type == Item.ATTACK:
            if target is None or not target.is_alive():
                result = ActionResult(False, "no valid target", item=item)
                self.last_result = result
                return result
            entry["quantity"] -= 1
            target.take_damage(item.prop)
            result = ActionResult(True, "", killed=target if not target.is_alive() else None,
                                  item=item, meta={"damage": item.prop})
        else:
            result = ActionResult(False, item.name + " cannot be used in combat", item=item)
            self.last_result = result
            return result

        self.last_result = result
        self.settle()
        return result

    def equip(self, person, entry):
        blocked = self._assert_actor(actor=person)
        if blocked is not None:
            self.last_result = blocked
            return blocked
        if entry is None or entry not in person.items or entry["quantity"] <= 0:
            result = ActionResult(False, "None left...", item=entry)
            self.last_result = result
            return result
        item = entry["item"]
        if item.type == Item.WEAPON:
            slot = "weapon"
        elif item.type == Item.ARMOR:
            slot = "armor"
        else:
            result = ActionResult(False, item.name + " is not equipment", item=item)
            self.last_result = result
            return result

        entry["quantity"] -= 1
        previous = getattr(person, slot)
        if previous is not None:
            person.add_item(previous, 1)
        setattr(person, slot, item)
        if entry["quantity"] <= 0:
            person.items.remove(entry)
        result = ActionResult(True, "", item=item,
                              meta={"slot": slot, "replaced": previous})
        self.last_result = result
        return result

    def flee(self, actor):
        blocked = self._assert_actor(actor=actor)
        if blocked is not None:
            self.last_result = blocked
            return blocked
        escaped = self.rng.random() < self.flee_chance
        if escaped:
            self.state = BattleState.FLED
            result = ActionResult(True, "", fled=True)
        else:
            result = ActionResult(False, "failed to flee", fled=False)
        self.last_result = result
        return result

    def enemy_take_turn(self, enemy):
        blocked = self._assert_actor(actor=enemy)
        if blocked is not None:
            return blocked
        players = self.alive_players()
        if not players:
            self.settle()
            return ActionResult(False, "no target")

        spell, magic_dmg = enemy.choose_enemy_spell(self.rng)
        if spell is not None and enemy.can_cast(spell):
            enemy.reduce_mp(spell.cost)
            if spell.type == "white":
                before = enemy.hp
                enemy.heal(magic_dmg)
                result = ActionResult(True, "", healed=enemy.hp - before, spell=spell,
                                      meta={"kind": "spell", "target": enemy})
            else:
                target = players[self.rng.randrange(0, len(players))]
                target.take_damage(magic_dmg)
                result = ActionResult(True, "", killed=target if not target.is_alive() else None,
                                      spell=spell, meta={"kind": "spell", "target": target,
                                                        "damage": magic_dmg})
        else:
            target = players[self.rng.randrange(0, len(players))]
            dmg = self._attack_damage(enemy, target, self.rng)
            target.take_damage(dmg)
            result = ActionResult(True, "", killed=target if not target.is_alive() else None,
                                  meta={"kind": "attack", "target": target, "damage": dmg})
        self.last_result = result
        self.settle()
        return result

    def end_player_phase(self):
        if self.over:
            return self.state
        self.state = BattleState.ENEMY_TURN
        for enemy in list(self.alive_enemies()):
            if self.over:
                break
            self.enemy_take_turn(enemy)
        if not self.over:
            self.state = BattleState.PLAYER_TURN
        return self.state
