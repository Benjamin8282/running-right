# 장비 시스템 설계 문서

> "오른쪽 달리기" 장비/아이템 시스템 상세 설계
> 작성일: 2026-03-31

---

## 목차

1. [장비 시스템 개요](#1-장비-시스템-개요)
2. [장비 등급 체계](#2-장비-등급-체계)
3. [장비 데이터 테이블](#3-장비-데이터-테이블)
4. [장비 획득 방법](#4-장비-획득-방법)
5. [장비 강화 시스템](#5-장비-강화-시스템)
6. [장비 세트 효과](#6-장비-세트-효과)
7. [장비 비교 및 자동 장착](#7-장비-비교-및-자동-장착)
8. [장비 분해/재활용](#8-장비-분해재활용)
9. [ScriptableObject 스키마](#9-scriptableobject-스키마)

---

## 1. 장비 시스템 개요

### 1-1. 설계 철학

방치형 게임의 특성상 장비 시스템은 **간결하되 보상감이 큰** 구조로 설계한다.
플레이어가 복잡한 의사결정 없이도 성장을 느낄 수 있으면서, 가끔 드롭되는
고등급 장비가 "와!" 하는 순간을 만들어야 한다.

- DNF 패러디답게 장비 이름과 효과를 유머러스하게 구성
- 자동 장착 기능으로 방치 플레이 흐름을 끊지 않음
- 구슬 조각(Orb Fragment) 기반 가챠로 수집 재미 제공

### 1-2. 장비 슬롯 구성

총 **5개 슬롯**을 운용한다.

| 슬롯 | EquipSlot (enum) | 주요 영향 스탯 | 설명 |
|------|-------------------|----------------|------|
| 무기 | `Weapon` | ATK, CRIT_DMG | 공격의 핵심. 가장 큰 ATK 보너스 |
| 상의 | `Armor` | HP, ATK | 방어와 약간의 공격력 |
| 하의 | `Pants` | HP, MOVE_SPEED | 체력과 이동 속도 |
| 어깨 | `Shoulder` | ATK, ATK_SPEED | 공격력과 공격 속도 |
| 악세서리 | `Accessory` | CRIT_RATE, CRIT_DMG | 치명타 특화 |

### 1-3. 스탯 적용 공식

장비 스탯은 캐릭터 기본 스탯에 **가산(additive)** 방식으로 적용된다.

```
최종_ATK = Base_ATK + Sum(장비_ATK) + Sum(세트효과_ATK) + 강화_보너스_ATK
최종_CRIT_RATE = Base_CRIT_RATE + Sum(장비_CRIT_RATE)  // 상한 80%
최종_CRIT_DMG = Base_CRIT_DMG + Sum(장비_CRIT_DMG)
최종_ATK_SPEED = Base_ATK_SPEED + Sum(장비_ATK_SPEED)  // 상한 300%
최종_MOVE_SPEED = Base_MOVE_SPEED + Sum(장비_MOVE_SPEED)
```

스탯 상한(Cap):
- `CRIT_RATE`: 최대 80%
- `ATK_SPEED`: 최대 300% (기본 100% 기준)
- `MOVE_SPEED`: 최대 200% (기본 100% 기준)

---

## 2. 장비 등급 체계

### 2-1. 등급 정의

| 등급 | Rarity (enum) | 색상 코드 | 스탯 배율 범위 | 특수 효과 |
|------|---------------|-----------|---------------|----------|
| 일반 | `Common` | `#FFFFFF` (흰색) | 1.0x | 없음 |
| 고급 | `Uncommon` | `#4CAF50` (초록) | 1.3x ~ 1.5x | 없음 |
| 희귀 | `Rare` | `#2196F3` (파랑) | 1.6x ~ 2.0x | 없음 |
| 영웅 | `Epic` | `#9C27B0` (보라) | 2.2x ~ 2.8x | 랜덤 부가 옵션 1개 |
| 전설 | `Legendary` | `#FF9800` (주황) | 3.0x ~ 4.0x | 고유 특수 효과 + 부가 옵션 2개 |

### 2-2. 스탯 배율 적용 방식

장비의 최종 스탯은 다음과 같이 계산된다:

```
장비_스탯 = BaseStat * Random(배율_최소, 배율_최대)
```

예시: `Common` 무기의 BaseStat ATK가 10이라면, 최종 ATK = `10 * 1.0 = 10`
예시: `Epic` 무기의 BaseStat ATK가 10이라면, 최종 ATK = `10 * Random(2.2, 2.8)` = 22~28

### 2-3. 부가 옵션 풀

`Epic` 이상 등급에서 부여되는 랜덤 부가 옵션:

| 부가 옵션 | 수치 범위 | 비고 |
|-----------|----------|------|
| ATK +N | +5 ~ +30 | |
| ATK_SPEED +N% | +3% ~ +15% | |
| CRIT_RATE +N% | +2% ~ +10% | |
| CRIT_DMG +N% | +5% ~ +25% | |
| MOVE_SPEED +N% | +3% ~ +12% | |
| 골드 획득량 +N% | +5% ~ +20% | 방치형 특화 |
| 구슬 조각 획득량 +N% | +3% ~ +15% | 방치형 특화 |

---

## 3. 장비 데이터 테이블

### 3-1. 무기 (Weapon)

| ID | 이름 | Rarity | Base ATK | Base CRIT_DMG | 특수 효과 |
|----|------|--------|----------|---------------|----------|
| `WPN_001` | 동네 빨래방 방망이 | Common | 10 | 0% | - |
| `WPN_002` | 카잔의 중고 검 (반품불가) | Uncommon | 15 | 5% | - |
| `WPN_003` | 세리아의 요리칼 | Rare | 22 | 10% | - |
| `WPN_004` | 무색 큐브 조각으로 만든 대검 | Epic | 30 | 18% | - |
| `WPN_005` | 바칼의 이빨 요지개 | Legendary | 45 | 30% | **용치 가호**: 공격 시 10% 확률로 추가 데미지 50% 발동 |

### 3-2. 상의 (Armor)

| ID | 이름 | Rarity | Base ATK | Base HP | 특수 효과 |
|----|------|--------|----------|---------|----------|
| `ARM_001` | 헨돈마이어 할인 조끼 | Common | 3 | 50 | - |
| `ARM_002` | 고블린 패드에서 산 갑옷 | Uncommon | 5 | 80 | - |
| `ARM_003` | 아이러니한 천의 (구멍 남) | Rare | 8 | 130 | - |
| `ARM_004` | 마이어스의 수선한 판금갑 | Epic | 12 | 200 | - |

### 3-3. 하의 (Pants)

| ID | 이름 | Rarity | Base HP | Base MOVE_SPEED | 특수 효과 |
|----|------|--------|---------|-----------------|----------|
| `PNT_001` | 아라드 체육복 바지 | Common | 40 | 3% | - |
| `PNT_002` | 마계 직수입 청바지 | Uncommon | 65 | 5% | - |
| `PNT_003` | 시간의 문 통행증 바지 | Rare | 100 | 8% | - |
| `PNT_004` | 히든 에이브스 레깅스 | Epic | 160 | 12% | - |
| `PNT_005` | 루크의 심해 잠수복 하의 | Legendary | 250 | 18% | **심해의 가속**: 방 클리어 시 5초간 MOVE_SPEED +30% |

### 3-4. 어깨 (Shoulder)

| ID | 이름 | Rarity | Base ATK | Base ATK_SPEED | 특수 효과 |
|----|------|--------|----------|----------------|----------|
| `SHD_001` | 뻥튀기 어깨보호대 | Common | 5 | 3% | - |
| `SHD_002` | 세리아 손뜨개 견갑 | Uncommon | 8 | 5% | - |
| `SHD_003` | GBL교 수련용 어깨장식 | Rare | 13 | 8% | - |
| `SHD_004` | 사도의 끄적거린 어깨패드 | Epic | 18 | 13% | - |

### 3-5. 악세서리 (Accessory)

| ID | 이름 | Rarity | Base CRIT_RATE | Base CRIT_DMG | 특수 효과 |
|----|------|--------|----------------|---------------|----------|
| `ACC_001` | 고블린 동전 반지 | Common | 2% | 5% | - |
| `ACC_002` | 뻘건 큐브 목걸이 | Uncommon | 4% | 8% | - |
| `ACC_003` | 오즈마의 찌그러진 팔찌 | Rare | 6% | 13% | - |
| `ACC_004` | 시로코 진주 귀걸이 (가짜) | Epic | 9% | 20% | - |
| `ACC_005` | 카인의 잃어버린 열쇠고리 | Legendary | 12% | 30% | **열쇠 마스터**: 스테이지 클리어 시 구슬 조각 +20% 추가 획득 |

> **참고**: 전설 등급 아이템은 총 3종(WPN_005, PNT_005, ACC_005)이며,
> 각각 고유 특수 효과를 보유한다.

---

## 4. 장비 획득 방법

### 4-1. 몬스터 드롭

몬스터를 처치하면 일정 확률로 장비가 드롭된다.

**몬스터 유형별 드롭률:**

| 몬스터 유형 | 장비 드롭 확률 | 최대 드롭 등급 |
|------------|--------------|---------------|
| 일반 몬스터 | 1.0% | Rare |
| 정예 몬스터 | 5.0% | Epic |
| 개 얼굴 구슬 (보스) | 15.0% | Legendary |

**등급별 드롭 확률 (장비가 드롭되었을 때의 조건부 확률):**

| 등급 | 일반 몬스터 | 정예 몬스터 | 보스 (구슬) |
|------|-----------|-----------|------------|
| Common | 60% | 35% | 15% |
| Uncommon | 30% | 35% | 25% |
| Rare | 10% | 20% | 30% |
| Epic | - | 10% | 20% |
| Legendary | - | - | 10% |

**슬롯 결정**: 드롭 시 5개 슬롯 중 균등 확률(각 20%)로 결정.

### 4-2. 구슬 조각 가챠

개 얼굴 구슬 파괴 시 획득하는 **구슬 조각(Orb Fragment)**으로 가챠를 돌린다.

**가챠 비용:**

| 가챠 유형 | 비용 | 설명 |
|----------|------|------|
| 단일 뽑기 | 구슬 조각 50개 | 장비 1개 획득 |
| 10연 뽑기 | 구슬 조각 450개 (10% 할인) | 장비 10개 획득, **Rare 이상 1개 보장** |

**가챠 등급 확률:**

| 등급 | 확률 |
|------|------|
| Common | 40% |
| Uncommon | 35% |
| Rare | 18% |
| Epic | 6% |
| Legendary | 1% |

### 4-3. 천장(Pity) 시스템

플레이어의 불만을 방지하고 공정한 보상감을 제공하기 위한 안전장치.

| 천장 유형 | 조건 | 보장 내용 |
|----------|------|----------|
| 소천장 (Soft Pity) | 50회 연속 Epic 이상 미획득 | 51회째부터 Epic 확률 2배 (+6% = 12%) |
| 대천장 (Hard Pity) | 100회 연속 Legendary 미획득 | 100회째 **Legendary 확정** |

- 천장 카운터는 해당 등급 장비 획득 시 리셋
- 가챠 기록(pityCounter)은 저장 데이터에 포함

### 4-4. 구슬 조각 획득량 기준

| 소스 | 획득량 |
|------|--------|
| 보스 구슬 파괴 (기본) | `5 * (1 + floor(stage/10) * 0.25)` |
| 오프라인 보상 | 시간당 (stage * 0.5)개, 효율 계수 0.3 적용 |
| 업적 보상 | 고정 보상 (업적별 상이) |

**스테이지별 구슬 조각 획득 예시:**

| 스테이지 | 보스 1회 획득량 | 단일 뽑기(50개)까지 | 비고 |
|----------|----------------|-------------------|------|
| 1~9 | 5개 | 보스 10회 | `5 * (1 + 0) = 5` |
| 10~19 | 6개 (6.25 → 내림) | 보스 약 8회 | `5 * (1 + 1 * 0.25) = 6.25` |
| 20~29 | 7개 (7.5 → 내림) | 보스 약 7회 | `5 * (1 + 2 * 0.25) = 7.5` |
| 50~59 | 11개 (11.25 → 내림) | 보스 약 5회 | `5 * (1 + 5 * 0.25) = 11.25` |
| 100~109 | 17개 (17.5 → 내림) | 보스 약 3회 | `5 * (1 + 10 * 0.25) = 17.5` |

**전설 등급 기대 획득 소요 (대천장 100회 = 구슬 조각 5,000개 기준):**

| 스테이지 | 보스 1회 획득량 | 대천장까지 보스 횟수 |
|----------|----------------|-------------------|
| 1 | 5개 | 1,000회 |
| 10 | 6개 | 약 834회 |
| 50 | 11개 | 약 455회 |
| 100 | 17개 | 약 294회 |

---

## 5. 장비 강화 시스템

### 5-1. 강화 단계

장비는 **+0 ~ +15**까지 강화 가능하며, 강화 단계에 따라 성공률이 하락한다.

| 강화 단계 | 성공률 | 스탯 증가율 (BaseStat 대비) | 골드 비용 | 구슬 조각 비용 | 실패 패널티 |
|----------|--------|--------------------------|----------|--------------|-----------|
| +0 → +1 | 100% | +5% | 100 | 0 | - |
| +1 → +2 | 100% | +5% | 200 | 0 | - |
| +2 → +3 | 95% | +5% | 400 | 0 | - |
| +3 → +4 | 90% | +7% | 800 | 0 | - |
| +4 → +5 | 85% | +7% | 1,500 | 0 | - |
| +5 → +6 | 80% | +7% | 3,000 | 5 | - |
| +6 → +7 | 70% | +10% | 5,000 | 10 | - |
| +7 → +8 | 60% | +10% | 8,000 | 15 | 단계 유지 (하락 없음) |
| +8 → +9 | 50% | +10% | 12,000 | 20 | 단계 유지 |
| +9 → +10 | 40% | +15% | 18,000 | 30 | 단계 유지 |
| +10 → +11 | 30% | +15% | 25,000 | 40 | **1단계 하락** |
| +11 → +12 | 25% | +15% | 35,000 | 55 | **1단계 하락** |
| +12 → +13 | 20% | +20% | 50,000 | 70 | **1단계 하락** |
| +13 → +14 | 15% | +20% | 70,000 | 90 | **2단계 하락** |
| +14 → +15 | 10% | +25% | 100,000 | 120 | **2단계 하락** |

### 5-2. 강화 스탯 계산

```
강화_보너스 = BaseStat * Sum(각 단계 스탯 증가율)
```

예시: ATK 10짜리 Common 무기를 +5까지 강화 시
- 증가율 합계: 5% + 5% + 5% + 7% + 7% = 29%
- 강화 보너스 ATK: 10 * 0.29 = 2.9 (반올림 → 3)
- 최종 ATK: 10 + 3 = 13

예시: ATK 45짜리 Legendary 무기를 +15까지 강화 시
- 증가율 합계: 5%*3 + 7%*3 + 10%*3 + 15%*3 + 20%*2 + 25% = 15% + 21% + 30% + 45% + 40% + 25% = 176%
- 강화 보너스 ATK: 45 * 1.76 = 79.2 (반올림 → 79)
- 최종 ATK: 45 + 79 = 124

### 5-3. 강화 연출

| 결과 | 연출 |
|------|------|
| 성공 (+1~+9) | 장비 아이콘 금색 반짝임 + "강화 성공!" 텍스트 |
| 성공 (+10~+15) | 화면 전체 이펙트 + 카메라 셰이크 + "!!강화 대성공!!" |
| 실패 (유지) | 장비 아이콘 흔들림 + 회색 연기 이펙트 |
| 실패 (하락) | 적색 깨짐 이펙트 + 슬픈 효과음 |

### 5-4. 강화 보호권

| 아이템 | 효과 | 획득처 |
|--------|------|--------|
| 강화 보호권 (하급) | +10 이하 강화 실패 시 단계 유지 보장 | 업적, 이벤트 |
| 강화 보호권 (상급) | +11 이상 강화 실패 시 단계 유지 보장 | 보석 상점 (50보석) |

---

## 6. 장비 세트 효과

### 6-1. "아라드 패션왕" 세트

> *"던전에서도 패션은 포기할 수 없다."*

| 구성 아이템 | 슬롯 |
|------------|------|
| 카잔의 중고 검 (반품불가) `WPN_002` | Weapon |
| 아이러니한 천의 (구멍 남) `ARM_003` | Armor |
| 세리아 손뜨개 견갑 `SHD_002` | Shoulder |
| 뻘건 큐브 목걸이 `ACC_002` | Accessory |

| 세트 수 | 보너스 |
|---------|--------|
| 2세트 | ATK +15, ATK_SPEED +5% |
| 4세트 | **"패션 버프"**: 모든 스탯 +10%, 골드 획득량 +15% |

### 6-2. "심해 탐험대" 세트

> *"심해에서 건져 올린 것들이라 약간 비린내가 난다."*

| 구성 아이템 | 슬롯 |
|------------|------|
| 바칼의 이빨 요지개 `WPN_005` | Weapon |
| 루크의 심해 잠수복 하의 `PNT_005` | Pants |
| 시로코 진주 귀걸이 (가짜) `ACC_004` | Accessory |

| 세트 수 | 보너스 |
|---------|--------|
| 2세트 | CRIT_RATE +8%, HP +150 |
| 3세트 | **"심해의 분노"**: 치명타 시 ATK의 20% 추가 피해 (3초 쿨타임) |

### 6-3. "교단의 유물" 세트

> *"GBL교에서 남몰래 유출된 유물들. 사용 시 부작용이 있을 수도..."*

| 구성 아이템 | 슬롯 |
|------------|------|
| 무색 큐브 조각으로 만든 대검 `WPN_004` | Weapon |
| 마이어스의 수선한 판금갑 `ARM_004` | Armor |
| 사도의 끄적거린 어깨패드 `SHD_004` | Shoulder |
| 오즈마의 찌그러진 팔찌 `ACC_003` | Accessory |

| 세트 수 | 보너스 |
|---------|--------|
| 2세트 | ATK +25, CRIT_DMG +10% |
| 4세트 | **"사도의 축복"**: 10초마다 3초간 ATK +40%, 이후 1초간 ATK -20% (부작용) |

---

## 7. 장비 비교 및 자동 장착

### 7-1. 자동 장착 시스템

방치형 게임의 핵심 편의 기능. 플레이어가 직접 비교하지 않아도 최적의 장비를
자동으로 장착한다.

**자동 장착 로직:**

```
장비_점수(EquipmentScore) =
    (ATK * 1.0) +
    (HP * 0.3) +
    (ATK_SPEED * 50) +      // %를 소수로 변환 후 곱셈 (0.05 → 2.5)
    (CRIT_RATE * 80) +      // %를 소수로 변환 후 곱셈
    (CRIT_DMG * 40) +       // %를 소수로 변환 후 곱셈
    (MOVE_SPEED * 30) +     // %를 소수로 변환 후 곱셈
    세트효과_가중치           // 세트 완성 시 보너스 점수 +100
```

- 새 장비 획득 시 현재 장착 장비와 점수 비교
- 점수가 높으면 자동 장착 (설정에서 ON/OFF 가능)
- **자동 장착 ON**이 기본값 (방치형 특성)

### 7-2. 비교 UI 사양

장비 탭에서 아이템을 탭하면 비교 팝업이 표시된다.

```
┌─────────────────────────────────────────┐
│          장비 비교                 [X]   │
│                                         │
│  [현재 장비]         [새 장비]           │
│  ┌───────────┐      ┌───────────┐       │
│  │ WPN_002   │      │ WPN_004   │       │
│  │ 카잔의    │  VS  │ 무색 큐브  │       │
│  │ 중고 검   │      │ 대검      │       │
│  │ +3        │      │ +0        │       │
│  └───────────┘      └───────────┘       │
│                                         │
│  ATK:    18  →  30    ▲ +12 (초록)      │
│  CRIT:    5% →  18%   ▲ +13% (초록)    │
│  HP:      0  →   0      - (회색)        │
│  SCORE: 210  → 352    ▲ +142 (초록)    │
│                                         │
│  세트: "아라드 패션왕" 2/4               │
│  → 장착 해제 시 세트 효과 소실!  (빨강)  │
│                                         │
│       [장착하기]     [취소]              │
└─────────────────────────────────────────┘
```

**비교 UI 규칙:**
- 스탯 증가: 초록색 (▲)
- 스탯 감소: 빨간색 (▼)
- 변화 없음: 회색 (-)
- 세트 효과 변동 시 경고 메시지 표시

### 7-3. 인벤토리

- 인벤토리 슬롯: 최대 **100칸** (초기 50칸, 보석으로 확장 가능)
- 정렬 옵션: 등급순, 슬롯순, 점수순, 획득순
- 필터: 슬롯별, 등급별
- 인벤토리 가득 참 시: 자동으로 가장 낮은 점수의 Common 장비 분해 (설정 가능)

---

## 8. 장비 분해/재활용

### 8-1. 분해 시스템

불필요한 장비를 분해하여 자원을 회수한다.

**분해 획득 자원:**

| 등급 | 골드 | 구슬 조각 | 강화석 |
|------|------|----------|--------|
| Common | 50 | 1 | 0 |
| Uncommon | 150 | 3 | 1 |
| Rare | 400 | 8 | 3 |
| Epic | 1,000 | 20 | 8 |
| Legendary | 3,000 | 50 | 20 |

**강화된 장비 분해 보너스:**
- 강화 레벨 1당 골드 +10%, 구슬 조각 +5% 추가
- 예시: +5 Rare 분해 → 골드 400 * 1.5 = 600, 구슬 조각 8 * 1.25 = 10

### 8-2. 강화석 (Enhancement Stone)

분해로 얻는 보조 자원. 강화 시 **골드 비용을 50% 감소**시키는 데 사용.

| 사용처 | 소모량 |
|--------|--------|
| +1~+5 강화 시 골드 50% 할인 | 강화석 1개 |
| +6~+10 강화 시 골드 50% 할인 | 강화석 3개 |
| +11~+15 강화 시 골드 50% 할인 | 강화석 5개 |

### 8-3. 일괄 분해

편의 기능으로 **일괄 분해**를 지원한다.

- "Common 전체 분해" 버튼
- "Uncommon 이하 전체 분해" 버튼
- 잠금(Lock) 기능: 중요한 장비에 자물쇠를 걸어 실수 분해 방지
- 장착 중인 장비는 분해 불가

---

## 9. ScriptableObject 스키마

### 9-1. EquipmentData (장비 정의 - ScriptableObject)

에디터에서 장비 원본 데이터를 정의하는 ScriptableObject.

```csharp
[CreateAssetMenu(fileName = "NewEquipment", menuName = "Data/EquipmentData")]
public class EquipmentData : ScriptableObject
{
    [Header("기본 정보")]
    public string equipmentId;         // "WPN_001", "ARM_003" 등
    public string equipmentName;       // "동네 빨래방 방망이"
    public string description;         // 장비 설명 텍스트
    public Sprite icon;                // 장비 아이콘 스프라이트
    public EquipSlot slot;             // Weapon, Armor, Pants, Shoulder, Accessory
    public Rarity rarity;              // Common, Uncommon, Rare, Epic, Legendary

    [Header("기본 스탯")]
    public float baseATK;
    public float baseHP;
    public float baseATK_SPEED;        // % 단위 (예: 5 = 5%)
    public float baseCRIT_RATE;        // % 단위
    public float baseCRIT_DMG;         // % 단위
    public float baseMOVE_SPEED;       // % 단위

    [Header("등급 배율")]
    public float rarityMultiplierMin;  // 해당 등급 배율 최소값
    public float rarityMultiplierMax;  // 해당 등급 배율 최대값

    [Header("특수 효과 (Legendary 전용)")]
    public bool hasSpecialEffect;
    public string specialEffectId;     // "dragon_tooth_blessing", "deep_sea_accel" 등
    public string specialEffectDesc;   // "공격 시 10% 확률로 추가 데미지 50% 발동"
    public float specialEffectValue1;  // 효과 수치 1 (확률, 지속시간 등)
    public float specialEffectValue2;  // 효과 수치 2 (데미지 배율, 버프량 등)

    [Header("세트 정보")]
    public string setId;               // "arad_fashion", "deep_sea", "cult_relics" (없으면 "")
}
```

### 9-2. EquipmentInstance (장비 인스턴스 - 런타임 데이터)

플레이어가 보유한 개별 장비 인스턴스. JSON 직렬화하여 저장.

```csharp
[System.Serializable]
public class EquipmentInstance
{
    public string instanceId;          // 고유 인스턴스 ID (GUID)
    public string equipmentDataId;     // EquipmentData의 equipmentId 참조

    [Header("실제 적용 스탯 (생성 시 배율 랜덤 적용 결과)")]
    public float finalATK;
    public float finalHP;
    public float finalATK_SPEED;
    public float finalCRIT_RATE;
    public float finalCRIT_DMG;
    public float finalMOVE_SPEED;

    [Header("강화")]
    public int enhanceLevel;           // 0 ~ 15
    public float enhanceBonusATK;      // 강화로 인한 추가 ATK
    public float enhanceBonusHP;
    public float enhanceBonusATK_SPEED;
    public float enhanceBonusCRIT_RATE;
    public float enhanceBonusCRIT_DMG;
    public float enhanceBonusMOVE_SPEED;

    [Header("부가 옵션 (Epic 이상)")]
    public List<BonusOption> bonusOptions;  // 0~2개

    [Header("상태")]
    public bool isEquipped;            // 현재 장착 중 여부
    public bool isLocked;             // 분해 잠금 여부
    public long acquiredTimestamp;      // 획득 시각 (Unix timestamp)
}

[System.Serializable]
public class BonusOption
{
    public StatType statType;          // ATK, HP, ATK_SPEED, CRIT_RATE, CRIT_DMG, MOVE_SPEED, GOLD_BONUS, ORB_BONUS
    public float value;                // 수치
}
```

### 9-3. Enum 정의

```csharp
public enum EquipSlot
{
    Weapon,
    Armor,
    Pants,
    Shoulder,
    Accessory
}

public enum Rarity
{
    Common,
    Uncommon,
    Rare,
    Epic,
    Legendary
}

public enum StatType
{
    ATK,
    HP,
    ATK_SPEED,
    CRIT_RATE,
    CRIT_DMG,
    MOVE_SPEED,
    GOLD_BONUS,
    ORB_BONUS
}
```

### 9-4. EquipmentSetData (세트 정의 - ScriptableObject)

```csharp
[CreateAssetMenu(fileName = "NewEquipmentSet", menuName = "Data/EquipmentSetData")]
public class EquipmentSetData : ScriptableObject
{
    public string setId;               // "arad_fashion"
    public string setName;             // "아라드 패션왕"
    public string setDescription;      // 세트 설명 (유머 포함)
    public List<string> equipmentIds;  // 세트에 포함된 장비 ID 목록

    [Header("2세트 효과")]
    public List<BonusOption> twoSetBonus;
    public string twoSetDescription;

    [Header("3세트 효과 (선택)")]
    public List<BonusOption> threeSetBonus;
    public string threeSetDescription;

    [Header("4세트 효과 (선택)")]
    public List<BonusOption> fourSetBonus;
    public string fourSetDescription;
    public string fourSetSpecialEffectId;  // 특수 효과 ID (있는 경우)
}
```

### 9-5. 저장 데이터 구조

```csharp
[System.Serializable]
public class EquipmentSaveData
{
    public List<EquipmentInstance> inventory;    // 보유 장비 전체
    public Dictionary<EquipSlot, string> equipped; // 슬롯별 장착된 instanceId
    public int inventoryCapacity;               // 현재 인벤토리 최대 칸 수
    public int gachaPityCounter;                // 가챠 천장 카운터
    public int gachaEpicPityCounter;            // Epic 소천장 카운터
    public int totalGachaPulls;                 // 누적 가챠 횟수 (통계용)
}
```

---

## 부록: 밸런스 노트

### 장비 파워 기여도 목표

전체 캐릭터 전투력에서 장비가 차지하는 비율 목표:

| 게임 진행 구간 | 장비 기여도 | 스탯 강화 기여도 | 스킬 기여도 |
|--------------|-----------|----------------|-----------|
| 초반 (1~50 스테이지) | 20% | 60% | 20% |
| 중반 (51~200 스테이지) | 35% | 40% | 25% |
| 후반 (201+ 스테이지) | 45% | 30% | 25% |

### 장비 확장 계획

향후 업데이트에서 추가 가능한 요소:
- **신화(Mythic)** 등급: 전설 위의 최상위 등급, 고유 스킬 부여
- **각성 시스템**: 동일 장비 5개 합성으로 각성, 외형 변경 + 스탯 대폭 상승
- **코스튬 슬롯**: 전투력 무관, 외형 변경용 (과금 요소)
- **펫 장비**: 펫 시스템 도입 시 함께 추가

---

> 이 문서는 개발 진행에 따라 지속적으로 업데이트됩니다.
> 밸런스 수치는 플레이테스트 결과에 따라 조정될 수 있습니다.
