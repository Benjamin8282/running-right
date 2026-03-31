"""골드 경제 시뮬레이션 — 수입/지출/강화 최적화"""

from config import (
    upgrade_cost, cumulative_upgrade_cost, UPGRADES,
    gold_per_monster, monsters_per_room, boss_room_monsters,
    rooms_per_stage, BOSS_GOLD_MULTIPLIER, EQUIPMENT_SELL_PRICE,
)
from models import PlayerStats


def stage_gold_income(stage: int) -> float:
    """한 스테이지 전체 골드 수입"""
    rooms = rooms_per_stage(stage)
    normal_rooms = rooms - 1
    mobs = monsters_per_room(stage)
    boss_mobs = boss_room_monsters(stage)
    gold = gold_per_monster(stage)

    normal_gold = normal_rooms * mobs * gold
    boss_mob_gold = boss_mobs * gold
    boss_orb_gold = gold * BOSS_GOLD_MULTIPLIER
    return normal_gold + boss_mob_gold + boss_orb_gold


def cumulative_gold_income(from_stage: int, to_stage: int) -> float:
    """스테이지 범위 누적 골드 수입"""
    return sum(stage_gold_income(s) for s in range(from_stage, to_stage + 1))


def optimal_upgrade_path(total_gold: float, player: PlayerStats, priority: str = "atk_first") -> PlayerStats:
    """
    주어진 골드로 최적 강화 수행.
    priority:
      - "atk_first": ATK 70%, HP 20%, 나머지 10%
      - "balanced": 각 스탯 균등
      - "survival": HP 50%, ATK 30%, 나머지 20%
    """
    import copy
    p = copy.deepcopy(player)

    if priority == "atk_first":
        budget = {"atk": 0.60, "hp": 0.25, "atk_speed": 0.05, "crit_rate": 0.05, "crit_dmg": 0.05}
    elif priority == "survival":
        budget = {"atk": 0.30, "hp": 0.50, "atk_speed": 0.05, "crit_rate": 0.05, "crit_dmg": 0.10}
    else:  # balanced
        budget = {"atk": 0.30, "hp": 0.30, "atk_speed": 0.15, "crit_rate": 0.10, "crit_dmg": 0.15}

    for stat, ratio in budget.items():
        remaining = total_gold * ratio
        while remaining > 0:
            cost = upgrade_cost(stat, p.levels[stat])
            if cost > remaining:
                break
            u = UPGRADES[stat]
            if u["max_val"] is not None:
                current = getattr(p, stat if stat != "crit_rate" else "crit_rate")
                if stat == "atk_speed" and p.atk_speed >= u["max_val"]:
                    break
                if stat == "crit_rate" and p.crit_rate >= u["max_val"]:
                    break
                if stat == "crit_dmg" and p.crit_dmg >= u["max_val"]:
                    break
                if stat == "move_speed" and p.move_speed >= u["max_val"]:
                    break
            remaining -= cost
            p.upgrade(stat)

    return p


def gold_economy_report(max_stage: int = 100) -> list[dict]:
    """스테이지별 골드 수입/강화 비용 리포트"""
    results = []
    cumulative = 0.0
    player = PlayerStats()

    for stage in range(1, max_stage + 1):
        income = stage_gold_income(stage)
        cumulative += income

        # 현재 누적 골드로 최적 강화
        upgraded = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")

        results.append({
            "stage": stage,
            "stage_income": round(income),
            "cumulative_income": round(cumulative),
            "upgraded_atk": round(upgraded.atk, 1),
            "upgraded_hp": round(upgraded.hp, 1),
            "upgraded_atk_speed": round(upgraded.atk_speed, 2),
            "upgraded_crit_rate": round(upgraded.crit_rate * 100, 1),
            "atk_level": upgraded.levels["atk"],
            "hp_level": upgraded.levels["hp"],
        })

    return results
