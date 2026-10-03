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


class Person:
    def __init__(self, name, hp, mp, atk, df, magic, items):
        self.base_maxhp = max(0, hp)
        self.base_maxmp = max(0, mp)
        self.base_atk = atk
        self.base_df = df
        self.magic = magic
        self.items = items
        self.actions = ["Attack", "Magic", "Items", "Equip", "Flee"]
        self.name = name
        self.equipment = {}
        self.armory = []
        self.hp = self.base_maxhp
        self.mp = self.base_maxmp
        self._recalculate_stats()
        self.hp = min(max(hp, 0), self.maxhp)
        self.mp = min(max(mp, 0), self.maxmp)

    def _recalculate_stats(self):
        def bonus(attr):
            return sum(getattr(e, attr) for e in self.equipment.values())

        self.maxhp = max(0, self.base_maxhp + bonus("maxhp"))
        self.maxmp = max(0, self.base_maxmp + bonus("maxmp"))
        atk = self.base_atk + bonus("atk")
        self.atkl = atk - 10
        self.atkh = atk + 10
        self.df = self.base_df + bonus("df")
        self.clamp_stats()

    def clamp_stats(self):
        self.hp = min(max(self.hp, 0), self.maxhp)
        self.mp = min(max(self.mp, 0), self.maxmp)

    def is_alive(self):
        return self.hp > 0

    def equip(self, item):
        self.equipment[item.slot] = item
        self._recalculate_stats()

    def unequip(self, slot):
        if slot in self.equipment:
            del self.equipment[slot]
            self._recalculate_stats()

    def generate_damage(self):
        low = min(self.atkl, self.atkh)
        high = max(self.atkl, self.atkh)
        return random.randrange(low, high + 1)

    def take_damage(self, dmg):
        dmg = max(0, dmg)
        self.hp -= dmg
        if self.hp < 0:
            self.hp = 0
        return self.hp

    def heal(self, dmg):
        self.hp += max(0, dmg)
        if self.hp > self.maxhp:
            self.hp = self.maxhp

    def full_restore(self):
        self.hp = self.maxhp
        self.mp = self.maxmp

    def get_hp(self):
        return self.hp

    def get_max_hp(self):
        return self.maxhp

    def get_mp(self):
        return self.mp

    def get_max_mp(self):
        return self.maxmp

    def reduce_mp(self, cost):
        self.mp -= max(0, cost)
        if self.mp < 0:
            self.mp = 0

    def restore_mp(self, amount):
        self.mp += max(0, amount)
        if self.mp > self.maxmp:
            self.mp = self.maxmp

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
            print("        " + str(i) + ".", item["item"].name + ":", item["item"].description,
                  " (x" + str(item["quantity"]) + ")")
            i += 1

    def choose_equipment(self):
        i = 1

        print("\n" + bcolors.WARNING + bcolors.BOLD + "    EQUIPMENT:" + bcolors.ENDC)
        for eq in self.armory:
            print("        " + str(i) + ".", eq.name + ":", eq.description)
            i += 1

    def choose_target(self, enemies):
        targets = [e for e in enemies if e.is_alive()]
        if not targets:
            return None
        i = 1

        print("\n" + bcolors.FAIL + bcolors.BOLD + "    TARGET:" + bcolors.ENDC)
        for enemy in targets:
            print("        " + str(i) + ".", enemy.name)
            i += 1
        while True:
            try:
                choice = int(input("    Choose target:")) - 1
            except ValueError:
                continue
            if 0 <= choice < len(targets):
                return targets[choice]

    def get_enemy_stats(self):
        hp_bar = ""
        bar_ticks = (self.hp / self.maxhp) * 100 / 2 if self.maxhp > 0 else 0

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
        bar_ticks = (self.hp / self.maxhp) * 100 / 4 if self.maxhp > 0 else 0

        mp_bar = ""
        mp_ticks = (self.mp / self.maxmp) * 100 / 10 if self.maxmp > 0 else 0

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

    def choose_enemy_spell(self):
        pct = self.hp / self.maxhp * 100 if self.maxhp > 0 else 0
        castable = [s for s in self.magic
                    if s.cost <= self.mp and not (s.type == "white" and pct > 50)]
        if not castable:
            return None
        spell = castable[random.randrange(0, len(castable))]
        return spell, spell.generate_damage()
