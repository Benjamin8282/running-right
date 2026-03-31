# 스킬 데이터 설계 문서

> "오른쪽 달리기" (Running Right) - 스킬 시스템 상세 설계
> 작성일: 2026-03-31
> 버전: 1.0
> 관련 문서: [MASTER_PLAN.md](../../MASTER_PLAN.md), [CLAUDE.md](../../CLAUDE.md)

---

## 목차

1. [스킬 시스템 개요](#1-스킬-시스템-개요)
2. [기본 평타 콤보](#2-기본-평타-콤보)
3. [액티브 스킬 테이블](#3-액티브-스킬-테이블)
4. [스킬 레벨업 테이블](#4-스킬-레벨업-테이블)
5. [스킬 시전 우선순위](#5-스킬-시전-우선순위)
6. [스킬 이펙트 명세](#6-스킬-이펙트-명세)
7. [스킬 밸런스 기준](#7-스킬-밸런스-기준)
8. [ScriptableObject 스키마](#8-scriptableobject-스키마)

---

## 1. 스킬 시스템 개요

### 1-1. 자동 시전 원칙

모든 스킬은 쿨타임 기반 자동 시전이다. 플레이어 개입 없이 AI가 최적의 스킬을 선택하여 시전한다.

| 항목 | 설명 |
|------|------|
| 시전 조건 | 공격 범위 내에 몬스터 1마리 이상 존재 |
| 시전 판정 주기 | 매 프레임 (Update) |
| 쿨타임 시작 시점 | 스킬 시전 시작 시 |
| 글로벌 쿨타임 (GCD) | 0.3초 (모든 스킬 공유, 평타 제외) |

### 1-2. 자동 시전 우선순위 (요약)

```
궁극기 (cooldown ready) → 범위 스킬 (cooldown ready) → 단일 스킬 (cooldown ready) → 기본 평타 콤보
```

상세 로직은 [5장](#5-스킬-시전-우선순위) 참조.

### 1-3. 애니메이션 캔슬 규칙

| 규칙 | 설명 |
|------|------|
| 평타 → 스킬 캔슬 | **허용.** 평타 모션 중 스킬 쿨타임이 돌아오면 즉시 스킬로 전환 |
| 스킬 → 스킬 캔슬 | **불가.** 현재 스킬 모션이 끝나야 다음 스킬 시전 가능 |
| 스킬 → 평타 캔슬 | **불가.** 스킬 모션 완료 후 평타 재개 |
| 궁극기 중 캔슬 | **불가.** 궁극기는 무적 + 모션 완료 보장 |
| 평타 콤보 내 캔슬 | 현재 타수의 hitFrame 이후에만 다음 타수 또는 스킬로 전환 가능 |

### 1-4. 스킬 상태 머신

```
StateMachine:
  Idle
    → 몬스터 감지 → ComboAttack (평타)
    → 스킬 쿨타임 완료 + 몬스터 감지 → SkillCast

  ComboAttack
    → 콤보 완료 → Idle
    → 스킬 쿨타임 완료 (hitFrame 이후) → SkillCast

  SkillCast
    → 모션 완료 → Idle

  Idle
    → 몬스터 미감지 → Run
```

---

## 2. 기본 평타 콤보

### 2-1. 콤보 구성

4타 콤보 체인. 마지막 타격에 넉백과 높은 대미지 계수 부여로 호쾌한 마무리 연출.

| 타수 | animationClip | damageCoefficient | hitboxWidth | hitboxHeight | knockback | hitStopDuration | 모션 시간 |
|------|--------------|-------------------|-------------|--------------|-----------|-----------------|-----------|
| 1타 | combo_hit_1 | 100% | 2.0 | 1.5 | 0.3 | 0.02초 | 0.35초 |
| 2타 | combo_hit_2 | 100% | 2.0 | 1.5 | 0.3 | 0.02초 | 0.30초 |
| 3타 | combo_hit_3 | 120% | 2.5 | 2.0 | 0.5 | 0.03초 | 0.35초 |
| 4타 | combo_hit_4 | 150% | 3.0 | 2.5 | 1.2 | 0.05초 | 0.45초 |

### 2-2. 콤보 상세

| 항목 | 값 | 설명 |
|------|-----|------|
| 총 콤보 시간 | 1.45초 | 4타 전체 모션 합산 |
| 콤보 리셋 시간 | 0.8초 | 마지막 타격 후 이 시간 동안 다음 타격 미입력 시 1타로 리셋 |
| hitFrame | 모션의 40% 시점 | 대미지 적용 및 히트박스 활성화 시점 |
| 다단 히트 | 없음 | 각 타수 1히트 |
| 평타 총 계수 | 470% | 4타 합산 (100+100+120+150) |
| 사이클 DPS 계수 | 324%/초 | 470% / 1.45초 |

### 2-3. 콤보 데이터 구조

```csharp
[System.Serializable]
public class ComboHitData
{
    public int hitIndex;                // 0~3 (1타~4타)
    public float damageCoefficient;     // 1.0, 1.0, 1.2, 1.5
    public float hitboxWidth;           // 유닛 단위
    public float hitboxHeight;          // 유닛 단위
    public float knockbackForce;        // 넉백 힘
    public float hitStopDuration;       // 히트스톱 시간(초)
    public float motionDuration;        // 모션 재생 시간(초)
    public float hitFrameRatio;         // 대미지 적용 시점 (0~1)
    public string animationClipName;    // 애니메이션 클립 참조
}
```

---

## 3. 액티브 스킬 테이블

### 3-1. 스킬 타입 분류

| skillType | 설명 | 예시 |
|-----------|------|------|
| single | 단일/소범위 대상 | 빠른 시전, 짧은 쿨타임 |
| aoe | 광역 다수 대상 | 넓은 범위, 다단 히트 |
| ultimate | 궁극기 (초광역/화면 전체) | 긴 쿨타임, 무적, 최대 대미지 |

### 3-2. 스킬 목록

총 8개 스킬 (single 3 / aoe 3 / ultimate 2)

---

#### SKILL_001: 뒷목 잡기 (Gore Cross)

> DNF "고어 크로스" 패러디. 뒤통수를 후려치는 강타.

| 필드 | 값 |
|------|-----|
| id | SKILL_001 |
| name | 뒷목 잡기 |
| nameEn | Neck Grab |
| description | "뒤통수를 후려쳐서 적의 뒷목을 잡게 만든다. 던파 유저의 뒷목도 함께 잡힌다." |
| skillType | single |
| baseDamageCoefficient | 350% |
| cooldown | 4.0초 |
| rangeWidth | 3.0 |
| rangeHeight | 2.0 |
| hitCount | 1 |
| knockback | 2.0 |
| unlockCondition | 스테이지 1 클리어 |
| unlockStage | 1 |

---

#### SKILL_002: 마구 찌르기 (Moon Light Slash)

> DNF "문라이트 슬래시" 패러디. 달빛이고 뭐고 그냥 마구 찌른다.

| 필드 | 값 |
|------|-----|
| id | SKILL_002 |
| name | 마구 찌르기 |
| nameEn | Stab Frenzy |
| description | "달빛 같은 건 없다. 그냥 미친 듯이 찌를 뿐이다." |
| skillType | single |
| baseDamageCoefficient | 180% |
| cooldown | 3.0초 |
| rangeWidth | 2.5 |
| rangeHeight | 1.5 |
| hitCount | 4 |
| knockback | 0.2 |
| unlockCondition | 스테이지 5 클리어 |
| unlockStage | 5 |

> 총 계수: 180% x 4 = 720%. 빠른 다단 히트로 체감 DPS 높음.

---

#### SKILL_003: 승룡 비스무리한 것 (Rising Uppercut-ish)

> DNF "라이징 컷" 패러디. 승룡권을 시전하고 싶었지만 팔이 짧아서 어퍼컷이 됐다.

| 필드 | 값 |
|------|-----|
| id | SKILL_003 |
| name | 승룡 비스무리한 것 |
| nameEn | Rising Uppercut-ish |
| description | "하늘을 찌르는 주먹! ...까지는 못 올라가고 어깨 높이가 한계다." |
| skillType | single |
| baseDamageCoefficient | 500% |
| cooldown | 6.0초 |
| rangeWidth | 2.0 |
| rangeHeight | 3.5 |
| hitCount | 2 |
| knockback | 3.0 |
| unlockCondition | 스테이지 10 클리어 |
| unlockStage | 10 |

> 총 계수: 500% x 2 = 1000%. 높은 단일 피해 + 공중 띄우기 연출.

---

#### SKILL_004: 대회전 날먹 (SST: Spin-Spin-Tornado)

> DNF "SST" 패러디. 빙글빙글 돌면서 주변을 쓸어버린다.

| 필드 | 값 |
|------|-----|
| id | SKILL_004 |
| name | 대회전 날먹 |
| nameEn | Spin Spin Tornado |
| description | "빙글빙글~ 돌면 모든 게 해결된다. 현실에선 그냥 어지러울 뿐이지만." |
| skillType | aoe |
| baseDamageCoefficient | 250% |
| cooldown | 8.0초 |
| rangeWidth | 6.0 |
| rangeHeight | 3.0 |
| hitCount | 3 |
| knockback | 1.5 |
| unlockCondition | 스테이지 15 클리어 |
| unlockStage | 15 |

> 총 계수: 250% x 3 = 750%. 넓은 범위의 다수 타격.

---

#### SKILL_005: 돌진 냅다 (Charge Recklessly)

> DNF "어퍼 슬래시/가드 크래시" 패러디. 앞으로 돌진하며 경로상 모든 적 타격.

| 필드 | 값 |
|------|-----|
| id | SKILL_005 |
| name | 돌진 냅다 |
| nameEn | Charge Recklessly |
| description | "앞만 보고 돌진! 어딜 가는지는 나도 모른다. 근데 맞으면 아프다." |
| skillType | aoe |
| baseDamageCoefficient | 300% |
| cooldown | 7.0초 |
| rangeWidth | 8.0 |
| rangeHeight | 2.0 |
| hitCount | 2 |
| knockback | 2.5 |
| unlockCondition | 스테이지 20 클리어 |
| unlockStage | 20 |

> 총 계수: 300% x 2 = 600%. 전방 긴 직선 범위. 돌진 이동 포함.

---

#### SKILL_006: 바닥은 용암 (Floor is Lava Wave)

> DNF "화염 강타" 패러디. 바닥에 불기둥을 소환한다.

| 필드 | 값 |
|------|-----|
| id | SKILL_006 |
| name | 바닥은 용암 |
| nameEn | Floor is Lava Wave |
| description | "어릴 때 바닥은 용암 놀이 해봤지? 이번엔 진짜다. 근데 나도 뜨겁다." |
| skillType | aoe |
| baseDamageCoefficient | 200% |
| cooldown | 10.0초 |
| rangeWidth | 10.0 |
| rangeHeight | 2.0 |
| hitCount | 5 |
| knockback | 0.5 |
| unlockCondition | 스테이지 30 클리어 |
| unlockStage | 30 |

> 총 계수: 200% x 5 = 1000%. 지속 피해형 넓은 범위. 화면 절반 이상 커버.

---

#### SKILL_007: 각성기인 척 (Pretend Awakening)

> DNF "각성기" 패러디. 각성기처럼 보이지만 실제로는 그냥 온 힘을 다해 때린다.

| 필드 | 값 |
|------|-----|
| id | SKILL_007 |
| name | 각성기인 척 |
| nameEn | Pretend Awakening |
| description | "뒤에서 거대한 환영이 나타나는 줄 알았지? 그냥 조명 효과였다. 근데 아프긴 아프다." |
| skillType | ultimate |
| baseDamageCoefficient | 800% |
| cooldown | 30.0초 |
| rangeWidth | 14.0 |
| rangeHeight | 6.0 |
| hitCount | 3 |
| knockback | 5.0 |
| unlockCondition | 스테이지 50 클리어 |
| unlockStage | 50 |

> 총 계수: 800% x 3 = 2400%. 화면 전체 범위. 시전 중 무적.

---

#### SKILL_008: 진짜 최종 오의 (True Final Secret Art For Real This Time)

> DNF "2각성기" 패러디. 이번엔 진짜 궁극기다. 아마도.

| 필드 | 값 |
|------|-----|
| id | SKILL_008 |
| name | 진짜 최종 오의 |
| nameEn | True Final Secret Art |
| description | "'이번엔 진짜 최종이다'라고 세 번째 말하는 중. 그래도 화면이 하얘지긴 한다." |
| skillType | ultimate |
| baseDamageCoefficient | 1500% |
| cooldown | 60.0초 |
| rangeWidth | 화면 전체 |
| rangeHeight | 화면 전체 |
| hitCount | 5 |
| knockback | 10.0 |
| unlockCondition | 스테이지 100 클리어 |
| unlockStage | 100 |

> 총 계수: 1500% x 5 = 7500%. 화면 내 모든 적 타격. 시전 중 무적 + 연출 컷신.

---

### 3-3. 스킬 요약 비교표

| ID | 이름 | 타입 | 총 계수 | 쿨타임 | 초당 계수 (DPC/CD) | 해금 |
|----|------|------|---------|--------|-------------------|------|
| SKILL_001 | 뒷목 잡기 | single | 350% | 4.0초 | 87.5%/초 | Stg 1 |
| SKILL_002 | 마구 찌르기 | single | 720% | 3.0초 | 240%/초 | Stg 5 |
| SKILL_003 | 승룡 비스무리한 것 | single | 1000% | 6.0초 | 166.7%/초 | Stg 10 |
| SKILL_004 | 대회전 날먹 | aoe | 750% | 8.0초 | 93.8%/초 | Stg 15 |
| SKILL_005 | 돌진 냅다 | aoe | 600% | 7.0초 | 85.7%/초 | Stg 20 |
| SKILL_006 | 바닥은 용암 | aoe | 1000% | 10.0초 | 100%/초 | Stg 30 |
| SKILL_007 | 각성기인 척 | ultimate | 2400% | 30.0초 | 80%/초 | Stg 50 |
| SKILL_008 | 진짜 최종 오의 | ultimate | 7500% | 60.0초 | 125%/초 | Stg 100 |

> **참고:** 초당 계수는 단일 대상 기준. AoE 스킬은 실제로 다수 적에게 적중하므로 체감 효율이 훨씬 높다.

---

## 4. 스킬 레벨업 테이블

### 4-1. 레벨업 공식

| 항목 | 공식 | 설명 |
|------|------|------|
| 대미지 배율 | `1.0 + (level - 1) * 0.08` | 레벨당 8% 대미지 증가 |
| 쿨타임 감소 | `baseCooldown * (1 - level * 0.015)` | 레벨당 1.5% 쿨타임 감소 (최소 50%) |
| 골드 비용 | `baseGoldCost * (1.18 ^ (level - 1))` | 레벨당 18% 비용 증가 |
| 구슬 조각 비용 | 레벨 5부터 추가, 레벨 10부터 2배 | 후반 강화에 희귀 재화 필요 |

### 4-2. 스킬별 기본 강화 비용

| 스킬 | baseGoldCost | 구슬 조각 시작 레벨 |
|------|-------------|-------------------|
| SKILL_001 뒷목 잡기 | 500 | Lv.5 |
| SKILL_002 마구 찌르기 | 800 | Lv.5 |
| SKILL_003 승룡 비스무리한 것 | 1,200 | Lv.5 |
| SKILL_004 대회전 날먹 | 2,000 | Lv.5 |
| SKILL_005 돌진 냅다 | 1,800 | Lv.5 |
| SKILL_006 바닥은 용암 | 3,000 | Lv.5 |
| SKILL_007 각성기인 척 | 8,000 | Lv.3 |
| SKILL_008 진짜 최종 오의 | 20,000 | Lv.3 |

### 4-3. SKILL_001 뒷목 잡기 레벨업 테이블 (대표 예시)

| Level | damageMultiplier | cooldown | goldCost | orbFragments | 총 계수 |
|-------|-----------------|----------|----------|-------------|---------|
| 1 | 1.00 | 4.00초 | - | - | 350% |
| 2 | 1.08 | 3.94초 | 500 | 0 | 378% |
| 3 | 1.16 | 3.88초 | 590 | 0 | 406% |
| 4 | 1.24 | 3.82초 | 696 | 0 | 434% |
| 5 | 1.32 | 3.76초 | 821 | 2 | 462% |
| 6 | 1.40 | 3.70초 | 969 | 3 | 490% |
| 7 | 1.48 | 3.64초 | 1,143 | 4 | 518% |
| 8 | 1.56 | 3.58초 | 1,349 | 5 | 546% |
| 9 | 1.64 | 3.52초 | 1,592 | 6 | 574% |
| 10 | 1.72 | 3.46초 | 1,878 | 8 | 602% |
| 11 | 1.80 | 3.40초 | 2,216 | 10 | 630% |
| 12 | 1.88 | 3.34초 | 2,615 | 12 | 658% |
| 13 | 1.96 | 3.28초 | 3,086 | 14 | 686% |
| 14 | 2.04 | 3.22초 | 3,641 | 17 | 714% |
| 15 | 2.12 | 3.16초 | 4,296 | 20 | 742% |
| 16 | 2.20 | 3.10초 | 5,070 | 24 | 770% |
| 17 | 2.28 | 3.04초 | 5,982 | 28 | 798% |
| 18 | 2.36 | 2.98초 | 7,059 | 33 | 826% |
| 19 | 2.44 | 2.92초 | 8,330 | 39 | 854% |
| 20 | 2.52 | 2.86초 | 9,829 | 46 | 882% |

> Lv.20 기준: 대미지 2.52배, 쿨타임 28.5% 감소. 총 투자 골드: 약 61,000 / 구슬 조각: 약 270개

### 4-4. 궁극기 레벨업 테이블 (SKILL_007 각성기인 척)

| Level | damageMultiplier | cooldown | goldCost | orbFragments | 총 계수 |
|-------|-----------------|----------|----------|-------------|---------|
| 1 | 1.00 | 30.0초 | - | - | 2,400% |
| 2 | 1.08 | 29.6초 | 8,000 | 0 | 2,592% |
| 3 | 1.16 | 29.1초 | 9,440 | 5 | 2,784% |
| 4 | 1.24 | 28.7초 | 11,139 | 7 | 2,976% |
| 5 | 1.32 | 28.2초 | 13,144 | 10 | 3,168% |
| 6 | 1.40 | 27.8초 | 15,510 | 14 | 3,360% |
| 7 | 1.48 | 27.3초 | 18,302 | 18 | 3,552% |
| 8 | 1.56 | 26.9초 | 21,596 | 23 | 3,744% |
| 9 | 1.64 | 26.4초 | 25,483 | 29 | 3,936% |
| 10 | 1.72 | 26.0초 | 30,070 | 36 | 4,128% |
| 11 | 1.80 | 25.5초 | 35,483 | 44 | 4,320% |
| 12 | 1.88 | 25.1초 | 41,870 | 53 | 4,512% |
| 13 | 1.96 | 24.6초 | 49,406 | 64 | 4,704% |
| 14 | 2.04 | 24.2초 | 58,299 | 76 | 4,896% |
| 15 | 2.12 | 23.7초 | 68,793 | 90 | 5,088% |
| 16 | 2.20 | 23.3초 | 81,176 | 106 | 5,280% |
| 17 | 2.28 | 22.8초 | 95,787 | 124 | 5,472% |
| 18 | 2.36 | 22.4초 | 113,028 | 145 | 5,664% |
| 19 | 2.44 | 21.9초 | 133,373 | 168 | 5,856% |
| 20 | 2.52 | 21.5초 | 157,380 | 195 | 6,048% |

> 궁극기는 기본 비용이 높고, 구슬 조각이 Lv.3부터 필요. 최종 투자 비용 대비 DPS 효율은 일반 스킬보다 낮지만 순간 폭발력으로 보상.

### 4-5. 전체 스킬 Lv.20 요약

| 스킬 | Lv.1 총 계수 | Lv.20 총 계수 | Lv.20 쿨타임 | 총 골드 | 총 구슬 |
|------|-------------|-------------|------------|---------|---------|
| 뒷목 잡기 | 350% | 882% | 2.86초 | ~61K | ~270 |
| 마구 찌르기 | 720% | 1,814% | 2.14초 | ~98K | ~430 |
| 승룡 비스무리한 것 | 1,000% | 2,520% | 4.29초 | ~146K | ~650 |
| 대회전 날먹 | 750% | 1,890% | 5.71초 | ~244K | ~1,080 |
| 돌진 냅다 | 600% | 1,512% | 5.00초 | ~220K | ~970 |
| 바닥은 용암 | 1,000% | 2,520% | 7.14초 | ~366K | ~1,620 |
| 각성기인 척 | 2,400% | 6,048% | 21.5초 | ~938K | ~1,207 |
| 진짜 최종 오의 | 7,500% | 18,900% | 42.9초 | ~2,345K | ~3,018 |

---

## 5. 스킬 시전 우선순위

### 5-1. 자동 시전 AI 로직

```
매 프레임 실행:
1. 현재 스킬 모션 중인가?
   → YES: 모션 완료 대기 (캔슬 불가)
   → NO: 2단계로

2. 글로벌 쿨타임(GCD) 중인가?
   → YES: 대기
   → NO: 3단계로

3. 공격 범위 내 몬스터가 있는가?
   → NO: Run 상태 유지
   → YES: 4단계로

4. 우선순위 순서대로 스킬 확인:
   4-1. 궁극기 중 사용 가능한 것이 있는가? (쿨타임 완료)
        → YES: 시전 (더 높은 계수의 궁극기 우선)
   4-2. AoE 스킬 중 사용 가능한 것이 있는가?
        → YES: 범위 내 적 수 확인
           → 적 3마리 이상: 시전 (더 높은 계수의 AoE 우선)
           → 적 2마리 이하: 5단계로
   4-3. Single 스킬 중 사용 가능한 것이 있는가?
        → YES: 시전 (더 높은 계수의 Single 우선)
   4-4. 모든 스킬 쿨타임 중
        → 기본 평타 콤보 시전

5. AoE 스킬이 있지만 적이 2마리 이하:
   5-1. Single 스킬 사용 가능? → 시전
   5-2. 불가 → AoE 스킬 시전 (적이 적어도 사용)
```

### 5-2. 우선순위 정렬 기준

```
Priority = skillType 가중치 * (totalCoefficient / cooldown)

skillType 가중치:
  ultimate = 3.0
  aoe      = 2.0 * (범위 내 적 수 / 3)  // 적 3마리 기준 정규화
  single   = 1.0
```

### 5-3. 스킬 선택 조건 보조 규칙

| 규칙 | 설명 |
|------|------|
| 보스 우선 궁극기 | 구슬 보스 등장 시, 궁극기 쿨타임이 5초 이내면 평타로 버티다가 궁극기 시전 |
| AoE 임계치 | AoE 스킬은 범위 내 적이 3마리 이상일 때 최우선 사용 |
| 오버킬 방지 | 대상 HP가 평타 1타로 처치 가능하면 스킬 사용 안 함 (쿨타임 절약) |
| 쿨타임 정렬 | 동일 타입 내에서는 쿨타임이 짧은 스킬 우선 (DPS 극대화) |

### 5-4. 의사 코드

```csharp
public SkillData SelectBestSkill(List<SkillData> availableSkills, int enemyCount, bool isBossPresent)
{
    // 보스 앞 궁극기 예약
    if (isBossPresent)
    {
        var ultimateNearReady = availableSkills
            .Where(s => s.skillType == SkillType.Ultimate && GetRemainingCooldown(s) <= 5f)
            .OrderByDescending(s => s.TotalCoefficient)
            .FirstOrDefault();
        if (ultimateNearReady != null && GetRemainingCooldown(ultimateNearReady) > 0)
            return null; // 평타로 대기
    }

    // 궁극기 확인
    var ultimate = availableSkills
        .Where(s => s.skillType == SkillType.Ultimate && IsReady(s))
        .OrderByDescending(s => s.TotalCoefficient)
        .FirstOrDefault();
    if (ultimate != null) return ultimate;

    // AoE 확인 (적 3마리 이상)
    if (enemyCount >= 3)
    {
        var aoe = availableSkills
            .Where(s => s.skillType == SkillType.AoE && IsReady(s))
            .OrderByDescending(s => s.TotalCoefficient / s.cooldown)
            .FirstOrDefault();
        if (aoe != null) return aoe;
    }

    // Single 스킬 확인 (오버킬 방지)
    var single = availableSkills
        .Where(s => s.skillType == SkillType.Single && IsReady(s))
        .OrderByDescending(s => s.TotalCoefficient / s.cooldown)
        .FirstOrDefault();
    if (single != null) return single;

    // 적이 2마리 이하여도 AoE 사용 (다른 스킬 없을 때)
    var fallbackAoe = availableSkills
        .Where(s => s.skillType == SkillType.AoE && IsReady(s))
        .OrderBy(s => s.cooldown)
        .FirstOrDefault();
    if (fallbackAoe != null) return fallbackAoe;

    return null; // 기본 평타
}
```

---

## 6. 스킬 이펙트 명세

### 6-1. 기본 평타 콤보

| 타수 | 비주얼 이펙트 | 오디오 | 카메라 |
|------|-------------|--------|--------|
| 1타 | 흰색 슬래시 아크 (작음) | sfx_hit_light_01 | - |
| 2타 | 흰색 슬래시 아크 (작음, 반대 방향) | sfx_hit_light_02 | - |
| 3타 | 노란색 슬래시 아크 (중간) | sfx_hit_medium_01 | 미세 셰이크 (0.02초) |
| 4타 | 주황색 임팩트 버스트 + 넉백 잔상 | sfx_hit_heavy_01 | 셰이크 (0.05초) + 히트스톱 |

### 6-2. 액티브 스킬 이펙트

#### SKILL_001: 뒷목 잡기

| 구분 | 설명 |
|------|------|
| 시전 모션 | 0.5초. 크게 손을 치켜든 후 내려찍기 |
| 히트 이펙트 | 빨간색 별 모양 임팩트 + "뒷목!" 텍스트 팝업 |
| 파티클 | 충격파 링 (전방 작은 범위) |
| SFX | sfx_skill_neckgrab (둔탁한 타격음) |
| 카메라 | 셰이크 0.1초, 강도 0.3 |
| 히트스톱 | 0.08초 |

#### SKILL_002: 마구 찌르기

| 구분 | 설명 |
|------|------|
| 시전 모션 | 0.8초. 빠르게 4회 찌르기 (0.2초 간격) |
| 히트 이펙트 | 흰색 찌르기 궤적 (각 히트마다) |
| 파티클 | 스파크 파티클 (찌르기 접촉점마다) |
| SFX | sfx_skill_stab_01 ~ 04 (빠른 연속 타격음) |
| 카메라 | 미세 셰이크 유지 (모션 동안) |
| 히트스톱 | 0.02초 x 4 (각 히트마다) |

#### SKILL_003: 승룡 비스무리한 것

| 구분 | 설명 |
|------|------|
| 시전 모션 | 0.7초. 어퍼컷 모션 → 점프 (살짝) → 착지 |
| 히트 이펙트 | 노란색 상승 기류 + 적 공중 띄우기 |
| 파티클 | 바닥에서 바람 이펙트 → 상승 이펙트 |
| SFX | sfx_skill_uppercut (펀치 + 바람 소리) |
| 카메라 | 셰이크 0.15초, 강도 0.5 + 줌인 5% |
| 히트스톱 | 0.1초 (1히트), 0.15초 (2히트 피니시) |
| 특수 | 적이 공중에 뜨는 연출 (0.3초간 체공) |

#### SKILL_004: 대회전 날먹

| 구분 | 설명 |
|------|------|
| 시전 모션 | 1.2초. 캐릭터가 빙글빙글 회전 (3회전) |
| 히트 이펙트 | 원형 슬래시 궤적 (회전마다 확장) |
| 파티클 | 나선형 바람 이펙트 + 먼지 파티클 |
| SFX | sfx_skill_spin_loop (회전 동안 반복) + sfx_skill_spin_finish |
| 카메라 | 셰이크 0.2초, 강도 0.3 (마지막 회전) |
| 히트스톱 | 0.03초 x 3 (각 회전마다) |
| 특수 | 캐릭터 회전 중 이동 불가, 스프라이트 회전 |

#### SKILL_005: 돌진 냅다

| 구분 | 설명 |
|------|------|
| 시전 모션 | 0.6초. 전방 8유닛 돌진 |
| 히트 이펙트 | 돌진 경로 따라 잔상 3개 + 충돌 임팩트 |
| 파티클 | 속도선 이펙트 + 먼지 궤적 |
| SFX | sfx_skill_charge (돌진음) + sfx_skill_charge_hit (충돌음) |
| 카메라 | 스피드 줌 (돌진 중 줌아웃 5% → 충돌 시 줌인 복귀) |
| 히트스톱 | 0.1초 (최종 충돌 시) |
| 특수 | 캐릭터가 실제로 전방 이동. 돌진 중 무적 |

#### SKILL_006: 바닥은 용암

| 구분 | 설명 |
|------|------|
| 시전 모션 | 1.5초. 바닥 찍기 → 용암 기둥 5개 순차 솟아오름 (0.25초 간격) |
| 히트 이펙트 | 빨간-주황 화염 기둥 (바닥에서 솟아오름) |
| 파티클 | 화염 파티클 시스템 + 바닥 균열 이펙트 |
| SFX | sfx_skill_lava_cast (시전음) + sfx_skill_lava_eruption x5 (분출음) |
| 카메라 | 셰이크 0.3초, 강도 0.4 (연속) |
| 히트스톱 | 0.02초 x 5 (각 기둥마다) |
| 특수 | 화면 틴트 (붉은색 오버레이 20%) 1초간 |

#### SKILL_007: 각성기인 척

| 구분 | 설명 |
|------|------|
| 시전 모션 | 2.5초. 포효 → 거대 환영 등장 → 강타 3회 |
| 히트 이펙트 | 화면 전체 플래시 → 거대 임팩트 원 3개 |
| 파티클 | 배경 암전 + 집중선 + 오라 파티클 |
| SFX | sfx_skill_awakening_roar + sfx_skill_awakening_hit x3 |
| 카메라 | 강한 셰이크 0.5초, 강도 0.8 + 줌인 10% → 줌아웃 복귀 |
| 히트스톱 | 0.2초 x 3 (각 강타마다) |
| 특수 | 시전 중 무적. 배경 어두워짐 (70%). "뒤에서 거대한 그림자" 연출 (실제로는 조명). 컷인 연출 (캐릭터 얼굴 클로즈업 0.5초) |
| UI | 스킬명 텍스트 화면 중앙 표시 (1초간 페이드) |

#### SKILL_008: 진짜 최종 오의

| 구분 | 설명 |
|------|------|
| 시전 모션 | 4.0초. 긴 차징 → 컷신 → 화면 전체 폭발 |
| 히트 이펙트 | 화면 완전 화이트아웃 → 다중 폭발 → 연쇄 임팩트 |
| 파티클 | 배경 완전 암전 → 에너지 수렴 → 대폭발 파티클 |
| SFX | sfx_skill_final_charge (차징 2초) + sfx_skill_final_explosion (폭발) |
| 카메라 | 줌인 20% (차징) → 초강력 셰이크 1.0초, 강도 1.0 → 줌아웃 복귀 |
| 히트스톱 | 0.3초 x 5 (각 폭발마다) |
| 특수 | 시전 중 무적. 2초 컷신 (캐릭터 실루엣 + 에너지 집중). 화면 내 모든 적 HP바 표시. "진짜 최종" 텍스트 연출 (크게 → 작게 → 사라짐) |
| UI | 풀스크린 연출. 스킬명 + 레벨 표시. 총 대미지 숫자 대형 표시 (피니시 후) |

### 6-3. 치명타 이펙트 (공통)

| 구분 | 일반 히트 | 치명타 히트 |
|------|----------|------------|
| 대미지 텍스트 색상 | 흰색 | 노란색 |
| 대미지 텍스트 크기 | 1.0x | 1.5x |
| 추가 이펙트 | - | 별 모양 스파크 |
| 추가 SFX | - | sfx_critical (유리 깨지는 소리) |
| 히트스톱 추가 | - | +0.03초 |

---

## 7. 스킬 밸런스 기준

### 7-1. DPS 설계 목표

전투의 핵심 체감 목표: **스킬을 쓰면 확실히 강해진 느낌, 하지만 평타만으로도 진행 가능.**

| 항목 | 목표 비율 | 설명 |
|------|----------|------|
| 평타 DPS | 기준 (1.0x) | 모든 계산의 기준 |
| 평타 + Single 스킬 DPS | 1.8x ~ 2.2x | 평타 대비 약 2배 |
| 평타 + All 스킬 DPS (단일 대상) | 2.5x ~ 3.5x | 스킬 전부 사용 시 |
| 평타 + All 스킬 DPS (다수 대상) | 4.0x ~ 6.0x | AoE 스킬의 진가 |
| 궁극기 순간 DPS | 10x ~ 15x | 궁극기 시전 순간 폭발력 |

### 7-2. 기본 DPS 계산 (Lv.1, ATK=100 기준)

#### 평타 DPS

```
평타 1사이클 = 4타 (100% + 100% + 120% + 150%) = 470% ATK
사이클 시간 = 1.45초
평타 DPS = 470 / 1.45 = 324.1% ATK/초

ATK=100 기준 → 평타 DPS = 324.1 대미지/초
```

#### Single 스킬 DPS 기여

```
SKILL_001 (뒷목 잡기):  350% / 4.0초  = 87.5%/초
SKILL_002 (마구 찌르기):  720% / 3.0초  = 240.0%/초
SKILL_003 (승룡 비스무리한 것): 1000% / 6.0초 = 166.7%/초

Single 스킬 합산 DPS 기여 = 494.2%/초

※ 실제로는 스킬 모션 시간 동안 평타 불가이므로 보정 필요
```

#### 보정된 총 DPS (단일 대상, Lv.1 전체 스킬)

```
60초 전투 시뮬레이션:

궁극기 시전 횟수:
  SKILL_007: 60/30 = 2회, 모션 2.5초 × 2 = 5.0초 소비, 2400% × 2 = 4800%
  SKILL_008: 60/60 = 1회, 모션 4.0초 × 1 = 4.0초 소비, 7500% × 1 = 7500%

AoE 스킬 시전 횟수 (단일 대상 환경):
  SKILL_004: 60/8 = 7회, 모션 1.2초 × 7 = 8.4초 소비, 750% × 7 = 5250%
  SKILL_005: 60/7 = 8회, 모션 0.6초 × 8 = 4.8초 소비, 600% × 8 = 4800%
  SKILL_006: 60/10 = 6회, 모션 1.5초 × 6 = 9.0초 소비, 1000% × 6 = 6000%

Single 스킬 시전 횟수:
  SKILL_001: 60/4 = 15회, 모션 0.5초 × 15 = 7.5초 소비, 350% × 15 = 5250%
  SKILL_002: 60/3 = 20회, 모션 0.8초 × 20 = 16.0초 소비, 720% × 20 = 14400%
  SKILL_003: 60/6 = 10회, 모션 0.7초 × 10 = 7.0초 소비, 1000% × 10 = 10000%

스킬 모션 총 소비 시간: 5.0 + 4.0 + 8.4 + 4.8 + 9.0 + 7.5 + 16.0 + 7.0 = 61.7초

※ 60초를 초과하므로 실제로는 우선순위에 따라 일부 스킬만 사용됨
```

#### 현실적 60초 시뮬레이션 (우선순위 적용)

```
시간 배분 (우선순위 순):
  궁극기 모션: 9.0초 → 대미지 12,300%
  AoE 스킬 모션 (제한적): 15.0초 → 대미지 약 10,500%
  Single 스킬 모션: 12.0초 → 대미지 약 12,000%
  GCD 대기: 약 3.0초
  평타 시간: 60 - 9 - 15 - 12 - 3 = 21초 → 대미지 21 × 324.1 = 6,806%

총 대미지 (60초): 12,300 + 10,500 + 12,000 + 6,806 = 41,606%
총 DPS: 41,606 / 60 = 693.4%/초

DPS 배율: 693.4 / 324.1 = 2.14x (평타 대비)
```

#### 다수 대상 (5마리) 시뮬레이션

```
AoE/궁극기 대미지에 적 수 적용:
  궁극기: 12,300% × 5 = 61,500% (전체)
  AoE: 10,500% × 5 = 52,500% (전체)
  Single: 12,000% × 1 = 12,000% (단일)
  평타: 6,806% × 1 = 6,806% (단일)

총 전체 대미지: 132,806%
유효 DPS (적당 평균): 132,806 / 60 / 5 = 442.7%/초
→ 하지만 AoE 대미지가 전체에 적용되므로 체감 클리어 속도는 약 4.1x
```

### 7-3. 밸런스 지표 요약

| 지표 | Lv.1 값 | 목표 범위 | 판정 |
|------|---------|----------|------|
| 평타 DPS | 324.1%/초 | 기준값 | - |
| 전체 스킬 DPS (단일) | 693.4%/초 (2.14x) | 2.5x~3.5x | 약간 낮음 (레벨업으로 보정) |
| 전체 스킬 DPS (5마리) | ~4.1x | 4.0x~6.0x | 적정 |
| 궁극기 순간 DPS | 2400% / 2.5초 = 960%/초 (~3x) | 즉시 체감 | 적정 (연출 보상) |

### 7-4. 스테이지별 밸런스 포인트

```
몬스터 HP 스케일링: BaseHP * (1 + stage * 0.15)

밸런스 목표:
  - 스테이지 1~10: 평타만으로 10초 내 방 클리어 가능
  - 스테이지 11~30: 스킬 사용 시 15초, 평타만 25초
  - 스테이지 31~50: 스킬 필수, 20초 내 클리어
  - 스테이지 51~100: 스킬 레벨업 필요, 궁극기 활용 필수
  - 스테이지 100+: 장비/전생 시스템과 연동

스킬 레벨업으로 인한 DPS 스케일링:
  Lv.1 전체 DPS: 693%/초
  Lv.10 전체 DPS: 약 1,190%/초 (+72%)
  Lv.20 전체 DPS: 약 1,747%/초 (+152%)
```

### 7-5. 골드 수입 대비 스킬 투자 비용

```
골드 수입 예상 (스테이지 기준, 공식: baseGold * (1 + stage * 0.12)^1.15, 평균 baseGold ~11):
  Stg 1~10:  약 400~1,500 골드/분
  Stg 11~30: 약 1,500~4,000 골드/분
  Stg 31~50: 약 4,000~10,000 골드/분
  Stg 51~100: 약 10,000~30,000 골드/분

설계 원칙:
  - 스킬 1레벨업에 필요한 골드 = 해당 스테이지 5~10분 수입
  - 너무 빠른 성장 → 컨텐츠 소진 가속
  - 너무 느린 성장 → 지루함, 이탈
  - "벽" 구간에서 전생 시스템으로 돌파 유도
```

---

## 8. ScriptableObject 스키마

### 8-1. SkillData ScriptableObject

```csharp
using UnityEngine;

public enum SkillType
{
    Single,     // 단일/소범위 대상
    AoE,        // 광역 다수 대상
    Ultimate    // 궁극기
}

[CreateAssetMenu(fileName = "NewSkill", menuName = "RunningRight/SkillData")]
public class SkillData : ScriptableObject
{
    [Header("기본 정보")]
    public string skillId;              // "SKILL_001" 형식
    public string skillName;            // 한글 스킬명
    public string skillNameEn;          // 영문 스킬명
    [TextArea(2, 4)]
    public string description;          // 스킬 설명 (패러디 포함)
    public Sprite icon;                 // 스킬 아이콘

    [Header("스킬 타입")]
    public SkillType skillType;         // Single / AoE / Ultimate

    [Header("대미지")]
    public float baseDamageCoefficient; // 기본 대미지 계수 (1.0 = 100%)
    public int hitCount;                // 히트 수

    [Header("쿨타임")]
    public float cooldown;              // 기본 쿨타임(초)

    [Header("범위")]
    public float rangeWidth;            // 히트박스 너비 (유닛)
    public float rangeHeight;           // 히트박스 높이 (유닛)
    public bool isFullScreen;           // 화면 전체 범위 여부

    [Header("물리")]
    public float knockbackForce;        // 넉백 힘
    public float hitStopDuration;       // 히트스톱 시간(초)

    [Header("모션")]
    public AnimationClip castAnimation; // 시전 애니메이션
    public float castDuration;          // 시전 시간(초)
    public float hitFrameRatio;         // 대미지 적용 시점 (0~1)
    public bool isInvincible;           // 시전 중 무적 여부

    [Header("이펙트")]
    public GameObject hitEffectPrefab;  // 히트 이펙트 프리팹
    public GameObject castEffectPrefab; // 시전 이펙트 프리팹
    public AudioClip castSfx;           // 시전 효과음
    public AudioClip hitSfx;            // 히트 효과음

    [Header("카메라")]
    public float cameraShakeDuration;   // 카메라 셰이크 시간
    public float cameraShakeIntensity;  // 카메라 셰이크 강도
    public float cameraZoomAmount;      // 줌인/아웃 비율 (0 = 없음)

    [Header("해금")]
    public int unlockStage;             // 해금 필요 스테이지

    [Header("레벨업")]
    public int maxLevel;                // 최대 레벨 (기본 20)
    public int baseGoldCost;            // Lv.2 강화 기본 골드 비용
    public float goldCostMultiplier;    // 레벨당 비용 증가율 (기본 1.18)
    public int orbFragmentStartLevel;   // 구슬 조각 필요 시작 레벨
    public float damagePerLevel;        // 레벨당 대미지 증가율 (기본 0.08)
    public float cooldownReductionPerLevel; // 레벨당 쿨타임 감소율 (기본 0.015)
    public float maxCooldownReduction;  // 최대 쿨타임 감소 비율 (기본 0.5)

    [Header("특수 연출")]
    public bool hasCutIn;               // 컷인 연출 여부
    public Sprite cutInSprite;          // 컷인 이미지
    public bool hasScreenTint;          // 화면 틴트 여부
    public Color screenTintColor;       // 틴트 색상
    public bool hasSkillNameDisplay;    // 스킬명 화면 표시 여부

    // === 계산 프로퍼티 ===

    /// <summary>
    /// 총 대미지 계수 (기본 계수 × 히트 수)
    /// </summary>
    public float TotalCoefficient => baseDamageCoefficient * hitCount;

    /// <summary>
    /// 특정 레벨에서의 대미지 배율
    /// </summary>
    public float GetDamageMultiplier(int level)
    {
        return 1.0f + (level - 1) * damagePerLevel;
    }

    /// <summary>
    /// 특정 레벨에서의 쿨타임
    /// </summary>
    public float GetCooldown(int level)
    {
        float reduction = Mathf.Min(level * cooldownReductionPerLevel, maxCooldownReduction);
        return cooldown * (1f - reduction);
    }

    /// <summary>
    /// 특정 레벨에서의 강화 골드 비용
    /// </summary>
    public int GetGoldCost(int level)
    {
        return Mathf.RoundToInt(baseGoldCost * Mathf.Pow(goldCostMultiplier, level - 1));
    }

    /// <summary>
    /// 특정 레벨에서의 구슬 조각 비용
    /// </summary>
    public int GetOrbFragmentCost(int level)
    {
        if (level < orbFragmentStartLevel) return 0;

        int baseCost = 2;
        int levelsAboveStart = level - orbFragmentStartLevel;
        float multiplier = (level >= 10) ? 2.0f : 1.0f;

        return Mathf.RoundToInt(baseCost * (1 + levelsAboveStart * 0.5f) * multiplier);
    }

    /// <summary>
    /// 초당 대미지 계수 (DPS 효율)
    /// </summary>
    public float GetDpsCoefficient(int level)
    {
        return TotalCoefficient * GetDamageMultiplier(level) / GetCooldown(level);
    }
}
```

### 8-2. ComboData ScriptableObject

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "NewCombo", menuName = "RunningRight/ComboData")]
public class ComboData : ScriptableObject
{
    public string comboName;             // "BasicCombo"
    public ComboHitData[] hits;          // 4타 콤보 데이터 배열
    public float comboResetTime;         // 콤보 리셋 시간 (0.8초)

    /// <summary>
    /// 콤보 1사이클 총 대미지 계수
    /// </summary>
    public float TotalCoefficient
    {
        get
        {
            float total = 0f;
            foreach (var hit in hits)
                total += hit.damageCoefficient;
            return total;
        }
    }

    /// <summary>
    /// 콤보 1사이클 총 시간
    /// </summary>
    public float TotalDuration
    {
        get
        {
            float total = 0f;
            foreach (var hit in hits)
                total += hit.motionDuration;
            return total;
        }
    }

    /// <summary>
    /// 콤보 DPS 계수 (계수/초)
    /// </summary>
    public float DpsCoefficient => TotalCoefficient / TotalDuration;
}

[System.Serializable]
public class ComboHitData
{
    public int hitIndex;                // 0~3 (1타~4타)
    public float damageCoefficient;     // 대미지 계수 (1.0 = 100%)
    public float hitboxWidth;           // 히트박스 너비 (유닛)
    public float hitboxHeight;          // 히트박스 높이 (유닛)
    public float knockbackForce;        // 넉백 힘
    public float hitStopDuration;       // 히트스톱 시간(초)
    public float motionDuration;        // 모션 재생 시간(초)
    public float hitFrameRatio;         // 대미지 적용 시점 (0~1, 기본 0.4)
    public string animationClipName;    // 애니메이션 클립 이름
    public AudioClip hitSfx;            // 타격 효과음
    public GameObject hitEffectPrefab;  // 히트 이펙트 프리팹
}
```

### 8-3. SkillLevelSaveData (저장용)

```csharp
[System.Serializable]
public class SkillLevelSaveData
{
    public string skillId;              // 스킬 ID
    public int currentLevel;            // 현재 레벨
    public bool isUnlocked;             // 해금 여부
}

[System.Serializable]
public class SkillSaveContainer
{
    public List<SkillLevelSaveData> skills = new List<SkillLevelSaveData>();
    public int[] comboCounts;           // 콤보 타수별 누적 사용 횟수 (통계용)
}
```

### 8-4. 파일 구조

```
Assets/
├── ScriptableObjects/
│   ├── Skills/
│   │   ├── SKILL_001_NeckGrab.asset
│   │   ├── SKILL_002_StabFrenzy.asset
│   │   ├── SKILL_003_RisingUppercutIsh.asset
│   │   ├── SKILL_004_SpinSpinTornado.asset
│   │   ├── SKILL_005_ChargeRecklessly.asset
│   │   ├── SKILL_006_FloorIsLavaWave.asset
│   │   ├── SKILL_007_PretendAwakening.asset
│   │   └── SKILL_008_TrueFinalSecretArt.asset
│   └── Combos/
│       └── BasicCombo.asset
├── Scripts/
│   ├── Data/
│   │   ├── SkillData.cs
│   │   ├── ComboData.cs
│   │   └── SkillLevelSaveData.cs
│   └── Character/
│       ├── SkillManager.cs            # 스킬 시전 관리
│       ├── SkillAutoCaster.cs         # 자동 시전 AI
│       └── ComboController.cs         # 평타 콤보 관리
```

---

## 부록 A: 설계 근거 및 참고 사항

### A. DNF 패러디 네이밍 원칙

| 원칙 | 예시 |
|------|------|
| 원작 스킬명 유사 발음/의미 | 고어 크로스 → 뒷목 잡기 (고어=뒷목 잡힘) |
| 스킬 효과의 과장된 셀프 디스 | "팔이 짧아서 어깨 높이가 한계" |
| 메타 유머 (게임/유저 경험 풍자) | "던파 유저의 뒷목도 함께 잡힌다" |
| 인터넷 밈 활용 | "바닥은 용암 놀이" |
| 자기 비하적 과장 | "진짜 최종이라고 세 번째 말하는 중" |

### B. 밸런스 조정 시 주의점

1. **스킬 레벨업 비용 곡선은 골드 수입과 연동 필수** - 스테이지별 골드 수입 설계 후 역산
2. **궁극기는 DPS 효율보다 연출/쾌감이 핵심** - 숫자보다 화면이 화려해야 함
3. **AoE 스킬의 체감 효율은 적 밀집도에 크게 의존** - 몬스터 스폰 배치와 연동
4. **오버킬 방지 로직 튜닝** - 너무 엄격하면 스킬 사용 빈도 감소, 너무 느슨하면 쿨타임 낭비
5. **히트스톱/카메라 셰이크 과다 주의** - 모바일 환경에서 과도한 연출은 멀미 유발

### C. 향후 확장 포인트

| 항목 | 설명 |
|------|------|
| 스킬 각성 | 스킬 Lv.20 달성 후 "각성" 시스템 (스킬 변형/강화) |
| 스킬 룬 | 스킬에 장착하는 룬으로 추가 효과 (화상, 빙결, 출혈 등) |
| 스킬 프리셋 | 자동 시전 우선순위 커스텀 (상급 유저용) |
| 패시브 스킬 | 스탯 보너스형 패시브 스킬 트리 |
| 전생 스킬 | 전생 시 해금되는 특수 스킬 라인 |

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| 1.0 | 2026-03-31 | 초안 작성 |
| 1.1 | 2026-03-31 | 수치 정합 (골드 수입 참조값 수정) |
| 1.2 | 2026-03-31 | 포맷 표준화 |
