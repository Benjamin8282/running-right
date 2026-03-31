"""기획서 YAML 파라미터 → Python 설정"""

import math

# === 캐릭터 ===
PLAYER = {
    "base_hp": 100,
    "base_atk": 10,
    "base_atk_speed": 1.0,
    "base_crit_rate": 0.15,
    "base_crit_dmg": 1.5,
    "base_move_speed": 6.0,
    "max_move_speed": 15.0,
}

COMBO = {
    "hit_1": {"dmg_mult": 1.0, "delay": 0.25},
    "hit_2": {"dmg_mult": 1.1, "delay": 0.30},
    "hit_3": {"dmg_mult": 1.5, "delay": 0.40},
    "reset_delay": 0.20,
}
COMBO_CYCLE_TIME = sum(h["delay"] for h in [COMBO["hit_1"], COMBO["hit_2"], COMBO["hit_3"]]) + COMBO["reset_delay"]
COMBO_TOTAL_MULT = sum(h["dmg_mult"] for h in [COMBO["hit_1"], COMBO["hit_2"], COMBO["hit_3"]])

SKILL = {
    "cooldown": 5.0,
    "dmg_mult": 3.5,
    "range": (6.0, 3.0),
}

# === 몬스터 ===
MONSTER = {
    "base_hp": 20,
    "hp_scale_per_stage": 0.15,  # (stage-1) * 0.15
    "move_speed": 2.5,
    "rush_speed": 3.5,
    "contact_damage_base": 2,
    "contact_damage_scale": 0.05,  # (stage-1) * 0.05 (완화)
}

BOSS_HP_MULTIPLIER = {
    "common": 5,
    "uncommon": 8,
    "rare": 12,
    "epic": 18,
    "legendary": 25,
    "mythic": 35,
}

BOSS_GOLD_MULTIPLIER = 10

# === 벽 배율 ===
WALL_MULTIPLIER = {
    10: 1.3,
    20: 1.4,
    35: 1.5,
    50: 1.7,
    80: 1.8,
    100: 2.0,
}

# === 방/스테이지 ===
ROOM = {
    "monsters_per_room_base": 15,
    "monsters_per_room_scale": 0.3,
    "monsters_per_room_cap": 30,
    "boss_room_monsters_base": 8,
    "boss_room_monsters_scale": 0.15,
    "move_time_per_horde": 0.6,  # 무리 간 달리기 시간 (평균)
    "clear_delay": 0.3,
}

# === 골드 ===
def gold_per_monster(stage: int) -> int:
    return 5 + stage * 2

# === 강화 ===
UPGRADES = {
    "atk":       {"base_cost": 50,  "growth": 1.12, "per_level": 3,    "max_val": None},
    "hp":        {"base_cost": 50,  "growth": 1.12, "per_level": 15,   "max_val": None},
    "atk_speed": {"base_cost": 80,  "growth": 1.15, "per_level": 0.05, "max_val": 2.5},
    "crit_rate": {"base_cost": 100, "growth": 1.18, "per_level": 0.01, "max_val": 0.60},
    "crit_dmg":  {"base_cost": 100, "growth": 1.18, "per_level": 0.05, "max_val": 3.0},
    "move_speed":{"base_cost": 60,  "growth": 1.10, "per_level": 0.3,  "max_val": 15.0},
}

# === 드랍 확률 ===
DROP_BASE_RATES = {
    "common": 0.40,
    "uncommon": 0.30,
    "rare": 0.18,
    "epic": 0.09,
    "legendary": 0.025,
    "mythic": 0.005,
}

DROP_STAGE_BONUS_RATE = 0.002
DROP_STAGE_BONUS_TARGETS = ["epic", "legendary", "mythic"]

PITY = {
    "soft_trigger": 5,
    "soft_bonus_per_stack": 0.05,
    "hard_pity": 15,
    "legendary_hard_pity": 40,
    "mythic_hard_pity": 100,
}

MYTHIC_UNLOCK_STAGE = 10

# === 장비 ===
EQUIPMENT_ATK_BONUS = {
    "common": 0.05,
    "uncommon": 0.10,
    "rare": 0.20,
    "epic": 0.35,
    "legendary": 0.50,
    "mythic": 0.80,
}

EQUIPMENT_SELL_PRICE = {
    "common": 50,
    "uncommon": 100,
    "rare": 300,
    "epic": 800,
    "legendary": 2000,
    "mythic": 5000,
}

# === 오프라인 ===
OFFLINE = {
    "max_hours": 8,
    "efficiency": 0.1,
    "death_fallback_efficiency": 0.05,
}


# === 유틸리티 함수 ===
def monster_hp(stage: int) -> float:
    return MONSTER["base_hp"] * (1 + (stage - 1) * MONSTER["hp_scale_per_stage"])


def wall_mult(stage: int) -> float:
    return WALL_MULTIPLIER.get(stage, 1.0)


def effective_monster_hp(stage: int) -> float:
    return monster_hp(stage) * wall_mult(stage)


def monsters_per_room(stage: int) -> int:
    return min(math.floor(ROOM["monsters_per_room_base"] + stage * ROOM["monsters_per_room_scale"]),
               ROOM["monsters_per_room_cap"])


def boss_room_monsters(stage: int) -> int:
    return math.floor(ROOM["boss_room_monsters_base"] + stage * ROOM["boss_room_monsters_scale"])


def rooms_per_stage(stage: int) -> int:
    return 2 + (1 if stage % 3 == 0 else 0)


def contact_damage(stage: int) -> float:
    return MONSTER["contact_damage_base"] * (1 + (stage - 1) * MONSTER["contact_damage_scale"])


def upgrade_cost(stat: str, level: int) -> float:
    u = UPGRADES[stat]
    return u["base_cost"] * (u["growth"] ** level)


def cumulative_upgrade_cost(stat: str, from_level: int, to_level: int) -> float:
    return sum(upgrade_cost(stat, lv) for lv in range(from_level, to_level))
