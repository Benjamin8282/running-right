"""밸런스 시뮬레이터 — 메인 실행"""

from config import (
    effective_monster_hp, monsters_per_room, boss_room_monsters,
    rooms_per_stage, contact_damage, wall_mult, monster_hp,
    gold_per_monster, BOSS_HP_MULTIPLIER, OFFLINE,
)
from models import PlayerStats, simulate_stage
from economy import stage_gold_income, cumulative_gold_income, optimal_upgrade_path
from pity import monte_carlo_pity


def print_header(title: str):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def report_1_clear_time():
    """1. Stage 1~100 클리어 타임 곡선 (미강화 + 강화)"""
    print_header("1. 클리어 타임 곡선 (미강화 vs 강화)")

    stages = [1, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100]
    base_player = PlayerStats()

    print(f"\n{'Stage':>6} | {'벽':>4} | {'잡몹HP':>7} | {'미강화DPS':>9} | {'미강화클리어':>11} | "
          f"{'강화ATK':>7} | {'강화DPS':>8} | {'강화클리어':>10} | {'장비효과':>8}")
    print("-" * 105)

    cumulative = 0.0
    for s in stages:
        # 미강화
        result_raw = simulate_stage(s, base_player)

        # 누적 골드로 강화
        cumulative = cumulative_gold_income(1, s)
        upgraded = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")
        # 장비 효과 (평균 희귀 장비 가정)
        upgraded_eq = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")
        upgraded_eq.equipment_grade = "rare"
        result_up = simulate_stage(s, upgraded)
        result_eq = simulate_stage(s, upgraded_eq)

        print(f"{s:>6} | {'×'+str(wall_mult(s)):>4} | {effective_monster_hp(s):>7.1f} | "
              f"{result_raw.player_dps:>9.1f} | {result_raw.total_clear_time:>9.1f}초 | "
              f"{upgraded.effective_atk:>7.1f} | {result_up.player_dps:>8.1f} | "
              f"{result_up.total_clear_time:>8.1f}초 | {result_eq.total_clear_time:>6.1f}초")


def report_2_survival():
    """2. DPS vs HP — 생존/즉사 판정"""
    print_header("2. 생존 판정 (강화 기준)")

    stages = [1, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100]

    print(f"\n{'Stage':>6} | {'접촉뎀/초':>9} | {'기대HP':>7} | {'생존시간':>8} | "
          f"{'클리어시간':>10} | {'여유':>6} | {'판정':>4}")
    print("-" * 80)

    for s in stages:
        cumulative = cumulative_gold_income(1, s)
        upgraded = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")
        result = simulate_stage(s, upgraded)

        margin = result.survival_time - result.total_clear_time
        status = "✓ 안전" if result.can_survive else "✗ 위험"

        print(f"{s:>6} | {result.contact_dmg:>7.1f}/s | {upgraded.hp:>7.0f} | "
              f"{result.survival_time:>6.1f}초 | {result.total_clear_time:>8.1f}초 | "
              f"{margin:>+5.1f}s | {status}")


def report_3_gold_economy():
    """3. 골드 수입 vs 강화 비용"""
    print_header("3. 골드 경제 (수입 vs 강화)")

    stages = [1, 5, 10, 20, 30, 40, 50, 60, 80, 100]

    print(f"\n{'Stage':>6} | {'스테이지수입':>11} | {'누적수입':>10} | "
          f"{'ATK Lv':>7} | {'ATK값':>6} | {'HP Lv':>6} | {'HP값':>6}")
    print("-" * 75)

    for s in stages:
        income = stage_gold_income(s)
        cumulative = cumulative_gold_income(1, s)
        upgraded = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")

        print(f"{s:>6} | {income:>10,.0f}G | {cumulative:>9,.0f}G | "
              f"Lv{upgraded.levels['atk']:>4} | {upgraded.atk:>5.0f} | "
              f"Lv{upgraded.levels['hp']:>3} | {upgraded.hp:>5.0f}")


def report_4_equipment_impact():
    """4. 장비 등급별 DPS 영향"""
    print_header("4. 장비 등급별 DPS 영향 (Stage 50 기준)")

    cumulative = cumulative_gold_income(1, 50)
    base = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")

    grades = ["none", "common", "uncommon", "rare", "epic", "legendary", "mythic"]
    print(f"\n{'등급':>12} | {'실효ATK':>8} | {'DPS':>10} | {'클리어시간':>10} | {'DPS 증가':>9}")
    print("-" * 65)

    base_result = simulate_stage(50, base)
    for g in grades:
        import copy
        p = copy.deepcopy(base)
        p.equipment_grade = g
        result = simulate_stage(50, p)
        increase = (result.player_dps / base_result.player_dps - 1) * 100 if g != "none" else 0

        print(f"{g:>12} | {p.effective_atk:>8.1f} | {result.player_dps:>10.1f} | "
              f"{result.total_clear_time:>8.1f}초 | {increase:>+8.1f}%")


def report_5_pity():
    """5. Pity 시스템 몬테카를로 시뮬레이션"""
    print_header("5. Pity 시스템 시뮬레이션 (10만회, 100스테이지)")

    print("\n시뮬레이션 실행 중 (10만회)...")
    result = monte_carlo_pity(num_trials=100_000, num_stages=100)

    print(f"\n{'등급':>12} | {'기본확률':>8} | {'실제분포':>8}")
    print("-" * 40)
    base = {"common": 40.0, "uncommon": 30.0, "rare": 18.0, "epic": 9.0, "legendary": 2.5, "mythic": 0.5}
    for g in ["common", "uncommon", "rare", "epic", "legendary", "mythic"]:
        print(f"{g:>12} | {base[g]:>7.1f}% | {result['distribution'][g]:>7.2f}%")

    print(f"\n첫 영웅+ 획득까지 평균: {result['first_epic_avg']}스테이지")
    print(f"첫 전설 획득까지 평균: {result['first_legendary_avg']}스테이지")
    print(f"첫 신화 획득까지 평균: {result['first_mythic_avg']}스테이지")


def report_6_offline():
    """6. 오프라인 보상 시뮬레이션"""
    print_header("6. 오프라인 보상 (시간대별)")

    stages = [1, 10, 25, 50, 100]
    hours = [1, 2, 4, 8]

    print(f"\n{'Stage':>6} | {'골드/초':>8} | ", end="")
    for h in hours:
        print(f"{h}시간 보상  | ", end="")
    print()
    print("-" * 70)

    for s in stages:
        income = stage_gold_income(s)
        mobs = monsters_per_room(s)
        # 방당 클리어 시간 추정 (강화 기준)
        cumulative = cumulative_gold_income(1, s)
        upgraded = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")
        result = simulate_stage(s, upgraded)
        room_time = max(result.room_clear_time, 5.0)  # 최소 5초

        gold_per_sec = (mobs * gold_per_monster(s)) / room_time
        eff = OFFLINE["efficiency"]

        print(f"{s:>6} | {gold_per_sec:>6.1f}G/s | ", end="")
        for h in hours:
            reward = gold_per_sec * h * 3600 * eff
            print(f"{reward:>9,.0f}G | ", end="")
        print()


def report_7_wall_analysis():
    """7. 벽 구간 상세 분석"""
    print_header("7. 벽 구간 상세 분석")

    wall_stages = [9, 10, 11, 19, 20, 21, 34, 35, 36, 49, 50, 51, 79, 80, 81, 99, 100, 101]

    print(f"\n{'Stage':>6} | {'벽배율':>6} | {'실효HP':>8} | {'강화ATK':>7} | "
          f"{'DPS':>8} | {'클리어':>7} | {'생존':>6} | {'상태':>6}")
    print("-" * 80)

    for s in wall_stages:
        cumulative = cumulative_gold_income(1, s)
        upgraded = optimal_upgrade_path(cumulative, PlayerStats(), "atk_first")
        result = simulate_stage(s, upgraded)
        margin = result.survival_time - result.total_clear_time
        status = "✓" if result.can_survive else "✗ 위험"
        is_wall = "◆벽" if wall_mult(s) > 1.0 else ""

        print(f"{s:>6} | ×{wall_mult(s):>4.1f} | {effective_monster_hp(s):>8.1f} | "
              f"{upgraded.effective_atk:>7.1f} | {result.player_dps:>8.1f} | "
              f"{result.total_clear_time:>5.1f}초 | {result.survival_time:>4.1f}s | "
              f"{status} {is_wall}")


def main():
    print("=" * 80)
    print("  오른쪽 달리기 — 밸런스 시뮬레이터")
    print("  기획서: docs/design/01_core_loop.md")
    print("=" * 80)

    report_1_clear_time()
    report_2_survival()
    report_3_gold_economy()
    report_4_equipment_impact()
    report_5_pity()
    report_6_offline()
    report_7_wall_analysis()

    print_header("시뮬레이션 완료")
    print("\n모든 리포트가 출력되었습니다.")


if __name__ == "__main__":
    main()
