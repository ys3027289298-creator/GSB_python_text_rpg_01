# 复现记录：原始战斗逻辑的边界错误

复现方式：原始代码（git HEAD）中 `main.py` 引用 `from classes.game import ...`，
但 `game.py / magic.py / inventory.py` 平铺在仓库根目录，直接运行即
`ModuleNotFoundError: No module named 'classes'`。将三个模块原样放进
临时 `classes/` 包后，喂入脚本化输入即可触发以下错误。

1. **失败后继续下一步（结算顺序）**：所有玩家阵亡后打印
   `Your enemies have defeated you!`，但同回合敌方攻击阶段继续执行，
   敌人继续攻击；胜利判定同样硬编码为 `defeated_enemies == 2`。
2. **结算数量错误**：敌人死亡即被 `del`，之后按 `hp == 0` 计数恒为 0，
   3 个敌人全灭时永远不会出现 `You win!`，空列表后继续要求选目标直到 EOF 崩溃。
3. **错误删除玩家**：敌方黑魔击杀玩家时执行 `del players[player]`，
   `player` 是循环变量（Person 对象），触发
   `TypeError: list indices must be integers or slices, not Person`。
4. **敌方施法分支**：`choose_enemy_spell` 递归调用丢弃返回值，无可用法术时
   返回 `None` → `cannot unpack non-iterable NoneType`；MP 不足时还会无限递归
   直到 `RecursionError`。实测喂输入 1 轮即崩溃。
5. **MP 下限**：`reduce_mp` 不夹取，MP 可为负数（9999 消耗后得到 -9989）。
6. **零防御 / 高防御**：`df` 属性从未参与伤害计算；旧逻辑也无法保证
   `伤害 - 防御` 不为负（负伤害等于治疗）。
7. **空背包 / 重复喝药**：空物品列表直接 `player.items[0]` → `IndexError`；
   数量判断是 `== 0`，`-1` 也能通过并继续减到 `-2`；满血喝药照样消耗。
8. **低血量**：MegaElixer 对 `hp == 0` 的死者直接回满，等于复活；
   治疗量不夹取。
9. **目标索引错位**：`choose_target` 打印时过滤死亡敌人，但返回的序号用于
   原始完整列表，死后目标指向错误敌人；敌方 `randrange(0, 3)` 硬编码，
   可能选中已死亡玩家。
10. **切换装备 / 逃跑**：原代码没有这两个功能，无法处理换装对攻防属性的
    影响，也无法处理逃跑失败后的回合归属。

修复后对应回归测试见 `tests/test_battle.py`（`python3 -m unittest discover -s tests`）。
