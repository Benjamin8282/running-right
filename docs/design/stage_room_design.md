# 스테이지 / 방 설계 문서

> "오른쪽 달리기" 스테이지 및 방(Room) 시스템 상세 설계
> 작성일: 2026-03-31

---

## 목차

1. [스테이지 구조 개요](#1-스테이지-구조-개요)
2. [방 타입 정의](#2-방-타입-정의)
3. [방 구성 상세](#3-방-구성-상세)
4. [스테이지 진행 테이블](#4-스테이지-진행-테이블)
5. [난이도 곡선](#5-난이도-곡선)
6. [방 전환 연출](#6-방-전환-연출)
7. [맵 생성 규칙](#7-맵-생성-규칙)
8. [환경 테마](#8-환경-테마)
9. [StageManager / RoomManager 데이터 스키마](#9-stagemanager--roommanager-데이터-스키마)

---

## 1. 스테이지 구조 개요

### 1-1. 계층 구조

```
Game (무한 반복)
└── Stage (스테이지 N)
    ├── Room 1  (일반 전투방)
    ├── Room 2  (일반 전투방)
    ├── Room 3  (정예방 또는 일반방)
    ├── Room 4  (휴식/보물방 - 확률 등장)
    ├── Room 5  (일반 전투방)
    ├── ...
    └── Room N  (보스방 - 개 얼굴 구슬) ← 항상 마지막
```

### 1-2. 핵심 루프

```
[스테이지 시작]
    → 방 입장 (자동 이동)
    → 몬스터 웨이브 전투 (자동 공격)
    → 클리어 판정 (모든 몬스터 처치)
    → 다음 방으로 이동
    → ... (반복)
    → 마지막 방: 개 얼굴 구슬 등장
    → 구슬 파괴
    → 스테이지 클리어 연출
    → 보상 획득
    → 다음 스테이지 자동 시작
[무한 반복]
```

### 1-3. 무한 진행 설계 원칙

- 스테이지 번호에 상한 없음 (int 범위 내 무한)
- 난이도는 공식 기반 스케일링으로 자동 증가
- 10스테이지 단위로 환경 테마 순환
- 플레이어 성장 속도보다 약간 빠른 난이도 상승 → 전생(Prestige) 동기 부여
- 모든 수치는 `ScriptableObject` 기반 테이블 + 공식 하이브리드 방식

---

## 2. 방 타입 정의

### 2-1. 일반 전투방 (NormalRoom)

| 항목 | 내용 |
|------|------|
| 출현 빈도 | 가장 높음 (스테이지당 3~6개) |
| 몬스터 구성 | 일반 몬스터 3~8마리 (스테이지에 따라 증가) |
| 웨이브 수 | 1~2 웨이브 |
| 클리어 조건 | 모든 몬스터 처치 |
| 보상 | 골드 (기본) |
| 특징 | 핵심 전투 경험. 빠르게 쓸어가는 호쾌함이 관건 |

### 2-2. 정예방 (EliteRoom)

| 항목 | 내용 |
|------|------|
| 출현 빈도 | 스테이지당 0~2개 (스테이지 진행에 따라 증가) |
| 몬스터 구성 | 정예 몬스터 1~2마리 + 일반 몬스터 2~4마리 |
| 웨이브 수 | 1 웨이브 (정예가 포함된 단일 조합) |
| 클리어 조건 | 모든 몬스터 처치 (정예 포함) |
| 보상 | 골드 2배 + 구슬 조각 소량 드랍 확률 |
| 특징 | 정예 몬스터는 HP 3배(100+ 시 5배), 약한 공격 패턴 보유. 입장 시 경고 UI 표시 |

**정예 몬스터 특성:**
- HP: 스테이지 1~99: `일반 몬스터 HP * 3.0` / 스테이지 100+: `일반 몬스터 HP * 5.0`
- 공격 패턴: 근접 돌진 또는 원거리 투사체 (1가지 패턴만)
- 사망 시 골드 3배 드랍 + 구슬 조각 드랍 확률 30%
- 체력바 머리 위 표시 (일반 몬스터는 체력바 없음)

> **정예 몬스터는 정예방에서만 등장하며, 정예방은 스테이지 5 이상부터 생성된다. 일반 방에는 정예가 등장하지 않는다.**
>
> **정예 해금 스테이지:**
> - 스테이지 5+: 마법사 코드리뷰어
> - 스테이지 10+: + 오크 팀장
> - 스테이지 20+: + 골렘 서버

> **정예 HP 배율 전환 규칙:**
> - 스테이지 1~99: 정예 HP = 일반 HP × 3.0
> - 스테이지 100+: 정예 HP = 일반 HP × 5.0
> - 전환은 스테이지 100 진입 시 즉시 적용 (점진적 전환 없음)

### 2-3. 휴식/보물방 (TreasureRoom)

| 항목 | 내용 |
|------|------|
| 출현 빈도 | 스테이지당 0~1개 (출현 확률 15%) |
| 몬스터 구성 | 없음 |
| 내부 오브젝트 | 보물 상자 1~3개 |
| 클리어 조건 | 방 끝까지 이동 (자동) |
| 보상 | 골드 대량 / 구슬 조각 / 일시적 버프 중 랜덤 |
| 특징 | 전투 없는 쉬어가는 구간. 캐릭터가 지나가면 상자 자동 열림 |

**보물 상자 보상 풀:**

| 보상 | 확률 | 내용 |
|------|------|------|
| 골드 보너스 | 40% | 현재 스테이지 기본 골드의 5배 |
| 구슬 조각 | 30% | 1~3개 |
| 공격력 버프 | 15% | 30초간 ATK +20% |
| 속도 버프 | 10% | 30초간 MOVE_SPEED +30% |
| 치명타 버프 | 5% | 30초간 CRIT_RATE +15% |

### 2-4. 보스방 (BossRoom)

| 항목 | 내용 |
|------|------|
| 출현 빈도 | 스테이지당 정확히 1개 (항상 마지막 방) |
| 몬스터 구성 | **개 얼굴 구슬** 1체 (+ 호위 일반 몬스터 0~4마리) |
| 웨이브 수 | 1 웨이브 |
| 클리어 조건 | 개 얼굴 구슬 파괴 |
| 보상 | 구슬 조각 확정 + 대량 골드 + 스테이지 클리어 보너스 |
| 특징 | 전용 BGM, HP바 화면 상단 표시, 파괴 시 특별 연출 |

**개 얼굴 구슬 스탯:**
- HP: `BaseOrbHP * (1 + stage * 0.2)` (일반 몬스터보다 높은 스케일링)
- BaseOrbHP: 500 (스테이지 1 기준)
- 공격 없음 (구슬은 가만히 있고, 호위 몬스터가 방해)
- 호위 몬스터 수: `min(floor(stage / 10), 4)` (최대 4마리)

---

## 3. 방 구성 상세

### 3-1. 물리적 레이아웃

#### 기본 방 구조

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  [진입 트리거]    [스폰 영역]       [출구 트리거]     │
│       │              │                   │           │
│       ▼              ▼                   ▼           │
│   x=0          x=width*0.3~0.8      x=width          │
│                                                      │
│   ← ─ ─ ─ ─  방 너비 (width)  ─ ─ ─ ─ →           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### 방 타입별 너비

| 방 타입 | 너비 (유닛) | 화면 수 | 비고 |
|---------|------------|---------|------|
| 일반 전투방 | 30~40 | 2~2.5 화면 | 기본 크기 |
| 정예방 | 40~50 | 2.5~3 화면 | 정예 전투 공간 확보 |
| 휴식/보물방 | 20~25 | 1.5 화면 | 짧게 통과 |
| 보스방 | 45~55 | 3~3.5 화면 | 보스 전투 공간 + 연출 여유 |

> 기준: 카메라 뷰포트 너비 약 16 유닛 (1920x1080, Orthographic Size 5.4 기준)

#### 몬스터 스폰 포인트 배치

**일반 전투방:**
```
[입구]                                          [출구]
  │    SP1(x=30%)   SP2(x=50%)   SP3(x=70%)     │
  │        ●            ●            ●           │
  │     몬스터2~3     몬스터2~3    몬스터1~2      │
  └──────────────────────────────────────────────┘
```

- SP (Spawn Point): 방 너비의 30%, 50%, 70% 지점
- 각 SP에서 y축 랜덤 분산 배치 (바닥 ±0.5 유닛)
- 웨이브 2가 있을 경우, SP2~SP3 영역에 추가 스폰

**정예방:**
```
[입구]                                                [출구]
  │    SP1(x=25%)    ELITE(x=50%)    SP2(x=75%)       │
  │     일반2~3        ★정예★         일반1~2          │
  └────────────────────────────────────────────────────┘
```

- 정예 몬스터는 항상 방 중앙 배치
- 일반 몬스터가 양 옆에서 호위

**보스방:**
```
[입구]                                                      [출구]
  │   호위SP(x=40%)       ORB(x=70%)        벽(x=100%)      │
  │    일반0~4            ◉구슬◉                             │
  └──────────────────────────────────────────────────────────┘
```

- 구슬은 방 우측 70% 지점 고정
- 호위 몬스터는 구슬 앞에서 방어선 형성
- 출구 트리거 없음 (구슬 파괴 = 스테이지 클리어)

### 3-2. 진입/출구 트리거

```csharp
// 진입 트리거 (방 시작점)
EntryTrigger:
  - 위치: x = 0 (방 시작)
  - 동작: 몬스터 활성화, 방 UI 갱신 ("Room 3/6")
  - 크기: BoxCollider2D (1 x 10)

// 출구 트리거 (방 끝점)
ExitTrigger:
  - 위치: x = width (방 끝)
  - 동작: 방 클리어 확인 → 다음 방 로드
  - 활성화 조건: 모든 몬스터 처치 완료 시에만 통과 가능
  - 크기: BoxCollider2D (1 x 10)

// 보이지 않는 벽 (몬스터 처치 전)
InvisibleWall:
  - 위치: 첫 번째 스폰 포인트 x - 2 유닛
  - 동작: 모든 몬스터 처치 후 비활성화
  - 목적: 캐릭터가 몬스터 없이 방을 통과하는 것 방지
```

### 3-3. 배경 구성

각 방은 다음 배경 레이어로 구성:

| 레이어 | Sorting Order | 스크롤 속도 (패럴랙스) | 내용 |
|--------|---------------|----------------------|------|
| 원경 (Sky) | -100 | 0.1x | 하늘/동굴 천장 |
| 중경 (Mid) | -50 | 0.3x | 원거리 건물/기둥 |
| 근경 (Near) | -10 | 0.6x | 가까운 오브젝트 |
| 바닥 (Floor) | 0 | 1.0x (카메라 동기) | 타일맵 지형 |
| 전경 (Foreground) | 100 | 1.2x | 안개/파티클 효과 |

- 배경 타일은 테마별로 교체 (8장 참조)
- 방 내에서 배경 변형: 같은 테마라도 방마다 소품(횃불, 뼈, 바위 등)을 랜덤 배치

---

## 4. 스테이지 진행 테이블

### 4-1. 기본 스테이지 구성 테이블

| 스테이지 | 방 수 | 일반방 | 정예방 | 보물방 | 보스방 | 테마 |
|---------|-------|--------|--------|--------|--------|------|
| 1~4 | 5 | 4 | 0 | 0 | 1 | 고블린 동굴 |
| 5~10 | 5 | 3 | 1 | 0 | 1 | 고블린 동굴 |
| 11~20 | 6 | 4 | 1 | 0~1 | 1 | 언데드 묘지 |
| 21~30 | 6 | 3~4 | 1~2 | 0~1 | 1 | 언데드 묘지 |
| 31~40 | 7 | 4~5 | 1~2 | 0~1 | 1 | 화염 던전 |
| 41~50 | 7 | 3~4 | 2 | 0~1 | 1 | 화염 던전 |
| 51~70 | 7 | 3~4 | 2 | 0~1 | 1 | 빙결 성채 |
| 71~100 | 8 | 4~5 | 2 | 0~1 | 1 | 암흑 심연 |
| 100+ | 8 | 3~4 | 2~3 | 0~1 | 1 | 테마 순환 |

### 4-2. 방 수 공식

```
roomsPerStage = min(5 + floor(stage / 20), 8)
```

| 스테이지 범위 | 계산 | 방 수 |
|-------------|------|-------|
| 1~19 | 5 + 0 | 5 |
| 20~39 | 5 + 1 | 6 |
| 40~59 | 5 + 2 | 7 |
| 60+ | 5 + 3 (cap) | 8 |

### 4-3. 몬스터 밀도 테이블

| 스테이지 범위 | 일반방 기본 몬스터 수 | 웨이브 수 | 정예방 일반 몬스터 수 | 보스방 호위 수 |
|-------------|---------------------|----------|---------------------|-------------|
| 1~10 | 3~4 | 1 | 2 | 0 |
| 11~30 | 4~5 | 1 | 3 | 1 |
| 31~50 | 5~6 | 1~2 | 3~4 | 1~2 |
| 51~100 | 6~7 | 2 | 4 | 2~3 |
| 100+ | 7~8 | 2 | 4~5 | 3~4 |

**몬스터 수 공식 (일반방):**
```
monstersPerRoom = min(3 + floor(stage / 15), 8)
```

### 4-4. 정예방 출현률

```
eliteRoomCount:
  stage 1~4:   0개 (튜토리얼 구간)
  stage 5~20:  1개 (고정)
  stage 21~50: 1~2개 (50% 확률로 2개)
  stage 51+:   2개 (고정) + 3개 확률 (stage/100 * 10%)
```

### 4-5. 예시 스테이지 구성

**스테이지 1 (튜토리얼):**
```
Room 1: 일반방 (고블린 3마리, 1웨이브)
Room 2: 일반방 (고블린 3마리, 1웨이브)
Room 3: 일반방 (고블린 4마리, 1웨이브)
Room 4: 일반방 (고블린 3마리, 1웨이브)
Room 5: 보스방 (개 얼굴 구슬 HP:500, 호위 0마리)
```

**스테이지 35 (중반):**
```
Room 1: 일반방 (화염 임프 5마리, 1웨이브)
Room 2: 정예방 (화염 정예기사 1 + 임프 3마리)
Room 3: 일반방 (화염 임프 6마리, 2웨이브)
Room 4: 보물방 (상자 2개)
Room 5: 일반방 (화염 임프 5마리, 1웨이브)
Room 6: 정예방 (화염 정예마법사 1 + 임프 4마리)
Room 7: 보스방 (개 얼굴 구슬 HP:4000, 호위 2마리)
```

**스테이지 100 (후반):**
```
Room 1: 정예방 (심연 정예전사 1 + 그림자 4마리)
Room 2: 일반방 (그림자 7마리, 2웨이브)
Room 3: 일반방 (그림자 8마리, 2웨이브)
Room 4: 정예방 (심연 정예마법사 1 + 그림자 5마리)
Room 5: 보물방 (상자 3개)
Room 6: 일반방 (그림자 7마리, 2웨이브)
Room 7: 일반방 (그림자 8마리, 2웨이브)
Room 8: 보스방 (개 얼굴 구슬 HP:10500, 호위 4마리)
```

---

## 5. 난이도 곡선

### 5-1. 구간별 난이도 설계

#### 튜토리얼 구간 (스테이지 1~10)

| 항목 | 값 | 목적 |
|------|------|------|
| 몬스터 HP 계수 | `BaseHP * (1 + stage * 0.10)` | 완만한 증가, 적응 유도 |
| 몬스터 수 | 3~4마리 | 압도적 쾌감 제공 |
| 정예 등장 | 스테이지 5부터 | 정예 시스템 학습 |
| 보물방 | 미등장 | 심플함 유지 |
| 구슬 호위 | 0마리 | 보스 시스템 학습 |
| 골드 드랍 | 기본 * 1.5 (보너스) | 초반 성장 가속 |
| 스킬 시스템 | 스테이지 3부터 첫 스킬 해금 | 단계적 시스템 소개 |

**설계 의도:** 플레이어가 코어 루프를 자연스럽게 체화. "달린다 → 때린다 → 부순다"만 반복해도 재미있어야 함. 성장 속도 > 난이도 상승.

#### 초반 구간 (스테이지 11~50)

| 항목 | 값 | 목적 |
|------|------|------|
| 몬스터 HP 계수 | `BaseHP * (1 + stage * 0.15)` | 표준 스케일링 시작 |
| 몬스터 수 | 4~6마리 | 점진적 증가 |
| 정예 등장 | 스테이지당 1~2개 | 전투 다양성 |
| 보물방 | 15% 확률 등장 | 전략적 보상 경험 |
| 구슬 호위 | 1~2마리 | 보스방 난이도 상승 |
| 새 몬스터 종류 | 테마별 2~3종 추가 | 시각적 다양성 |
| 웨이브 시스템 | 2웨이브 등장 시작 (스테이지 30+) | 전투 길이 증가 |

**설계 의도:** 성장 시스템의 필요성을 느끼기 시작. 강화하지 않으면 클리어 시간이 늘어남. 스킬 조합의 중요성 인식.

**난이도 벽 포인트:**
- 스테이지 25: 첫 번째 "벽" — 스탯 강화 없이는 정예 처치 시간 급증
- 스테이지 40: 두 번째 "벽" — 스킬 레벨업 필요성 체감

#### 중반 구간 (스테이지 51~100)

| 항목 | 값 | 목적 |
|------|------|------|
| 몬스터 HP 계수 | `BaseHP * (1 + stage * 0.15)` | 동일 공식, 누적 효과 |
| 몬스터 ATK 계수 | `BaseATK * (1 + stage * 0.10)` | 캐릭터 HP 시스템 활용 |
| 몬스터 수 | 6~8마리 | 화면 가득 몬스터 |
| 정예 등장 | 스테이지당 2개 고정 | 정예가 일상적 존재 |
| 구슬 호위 | 2~3마리 | 보스방 전투 시간 증가 |
| 정예 패턴 | 2가지 패턴 보유 | 회피/대응 필요 |
| 보물방 보상 | 강화 재화 추가 | 성장 촉진 |

**설계 의도:** 전생(Prestige) 시스템의 필요성 강하게 어필. "현재 성장으로는 한계" 느낌. 전생 후 영구 버프로 돌파하는 쾌감.

**난이도 벽 포인트:**
- 스테이지 60: 세 번째 "벽" — 전생 시스템 처음 안내
- 스테이지 80: 전생 없이 진행 시 1방당 30초+ 소요
- 스테이지 100: 사실상 전생 필수 구간

#### 후반 구간 (스테이지 100+)

| 항목 | 값 | 목적 |
|------|------|------|
| 몬스터 HP 계수 | `BaseHP * (1 + stage * 0.15) * (1 + prestigeMultiplier)` | 전생 횟수 반영 |
| 몬스터 수 | 7~8마리 (고정 상한) | 성능 고려 상한 |
| 정예 등장 | 2~3개 | 최대 밀도 |
| 구슬 호위 | 4마리 (고정 상한) | 최대 난이도 |
| 정예 몬스터 | HP 5배, 3패턴 | 상위 정예 |
| 테마 | 10스테이지 단위 순환 | 무한 반복에도 시각적 변화 |

**설계 의도:** 전생 성장의 "맛"을 보여주는 구간. 영구 버프가 누적될수록 이전 벽 구간을 손쉽게 돌파하는 쾌감. 방치형 + 성장의 선순환.

### 5-2. 난이도 스케일링 공식 종합

```
몬스터 HP:
  MonsterHP = BaseHP * (1 + stage * 0.15)
  BaseHP = 몬스터별 개별 값 (실제 개별 값은 monster_data.md 참조: 35~90, 평균 57)
  정예 HP = MonsterHP * 3.0 (스테이지 1~99) / MonsterHP * 5.0 (스테이지 100+)
  구슬 HP = BaseOrbHP * (1 + stage * 0.20), BaseOrbHP = 500

몬스터 ATK (stage 30+부터 적용):
  MonsterATK = BaseATK * (1 + max(0, stage - 30) * 0.10)
  BaseATK = 5

골드 드랍:
  GoldDrop = baseGold * (1 + stage * 0.12)^1.15
  BaseGold = 10

구슬 조각 드랍:
  OrbShardDrop = 5 * (1 + floor(stage/10) * 0.25)

클리어 예상 시간 (적정 레벨 기준):
  NormalRoom: 8~15초
  EliteRoom: 15~25초
  BossRoom: 20~40초
  전체 스테이지: 1.5~4분
```

### 5-3. 난이도 곡선 시각화

```
난이도
  │
  │                                          ╱ 후반 (급상승)
  │                                        ╱
  │                                      ╱
  │                              ╱──────╱  중반 (가속)
  │                       ╱─────╱
  │                 ╱────╱         초반 (선형)
  │          ╱─────╱
  │    ╱────╱
  │───╱        튜토리얼 (완만)
  │
  └────┬────┬────┬────┬────┬────┬────┬────┬── 스테이지
       10   20   30   40   50   60   80  100+

       벽1(25)  벽2(40)    벽3(60)  벽4(80)
                                    전생권장(100)
```

---

## 6. 방 전환 연출

### 6-1. 방 간 전환 (Room Transition)

**전환 방식: 심리스 스크롤 (Seamless Scroll)**

방과 방 사이에 로딩 화면 없이 자연스러운 연결 구간 존재.

```
[현재 방 끝] ──── [연결 통로 (3유닛)] ──── [다음 방 시작]
              문/게이트 닫힘 → 열림         새 방 진입 트리거
```

**연결 통로 연출:**
1. 캐릭터가 방 끝에 도달
2. 출구 게이트 문이 열리는 애니메이션 (0.3초)
3. 캐릭터가 짧은 통로 (3유닛)를 달려서 통과 — 이 사이 다음 방 프리로드
4. 다음 방 진입 트리거 활성화 → 몬스터 스폰
5. 화면 상단 "Room 4/7" 텍스트 페이드인 (0.5초)

**카메라 동작:**
- Cinemachine 2D의 `CinemachineConfiner2D`로 방 범위 제한
- 방 전환 시 Confiner 영역을 다음 방으로 확장
- 부드러운 카메라 이동 (Damping X: 0.5, Y: 0.3)

### 6-2. 보스방 진입 연출

```
[마지막 일반방 클리어]
    → 연결 통로 진입
    → 통로 조명 어두워짐 (0.5초)
    → "WARNING" 텍스트 화면 중앙 점멸 (1초)
    → 보스 BGM 전환 (크로스페이드 1초)
    → 통로 끝 거대한 문 열림 (0.5초)
    → 보스방 진입
    → 개 얼굴 구슬 + HP바 등장 애니메이션 (0.8초)
    → 전투 시작
```

### 6-3. 구슬 파괴 연출 (스테이지 클리어)

```
[구슬 HP 0 도달]
    → 히트스톱 0.3초 (화면 정지)
    → 구슬 균열 애니메이션 (0.5초)
    → 카메라 줌인 (1.2배, 0.3초)
    → 구슬 폭발 파티클 (화면 가득 파편)
    → 카메라 셰이크 (강도 0.5, 0.4초)
    → 화면 화이트 플래시 (0.2초)
    → "STAGE CLEAR!" 텍스트 (1.5초 표시)
    → 보상 팝업 UI (골드, 구슬 조각 표시)
    → 2초 후 자동으로 다음 스테이지 시작
```

**보상 팝업 구성:**
```
┌─────────────────────────────┐
│       STAGE 35 CLEAR!       │
│                             │
│   💰 골드: 12,450           │
│   🔮 구슬 조각: 3           │
│   ⏱️ 클리어 시간: 2:34      │
│                             │
│      [ 다음 스테이지 ]       │
└─────────────────────────────┘
```

### 6-4. 스테이지 시작 연출

```
[다음 스테이지 시작]
    → 화면 페이드 아웃 (0.3초, 검정)
    → 배경 테마 전환 (필요 시)
    → "STAGE 36" 텍스트 화면 중앙 표시 (0.8초)
    → 화면 페이드 인 (0.3초)
    → 캐릭터 달리기 시작
    → Room 1 진입
```

---

## 7. 맵 생성 규칙

### 7-1. 절차적 방 배치 알고리즘

```
GenerateStage(stageNumber):

  1. 방 수 결정
     totalRooms = min(5 + floor(stage / 20), 8)

  2. 보스방 배치 (마지막 방 고정)
     rooms[totalRooms - 1] = BossRoom

  3. 정예방 배치
     eliteCount = GetEliteCount(stage)
     정예방 배치 가능 위치: index 1 ~ (totalRooms - 2)
     → 연속 배치 금지 (최소 1개 일반방 간격)
     → 랜덤 위치 선택

  4. 보물방 배치 (확률)
     if Random(0,1) < 0.15:
       보물방 배치 가능 위치: 정예방/보스방이 아닌 index 2 ~ (totalRooms - 2)
       → 정예방 직후 우선 배치 (전투 후 쉬어가기)

  5. 나머지 = 일반 전투방

  6. 첫 번째 방은 항상 일반 전투방 (진입 안정성)

  return rooms[]
```

### 7-2. 방 배치 규칙 (제약 조건)

| 규칙 번호 | 규칙 내용 | 이유 |
|----------|----------|------|
| R1 | 첫 번째 방은 항상 일반 전투방 | 안정적 시작, 체감 리듬 |
| R2 | 마지막 방은 항상 보스방 | 스테이지 클리어 구조 |
| R3 | 정예방 연속 배치 금지 | 난이도 급등 방지 |
| R4 | 보물방은 정예방 직후 우선 배치 | 긴장 → 이완 리듬 |
| R5 | 보물방은 첫 번째/마지막 방 불가 | 구조적 의미 유지 |
| R6 | 최소 방 수: 5, 최대 방 수: 8 | 플레이 시간 밸런스 |
| R7 | 정예방 최대 3개 | 과도한 난이도 방지 |
| R8 | 보물방 최대 1개 | 보상 밸런스 |

### 7-3. 정예방 개수 결정 함수

```
GetEliteCount(stage):
  if stage < 5:
    return 0
  elif stage <= 20:
    return 1
  elif stage <= 50:
    return 1 + (Random(0,1) < 0.5 ? 1 : 0)   // 1 또는 2
  elif stage <= 100:
    return 2
  else:
    base = 2
    bonus = (Random(0,1) < stage/1000) ? 1 : 0  // 점진적 3개 확률 증가
    return min(base + bonus, 3)
```

### 7-4. 방 내부 생성 규칙

```
GenerateRoom(roomType, stageNumber, themeId):

  1. 방 너비 결정 (타입별 범위 내 랜덤)
  2. 바닥 타일맵 생성 (테마별 타일셋)
  3. 배경 레이어 배치 (패럴랙스 5레이어)
  4. 소품 배치 (테마별 소품 풀에서 랜덤 3~7개)
     - 배치 규칙: 스폰 포인트와 2유닛 이상 간격
     - 소품은 장식용 (충돌 없음)
  5. 몬스터 스폰 포인트 배치 (방 타입별 로직)
  6. 진입/출구 트리거 배치
  7. 조명 설정 (테마별 Ambient Color)

  return roomData
```

### 7-5. 오브젝트 풀링 연동

```
방 생성/제거 시 풀링 규칙:

  방 진입 시:
    - MonsterPool에서 몬스터 Activate (새로 생성 X)
    - PropPool에서 소품 Activate

  방 클리어 후:
    - 2방 전 몬스터/소품 → Pool로 반환 (Deactivate)
    - 현재 방 + 다음 방만 메모리에 유지 (최대 2방 동시 활성)

  스테이지 전환 시:
    - 모든 활성 오브젝트 Pool 반환
    - 테마 변경 시 스프라이트 교체 (풀 오브젝트 재활용)
```

---

## 8. 환경 테마

### 8-1. 테마 순환 규칙

```
themeIndex = floor((stage - 1) / 10) % 5
```

| themeIndex | 테마 이름 | 스테이지 (첫 순환) | 분위기 |
|-----------|----------|------------------|--------|
| 0 | 고블린 동굴 | 1~10 | 어둡고 습한 동굴 |
| 1 | 언데드 묘지 | 11~20 | 음산한 묘지/지하묘실 |
| 2 | 화염 던전 | 21~30 | 붉은 용암 지대 |
| 3 | 빙결 성채 | 31~40 | 차가운 얼음 성 |
| 4 | 암흑 심연 | 41~50 | 보라빛 차원의 틈 |

> 스테이지 51부터 테마 순환 반복. 순환할 때마다 색조/채도 변형으로 시각 차이 부여.

### 8-2. 테마별 상세 설정

#### 테마 0: 고블린 동굴 (Goblin Cave)

| 항목 | 내용 |
|------|------|
| Ambient Color | `#3A2F1F` (어두운 갈색) |
| 바닥 타일 | 흙/돌 바닥 |
| 배경 오브젝트 | 석순, 동굴 벽, 이끼, 횃불 |
| 소품 | 나무 상자, 뼈다귀, 거미줄, 버섯 |
| 파티클 | 먼지, 물방울 (천장에서) |
| 일반 몬스터 | 고블린 전사, 고블린 궁수, 동굴 박쥐 |
| 정예 몬스터 | 고블린 족장 (근접 돌진 패턴) |
| BGM | 긴장감 낮은 동굴 탐험 BGM |

#### 테마 1: 언데드 묘지 (Undead Cemetery)

| 항목 | 내용 |
|------|------|
| Ambient Color | `#1A1A2E` (어두운 남색) |
| 바닥 타일 | 금 간 석판, 풀이 자란 돌바닥 |
| 배경 오브젝트 | 묘비, 십자가, 부서진 관, 철 울타리 |
| 소품 | 두개골, 부서진 갑옷, 촛대, 썩은 나무 |
| 파티클 | 안개(지면), 도깨비불(녹색 부유) |
| 일반 몬스터 | 스켈레톤 전사, 좀비, 유령 |
| 정예 몬스터 | 데스나이트 (원거리 뼈 투사체 패턴) |
| BGM | 음산한 오르간 + 으스스한 분위기 |

#### 테마 2: 화염 던전 (Flame Dungeon)

| 항목 | 내용 |
|------|------|
| Ambient Color | `#4A0E0E` (어두운 적색) |
| 바닥 타일 | 검은 화산암, 용암 갈라진 틈 |
| 배경 오브젝트 | 용암 흐름, 화산 기둥, 쇠사슬, 불꽃 벽 |
| 소품 | 불타는 뼈, 용암 웅덩이(장식), 그을린 기둥 |
| 파티클 | 불씨(상승), 연기, 열기 왜곡(셰이더) |
| 일반 몬스터 | 화염 임프, 마그마 슬라임, 화염 박쥐 |
| 정예 몬스터 | 화염 기사 (돌진 + 화염 방사 2패턴) |
| BGM | 강렬한 드럼 + 위기감 있는 BGM |

#### 테마 3: 빙결 성채 (Frozen Citadel)

| 항목 | 내용 |
|------|------|
| Ambient Color | `#0E1E3A` (차가운 청색) |
| 바닥 타일 | 얼음 바닥, 눈 덮인 석판 |
| 배경 오브젝트 | 얼음 기둥, 고드름, 결빙 창문, 눈더미 |
| 소품 | 얼어붙은 갑옷, 빙결 횃불(파란불), 눈꽃 결정 |
| 파티클 | 눈보라(수평), 빙결 결정(부유), 안개(지면) |
| 일반 몬스터 | 프로스트 고블린, 아이스 엘리멘탈, 냉기 유령 |
| 정예 몬스터 | 빙결 골렘 (범위 동결 + 돌진 2패턴) |
| BGM | 신비로운 피아노 + 바람 소리 |

#### 테마 4: 암흑 심연 (Dark Abyss)

| 항목 | 내용 |
|------|------|
| Ambient Color | `#0A0014` (깊은 보라/검정) |
| 바닥 타일 | 부유하는 석판, 보라빛 에너지 바닥 |
| 배경 오브젝트 | 차원의 틈, 눈알 오브젝트, 부유 바위, 촉수 |
| 소품 | 깨진 차원석, 보라빛 수정, 고대 문양 |
| 파티클 | 보라빛 에너지 입자(부유), 차원 왜곡(셰이더) |
| 일반 몬스터 | 그림자 워커, 심연 촉수, 차원 와프 |
| 정예 몬스터 | 심연의 눈 (텔레포트 + 레이저 + 소환 3패턴) |
| BGM | 불안한 앰비언트 + 저음 드론 |

### 8-3. 테마 순환 시 변형 규칙

2번째 순환(스테이지 51+)부터 시각적 차이 적용:

| 순환 회차 | 변형 내용 |
|----------|----------|
| 2회차 (51~100) | 채도 -10%, 소품 배치 밀도 +20% |
| 3회차 (101~150) | 색조 Hue shift +15도, 안개 농도 증가 |
| 4회차 (151~200) | 전체 색상 반전 필터, 파티클 크기 1.5배 |
| 5회차+ | 위 변형 조합 랜덤 적용 |

---

## 9. StageManager / RoomManager 데이터 스키마

### 9-1. StageData (ScriptableObject)

```csharp
[CreateAssetMenu(fileName = "StageData", menuName = "RunningRight/StageData")]
public class StageData : ScriptableObject
{
    [Header("기본 설정")]
    public int stageNumber;                    // 스테이지 번호
    public int baseRoomsPerStage = 5;          // 기본 방 수
    public int maxRoomsPerStage = 8;           // 최대 방 수
    public int roomIncreaseInterval = 20;      // 방 수 증가 간격 (스테이지)

    [Header("난이도 스케일링")]
    public float monsterHpMultiplierPerStage = 0.15f;   // HP 증가율
    public float monsterAtkMultiplierPerStage = 0.10f;   // ATK 증가율
    public int monsterAtkStartStage = 30;                // ATK 스케일링 시작
    public float goldDropMultiplierPerStage = 0.12f;      // 골드 증가율

    [Header("몬스터 기본 스탯")]
    // 일반 몬스터 HP는 개별 ScriptableObject에서 정의 (monster_data.md 참조: 35~90, 평균 57)
    // public float baseMonsterHp → 개별 MonsterData.baseHP 사용
    public float baseOrbHp = 500f;
    public float baseMonsterAtk = 5f;
    public float baseGoldDrop = 10f;

    [Header("정예방 설정")]
    public int eliteStartStage = 5;            // 정예 등장 시작
    public int eliteGuaranteedTwoStage = 51;   // 2개 확정 시작
    public float eliteBonusChance = 0.5f;      // 추가 정예방 확률

    [Header("보물방 설정")]
    public float treasureRoomChance = 0.15f;   // 보물방 등장 확률

    [Header("보스 설정")]
    public float orbHpMultiplierPerStage = 0.20f;   // 구슬 HP 증가율
    public int maxEscortMonsters = 4;                // 최대 호위 몬스터

    [Header("테마 설정")]
    public int stagesPerTheme = 10;            // 테마당 스테이지 수
    public ThemeData[] themes;                 // 테마 데이터 배열 (5개)
}
```

### 9-2. RoomData (런타임 생성 데이터)

```csharp
[System.Serializable]
public class RoomData
{
    public int roomIndex;                      // 방 인덱스 (0-based)
    public RoomType roomType;                  // Normal, Elite, Treasure, Boss
    public float roomWidth;                    // 방 너비 (유닛)
    public Vector2 entryPosition;              // 진입 위치
    public Vector2 exitPosition;               // 출구 위치
    public List<SpawnPointData> spawnPoints;   // 몬스터 스폰 포인트
    public List<PropData> props;               // 소품 데이터
    public int waveCount;                      // 웨이브 수
    public bool isCleared;                     // 클리어 여부
}

public enum RoomType
{
    Normal,     // 일반 전투방
    Elite,      // 정예방
    Treasure,   // 보물방
    Boss        // 보스방
}
```

### 9-3. SpawnPointData

```csharp
[System.Serializable]
public class SpawnPointData
{
    public Vector2 position;                   // 스폰 위치
    public MonsterType monsterType;            // 일반/정예/구슬
    public int monsterCount;                   // 스폰 수
    public int waveIndex;                      // 웨이브 번호 (0-based)
    public float spawnDelay;                   // 스폰 지연 (초)
}

public enum MonsterType
{
    Normal,     // 일반 몬스터
    Elite,      // 정예 몬스터
    Orb,        // 개 얼굴 구슬
    Escort      // 보스방 호위 몬스터
}
```

### 9-4. ThemeData (ScriptableObject)

```csharp
[CreateAssetMenu(fileName = "ThemeData", menuName = "RunningRight/ThemeData")]
public class ThemeData : ScriptableObject
{
    [Header("테마 식별")]
    public string themeId;                     // "goblin_cave", "undead_cemetery" 등
    public string themeName;                   // "고블린 동굴"

    [Header("시각 설정")]
    public Color ambientColor;                 // 조명 색상
    public TileBase[] floorTiles;              // 바닥 타일셋
    public Sprite[] backgroundLayers;          // 배경 레이어 (5개)
    public GameObject[] propPrefabs;           // 소품 프리팹 풀

    [Header("파티클")]
    public GameObject ambientParticle;         // 환경 파티클 (먼지/눈/불씨 등)
    public GameObject fogParticle;             // 안개 파티클

    [Header("몬스터")]
    public GameObject[] normalMonsterPrefabs;  // 일반 몬스터 프리팹 (2~3종)
    public GameObject[] eliteMonsterPrefabs;   // 정예 몬스터 프리팹 (1~2종)

    [Header("사운드")]
    public AudioClip bgm;                      // 테마 BGM
    public AudioClip bossBgm;                  // 보스 BGM
    public AudioClip ambientSfx;               // 환경음
}
```

### 9-5. StageManager 상태머신

```
┌─────────────────────────────────────────────────────────┐
│                   StageManager FSM                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Idle] ──(게임시작)──→ [StageInit]                      │
│                            │                            │
│                      방 배열 생성                        │
│                      테마 로드                           │
│                      UI 갱신                             │
│                            │                            │
│                            ▼                            │
│                      [RoomLoading]                       │
│                            │                            │
│                      방 오브젝트 생성                    │
│                      몬스터 풀에서 활성화                │
│                      트리거 배치                         │
│                            │                            │
│                            ▼                            │
│                      [RoomActive]                        │
│                            │                            │
│                   몬스터 전투 진행 중                    │
│                   클리어 판정 감시                       │
│                            │                            │
│              ┌─────────────┼─────────────┐              │
│              │             │             │              │
│         (일반/정예방)   (보물방)      (보스방)           │
│         모든 몬스터     방 끝 도달    구슬 파괴          │
│         처치 완료                                       │
│              │             │             │              │
│              ▼             ▼             ▼              │
│         [RoomClear]   [RoomClear]  [BossClear]          │
│              │             │             │              │
│         다음 방 있음?  다음 방 있음?  스테이지 클리어!   │
│              │             │             │              │
│          YES → [RoomTransition] → [RoomLoading]         │
│                                          │              │
│           NO → (불가능, 보스방이 마지막)  │              │
│                                          ▼              │
│                                   [StageClear]          │
│                                          │              │
│                                   클리어 연출            │
│                                   보상 지급             │
│                                   stage++               │
│                                          │              │
│                                          ▼              │
│                                   [StageInit] (반복)    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 9-6. StageManager 핵심 필드

```csharp
public class StageManager : MonoBehaviour
{
    // === 상태 ===
    public StageState currentState;            // 현재 FSM 상태
    public int currentStageNumber;             // 현재 스테이지 번호 (1-based)
    public int currentRoomIndex;               // 현재 방 인덱스 (0-based)
    public int totalRoomsInStage;              // 현재 스테이지 총 방 수

    // === 데이터 ===
    public StageData stageData;                // ScriptableObject 참조
    public RoomData[] currentRoomLayout;       // 현재 스테이지 방 배열
    public ThemeData currentTheme;             // 현재 적용 테마

    // === 런타임 계산값 ===
    public float currentMonsterHpMultiplier;   // 현재 몬스터 HP 계수
    public float currentMonsterAtkMultiplier;  // 현재 몬스터 ATK 계수
    public float currentGoldDropMultiplier;    // 현재 골드 드랍 계수
    public float currentOrbHp;                 // 현재 구슬 HP

    // === 이벤트 ===
    public event Action<int> OnRoomEnter;      // 방 진입 (roomIndex)
    public event Action<int> OnRoomClear;      // 방 클리어 (roomIndex)
    public event Action<int> OnStageClear;     // 스테이지 클리어 (stageNumber)
    public event Action<RoomType> OnRoomTypeChanged;  // 방 타입 변경 알림

    // === 참조 ===
    public RoomManager roomManager;            // 방 생성/관리 담당
    public MonsterSpawner monsterSpawner;      // 몬스터 스폰 담당
    public RewardManager rewardManager;        // 보상 처리 담당
}

public enum StageState
{
    Idle,
    StageInit,
    RoomLoading,
    RoomActive,
    RoomClear,
    RoomTransition,
    BossClear,
    StageClear
}
```

### 9-7. RoomManager 핵심 필드

```csharp
public class RoomManager : MonoBehaviour
{
    // === 현재 방 ===
    public RoomData activeRoom;                // 현재 활성 방
    public GameObject activeRoomObject;        // 현재 방 게임오브젝트
    public Collider2D roomConfinerBounds;      // Cinemachine Confiner 범위

    // === 풀링 ===
    public ObjectPool<GameObject> monsterPool;
    public ObjectPool<GameObject> propPool;
    public ObjectPool<GameObject> effectPool;

    // === 방 생성 ===
    public float roomSpawnOffsetX;             // 다음 방 생성 X 오프셋 (누적)
    public int maxActiveRooms = 2;             // 동시 활성 방 수 (성능)

    // === 전투 상태 ===
    public int aliveMonsterCount;              // 현재 방 생존 몬스터 수
    public int totalMonstersInRoom;            // 현재 방 총 몬스터 수
    public int currentWave;                    // 현재 웨이브 번호
    public int totalWaves;                     // 총 웨이브 수
    public bool isRoomCleared;                 // 방 클리어 여부

    // === 이벤트 ===
    public event Action OnAllMonstersDefeated;
    public event Action<int> OnWaveStart;      // 웨이브 시작 (waveIndex)
    public event Action OnOrbDestroyed;        // 구슬 파괴

    // === 메서드 (주요) ===
    // GenerateRoom(RoomData data, ThemeData theme)  → 방 생성
    // ActivateWave(int waveIndex)                   → 웨이브 활성화
    // OnMonsterDeath()                              → 몬스터 사망 처리
    // CheckClearCondition()                         → 클리어 판정
    // CleanupRoom()                                 → 방 정리 (풀 반환)
}
```

### 9-8. 저장 데이터 (SaveData 연동)

```csharp
[System.Serializable]
public class StageSaveData
{
    public int highestStageCleared;            // 최고 클리어 스테이지
    public int currentStage;                   // 현재 진행 스테이지
    public int currentRoom;                    // 현재 진행 방
    public int totalStagesCleared;             // 누적 클리어 스테이지 수
    public float totalPlayTime;                // 총 플레이 시간
    public string lastPlayTimestamp;           // 마지막 플레이 시각 (오프라인 보상용)
    public int prestigeCount;                  // 전생 횟수
    public Dictionary<string, int> themeEncounterCount;  // 테마별 방문 횟수
}
```

---

## 부록: 핵심 수치 요약표

| 항목 | 공식 / 값 |
|------|----------|
| 스테이지당 방 수 | `min(5 + floor(stage/20), 8)` |
| 일반 몬스터 HP | `BaseHP * (1 + stage * 0.15)` — BaseHP는 monster_data.md 참조 (35~90, 평균 57) |
| 정예 몬스터 HP | 일반 HP × 3.0 (스테이지 1~99) / × 5.0 (스테이지 100+) |
| 구슬 HP | `500 * (1 + stage * 0.20)` |
| 몬스터 ATK | `5 * (1 + max(0, stage-30) * 0.10)` (30+ 적용) |
| 방당 몬스터 수 | `min(3 + floor(stage/15), 8)` |
| 호위 몬스터 수 | `min(floor(stage/10), 4)` |
| 골드 드랍 | `10 * (1 + stage * 0.12)^1.15` |
| 구슬 조각 드랍 | `5 * (1 + floor(stage/10) * 0.25)` |
| 보물방 확률 | 15% |
| 정예 HP 배율 | 일반의 3배 (스테이지 1~99) / 5배 (스테이지 100+) |
| 테마 순환 | 10스테이지마다, 5테마 순환 |
| 일반방 클리어 시간 (적정) | 8~15초 |
| 정예방 클리어 시간 (적정) | 15~25초 |
| 보스방 클리어 시간 (적정) | 20~40초 |
| 스테이지 클리어 시간 (적정) | 1.5~4분 |
