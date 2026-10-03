from classes.game import Person, bcolors
from classes.magic import Spell
from classes.inventory import Item
from classes.equipment import Equipment
from classes.battle import Battle, BattleState
import random


# Create Black Magic
fire = Spell("Fire", 25, 600, "black")
thunder = Spell("Thunder", 25, 600, "black")
blizzard = Spell("Blizzard", 25, 600, "black")
meteor = Spell("Meteor", 40, 1200, "black")
quake = Spell("Quake", 14, 140, "black")

# Create White Magic
cure = Spell("Cure", 25, 620, "white")
cura = Spell("Cura", 32, 1500, "white")
curaga = Spell("Curaga", 50, 6000, "white")


# Create some Items
potion = Item("Potion", "potion", "Heals 50 HP", 50)
hipotion = Item("Hi-Potion", "potion", "Heals 100 HP", 100)
superpotion = Item("Super Potion", "potion", "Heals 1000 HP", 1000)
elixer = Item("Elixer", "elixer", "Fully restores HP/MP of one party member", 9999)
hielixer = Item("MegaElixer", "elixer", "Fully restores party's HP/MP", 9999)

grenade = Item("Grenade", "attack", "Deals 500 damage", 500)


# Create some Equipment
iron_sword = Equipment("Iron Sword", "weapon", "Atk +20", atk=20)
steel_sword = Equipment("Steel Sword", "weapon", "Atk +45", atk=45)
leather_armor = Equipment("Leather Armor", "armor", "Def +10", df=10)
iron_shield = Equipment("Iron Shield", "shield", "Def +25", df=25)


player_spells = [fire, thunder, blizzard, meteor, cure, cura]
enemy_spells = [fire, meteor, curaga]
player_items = [{"item": potion, "quantity": 15}, {"item": hipotion, "quantity": 5},
                {"item": superpotion, "quantity": 5}, {"item": elixer, "quantity": 5},
                {"item": hielixer, "quantity": 2}, {"item": grenade, "quantity": 5}]


def read_index(prompt):
    while True:
        try:
            return int(input(prompt)) - 1
        except ValueError:
            continue


# Instantiate People
player1 = Person("Valos:", 3260, 132, 300, 34, player_spells, player_items)
player2 = Person("Nick :", 4160, 188, 311, 34, player_spells, player_items)
player3 = Person("Robot:", 3089, 174, 288, 34, player_spells, player_items)

for player in (player1, player2, player3):
    player.armory = [iron_sword, steel_sword, leather_armor, iron_shield]

enemy1 = Person("Imp  ", 1250, 130, 560, 325, enemy_spells, [])
enemy2 = Person("Magus", 18200, 701, 525, 25, enemy_spells, [])
enemy3 = Person("Imp  ", 1250, 130, 560, 325, enemy_spells, [])


players = [player1, player2, player3]
enemies = [enemy1, enemy2, enemy3]

battle = Battle(players, enemies)

print(bcolors.FAIL + bcolors.BOLD + "AN ENEMY ATTACKS!" + bcolors.ENDC)

while not battle.is_over:
    print("======================")

    print("\n\n")
    print("NAME                 HP                                     MP")
    for player in players:
        player.get_stats()

    print("\n")

    for enemy in battle.living_enemies():
        enemy.get_enemy_stats()

    fled = False

    for player in players:
        if battle.is_over:
            break
        if not player.is_alive():
            continue

        player.choose_action()
        index = read_index("    Choose action: ")

        if index == 0:
            enemy = player.choose_target(enemies)
            if enemy is None:
                continue

            dmg = battle.attack(player, enemy)
            print("You attacked " + enemy.name.replace(" ", "") + " for", dmg, "points of damage.")

            if enemy.get_hp() == 0:
                print(enemy.name.replace(" ", "") + " has died.")

        elif index == 1:
            player.choose_magic()
            magic_choice = read_index("    Choose magic: ")

            if magic_choice == -1:
                continue
            if not 0 <= magic_choice < len(player.magic):
                continue

            spell = player.magic[magic_choice]

            if spell.cost > player.get_mp():
                print(bcolors.FAIL + "\nNot enough MP\n" + bcolors.ENDC)
                continue

            if spell.type == "white":
                magic_dmg = battle.cast_spell(player, spell)
                print(bcolors.OKBLUE + "\n" + spell.name + " heals for", str(magic_dmg), "HP." + bcolors.ENDC)
            elif spell.type == "black":
                enemy = player.choose_target(enemies)
                if enemy is None:
                    continue

                magic_dmg = battle.cast_spell(player, spell, enemy)
                print(bcolors.OKBLUE + "\n" + spell.name + " deals", str(magic_dmg),
                      "points of damage to " + enemy.name.replace(" ", "") + bcolors.ENDC)

                if enemy.get_hp() == 0:
                    print(enemy.name.replace(" ", "") + " has died.")

        elif index == 2:
            player.choose_item()
            item_choice = read_index("    Choose item: ")

            if item_choice == -1:
                continue
            if not 0 <= item_choice < len(player.items):
                continue

            entry = player.items[item_choice]
            item = entry["item"]

            if entry["quantity"] <= 0:
                print(bcolors.FAIL + "\n" + "None left..." + bcolors.ENDC)
                continue

            if item.type == "potion":
                if not battle.use_item(player, entry):
                    print(bcolors.FAIL + "\nHP is already full." + bcolors.ENDC)
                    continue
                print(bcolors.OKGREEN + "\n" + item.name + " heals for", str(item.prop), "HP" + bcolors.ENDC)
            elif item.type == "elixer":
                battle.use_item(player, entry, party=players)
                print(bcolors.OKGREEN + "\n" + item.name + " fully restores HP/MP" + bcolors.ENDC)
            elif item.type == "attack":
                enemy = player.choose_target(enemies)
                if enemy is None:
                    continue
                battle.use_item(player, entry, target=enemy)
                print(bcolors.FAIL + "\n" + item.name + " deals", str(item.prop),
                      "points of damage to " + enemy.name + bcolors.ENDC)

                if enemy.get_hp() == 0:
                    print(enemy.name.replace(" ", "") + " has died.")

        elif index == 3:
            player.choose_equipment()
            equip_choice = read_index("    Choose equipment: ")

            if equip_choice == -1:
                continue
            if not 0 <= equip_choice < len(player.armory):
                continue

            equipment = player.armory[equip_choice]
            battle.equip(player, equipment)
            print(bcolors.WARNING + "\n" + player.name.replace(" ", "") + " equipped " + equipment.name + bcolors.ENDC)

        elif index == 4:
            if battle.flee(player):
                print(bcolors.WARNING + "\nYou ran away!" + bcolors.ENDC)
                fled = True
                break
            else:
                print(bcolors.FAIL + "\nCouldn't escape!" + bcolors.ENDC)

    if battle.is_over or fled:
        break

    print("\n")
    # Enemy attack phase
    battle.state = BattleState.ENEMY_PHASE
    for enemy in battle.living_enemies():
        if battle.is_over:
            break
        targets = battle.living_players()
        if not targets:
            break

        enemy_choice = random.randrange(0, 2)

        if enemy_choice == 0:
            # Chose attack
            target = random.choice(targets)
            enemy_dmg = battle.attack(enemy, target)
            print(enemy.name.replace(" ", "") + " attacks " + target.name.replace(" ", "") + " for", enemy_dmg)

            if target.get_hp() == 0:
                print(target.name.replace(" ", "") + " has died.")

        elif enemy_choice == 1:
            chosen = enemy.choose_enemy_spell()
            if chosen is None:
                target = random.choice(targets)
                enemy_dmg = battle.attack(enemy, target)
                print(enemy.name.replace(" ", "") + " attacks " + target.name.replace(" ", "") + " for", enemy_dmg)

                if target.get_hp() == 0:
                    print(target.name.replace(" ", "") + " has died.")
                continue

            spell, _ = chosen

            if spell.type == "white":
                magic_dmg = battle.cast_spell(enemy, spell)
                print(bcolors.OKBLUE + spell.name + " heals " + enemy.name + " for", str(magic_dmg), "HP." + bcolors.ENDC)
            elif spell.type == "black":
                target = random.choice(targets)
                magic_dmg = battle.cast_spell(enemy, spell, target)
                print(bcolors.OKBLUE + "\n" + enemy.name.replace(" ", "") + "'s " + spell.name + " deals",
                      str(magic_dmg), "points of damage to " + target.name.replace(" ", "") + bcolors.ENDC)

                if target.get_hp() == 0:
                    print(target.name.replace(" ", "") + " has died.")

    if not battle.is_over:
        battle.state = BattleState.PLAYER_PHASE

if battle.state == BattleState.VICTORY:
    print(bcolors.OKGREEN + "You win!" + bcolors.ENDC)
elif battle.state == BattleState.DEFEAT:
    print(bcolors.FAIL + "Your enemies have defeated you!" + bcolors.ENDC)
elif battle.state == BattleState.FLED:
    print(bcolors.WARNING + "You escaped the battle." + bcolors.ENDC)
