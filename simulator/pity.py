"""Pity 시스템 몬테카를로 시뮬레이션"""

import random
from config import DROP_BASE_RATES, PITY, MYTHIC_UNLOCK_STAGE, DROP_STAGE_BONUS_RATE

GRADES = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]
HIGH_GRADES = {"epic", "legendary", "mythic"}
LOW_RARE = {"common", "uncommon", "rare"}


def adjusted_drop_rates(stage: int) -> dict[str, float]:
    """스테이지 보정 적용된 드랍 확률"""
    rates = dict(DROP_BASE_RATES)

    # 신화 잠금
    if stage < MYTHIC_UNLOCK_STAGE:
        rates["mythic"] = 0.0

    # 스테이지 보정 — 상위 등급 비례 배분, 하위 등급 차감
    total_bonus = stage * DROP_STAGE_BONUS_RATE
    high_base_sum = sum(DROP_BASE_RATES[g] for g in ["epic", "legendary", "mythic"])
    low_base_sum = sum(DROP_BASE_RATES[g] for g in ["common", "uncommon"])

    if high_base_sum > 0:
        for g in ["epic", "legendary", "mythic"]:
            ratio = DROP_BASE_RATES[g] / high_base_sum
            rates[g] += total_bonus * ratio

        for g in ["common", "uncommon"]:
            ratio = DROP_BASE_RATES[g] / low_base_sum
            rates[g] -= total_bonus * ratio

    # 정규화 (합계 100%)
    total = sum(rates.values())
    if total > 0:
        rates = {k: v / total for k, v in rates.items()}

    return rates


def simulate_single_drop(stage: int, pity_counter: int, legendary_counter: int,
                         mythic_counter: int) -> tuple[str, int, int, int]:
    """단일 구슬 드랍 시뮬레이션 (Pity 적용)"""
    rates = adjusted_drop_rates(stage)

    # Soft Pity 보정
    if pity_counter >= PITY["soft_trigger"]:
        bonus = (pity_counter - PITY["soft_trigger"]) * PITY["soft_bonus_per_stack"]
        # 영웅+ 확률에 보너스 추가, common/uncommon에서 차감
        epic_plus = rates["epic"] + rates["legendary"] + rates["mythic"]
        new_epic_plus = min(epic_plus + bonus, 1.0)
        diff = new_epic_plus - epic_plus
        if diff > 0 and (rates["common"] + rates["uncommon"]) > diff:
            rates["epic"] += diff * (rates["epic"] / epic_plus) if epic_plus > 0 else diff
            ratio_c = rates["common"] / (rates["common"] + rates["uncommon"])
            ratio_u = 1 - ratio_c
            rates["common"] -= diff * ratio_c
            rates["uncommon"] -= diff * ratio_u

    # Hard Pity
    if pity_counter >= PITY["hard_pity"]:
        # 영웅 이상 확정
        for g in ["common", "uncommon", "rare"]:
            rates[g] = 0.0
        total = rates["epic"] + rates["legendary"] + rates["mythic"]
        if total > 0:
            rates = {k: (v / total if k in HIGH_GRADES else 0.0) for k, v in rates.items()}
        else:
            rates = {"epic": 1.0, **{g: 0.0 for g in GRADES if g != "epic"}}

    # 전설 Hard Pity
    if legendary_counter >= PITY["legendary_hard_pity"]:
        rates = {g: 0.0 for g in GRADES}
        rates["legendary"] = 0.7
        rates["mythic"] = 0.3

    # 신화 Hard Pity
    if mythic_counter >= PITY["mythic_hard_pity"]:
        rates = {g: 0.0 for g in GRADES}
        rates["mythic"] = 1.0

    # 확률 기반 드랍
    total = sum(rates.values())
    if total <= 0:
        return "common", 0, legendary_counter + 1, mythic_counter + 1

    r = random.random() * total
    cumulative = 0.0
    result = "common"
    for grade in GRADES:
        cumulative += rates[grade]
        if r <= cumulative:
            result = grade
            break

    # 카운터 업데이트
    new_pity = 0 if result in HIGH_GRADES else pity_counter + 1
    new_leg = 0 if result in {"legendary", "mythic"} else legendary_counter + 1
    new_myth = 0 if result == "mythic" else mythic_counter + 1

    return result, new_pity, new_leg, new_myth


def monte_carlo_pity(num_trials: int = 100_000, num_stages: int = 100,
                     start_stage: int = 1) -> dict:
    """몬테카를로 시뮬레이션으로 등급별 실제 획득 분포 계산"""
    counts = {g: 0 for g in GRADES}
    first_epic = []
    first_legendary = []
    first_mythic = []

    for _ in range(num_trials):
        pity = 0
        leg_counter = 0
        myth_counter = 0
        found_epic = False
        found_leg = False
        found_myth = False

        for stage in range(start_stage, start_stage + num_stages):
            grade, pity, leg_counter, myth_counter = simulate_single_drop(
                stage, pity, leg_counter, myth_counter
            )
            counts[grade] += 1

            if not found_epic and grade in HIGH_GRADES:
                first_epic.append(stage - start_stage + 1)
                found_epic = True
            if not found_leg and grade in {"legendary", "mythic"}:
                first_legendary.append(stage - start_stage + 1)
                found_leg = True
            if not found_myth and grade == "mythic":
                first_mythic.append(stage - start_stage + 1)
                found_myth = True

    total = sum(counts.values())
    distribution = {g: counts[g] / total * 100 for g in GRADES}

    def avg_or_na(lst):
        return round(sum(lst) / len(lst), 1) if lst else "N/A"

    return {
        "distribution": distribution,
        "first_epic_avg": avg_or_na(first_epic),
        "first_legendary_avg": avg_or_na(first_legendary),
        "first_mythic_avg": avg_or_na(first_mythic),
        "total_drops": total,
        "trials": num_trials,
    }
