import random


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _clamp(value, low, high):
    return max(low, min(high, value))


class Person:
    def __init__(self, name, hp, mp, atk, df, magic, items):
        self.name = name
        self.maxhp = max(1, int(hp))
        self.hp = _clamp(hp, 0, self.maxhp)
        self.maxmp = max(0, int(mp))
        self.mp = _clamp(mp, 0, self.maxmp)
        self.base_atk = max(0, int(atk))
        self.base_df = max(0, int(df))
        self.magic = list(magic or [])
        self.items = list(items or [])
        self.weapon = None
        self.armor = None
        self.actions = ["Attack", "Magic", "Items", "Flee"]

    def get_atk(self):
        bonus = self.weapon.prop if self.weapon else 0
        return max(0, self.base_atk + bonus)

    def get_df(self):
        bonus = self.armor.prop if self.armor else 0
        return max(0, self.base_df + bonus)

    def generate_damage(self, rng=None):
        rng = rng or random
        atk = self.get_atk()
        low = max(0, atk - 10)
        high = atk + 10
        if high <= low:
            return low
        return rng.randrange(low, high)

    def take_damage(self, dmg):
        dmg = max(0, int(dmg))
        self.hp = _clamp(self.hp - dmg, 0, self.maxhp)
        return self.hp

    def heal(self, dmg):
        if self.hp <= 0:
            return self.hp
        dmg = max(0, int(dmg))
        self.hp = _clamp(self.hp + dmg, 0, self.maxhp)
        return self.hp

    def restore(self):
        self.hp = self.maxhp
        self.mp = self.maxmp

    def reduce_mp(self, cost):
        self.mp = _clamp(self.mp - max(0, int(cost)), 0, self.maxmp)
        return self.mp

    def restore_mp(self, amount):
        self.mp = _clamp(self.mp + max(0, int(amount)), 0, self.maxmp)
        return self.mp

    def get_hp(self):
        return self.hp

    def get_max_hp(self):
        return self.maxhp

    def get_mp(self):
        return self.mp

    def get_max_mp(self):
        return self.maxmp

    def is_alive(self):
        return self.hp > 0

    def can_cast(self, spell):
        return self.mp >= spell.cost

    def add_item(self, item, quantity=1):
        for entry in self.items:
            if entry["item"] is item:
                entry["quantity"] += quantity
                return
        self.items.append({"item": item, "quantity": quantity})

    def choose_action(self):
        i = 1
        print("\n" + "    " + bcolors.BOLD + self.name + bcolors.ENDC)
        print(bcolors.OKBLUE + bcolors.BOLD + "    ACTIONS:" + bcolors.ENDC)
        for item in self.actions:
            print("        " + str(i) + ".", item)
            i += 1

    def choose_magic(self):
        i = 1

        print("\n" + bcolors.OKBLUE + bcolors.BOLD + "    MAGIC:" + bcolors.ENDC)
        for spell in self.magic:
            print("        " + str(i) + ".", spell.name, "(cost:", str(spell.cost) + ")")
            i += 1

    def choose_item(self):
        i = 1

        print("\n" + bcolors.OKGREEN + bcolors.BOLD + "    ITEMS:" + bcolors.ENDC)
        for item in self.items:
            print("        " + str(i) + ".", item["item"].name + ":", item["item"].description, " (x" + str(item["quantity"]) + ")")
            i += 1

    def get_enemy_stats(self):
        hp_bar = ""
        bar_ticks = (self.hp / self.maxhp) * 100 / 2

        while bar_ticks > 0:
            hp_bar += "█"
            bar_ticks -= 1

        while len(hp_bar) < 50:
            hp_bar += " "

        hp_string = str(self.hp) + "/" + str(self.maxhp)
        current_hp = ""

        if len(hp_string) < 11:
            decreased = 11 - len(hp_string)

            while decreased > 0:
                current_hp += " "
                decreased -= 1

            current_hp += hp_string
        else:
            current_hp = hp_string

        print("                    __________________________________________________ ")
        print(bcolors.BOLD + self.name + "  " +
              current_hp + " |" + bcolors.FAIL + hp_bar + bcolors.ENDC + "|")

    def get_stats(self):
        hp_bar = ""
        bar_ticks = (self.hp / self.maxhp) * 100 / 4

        mp_bar = ""
        mp_ticks = (self.mp / self.maxmp) * 100 / 10 if self.maxmp else 0

        while bar_ticks > 0:
            hp_bar += "█"
            bar_ticks -= 1

        while len(hp_bar) < 25:
            hp_bar += " "

        while mp_ticks > 0:
            mp_bar += "█"
            mp_ticks -= 1

        while len(mp_bar) < 10:
            mp_bar += " "


        hp_string = str(self.hp) + "/" + str(self.maxhp)
        current_hp = ""

        if len(hp_string) < 9:
            decreased = 9 - len(hp_string)

            while decreased > 0:
                current_hp += " "
                decreased -= 1

            current_hp += hp_string
        else:
            current_hp = hp_string

        mp_string = str(self.mp) + "/" + str(self.maxmp)
        current_mp = ""

        if len(mp_string) < 7:
            decreased = 7 - len(mp_string)
            while decreased > 0:
                current_mp += " "
                decreased -= 1

            current_mp += mp_string

        else:
            current_mp = mp_string

        print("                     _________________________              __________ ")
        print(bcolors.BOLD + self.name + "    " +
              current_hp + " |" + bcolors.OKGREEN + hp_bar + bcolors.ENDC + "|    " +
              current_mp + " |" + bcolors.OKBLUE + mp_bar + bcolors.ENDC + "|")

    def choose_enemy_spell(self, rng=None):
        rng = rng or random
        pct = self.hp / self.maxhp * 100
        usable = [spell for spell in self.magic
                  if self.can_cast(spell)
                  and (spell.type != "white" or pct <= 50)]
        if not usable:
            return None, 0
        spell = usable[rng.randrange(0, len(usable))]
        return spell, spell.generate_damage(rng)
