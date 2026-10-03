from classes.battle import Battle, BattleState
from classes.game import Person, bcolors
from classes.inventory import Item
from classes.magic import Spell


class InputClosed(Exception):
    pass


def read_index(prompt, count):
    while True:
        try:
            choice = input(prompt)
        except EOFError:
            raise InputClosed()
        try:
            index = int(choice) - 1
        except ValueError:
            continue
        if -1 <= index < count:
            return index


def choose_target(enemies):
    alive = [enemy for enemy in enemies if enemy.is_alive()]
    i = 1

    print("\n" + bcolors.FAIL + bcolors.BOLD + "    TARGET:" + bcolors.ENDC)
    for enemy in alive:
        print("        " + str(i) + ".", enemy.name)
        i += 1
    index = read_index("    Choose target:", len(alive))
    if index < 0:
        return None
    return alive[index]


def build_battle():
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

    # Equipment
    sword = Item("Sword", "weapon", "Boosts attack by 15", 15)
    shield = Item("Shield", "armor", "Boosts defense by 10", 10)


    player_spells = [fire, thunder, blizzard, meteor, cure, cura]
    enemy_spells = [fire, meteor, curaga]
    player_items = [{"item": potion, "quantity": 15}, {"item": hipotion, "quantity": 5},
                    {"item": superpotion, "quantity": 5}, {"item": elixer, "quantity": 5},
                    {"item": hielixer, "quantity": 2}, {"item": grenade, "quantity": 5},
                    {"item": sword, "quantity": 1}, {"item": shield, "quantity": 1}]


    # Instantiate People
    player1 = Person("Valos:", 3260, 132, 300, 34, player_spells, player_items)
    player2 = Person("Nick :", 4160, 188, 311, 34, player_spells, player_items)
    player3 = Person("Robot:", 3089, 174, 288, 34, player_spells, player_items)

    enemy1 = Person("Imp  ", 1250, 130, 560, 325, enemy_spells, [])
    enemy2 = Person("Magus", 18200, 701, 525, 25, enemy_spells, [])
    enemy3 = Person("Imp  ", 1250, 130, 560, 325, enemy_spells, [])


    players = [player1, player2, player3]
    enemies = [enemy1, enemy2, enemy3]

    return Battle(players, enemies)


def report_killed(result):
    if result.killed is not None:
        print(result.killed.name.replace(" ", "") + " has died.")


def player_turn(battle, player):
    while True:
        player.choose_action()
        index = read_index("    Choose action: ", len(player.actions))
        if index < 0:
            return

        if index == 0:
            target = choose_target(battle.enemies)
            if target is None:
                continue
            result = battle.attack(player, target)
            print("You attacked " + target.name.replace(" ", "") + " for",
                  result.meta["damage"], "points of damage.")
            report_killed(result)
            return

        elif index == 1:
            player.choose_magic()
            magic_choice = read_index("    Choose magic: ", len(player.magic))

            if magic_choice == -1:
                return

            spell = player.magic[magic_choice]

            if spell.cost > player.get_mp():
                print(bcolors.FAIL + "\nNot enough MP\n" + bcolors.ENDC)
                return

            if spell.type == "white":
                result = battle.cast(player, spell)
                print(bcolors.OKBLUE + "\n" + spell.name + " heals for",
                      str(result.healed), "HP." + bcolors.ENDC)
            elif spell.type == "black":
                target = choose_target(battle.enemies)
                if target is None:
                    continue
                result = battle.cast(player, spell, target)
                print(bcolors.OKBLUE + "\n" + spell.name + " deals", str(result.meta["damage"]),
                      "points of damage to " + target.name.replace(" ", "") + bcolors.ENDC)
                report_killed(result)
            return

        elif index == 2:
            player.choose_item()
            item_choice = read_index("    Choose item: ", len(player.items))

            if item_choice == -1:
                return

            entry = player.items[item_choice]
            item = entry["item"]

            if entry["quantity"] <= 0:
                print(bcolors.FAIL + "\n" + "None left..." + bcolors.ENDC)
                return

            if item.type == Item.POTION:
                result = battle.use_item(player, entry)
                if not result:
                    print(bcolors.FAIL + "\n" + result.message + bcolors.ENDC)
                    return
                print(bcolors.OKGREEN + "\n" + item.name + " heals for",
                      str(result.healed), "HP" + bcolors.ENDC)
            elif item.type == Item.ELIXER:
                result = battle.use_item(player, entry)
                if not result:
                    print(bcolors.FAIL + "\n" + result.message + bcolors.ENDC)
                    return
                print(bcolors.OKGREEN + "\n" + item.name + " fully restores HP/MP" + bcolors.ENDC)
            elif item.type == Item.ATTACK:
                target = choose_target(battle.enemies)
                if target is None:
                    continue
                result = battle.use_item(player, entry, target)
                print(bcolors.FAIL + "\n" + item.name + " deals", str(result.meta["damage"]),
                      "points of damage to " + target.name + bcolors.ENDC)
                report_killed(result)
            elif item.type in (Item.WEAPON, Item.ARMOR):
                result = battle.equip(player, entry)
                if not result:
                    print(bcolors.FAIL + "\n" + result.message + bcolors.ENDC)
                    return
                print(bcolors.OKGREEN + "\n" + player.name.replace(" ", "") + " equipped " +
                      item.name + bcolors.ENDC)
            return

        elif index == 3:
            result = battle.flee(player)
            if result.fled:
                print(bcolors.WARNING + "\nYou fled the battle!" + bcolors.ENDC)
            else:
                print(bcolors.FAIL + "\nCouldn't escape!" + bcolors.ENDC)
            return


def enemy_turn(battle):
    battle.state = BattleState.ENEMY_TURN
    for enemy in list(battle.alive_enemies()):
        if battle.over:
            break
        result = battle.enemy_take_turn(enemy)
        if not result:
            continue
        if result.spell is not None:
            spell = result.spell
            if spell.type == "white":
                print(bcolors.OKBLUE + spell.name + " heals " + enemy.name + " for",
                      str(result.healed), "HP." + bcolors.ENDC)
            else:
                target = result.meta["target"]
                print(bcolors.OKBLUE + "\n" + enemy.name.replace(" ", "") + "'s " + spell.name +
                      " deals", str(result.meta["damage"]), "points of damage to " +
                      target.name.replace(" ", "") + bcolors.ENDC)
                report_killed(result)
        else:
            target = result.meta["target"]
            print(enemy.name.replace(" ", "") + " attacks " + target.name.replace(" ", "") +
                  " for", result.meta["damage"])
            report_killed(result)
    if not battle.over:
        battle.state = BattleState.PLAYER_TURN


def play(battle):
    print(bcolors.FAIL + bcolors.BOLD + "AN ENEMY ATTACKS!" + bcolors.ENDC)

    while not battle.over:
        print("======================")

        print("\n\n")
        print("NAME                 HP                                     MP")
        for player in battle.players:
            player.get_stats()

        print("\n")

        for enemy in battle.enemies:
            enemy.get_enemy_stats()

        try:
            for player in battle.alive_players():
                if battle.over:
                    break
                player_turn(battle, player)
        except InputClosed:
            return battle.state

        if battle.over:
            break

        print("\n")
        # Enemy attack phase
        enemy_turn(battle)

    if battle.state == BattleState.WON:
        print(bcolors.OKGREEN + "You win!" + bcolors.ENDC)
    elif battle.state == BattleState.LOST:
        print(bcolors.FAIL + "Your enemies have defeated you!" + bcolors.ENDC)
    return battle.state


if __name__ == "__main__":
    play(build_battle())
