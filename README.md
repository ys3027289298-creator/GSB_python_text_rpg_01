## RPG Battle
##### A python implementation of a text based/terminal battle game

Ended up having to rewrite a good portion of it, so I've improved quite a bit of it.  Now with awesome HP/MP bars, multiple enemies and party members, and items.

![Alt text](/images/rpgbattle-screen.png?raw=true "2017 update")

## Project layout

- `main.py` — game entry point and terminal UI (prompts/keys unchanged; `4. Equip` and `5. Flee` added)
- `classes/game.py` — `Person`, `bcolors`
- `classes/magic.py` — `Spell`
- `classes/inventory.py` — `Item`
- `classes/equipment.py` — `Equipment` (weapon/armor/shield stat bonuses)
- `classes/battle.py` — reusable battle-resolution state machine (`Battle`, `BattleState`)

## Tests

    python3 -m unittest discover -s tests -v

Covers simultaneous death of both sides, consecutive flee attempts, using items
from an empty inventory, negative attributes, equipment switching, and proves
`0 <= hp <= maxhp` / `0 <= mp <= maxmp` for every combatant after every
battle settlement.
