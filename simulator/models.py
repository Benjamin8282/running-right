"""플레이어, 전투, 스테이지 모델"""

from dataclasses import dataclass, field
from config import (
    PLAYER, COMBO_CYCLE_TIME, COMBO_TOTAL_MULT, SKILL, UPGRADES,
    EQUIPMENT_ATK_BONUS, monster_hp, wall_mult, effective_monster_hp,
    monsters_per_room, boss_room_monsters, rooms_per_stage,
    contact_damage, gold_per_monster, BOSS_GOLD_MULTIPLIER, BOSS_HP_MULTIPLIER,
)


@dataclass
class PlayerStats:
    hp: float = PLAYER["base_hp"]
    atk: float = PLAYER["base_atk"]
    atk_speed: float = PLAYER["base_atk_speed"]
    crit_rate: float = PLAYER["base_crit_rate"]
    crit_dmg: float = PLAYER["base_crit_dmg"]
    move_speed: float = PLAYER["base_move_speed"]

    # 강화 레벨 추적
    levels: dict = field(default_factory=lambda: {
        "atk": 0, "hp": 0, "atk_speed": 0,
        "crit_rate": 0, "crit_dmg": 0, "move_speed": 0,
    })

    # 장비
    equipment_grade: str = "none"

    @property
    def equipment_atk_bonus(self) -> float:
        if self.equipment_grade == "none":
            return 0.0
        return EQUIPMENT_ATK_BONUS.get(self.equipment_grade, 0.0)

    @property
    def effective_atk(self) -> float:
        return self.atk * (1 + self.equipment_atk_bonus)

    @property
    def combo_dps(self) -> float:
        """평타 DPS (치명타 미포함)"""
        cycle_time = COMBO_CYCLE_TIME / self.atk_speed
        return (COMBO_TOTAL_MULT / cycle_time) * self.effective_atk

    @property
    def skill_dps(self) -> float:
        """돌풍베기 DPS"""
        return (SKILL["dmg_mult"] / SKILL["cooldown"]) * self.effective_atk

    @property
    def crit_multiplier(self) -> float:
        """치명타 기대값 보정"""
        return 1 + self.crit_rate * (self.crit_dmg - 1)

    @property
    def total_dps(self) -> float:
        """실효 복합 DPS (치명타 포함)"""
        return (self.combo_dps + self.skill_dps) * self.crit_multiplier

    def upgrade(self, stat: str):
        """스탯 1레벨 강화"""
        u = UPGRADES[stat]
        self.levels[stat] += 1

        if stat == "atk":
            self.atk += u["per_level"]
        elif stat == "hp":
            self.hp += u["per_level"]
        elif stat == "atk_speed":
            self.atk_speed = min(self.atk_speed + u["per_level"], u["max_val"])
        elif stat == "crit_rate":
            self.crit_rate = min(self.crit_rate + u["per_level"], u["max_val"])
        elif stat == "crit_dmg":
            self.crit_dmg = min(self.crit_dmg + u["per_level"], u["max_val"])
        elif stat == "move_speed":
            self.move_speed = min(self.move_speed + u["per_level"], u["max_val"])


@dataclass
class StageResult:
    stage: int
    rooms: int
    mob_hp: float
    wall_multiplier: float
    effective_hp: float
    mobs_per_room: int
    boss_room_mobs: int
    boss_grade: str
    boss_hp: float

    player_dps: float
    player_hp: float
    player_atk: float

    room_clear_time: float  # 잡몹 방 1개 클리어 시간
    boss_room_clear_time: float  # 보스 방 클리어 시간 (잡몹 + 구슬)
    total_clear_time: float  # 스테이지 전체

    contact_dmg: float
    survival_time: float  # HP / (contact_dmg * 동시접촉 추정)
    can_survive: bool

    gold_earned: float  # 스테이지 전체 골드


def simulate_stage(stage: int, player: PlayerStats, boss_grade: str = "common") -> StageResult:
    """단일 스테이지 시뮬레이션"""
    rooms = rooms_per_stage(stage)
    mob_hp_base = monster_hp(stage)
    wm = wall_mult(stage)
    eff_hp = mob_hp_base * wm
    mobs = monsters_per_room(stage)
    boss_mobs = boss_room_monsters(stage)
    boss_hp_val = mob_hp_base * BOSS_HP_MULTIPLIER.get(boss_grade, 5)

    dps = player.total_dps
    cdmg = contact_damage(stage)

    # 잡몹 방 클리어 시간
    total_mob_hp_room = eff_hp * mobs
    combat_time = total_mob_hp_room / dps if dps > 0 else float("inf")
    num_hordes = 2.5  # 평균 무리 수
    move_time = num_hordes * 0.6 + 0.3  # 달리기 + 클리어 딜레이
    room_clear = combat_time + move_time

    # 보스 방 클리어 시간
    boss_mob_hp_total = eff_hp * boss_mobs
    boss_mob_time = boss_mob_hp_total / dps if dps > 0 else float("inf")
    boss_orb_time = boss_hp_val / dps if dps > 0 else float("inf")
    boss_room_clear = boss_mob_time + boss_orb_time + move_time

    # 전체 클리어 시간
    normal_rooms = rooms - 1
    total_clear = normal_rooms * room_clear + boss_room_clear

    # 생존 판정 (평균 3마리 동시 접촉 가정)
    avg_contact_mobs = min(3, mobs)
    effective_cdmg = cdmg * avg_contact_mobs
    survival = player.hp / effective_cdmg if effective_cdmg > 0 else float("inf")
    can_survive = survival > total_clear

    # 골드
    gold_per_mob = gold_per_monster(stage)
    normal_gold = normal_rooms * mobs * gold_per_mob
    boss_mob_gold = boss_mobs * gold_per_mob
    boss_orb_gold = gold_per_mob * BOSS_GOLD_MULTIPLIER
    total_gold = normal_gold + boss_mob_gold + boss_orb_gold

    return StageResult(
        stage=stage, rooms=rooms,
        mob_hp=mob_hp_base, wall_multiplier=wm, effective_hp=eff_hp,
        mobs_per_room=mobs, boss_room_mobs=boss_mobs,
        boss_grade=boss_grade, boss_hp=boss_hp_val,
        player_dps=dps, player_hp=player.hp, player_atk=player.effective_atk,
        room_clear_time=room_clear, boss_room_clear_time=boss_room_clear,
        total_clear_time=total_clear,
        contact_dmg=cdmg, survival_time=survival, can_survive=can_survive,
        gold_earned=total_gold,
    )
