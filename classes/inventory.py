class Item:
    POTION = "potion"
    ELIXER = "elixer"
    ATTACK = "attack"
    WEAPON = "weapon"
    ARMOR = "armor"

    def __init__(self, name, type, description, prop):
        self.name = name
        self.type = type
        self.description = description
        self.prop = prop
