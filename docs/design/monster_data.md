# 몬스터 데이터 설계 문서

> "오른쪽 달리기" (Running Right) - 몬스터 시스템 상세 설계
> 작성일: 2026-03-31
> 버전: 1.0
> 관련 문서: [MASTER_PLAN.md](../../MASTER_PLAN.md), [CLAUDE.md](../../CLAUDE.md)

---

## 목차

1. [몬스터 분류 체계](#1-몬스터-분류-체계)
2. [기본 몬스터 데이터 테이블](#2-기본-몬스터-데이터-테이블)
3. [정예 몬스터 데이터 테이블](#3-정예-몬스터-데이터-테이블)
4. [구슬 보스 데이터](#4-구슬-보스-데이터)
5. [스케일링 공식](#5-스케일링-공식)
6. [드랍 테이블](#6-드랍-테이블)
7. [스폰 규칙](#7-스폰-규칙)
8. [행동 패턴(AI)](#8-행동-패턴ai)
9. [ScriptableObject 스키마](#9-scriptableobject-스키마)

---

## 1. 몬스터 분류 체계

### 1-1. 분류 개요

| 분류 | 등급 코드 | 역할 | 등장 빈도 | HP 계수 | 위험도 |
|------|-----------|------|-----------|---------|--------|
| **일반 (Normal)** | `N` | 잡몹, 쓸어버리는 쾌감 제공 | 매우 높음 | x1.0 | 낮음 |
| **정예 (Elite)** | `E` | 중간 긴장감, 약간의 전략 요구 | 보통 | x3.0 | 중간 |
| **보스 구슬 (Boss)** | `B` | 스테이지 마무리, 파괴 연출 | 스테이지당 1회 | x8.0 | 높음 |

### 1-2. 분류별 설계 의도

**일반 몬스터 (Normal)**
- 한 번에 5~8마리씩 등장하여 캐릭터의 범위 스킬로 한 방에 쓸려나가는 쾌감 제공
- HP가 낮아 플레이어의 성장을 체감하게 해주는 역할
- 주요 골드 수입원 (소량 x 다수)

**정예 몬스터 (Elite)**
- 일반 몬스터 사이에 1~2마리 섞여 등장하여 "잠깐 멈칫"하는 긴장감 제공
- 고유 공격 패턴이 있어 자동 전투에서도 시각적 변화를 줌
- 드랍 보상이 일반 대비 3~5배

**보스 구슬 (Boss)**
- 마지막 방에서만 등장하는 개 얼굴 구슬
- 공격 패턴 없이 높은 HP만 보유 (샌드백 역할)
- 파괴 시 화려한 연출 + 구슬 조각 드랍 + 스테이지 클리어

### 1-3. 시각 구분 규칙

| 분류 | 이름 색상 | 체력바 | 등장 연출 |
|------|-----------|--------|-----------|
| 일반 | 흰색 | 없음 (데미지 텍스트만) | 없음, 자연 배치 |
| 정예 | 주황색 | 몬스터 위 개별 HP바 | 등장 시 경고 마크 (!) |
| 보스 | 빨간색 | 화면 상단 대형 HP바 | 전용 등장 컷인 연출 |

---

## 2. 기본 몬스터 데이터 테이블

### 2-1. 일반 몬스터 5종

> DNF 패러디 컨셉: 던전앤파이터의 유명 몬스터들을 웃기게 패러디

| # | id | name | 한글명 | baseHP | baseATK | moveSpeed | attackRange | attackSpeed | knockbackResist | detectionRange | description |
|---|-----|------|--------|--------|---------|-----------|-------------|-------------|-----------------|----------------|-------------|
| 1 | `nm_goblin_parttimer` | GoblinPartTimer | 고블린 알바생 | 50 | 8 | 2.0 | 1.0 | 1.0 | 0.0 | 5.0 | 시급이 적어 의욕 없이 어슬렁거리는 고블린. 때리면 바로 날아간다. |
| 2 | `nm_slime_tax` | SlimeTax | 세금 슬라임 | 70 | 5 | 1.5 | 0.8 | 0.8 | 0.1 | 4.0 | 만지면 골드가 줄어드는 느낌이 드는 끈적한 슬라임. 느리지만 약간 질기다. |
| 3 | `nm_skeleton_intern` | SkeletonIntern | 해골 인턴 | 40 | 12 | 2.5 | 1.2 | 1.3 | 0.0 | 6.0 | 칼퇴를 꿈꾸며 빠르게 뛰어다니는 해골. 공격력은 있지만 HP가 종잇장. |
| 4 | `nm_mushroom_elder` | MushroomElder | 버섯 꼰대 | 90 | 6 | 1.0 | 0.5 | 0.6 | 0.2 | 3.0 | "내가 너만할 땐 말이야..." 말이 많은 버섯. 느리지만 제법 HP가 높다. |
| 5 | `nm_bat_streamer` | BatStreamer | 박쥐 스트리머 | 35 | 10 | 3.0 | 1.5 | 1.5 | 0.0 | 7.0 | 채팅을 읽으며 날아다니는 박쥐. 빠르지만 한 대만 맞으면 방종한다. |

### 2-2. 필드 상세 설명

| 필드 | 타입 | 단위 | 설명 |
|------|------|------|------|
| `id` | string | - | 고유 식별자. `nm_` 접두사는 Normal Monster |
| `name` | string | - | 영문 클래스명 (코드 참조용) |
| `baseHP` | float | HP | 스테이지 1 기준 체력. 스케일링 공식 적용 대상 |
| `baseATK` | float | DMG | 스테이지 1 기준 공격력. 스케일링 공식 적용 대상 |
| `moveSpeed` | float | units/s | 이동 속도. 플레이어 기본 이동 속도(5.0)의 비율 |
| `attackRange` | float | units | 공격 사거리. 이 범위 안에 플레이어가 들어오면 공격 시작 |
| `attackSpeed` | float | attacks/s | 초당 공격 횟수 |
| `knockbackResist` | float | 0.0~1.0 | 넉백 저항. 0.0 = 풀 넉백, 1.0 = 넉백 면역 |
| `detectionRange` | float | units | 플레이어 감지 거리. 이 범위 안에 플레이어가 들어오면 추적 시작 |
| `description` | string | - | 도감/UI용 설명 텍스트 |

### 2-3. 일반 몬스터 역할 분포

```
                  HP 높음
                    |
        [버섯 꼰대]  |
                    |
   느림 ────────────┼──────────── 빠름
                    |
        [세금 슬라임] | [고블린 알바생]
                    |  [해골 인턴]
                    |     [박쥐 스트리머]
                  HP 낮음
```

- **탱커형**: 버섯 꼰대 (높은 HP, 느린 속도)
- **균형형**: 세금 슬라임, 고블린 알바생
- **속공형**: 해골 인턴, 박쥐 스트리머 (낮은 HP, 빠른 속도/공격)

---

## 3. 정예 몬스터 데이터 테이블

### 3-1. 정예 몬스터 3종

| # | id | name | 한글명 | baseHP | baseATK | moveSpeed | attackRange | attackSpeed | knockbackResist | detectionRange | description |
|---|-----|------|--------|--------|---------|-----------|-------------|-------------|-----------------|----------------|-------------|
| 1 | `em_orc_teamlead` | OrcTeamLead | 오크 팀장 | 300 | 25 | 1.8 | 1.5 | 0.8 | 0.5 | 5.0 | "이거 오늘 안에 끝내야 해." 팀원(일반 몬스터)을 이끌고 다니는 오크 팀장. 주먹이 묵직하다. |
| 2 | `em_mage_reviewer` | MageReviewer | 마법사 코드리뷰어 | 200 | 35 | 1.2 | 3.0 | 0.6 | 0.3 | 7.0 | "이 코드 누가 짰어?" 원거리에서 불꽃 리뷰를 날리는 마법사. 사거리가 길다. |
| 3 | `em_golem_server` | GolemServer | 골렘 서버 | 300 | 15 | 0.8 | 1.0 | 0.5 | 0.8 | 4.0 | 504 Gateway Timeout처럼 느리지만 죽지 않는 골렘. 넉백도 안 먹힌다. |

### 3-2. 정예 몬스터 특수 공격 패턴

#### 오크 팀장 (OrcTeamLead)

| 패턴 | 이름 | 조건 | 효과 |
|------|------|------|------|
| 기본 공격 | 주먹 질타 | 사거리 내 플레이어 감지 | 단일 타겟 근접 공격, DMG x1.0 |
| **특수 1** | **야근 명령** | HP 50% 이하 | 3초간 자신의 attackSpeed 2배 증가 (분노 버프) |
| **특수 2** | **팀 소집** | 전투 시작 후 5초 경과 | 주변에 일반 몬스터 2마리 추가 소환 (1회 한정) |

```
[일반 패턴]
Idle → Chase(플레이어 방향) → 사거리 진입 → Attack → 0.3s 후딜 → 반복

[HP 50% 이하]
Attack → 야근명령(ATK_SPEED x2, 3초) → 강화 Attack 반복

[5초 경과 & 소환 미사용]
Attack → 팀소집(일반몹 2마리 소환) → Attack 반복
```

#### 마법사 코드리뷰어 (MageReviewer)

| 패턴 | 이름 | 조건 | 효과 |
|------|------|------|------|
| 기본 공격 | 불꽃 리뷰 | 사거리 내 플레이어 감지 | 원거리 투사체, DMG x1.0, 비행 속도 8.0 |
| **특수 1** | **리젝트 폭발** | 쿨타임 8초 | 플레이어 위치에 1.5초 후 폭발하는 장판 생성, DMG x2.0, 범위 2.0 |
| **특수 2** | **백도어 텔레포트** | 플레이어와 거리 < 1.5 | 플레이어 반대편으로 순간이동 (거리 4.0 확보) |

```
[일반 패턴]
Idle → 사거리 확인 → 불꽃리뷰(원거리) → 1.2s 후딜 → 반복

[플레이어 접근 시]
플레이어 거리 < 1.5 → 백도어 텔레포트(거리 확보) → 불꽃리뷰 재개

[8초마다]
불꽃리뷰 → 리젝트폭발(장판 1.5초 후 폭발) → 불꽃리뷰 재개
```

#### 골렘 서버 (GolemServer)

| 패턴 | 이름 | 조건 | 효과 |
|------|------|------|------|
| 기본 공격 | 서버 펀치 | 사거리 내 플레이어 감지 | 느린 근접 공격, DMG x1.0, 넉백 거리 2배 |
| **특수 1** | **503 에러** | HP 70% 이하 | 2초간 무적 (점검 중 상태, 회색 이펙트), HP 5% 회복 (최대 2,000) |
| **특수 2** | **DDoS 스톰프** | 쿨타임 12초 | 주변 범위 2.5에 DMG x1.5 + 0.5초 스턴 (바닥 찍기) |

```
[일반 패턴]
Idle → 느리게 Chase → 사거리 진입 → 서버펀치 → 1.5s 후딜 → 반복

[HP 70% 이하 & 503 미사용]
피격 → 503에러(2초 무적 + HP 5% 회복, 최대 2,000) → 서버펀치 재개
※ 503 에러는 전투당 최대 2회

[12초마다]
서버펀치 → DDoS 스톰프(범위 2.5, 스턴) → 서버펀치 재개
```

---

## 4. 구슬 보스 데이터

### 4-1. 기본 데이터

| 필드 | 값 | 설명 |
|------|-----|------|
| `id` | `boss_dog_orb` | 보스 구슬 고유 ID |
| `name` | DogFaceOrb | 영문명 |
| `한글명` | 개 얼굴 구슬 | 스테이지 마지막 방의 파괴 대상 |
| `baseHP` | 500 | 기본 체력 |
| `baseATK` | 0 | 공격하지 않음 |
| `moveSpeed` | 0.0 | 고정 위치 (이동 없음) |
| `attackRange` | 0.0 | 없음 |
| `attackSpeed` | 0.0 | 없음 |
| `knockbackResist` | 1.0 | 넉백 면역 (고정 오브젝트) |
| `description` | 왜 개 얼굴인지 아무도 모르는 신비한 구슬. 부수면 다음 던전으로 갈 수 있다. |

### 4-2. 페이즈 시스템

구슬 보스는 공격 패턴이 없는 대신, HP 구간별 시각 변화로 파괴 과정의 쾌감을 제공한다.

| 페이즈 | HP 구간 | 시각 효과 | 사운드 |
|--------|---------|-----------|--------|
| **Phase 1 - 온전** | 100% ~ 70% | 개 얼굴이 평온한 표정. 구슬이 은은하게 빛남 | 일반 타격음 |
| **Phase 2 - 균열** | 70% ~ 40% | 얼굴이 당황한 표정. 구슬에 금이 가기 시작 | 타격 시 "끼깅" 효과음 추가 |
| **Phase 3 - 붕괴** | 40% ~ 10% | 얼굴이 공포 표정. 구슬에 큰 균열 + 빛 누출 | 타격 시 유리 깨지는 소리 |
| **Phase 4 - 파괴** | 10% ~ 0% | 얼굴이 울상. 구슬 전체가 빛으로 가득 참 | 저음 웅웅거림 |
| **파괴 연출** | 0% 도달 | 폭발 이펙트 + 구슬 조각 사방 흩어짐 + 화면 화이트아웃 | 통쾌한 파괴 효과음 |

### 4-3. 파괴 연출 타임라인

```
[0.0s] HP 0 도달 → 히트스톱 0.3초
[0.3s] 구슬 부풀기 애니메이션 (0.5초)
[0.8s] 화면 셰이크 (강도: 0.5, 지속: 0.3초)
[0.8s] 폭발 파티클 + 구슬 조각 파티클 (8~12개 파편)
[1.1s] 화면 화이트아웃 페이드 (0.3초)
[1.4s] "STAGE CLEAR!" 텍스트 표시
[2.0s] 보상 팝업 (골드 + 구슬 조각)
[3.0s] 다음 스테이지 전환
```

### 4-4. 스테이지별 구슬 보스 외형 변화

| 스테이지 구간 | 구슬 외형 | 개 얼굴 표정 |
|---------------|-----------|-------------|
| 1 ~ 20 | 기본 구슬 (회색) | 시바견 무표정 |
| 21 ~ 50 | 초록빛 구슬 | 퍼그 찡그린 얼굴 |
| 51 ~ 100 | 파란빛 구슬 | 불독 화난 얼굴 |
| 101 ~ 200 | 보라빛 구슬 | 도베르만 험상궂은 얼굴 |
| 201+ | 금빛 구슬 | 삼두견 (머리 3개) |

---

## 5. 스케일링 공식

### 5-1. 핵심 공식

#### HP 스케일링

```
MonsterHP = baseHP * (1 + stage * 0.15)
```

#### ATK 스케일링

```
MonsterATK = baseATK * (1 + stage * 0.10)
```

> ATK은 HP보다 완만하게 증가한다. 플레이어가 강해지면 피해를 덜 받는 느낌을 주되,
> 완전히 무시할 수 없는 수준을 유지하기 위함.

#### 보스 구슬 HP 스케일링

```
BossOrbHP = baseHP * (1 + stage * 0.20)
```

> 보스 구슬은 일반/정예 몬스터보다 가파른 HP 스케일링(0.20)을 적용하여
> 후반 스테이지에서도 파괴에 적절한 시간이 소요되도록 한다.

#### 골드 보상 스케일링

```
GoldDrop = baseGold * (1 + stage * 0.12)^1.15
```

#### 구슬 조각 보상 스케일링

```
OrbFragments = baseOrbFragments * (1 + floor(stage / 10) * 0.25)
```

> 구슬 조각은 10스테이지마다 단계적으로 증가. 골드보다 희소한 재화.

### 5-2. 스케일링 예시 계산표

#### 일반 몬스터: 고블린 알바생 (baseHP=50, baseATK=8)

| 스테이지 | HP 공식 | HP | ATK 공식 | ATK |
|----------|---------|-----|----------|------|
| 1 | 50 * (1 + 1*0.15) | **57.5** | 8 * (1 + 1*0.10) | **8.8** |
| 10 | 50 * (1 + 10*0.15) | **125** | 8 * (1 + 10*0.10) | **16** |
| 50 | 50 * (1 + 50*0.15) | **425** | 8 * (1 + 50*0.10) | **48** |
| 100 | 50 * (1 + 100*0.15) | **800** | 8 * (1 + 100*0.10) | **88** |
| 500 | 50 * (1 + 500*0.15) | **3,800** | 8 * (1 + 500*0.10) | **408** |

#### 정예 몬스터: 오크 팀장 (baseHP=300, baseATK=25)

| 스테이지 | HP | ATK |
|----------|----|-----|
| 1 | 345 | 27.5 |
| 10 | 750 | 50 |
| 50 | 2,550 | 150 |
| 100 | 4,800 | 275 |
| 500 | 22,800 | 1,275 |

#### 정예 몬스터: 골렘 서버 (baseHP=300, baseATK=15)

| 스테이지 | HP | ATK |
|----------|----|-----|
| 1 | 345 | 16.5 |
| 10 | 750 | 30 |
| 50 | 2,550 | 90 |
| 100 | 4,800 | 165 |
| 500 | 22,800 | 765 |

#### 보스 구슬: 개 얼굴 구슬 (baseHP=500, 스케일링 0.20)

| 스테이지 | HP 공식 | HP |
|----------|---------|-----|
| 1 | 500 * (1 + 1*0.20) | **600** |
| 10 | 500 * (1 + 10*0.20) | **1,500** |
| 50 | 500 * (1 + 50*0.20) | **5,500** |
| 100 | 500 * (1 + 100*0.20) | **10,500** |
| 500 | 500 * (1 + 500*0.20) | **50,500** |

### 5-3. 난이도 구간 분석

```
스테이지별 상대 난이도 (플레이어 성장 대비)

난이도
  ^
  |           ★벽 구간
  |          /  \
  |    ★   /    \___
  |   / \_/         \___
  |  /                   \___ ← 전생(Prestige) 후 쉬워짐
  | /
  +-------------------------→ 스테이지
  0   30   50   80  100  120

★ 벽 구간 (의도적 정체기):
  - Stage 30 부근: 첫 번째 벽 → 스탯 강화 유도
  - Stage 50 부근: 두 번째 벽 → 스킬 레벨업/장비 유도
  - Stage 80 부근: 세 번째 벽 → 전생(Prestige) 유도
```

### 5-4. 밸런스 조절 상수

| 상수 | 기본값 | 설명 | 조절 범위 |
|------|--------|------|-----------|
| `HP_SCALE_FACTOR` | 0.15 | 스테이지당 HP 증가율 | 0.10 ~ 0.20 |
| `ATK_SCALE_FACTOR` | 0.10 | 스테이지당 ATK 증가율 | 0.05 ~ 0.15 |
| `GOLD_SCALE_FACTOR` | 0.12 | 스테이지당 골드 보상 증가율 (^1.15 지수 적용) | 0.08 ~ 0.18 |
| `ORB_SCALE_INTERVAL` | 10 | 구슬 조각 증가 간격 (스테이지) | 5 ~ 20 |
| `ORB_SCALE_FACTOR` | 0.25 | 구슬 조각 증가 계수 | 0.15 ~ 0.40 |
| `ELITE_HP_MULTIPLIER` | 3.0 | 정예 몬스터 HP 배율 (baseHP에 이미 반영) | 2.0 ~ 5.0 |
| `BOSS_HP_MULTIPLIER` | 8.0 | 보스 구슬 HP 배율 (baseHP에 이미 반영) | 5.0 ~ 12.0 |

---

## 6. 드랍 테이블

### 6-1. 일반 몬스터 드랍

| id | 한글명 | baseGold | goldVariance | dropRate | 특수 드랍 |
|-----|--------|----------|-------------|----------|-----------|
| `nm_goblin_parttimer` | 고블린 알바생 | 10 | +-20% | 100% | 없음 |
| `nm_slime_tax` | 세금 슬라임 | 15 | +-15% | 100% | 없음 |
| `nm_skeleton_intern` | 해골 인턴 | 8 | +-25% | 100% | 없음 |
| `nm_mushroom_elder` | 버섯 꼰대 | 18 | +-10% | 100% | 없음 |
| `nm_bat_streamer` | 박쥐 스트리머 | 6 | +-30% | 100% | 없음 |

> `goldVariance`: 최종 드랍 골드 = baseGold * (1 +- random(variance))

### 6-2. 정예 몬스터 드랍

| id | 한글명 | baseGold | goldVariance | dropRate | 특수 드랍 | 특수 확률 |
|-----|--------|----------|-------------|----------|-----------|-----------|
| `em_orc_teamlead` | 오크 팀장 | 50 | +-15% | 100% | 구슬 조각 x1 | 10% |
| `em_mage_reviewer` | 마법사 코드리뷰어 | 60 | +-20% | 100% | 구슬 조각 x1 | 15% |
| `em_golem_server` | 골렘 서버 | 80 | +-10% | 100% | 구슬 조각 x2 | 8% |

### 6-3. 보스 구슬 드랍

| 항목 | 값 | 스케일링 |
|------|-----|----------|
| 골드 | baseGold: 200 | `200 * (1 + stage * 0.12)^1.15` |
| 구슬 조각 (확정) | baseOrbFragments: 5 | `5 * (1 + floor(stage / 10) * 0.25)` |
| 보너스 구슬 조각 | +3 | 20% 확률로 추가 |
| 보석 (프리미엄) | 1 | 5% 확률 (stage 20 이상) |

### 6-4. 스테이지별 드랍 보상 예시

> 한 스테이지 기준. 방 수 = min(5 + floor(stage/20), 8), 방당 몬스터 수 = min(3 + floor(stage/15), 8)
> 골드 공식: baseGold * (1 + stage * 0.12)^1.15

| 스테이지 | 방 수 | 일반몹 수 | 정예 수 | 일반 골드 합계 | 정예 골드 합계 | 보스 골드 | **총 골드** | **구슬 조각** |
|----------|-------|-----------|---------|----------------|----------------|-----------|-------------|---------------|
| 1 | 5 | ~12 | ~1 | ~156 | ~72 | 228 | **~456** | 5~6 |
| 10 | 5 | ~12 | ~2 | ~336 | ~310 | 492 | **~1,138** | 6~8 |
| 50 | 7 | ~36 | ~4 | ~3,636 | ~2,236 | 1,774 | **~7,646** | 8~11 |
| 100 | 8 | ~56 | ~6 | ~11,200 | ~6,618 | 3,500 | **~21,318** | 10~14 |
| 500 | 8 | ~56 | ~8 | ~69,272 | ~54,688 | 21,700 | **~145,660** | 18~24 |

### 6-5. 골드 드랍 계산 공식 (상세)

```
// 개별 몬스터 골드 드랍 계산
float CalculateGoldDrop(MonsterData data, int stage)
{
    float scaledGold = data.baseGold * Mathf.Pow(1 + stage * GOLD_SCALE_FACTOR, 1.15f);
    float variance = Random.Range(-data.goldVariance, data.goldVariance);
    return scaledGold * (1 + variance);
}

// 구슬 조각 드랍 계산
int CalculateOrbFragments(int stage)
{
    int baseFragments = 5;
    float scaleMultiplier = 1 + Mathf.Floor(stage / ORB_SCALE_INTERVAL) * ORB_SCALE_FACTOR;
    int fragments = Mathf.RoundToInt(baseFragments * scaleMultiplier);

    // 20% 확률 보너스
    if (Random.value < 0.2f) fragments += 3;

    return fragments;
}
```

---

## 7. 스폰 규칙

### 7-1. 방(Room) 구성

| 항목 | 값 | 설명 |
|------|-----|------|
| 스테이지당 방 수 | 5 ~ 8 | `min(5 + floor(stage/20), 8)` |
| 마지막 방 | 항상 보스 방 | 개 얼굴 구슬만 등장 |
| 일반 방 수 | (총 방 수 - 1) | 일반 + 정예 몬스터 등장 |

### 7-2. 일반 방 스폰 규칙

| 항목 | 값 | 비고 |
|------|-----|------|
| 방당 일반 몬스터 수 | 3 ~ 8마리 | `min(3 + floor(stage/15), 8)` |
| 기본 수량 (baseCount) | min(3 + floor(stage / 15), 8) | 스테이지 진행 시 점진 증가 |
| 최대 수량 제한 | 8마리 | 성능 보호용 상한 |
| 몬스터 종류 혼합 | 방당 1~3종 | 같은 종류끼리 무리 배치 |

### 7-3. 몬스터 등장 해금

#### 일반 몬스터 해금

| 스테이지 | 해금 몬스터 |
|---------|-----------|
| 1~2 | 고블린 알바생만 |
| 3~5 | + 세금 슬라임 |
| 6~10 | + 해골 인턴 |
| 11~15 | + 버섯 꼰대 |
| 16+ | + 박쥐 스트리머 (전종 등장) |

#### 정예 몬스터 해금

| 스테이지 | 해금 몬스터 |
|---------|-----------|
| 5~9 | 마법사 코드리뷰어 (첫 정예) |
| 10~19 | + 오크 팀장 |
| 20+ | + 골렘 서버 |

### 7-4. 정예 몬스터 스폰 확률

> **정예 몬스터는 정예방(EliteRoom)에서만 등장하며, 일반 방에는 정예가 등장하지 않는다. 상세 방 구성은 stage_room_design.md 참조.**

> 정예는 스테이지 5부터 등장

| 스테이지 구간 | 방당 정예 등장 확률 | 최대 정예 수 (방당) |
|---------------|---------------------|---------------------|
| 1 ~ 4 | 0% | 0 |
| 5 ~ 10 | 15% | 1 |
| 11 ~ 30 | 25% | 1 |
| 31 ~ 60 | 35% | 1~2 |
| 61 ~ 100 | 45% | 1~2 |
| 101 ~ 200 | 55% | 2 |
| 201+ | 65% | 2~3 |

```csharp
int GetEliteCount(int stage, int roomIndex)
{
    if (stage < 5) return 0; // 정예는 스테이지 5부터 등장

    float baseChance = 0.15f + Mathf.Min((stage - 5) * 0.005f, 0.50f);
    int maxElites = stage < 31 ? 1 : (stage < 101 ? 2 : 3);

    int eliteCount = 0;
    for (int i = 0; i < maxElites; i++)
    {
        if (Random.value < baseChance) eliteCount++;
    }
    return eliteCount;
}
```

### 7-5. 몬스터 배치 포메이션

방 내에서 몬스터는 다음 포메이션 중 하나로 배치된다.

| 포메이션 | 코드 | 배치 형태 | 선택 확률 |
|----------|------|-----------|-----------|
| **일렬** | `LINE` | 가로 한 줄로 등간격 배치 | 30% |
| **V자** | `V_SHAPE` | V자 형태로 배치 (가운데 앞) | 20% |
| **군집** | `CLUSTER` | 한 지점에 밀집 배치 | 25% |
| **분산** | `SCATTERED` | 방 전체에 랜덤 분산 | 15% |
| **매복** | `AMBUSH` | 화면 양쪽에서 등장 | 10% |

```
[LINE]        [V_SHAPE]      [CLUSTER]     [SCATTERED]    [AMBUSH]
                  M                                       M   M
M M M M M       M M          M M M        M     M          →P←
                M M M          M M            M          M   M
                                M           M     M
```

### 7-6. 정예 몬스터 배치 규칙

- 정예는 항상 일반 몬스터 **뒤쪽**(오른쪽)에 배치
- 일반 몬스터를 "방패"로 사용하는 느낌
- 정예가 2마리일 경우, 서로 **최소 3.0 units** 간격 유지

```
[일반 방 배치 예시]

플레이어 →   M M M M   [E]     (정예 1마리)
플레이어 →   M M M  [E]  M M  [E]   (정예 2마리)
```

### 7-7. 보스 방 규칙

| 항목 | 값 |
|------|-----|
| 보스 방 크기 | 화면 2배 너비 |
| 구슬 위치 | 방 중앙 고정 |
| 호위 몬스터 수 | `min(floor(stage/10), 4)` (스테이지 10부터 1마리씩 증가, 최대 4마리) |
| 호위 몬스터 선택 | 해당 스테이지의 일반 몬스터 풀에서 랜덤 선택 |
| 진입 연출 | 카메라 줌인 → 구슬 클로즈업 → 줌아웃 → 전투 시작 |

---

## 8. 행동 패턴(AI)

### 8-1. AI 상태 머신 (공통)

모든 몬스터는 다음 기본 상태 머신을 공유한다.

```
                    ┌──────────────┐
                    │    SPAWN     │
                    │ (등장 연출)   │
                    └──────┬───────┘
                           ▼
              ┌──────────────────────┐
         ┌───►│        IDLE          │◄────┐
         │    │ (대기, 플레이어 감지) │     │
         │    └──────────┬───────────┘     │
         │               ▼                 │
         │    ┌──────────────────────┐      │
         │    │       CHASE          │      │
         │    │ (플레이어 방향 이동)  │      │
         │    └──────────┬───────────┘      │
         │               ▼                 │
         │    ┌──────────────────────┐      │
         │    │       ATTACK         │──────┘
         │    │ (공격 + 후딜레이)    │  사거리 이탈 시
         │    └──────────┬───────────┘
         │               ▼
         │    ┌──────────────────────┐
         │    │        HIT           │
         │    │ (피격 리액션)        │
         │    └──────────┬───────────┘
         │               ▼
         │    ┌──────────────────────┐
         └────│       DEATH          │
              │ (사망 연출 → 제거)   │
              └──────────────────────┘
```

### 8-2. 일반 몬스터 AI 상세

#### 고블린 알바생 (GoblinPartTimer)

| 상태 | 행동 | 전환 조건 |
|------|------|-----------|
| IDLE | 제자리에서 좌우 배회 (속도 0.5) | 플레이어 감지 거리 5.0 이내 → CHASE |
| CHASE | 플레이어 방향 이동 (속도 2.0) | 사거리 1.0 이내 → ATTACK |
| ATTACK | 주먹 휘두르기, 후딜 0.5초 | 사거리 이탈 → CHASE |
| HIT | 넉백 (풀), 0.2초 경직 | 경직 해제 → CHASE |
| DEATH | "으엑" 사운드, 뒤로 날아가며 사라짐 | 0.5초 후 오브젝트 풀 반환 |

**특이 행동**: 없음 (가장 단순한 AI)

#### 세금 슬라임 (SlimeTax)

| 상태 | 행동 | 전환 조건 |
|------|------|-----------|
| IDLE | 통통 튀며 대기 (0.8초 간격) | 플레이어 감지 거리 4.0 이내 → CHASE |
| CHASE | 통통 튀며 접근 (속도 1.5) | 사거리 0.8 이내 → ATTACK |
| ATTACK | 몸통 박치기, 후딜 0.8초 | 사거리 이탈 → CHASE |
| HIT | 넉백 (90%), 찌그러짐 애니메이션 0.3초 | 경직 해제 → CHASE |
| DEATH | 찌그러지며 바닥에 늘어남 | 0.7초 후 페이드아웃 → 풀 반환 |

**특이 행동**: 이동 시 통통 튀는 애니메이션 (바운스), 피격 시 일시적으로 찌그러짐

#### 해골 인턴 (SkeletonIntern)

| 상태 | 행동 | 전환 조건 |
|------|------|-----------|
| IDLE | 칼을 닦으며 대기 | 플레이어 감지 거리 6.0 이내 → CHASE |
| CHASE | 빠르게 달려옴 (속도 2.5) | 사거리 1.2 이내 → ATTACK |
| ATTACK | 빠른 칼 찌르기 x2 연속, 후딜 0.4초 | 사거리 이탈 → CHASE |
| HIT | 넉백 (풀), 뼈가 흔들리는 연출 0.15초 | 경직 해제 → CHASE |
| DEATH | 뼈가 분해되며 사라짐 (파티클) | 0.4초 후 풀 반환 |

**특이 행동**: 2연속 공격 (빠른 연타), 감지 거리가 김 (먼저 달려옴)

#### 버섯 꼰대 (MushroomElder)

| 상태 | 행동 | 전환 조건 |
|------|------|-----------|
| IDLE | 팔짱 끼고 서 있음, 말풍선 "흠..." | 플레이어 감지 거리 3.0 이내 → CHASE |
| CHASE | 느리게 걸어옴 (속도 1.0) | 사거리 0.5 이내 → ATTACK |
| ATTACK | 머리로 박치기, 후딜 1.0초 | 사거리 이탈 → CHASE |
| HIT | 넉백 (80%), 0.4초 경직, 말풍선 "아이고!" | 경직 해제 → CHASE |
| DEATH | "요즘 것들..." 말풍선 후 쓰러짐 | 0.8초 후 풀 반환 |

**특이 행동**: 피격 시 랜덤 말풍선 출력 (코믹 요소)

#### 박쥐 스트리머 (BatStreamer)

| 상태 | 행동 | 전환 조건 |
|------|------|-----------|
| IDLE | 공중에서 좌우 비행 대기 | 플레이어 감지 거리 7.0 이내 → CHASE |
| CHASE | 사인 곡선 비행으로 접근 (속도 3.0) | 사거리 1.5 이내 → ATTACK |
| ATTACK | 급강하 공격, 후딜 0.3초 | 사거리 이탈 → CHASE (상승 후 재접근) |
| HIT | 넉백 (풀), 0.15초 경직 | 경직 해제 → CHASE |
| DEATH | 나선형으로 추락하며 사라짐 | 0.3초 후 풀 반환 |

**특이 행동**: Y축 이동 있음 (사인 곡선 비행), 급강하 공격 패턴, 감지 거리 최장

### 8-3. 정예 몬스터 AI 상세

> 정예 몬스터는 기본 상태 머신에 추가로 특수 패턴 상태를 가진다.

#### 오크 팀장 (OrcTeamLead) - 상세 AI

```
상태 우선순위:
1. HP < 50% → ENRAGE (야근 명령)
2. 전투 5초 경과 & 소환 미사용 → SUMMON (팀 소집)
3. 사거리 내 → ATTACK
4. 감지 거리 내 → CHASE
5. 기본 → IDLE

[ENRAGE 상태]
- attackSpeed *= 2.0 (3초간)
- 스프라이트 빨간색 틴트
- 3초 후 자동 해제 → ATTACK 복귀
- 재사용 쿨타임: 15초

[SUMMON 상태]
- 0.5초 시전 모션 (손 들기)
- 양 옆에 일반 몬스터 각 1마리 소환
- 소환 몬스터: 고블린 알바생 (고정)
- 1회 한정 (전투당)
```

#### 마법사 코드리뷰어 (MageReviewer) - 상세 AI

```
상태 우선순위:
1. 플레이어 거리 < 1.5 → TELEPORT (백도어 텔레포트)
2. 쿨타임 완료 (8초) → SPECIAL_ATTACK (리젝트 폭발)
3. 사거리 내 → ATTACK (불꽃 리뷰)
4. 감지 거리 내 → RETREAT_CHASE (후퇴하며 공격 시도)
5. 기본 → IDLE

[TELEPORT 상태]
- 0.2초 페이드아웃
- 플레이어 기준 반대쪽 4.0 위치로 이동
- 0.2초 페이드인
- 즉시 ATTACK 전환
- 재사용 쿨타임: 5초

[SPECIAL_ATTACK 상태]
- 0.8초 시전 모션 (지팡이 들기, 경고 원 표시)
- 플레이어 현재 위치에 빨간 원 표시 (1.5초 카운트)
- 1.5초 후 해당 위치 폭발 (DMG x2.0, 범위 2.0)
- 폭발 후 → ATTACK 복귀

[RETREAT_CHASE 상태]
- 플레이어와 적정 거리(2.5) 유지하며 후퇴
- 후퇴하며 사거리 내면 ATTACK 실행
```

#### 골렘 서버 (GolemServer) - 상세 AI

```
상태 우선순위:
1. HP < 70% & 503 사용 횟수 < 2 → INVINCIBLE (503 에러)
2. 쿨타임 완료 (12초) → AOE_ATTACK (DDoS 스톰프)
3. 사거리 내 → ATTACK
4. 감지 거리 내 → CHASE (매우 느림)
5. 기본 → IDLE

[INVINCIBLE 상태]
- 즉시 무적 전환 (회색 이펙트)
- "점검 중..." 텍스트 표시
- 2초간 유지, HP 5% 회복 (최대 2,000)
- 2초 후 → ATTACK 복귀
- 전투당 최대 2회

[AOE_ATTACK 상태]
- 1.0초 선딜 (양팔 들어올리기)
- 바닥 내려찍기 → 범위 2.5 충격파
- DMG x1.5 + 0.5초 스턴
- 화면 셰이크 (강도 0.3)
- 1.5초 후딜 → ATTACK 복귀
```

### 8-4. 보스 구슬 AI

```
[상태: STATIONARY]
- 이동 없음, 공격 없음
- 피격 시 표정 변화 + 구슬 흔들림 애니메이션만 실행
- 페이즈 전환 시 파티클 이펙트 발생

페이즈 전환 이벤트:
  Phase 1→2 (HP 70%): 균열 파티클 + 표정 변경
  Phase 2→3 (HP 40%): 큰 균열 파티클 + 빛 누출 시작 + 표정 변경
  Phase 3→4 (HP 10%): 빛 폭주 파티클 + BGM 템포 증가 + 표정 변경
  Phase 4→파괴 (HP 0%): 파괴 연출 시퀀스 실행
```

---

## 9. ScriptableObject 스키마

### 9-1. MonsterData (기본 몬스터 데이터)

```csharp
[CreateAssetMenu(fileName = "NewMonster", menuName = "RunningRight/MonsterData")]
public class MonsterData : ScriptableObject
{
    [Header("식별 정보")]
    public string monsterId;           // 고유 ID (예: "nm_goblin_parttimer")
    public string monsterName;         // 영문명
    public string displayName;         // 한글 표시명
    public MonsterGrade grade;         // Normal, Elite, Boss

    [Header("기본 스탯")]
    public float baseHP;               // 기본 체력
    public float baseATK;              // 기본 공격력
    public float moveSpeed;            // 이동 속도 (units/s)
    public float attackRange;          // 공격 사거리 (units)
    public float attackSpeed;          // 공격 속도 (attacks/s)

    [Header("물리")]
    [Range(0f, 1f)]
    public float knockbackResist;      // 넉백 저항 (0=풀넉백, 1=면역)

    [Header("감지")]
    public float detectionRange;       // 플레이어 감지 거리 (units)

    [Header("보상")]
    public int baseGold;               // 기본 골드 드랍량
    [Range(0f, 0.5f)]
    public float goldVariance;         // 골드 편차 비율
    public int baseOrbFragments;       // 기본 구슬 조각 드랍량 (보스 전용)
    public float specialDropRate;      // 특수 드랍 확률 (정예 전용)

    [Header("시각")]
    public Sprite idleSprite;          // 대기 스프라이트
    public RuntimeAnimatorController animatorController;  // 애니메이터
    public Color nameColor;            // 이름 표시 색상
    public GameObject deathEffectPrefab;  // 사망 이펙트 프리팹

    [Header("사운드")]
    public AudioClip hitSound;         // 피격 사운드
    public AudioClip deathSound;       // 사망 사운드
    public AudioClip attackSound;      // 공격 사운드

    [Header("설명")]
    [TextArea(2, 5)]
    public string description;         // 도감용 설명 텍스트
}
```

### 9-2. MonsterGrade (등급 열거형)

```csharp
public enum MonsterGrade
{
    Normal,    // 일반 몬스터
    Elite,     // 정예 몬스터
    Boss       // 보스 구슬
}
```

### 9-3. EliteMonsterData (정예 전용 확장)

```csharp
[CreateAssetMenu(fileName = "NewEliteMonster", menuName = "RunningRight/EliteMonsterData")]
public class EliteMonsterData : MonsterData
{
    [Header("특수 공격 패턴")]
    public List<SpecialAttackPattern> specialAttacks;

    [Header("정예 연출")]
    public GameObject spawnWarningPrefab;   // 등장 경고 이펙트
    public AudioClip spawnSound;            // 등장 사운드
    public bool showIndividualHPBar;        // 개별 HP바 표시 여부
}
```

### 9-4. SpecialAttackPattern (특수 공격 패턴 데이터)

```csharp
[System.Serializable]
public class SpecialAttackPattern
{
    public string patternName;              // 패턴 이름 (예: "야근 명령")
    public SpecialAttackType attackType;    // 패턴 유형

    [Header("발동 조건")]
    public TriggerCondition triggerCondition;  // 발동 조건 유형
    public float triggerValue;              // 조건 값 (HP%, 시간, 거리 등)
    public float cooldown;                 // 재사용 대기 시간 (초)
    public int maxUses;                    // 최대 사용 횟수 (-1 = 무제한)

    [Header("효과")]
    public float damageMultiplier;         // 데미지 배율
    public float effectRange;              // 효과 범위
    public float effectDuration;           // 효과 지속 시간
    public float castTime;                 // 시전 시간 (선딜)
    public float recoveryTime;             // 회복 시간 (후딜)

    [Header("부가 효과")]
    public float stunDuration;             // 스턴 지속 시간
    public float buffMultiplier;           // 버프 배율
    public float buffDuration;             // 버프 지속 시간
    public float healPercent;              // 회복량 (HP %)
    public float healMaxAmount;            // 회복량 절대값 상한 (0 = 무제한)
    public int summonCount;                // 소환 수
    public string summonMonsterId;         // 소환할 몬스터 ID
    public float teleportDistance;         // 순간이동 거리

    [Header("시각/사운드")]
    public GameObject effectPrefab;        // 이펙트 프리팹
    public AudioClip castSound;            // 시전 사운드
    public Sprite warningIndicator;        // 경고 표시 스프라이트
}
```

### 9-5. 지원 열거형

```csharp
public enum SpecialAttackType
{
    Melee,          // 근접 특수 공격
    Ranged,         // 원거리 특수 공격
    AreaOfEffect,   // 범위 공격
    Buff,           // 자기 강화
    Summon,         // 소환
    Teleport,       // 순간이동
    Invincible,     // 무적
    Heal            // 회복
}

public enum TriggerCondition
{
    HPBelow,        // HP가 특정 % 이하일 때
    TimePassed,     // 전투 시작 후 특정 시간 경과
    DistanceBelow,  // 플레이어와 거리가 특정 값 이하
    Cooldown,       // 쿨타임 기반 주기적 발동
    OnSpawn         // 등장 시 즉시 발동
}
```

### 9-6. BossOrbData (보스 구슬 전용 확장)

```csharp
[CreateAssetMenu(fileName = "NewBossOrb", menuName = "RunningRight/BossOrbData")]
public class BossOrbData : MonsterData
{
    [Header("페이즈 설정")]
    public List<BossPhase> phases;

    [Header("파괴 연출")]
    public float hitStopDuration;           // 히트스톱 시간 (초)
    public float swellDuration;             // 부풀기 애니메이션 시간
    public float shakeIntensity;            // 화면 셰이크 강도
    public float shakeDuration;             // 화면 셰이크 지속 시간
    public float whiteOutDuration;          // 화이트아웃 페이드 시간
    public GameObject explosionPrefab;      // 폭발 이펙트 프리팹
    public GameObject fragmentPrefab;       // 파편 프리팹
    public int fragmentCount;               // 파편 수 (8~12)
    public AudioClip explosionSound;        // 폭발 사운드

    [Header("외형 변화 (스테이지 구간별)")]
    public List<OrbAppearance> stageAppearances;
}

[System.Serializable]
public class BossPhase
{
    public string phaseName;                // 페이즈 이름
    [Range(0f, 1f)]
    public float hpThreshold;              // HP 비율 경계 (1.0 → 0.0)
    public Sprite faceSprite;              // 개 얼굴 표정 스프라이트
    public Sprite orbSprite;               // 구슬 상태 스프라이트
    public GameObject phaseTransitionEffect;  // 전환 이펙트
    public AudioClip phaseTransitionSound; // 전환 사운드
    public Color glowColor;                // 빛 발산 색상
    public float glowIntensity;            // 빛 강도
}

[System.Serializable]
public class OrbAppearance
{
    public int stageMin;                   // 시작 스테이지
    public int stageMax;                   // 끝 스테이지
    public Sprite orbBaseSprite;           // 구슬 기본 스프라이트
    public Sprite faceBaseSprite;          // 기본 표정 스프라이트
    public string appearanceName;          // 외형 이름 (예: "시바견 무표정")
}
```

### 9-7. MonsterSpawnConfig (스폰 설정)

```csharp
[CreateAssetMenu(fileName = "SpawnConfig", menuName = "RunningRight/MonsterSpawnConfig")]
public class MonsterSpawnConfig : ScriptableObject
{
    [Header("방 설정")]
    public int minRoomsPerStage;           // 스테이지당 최소 방 수 (5)
    public int maxRoomsPerStage;           // 스테이지당 최대 방 수 (8)

    [Header("일반 몬스터 스폰")]
    public int baseMonsterCount;           // 기본 몬스터 수 (4)
    public int monsterCountRandomRange;    // 추가 랜덤 범위 (3)
    public int stagesPerExtraMonster;      // 몬스터 추가 증가 간격 (25 스테이지마다 +1)
    public int maxMonstersPerRoom;         // 방당 최대 몬스터 수 (12)

    [Header("일반 몬스터 풀")]
    public List<MonsterData> normalMonsterPool;  // 등장 가능한 일반 몬스터 목록

    [Header("정예 몬스터 스폰")]
    public float baseEliteChance;          // 기본 정예 등장 확률 (0.15)
    public float eliteChancePerStage;      // 스테이지당 증가 확률 (0.005)
    public float maxEliteChance;           // 최대 정예 등장 확률 (0.65)
    public List<EliteMonsterData> eliteMonsterPool;  // 등장 가능한 정예 몬스터 목록

    [Header("보스 구슬")]
    public BossOrbData bossOrbData;        // 보스 구슬 데이터

    [Header("포메이션")]
    public List<FormationWeight> formationWeights;  // 포메이션 가중치 목록

    [Header("스케일링 상수")]
    public float hpScaleFactor;            // HP 증가율 (0.15)
    public float atkScaleFactor;           // ATK 증가율 (0.10)
    public float goldScaleFactor;          // 골드 증가율 (0.12)
    public int orbScaleInterval;           // 구슬 조각 증가 간격 (10)
    public float orbScaleFactor;           // 구슬 조각 증가 계수 (0.25)
}

[System.Serializable]
public class FormationWeight
{
    public FormationType formationType;
    [Range(0f, 1f)]
    public float weight;                   // 선택 가중치 (합계 1.0)
}

public enum FormationType
{
    Line,       // 일렬 배치
    VShape,     // V자 배치
    Cluster,    // 군집 배치
    Scattered,  // 분산 배치
    Ambush      // 매복 배치
}
```

### 9-8. ScriptableObject 파일 구조

```
Assets/ScriptableObjects/
├── Monsters/
│   ├── Normal/
│   │   ├── GoblinPartTimer.asset
│   │   ├── SlimeTax.asset
│   │   ├── SkeletonIntern.asset
│   │   ├── MushroomElder.asset
│   │   └── BatStreamer.asset
│   ├── Elite/
│   │   ├── OrcTeamLead.asset
│   │   ├── MageReviewer.asset
│   │   └── GolemServer.asset
│   └── Boss/
│       └── DogFaceOrb.asset
├── SpawnConfig/
│   └── DefaultSpawnConfig.asset
└── Scaling/
    └── DifficultyConfig.asset
```

---

## 부록 A: 향후 확장 포인트

| 항목 | 설명 | 예상 Phase |
|------|------|------------|
| 속성 시스템 | 화/수/풍/암 속성 추가, 상성 관계 | Phase 2+ |
| 보스 호위 몬스터 | stage 100+ 보스 방에 호위 몬스터 추가 | Phase 2+ |
| 던전 테마별 몬스터 | 배경 테마에 따른 몬스터 리스킨 | Phase 6 |
| 미니보스 등급 | 정예와 보스 사이 등급 추가 | Phase 2+ |
| 몬스터 도감 | 처치 횟수, 드랍 정보 열람 | Phase 5 |
| 특수 이벤트 몬스터 | 시즌 이벤트 전용 몬스터 | 출시 후 |

## 부록 B: 밸런스 체크리스트

- [ ] 일반 몬스터가 현재 스테이지 플레이어 공격력으로 1~3타 내 처치 가능한가?
- [ ] 정예 몬스터가 5~15초 내 처치 가능한가?
- [ ] 보스 구슬이 10~30초 내 파괴 가능한가?
- [ ] 스테이지당 총 소요 시간이 30초~2분 사이인가?
- [ ] 골드 수입이 다음 강화 비용을 20~30 스테이지 내 충족하는가?
- [ ] 벽 구간에서 전생(Prestige)이 자연스럽게 유도되는가?
- [ ] stage 500에서 숫자 오버플로우 없이 정상 동작하는가?

## 부록 C: 참고 자료

- DNF 원작 몬스터 참고: 일반 → 고블린/해골/버섯 계열, 보스 → 안톤의 심장 (파괴 오브젝트 컨셉)
- 방치형 참고 게임: 어둠의 전설, 탭 타이탄, 아이들 히어로즈
- 스케일링 참고: 지수적 성장은 후반 밸런스 붕괴 → 선형 성장(현재 방식) 채택

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| 1.0 | 2026-03-31 | 초안 작성 |
| 1.1 | 2026-03-31 | 10회 리뷰 기반 수치 정합 (보스 HP, 골렘 HP, 해금 순서 등) |
| 1.2 | 2026-03-31 | 코어 루프 정합 (정예방 체계, 보스 호위 몬스터) |
