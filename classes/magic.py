import random


class Spell:
    BLACK = "black"
    WHITE = "white"

    def __init__(self, name, cost, dmg, type):
        self.name = name
        self.cost = max(0, cost)
        self.dmg = max(0, dmg)
        self.type = type

    def generate_damage(self, rng=None):
        rng = rng or random
        low = self.dmg - 15
        high = self.dmg + 15
        if high <= low:
            return max(0, self.dmg)
        return rng.randrange(max(0, low), high)
