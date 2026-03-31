# 방치형(Idle) 시스템 설계 문서

> 오른쪽 달리기 - Phase 4 방치형 시스템 상세 설계
> 작성일: 2026-03-31
> 버전: 1.0

---

## 목차

1. [방치 시스템 개요](#1-방치-시스템-개요)
2. [오프라인 보상 계산](#2-오프라인-보상-계산)
3. [오프라인 시간 상한](#3-오프라인-시간-상한)
4. [효율 계수 설계](#4-효율-계수-설계)
5. [오프라인 보상 종류](#5-오프라인-보상-종류)
6. [복귀 팝업 UI 명세](#6-복귀-팝업-ui-명세)
7. [광고 보상 설계](#7-광고-보상-설계)
8. [자동 전투 최적화](#8-자동-전투-최적화)
9. [배터리 절약 모드](#9-배터리-절약-모드)
10. [푸시 알림 시스템](#10-푸시-알림-시스템)
11. [저장/로드 시스템](#11-저장로드-시스템)

---

## 1. 방치 시스템 개요

### 1.1 설계 철학

방치형 시스템의 핵심 목표는 **"플레이하지 않아도 성장하지만, 플레이하면 더 빨리 성장한다"**는 느낌을 주는 것이다. 플레이어가 앱을 끄고 돌아왔을 때 보상이 쌓여 있어야 복귀 동기가 생기고, 동시에 직접 플레이하는 것보다 보상이 적어야 능동적 플레이 의욕이 유지된다.

### 1.2 앱 상태별 동작 정의

게임은 앱의 상태에 따라 세 가지 모드로 동작한다.

| 앱 상태 | 정의 | 보상 효율 | 렌더링 | 전투 시뮬레이션 |
|---------|------|-----------|--------|----------------|
| **활성(Active)** | 앱이 포그라운드에서 실행 중이고 플레이어가 조작 가능 | 100% | 전체 렌더링 | 실시간 전투 |
| **최소화(Minimized)** | 앱이 백그라운드로 내려간 상태 (홈 버튼, 다른 앱 전환) | 80% | 렌더링 중단 | 간소화 시뮬레이션 |
| **종료(Closed)** | 앱 프로세스가 완전히 종료된 상태 | 50% | 없음 | 오프라인 계산 |

#### 활성(Active) 모드
- 일반적인 게임 플레이 상태
- 모든 전투, 이펙트, 애니메이션이 정상 작동
- 골드, 경험치, 아이템 드랍 등 모든 보상 100% 획득
- 스킬 쿨타임, 몬스터 스폰 등 실시간 처리

#### 최소화(Minimized) 모드
- `OnApplicationPause(true)` 이벤트로 감지
- 렌더링을 완전히 중단하고 간소화된 전투 시뮬레이션 실행
- 초당 DPS 기반으로 몬스터 처치를 계산 (실제 충돌/물리 없음)
- Android에서 백그라운드 프로세스가 OS에 의해 종료될 수 있으므로, 최소화 진입 시점에 `lastPlayTime`을 즉시 저장
- 보상 효율 80% (렌더링 스킵으로 인한 최적화 보너스를 고려하되, 완전 오프라인보다 높게 설정)

#### 종료(Closed) 모드
- 앱이 완전히 종료되어 어떠한 코드도 실행되지 않는 상태
- `OnApplicationQuit()` 또는 `OnApplicationPause(true)` 시점에 저장된 `lastPlayTime`을 기준으로 경과 시간 계산
- 복귀 시 오프라인 보상 공식에 따라 일괄 보상 지급
- 보상 효율 50%

### 1.3 상태 전환 흐름

```
[활성] ──홈 버튼──→ [최소화] ──OS 종료──→ [종료]
  ↑                    │                    │
  │                    │ 앱 복귀            │ 앱 재시작
  │←───────────────────┘                    │
  │←────────────────────────────────────────┘
                  (오프라인 보상 팝업 표시)
```

### 1.4 핵심 타이밍 이벤트

| 이벤트 | 시점 | 동작 |
|--------|------|------|
| `OnApplicationPause(true)` | 앱 최소화 | `lastPlayTime` 저장, 간소화 모드 전환 |
| `OnApplicationPause(false)` | 앱 복귀 | 경과 시간 계산, 보상 지급, 정상 모드 복원 |
| `OnApplicationQuit()` | 앱 종료 | `lastPlayTime` 저장, 전체 게임 데이터 저장 |
| `Start()` / `Awake()` | 앱 시작 | 저장 데이터 로드, 오프라인 보상 계산 및 팝업 |

---

## 2. 오프라인 보상 계산

### 2.1 기본 공식

```
오프라인 골드 = goldPerSecond * elapsedSeconds * efficiencyCoefficient
```

각 변수의 정의:

| 변수 | 설명 | 산출 방식 |
|------|------|-----------|
| `goldPerSecond` | 초당 골드 획득량 | 현재 스테이지의 몬스터 골드 보상 기반 |
| `elapsedSeconds` | 오프라인 경과 시간 (초) | `min(실제 경과 시간, maxOfflineSeconds)` |
| `efficiencyCoefficient` | 오프라인 효율 계수 | 기본 0.5 (종료), 0.8 (최소화) |

### 2.2 goldPerSecond 산출

`goldPerSecond`는 플레이어의 현재 전투력과 스테이지 난이도를 기반으로 산출한다.

```
goldPerSecond = (monstersPerRoom * goldPerMonster * roomClearRate) + bossGoldPerClear * bossClearRate
```

세부 변수:

| 변수 | 설명 | 예시 값 |
|------|------|---------|
| `monstersPerRoom` | 방당 몬스터 수 | 5~8마리 |
| `goldPerMonster` | 몬스터 1마리당 골드 보상 | `BaseGold * (1 + stage * 0.1)` |
| `roomClearRate` | 초당 방 클리어 횟수 | `playerDPS / roomTotalHP` (방 전체 몬스터 HP 합계) |
| `bossGoldPerClear` | 구슬 보스 클리어 시 골드 | `goldPerMonster * 10` |
| `bossClearRate` | 초당 보스 클리어 횟수 | `playerDPS / bossHP` (스테이지당 1회) |

간소화된 산출 (실제 구현용):

```csharp
float CalculateGoldPerSecond(int currentStage, float playerDPS)
{
    // 스테이지별 몬스터 기본 HP
    float monsterHP = baseMonsterHP * (1f + currentStage * 0.15f);

    // 스테이지별 몬스터 골드 보상
    float goldPerMonster = baseGoldDrop * (1f + currentStage * 0.1f);

    // 방당 총 몬스터 HP
    int monstersPerRoom = Mathf.Min(5 + currentStage / 10, 8);
    float roomTotalHP = monsterHP * monstersPerRoom;

    // 방 클리어 소요 시간 (초)
    float roomClearTime = roomTotalHP / playerDPS;
    // 이동 시간 포함 (방 사이 이동 약 2초)
    float totalRoomTime = roomClearTime + 2f;

    // 방당 획득 골드
    float goldPerRoom = goldPerMonster * monstersPerRoom;

    // 초당 골드
    return goldPerRoom / totalRoomTime;
}
```

### 2.3 구체적 계산 예시

**기준 조건:**
- 현재 스테이지: 50
- playerDPS: 500
- baseMonsterHP: 100
- baseGoldDrop: 10
- 방당 몬스터 수: 8마리
- 효율 계수: 0.5 (종료 상태)

**변수 산출:**
```
monsterHP = 100 * (1 + 50 * 0.15) = 100 * 8.5 = 850
goldPerMonster = 10 * (1 + 50 * 0.1) = 10 * 6.0 = 60
roomTotalHP = 850 * 8 = 6,800
roomClearTime = 6,800 / 500 = 13.6초
totalRoomTime = 13.6 + 2 = 15.6초
goldPerRoom = 60 * 8 = 480
goldPerSecond = 480 / 15.6 = 30.77 골드/초
```

#### 시간별 오프라인 보상표

| 오프라인 시간 | 경과 초 | 공식 | 오프라인 골드 (효율 50%) | 광고 2배 적용 시 |
|--------------|---------|------|------------------------|-----------------|
| **1시간** | 3,600 | 30.77 * 3,600 * 0.5 | **55,386** | **110,772** |
| **4시간** | 14,400 | 30.77 * 14,400 * 0.5 | **221,544** | **443,088** |
| **8시간** | 28,800 | 30.77 * 28,800 * 0.5 | **443,088** | **886,176** |
| **12시간** | 43,200 | 30.77 * 43,200 * 0.5 | **664,632** | **1,329,264** |
| **24시간** (상한 적용 시) | 43,200 | 12시간 상한 적용 | **664,632** | **1,329,264** |

> **참고:** 24시간 오프라인이어도 12시간 상한이 적용되어 12시간과 동일한 보상을 받는다. 상한 설계에 대해서는 [3. 오프라인 시간 상한](#3-오프라인-시간-상한) 참조.

### 2.4 엣지 케이스 처리

| 상황 | 처리 방법 |
|------|-----------|
| 경과 시간이 0초 또는 음수 | 보상 0 처리, 로그 기록 |
| 경과 시간이 5분 미만 | 오프라인 보상 팝업 표시하지 않음 (너무 짧음) |
| goldPerSecond가 0 | 스테이지 1 기준 최소 goldPerSecond 적용 |
| 저장된 시간이 미래 시간 | 시간 조작으로 판단, 보상 0 처리 + 경고 |
| 서버 시간과 30분 이상 차이 | 시간 조작 의심, 서버 시간 기준으로 재계산 |
| 전생(Prestige) 후 오프라인 | 전생 전 스테이지 기준으로 보상 계산 (전생 보너스 별도 적용) |

---

## 3. 오프라인 시간 상한

### 3.1 상한 시간: 12시간 (43,200초)

```csharp
const int MAX_OFFLINE_SECONDS = 43200; // 12시간
float clampedSeconds = Mathf.Min(elapsedSeconds, MAX_OFFLINE_SECONDS);
```

### 3.2 12시간 상한 선택 근거

#### 비교 분석

| 상한 시간 | 장점 | 단점 |
|-----------|------|------|
| **6시간** | 자주 접속 유도, 경제 안정 | 수면 시간 커버 불가, 이탈 위험 |
| **8시간** | 수면 시간 딱 커버 | 직장/학교 시간 커버 부족 |
| **12시간** | 수면+직장 커버, 하루 2회 접속 유도 | 24시간 방치 플레이어에게 상한 도달 |
| **24시간** | 하루 1회 접속으로 충분 | 보상 과잉, 경제 인플레이션 위험 |

#### 12시간을 선택한 이유

1. **생활 패턴 대응:** 수면 8시간 + 출퇴근/등하교 시간을 고려하면 12시간이면 대부분의 일상적 공백을 커버한다.
2. **접속 빈도 유도:** 하루 최소 2회 접속을 자연스럽게 유도한다. (아침 출발 전 + 저녁 귀가 후)
3. **경제 밸런스:** 12시간 상한이면 오프라인으로 얻을 수 있는 최대 골드가 제한되어, 직접 플레이하는 유저와의 격차가 지나치게 벌어지지 않는다.
4. **푸시 알림 연계:** "보상이 가득 찼습니다!" 알림을 12시간 뒤에 보내 자연스러운 복귀를 유도한다.
5. **업계 기준 부합:** 대부분의 방치형 게임 (AFK Arena, Idle Heroes 등)이 12~24시간 상한을 사용한다.

### 3.3 상한 확장 시스템 (향후 고려)

상한 시간을 늘려주는 영구 업그레이드를 통해 추가 성장 축을 제공할 수 있다.

| 업그레이드 레벨 | 상한 시간 | 필요 재화 |
|----------------|-----------|-----------|
| 기본 | 12시간 | - |
| Lv.1 | 14시간 | 보석 100 |
| Lv.2 | 16시간 | 보석 300 |
| Lv.3 | 20시간 | 보석 800 |
| Lv.4 (최대) | 24시간 | 보석 2,000 |

---

## 4. 효율 계수 설계

### 4.1 효율 계수 정의

효율 계수(Efficiency Coefficient)는 오프라인 상태에서의 보상이 온라인 대비 어느 정도의 비율로 지급되는지를 결정하는 핵심 밸런스 파라미터다.

```
오프라인 보상 = 온라인 보상 * 효율 계수
```

### 4.2 계수별 비교 분석

#### 30% 효율 (`efficiencyCoefficient = 0.3`)

| 항목 | 분석 |
|------|------|
| **플레이 동기** | 매우 강함 - 직접 플레이 대비 3.3배 차이 |
| **복귀 만족감** | 낮음 - "이게 전부야?" 느낌 |
| **이탈 위험** | 높음 - 보상이 너무 적어 복귀 의욕 감소 |
| **경제 안정성** | 매우 안정 - 인플레이션 위험 최소 |
| **적합 장르** | 능동적 플레이가 핵심인 게임 (RPG, 전략) |
| **결론** | 방치형 게임에는 부적합. 보상이 너무 인색하면 "방치"가 아니라 "방기"가 된다. |

#### 50% 효율 (`efficiencyCoefficient = 0.5`) -- 채택

| 항목 | 분석 |
|------|------|
| **플레이 동기** | 적절 - 직접 플레이 대비 2배 차이 |
| **복귀 만족감** | 적절 - 의미 있는 보상이 쌓여 있음 |
| **이탈 위험** | 낮음 - 복귀할 이유가 명확 |
| **경제 안정성** | 안정 - 직접 플레이 대비 절반이므로 통제 가능 |
| **적합 장르** | 방치형 액션 (본 게임의 장르) |
| **결론** | **"방치해도 반은 벌 수 있다"**는 심리적 균형점. 업계 표준에 부합. |

#### 70% 효율 (`efficiencyCoefficient = 0.7`)

| 항목 | 분석 |
|------|------|
| **플레이 동기** | 약함 - 직접 플레이 대비 1.43배 차이뿐 |
| **복귀 만족감** | 높음 - 거의 온라인 수준의 보상 |
| **이탈 위험** | 낮음 - 하지만 접속 빈도도 감소 |
| **경제 안정성** | 위험 - 모든 유저가 거의 동일한 속도로 성장 |
| **적합 장르** | 순수 방치형 (클릭만으로 진행되는 게임) |
| **결론** | 직접 플레이 인센티브가 약해 액션 게임에는 부적합. "굳이 켜서 할 필요가 없네" 문제. |

### 4.3 50% 채택 사유 요약

1. **심리적 앵커:** "절반"이라는 수치는 직관적이고 공정하게 느껴진다.
2. **능동 플레이 보호:** 직접 플레이하는 유저는 2배 효율을 누리므로 플레이 동기가 유지된다.
3. **광고 보상 연계:** 광고 시청 시 2배(= 100%) 적용으로 "광고만 보면 온라인과 동일!" 이라는 강력한 광고 시청 인센티브가 생긴다.
4. **업계 검증:** AFK Arena(50%), Idle Heroes(50~60%), 클래시 로얄(오프라인 없음) 등 성공적인 방치형 게임들이 40~60% 범위를 사용한다.
5. **밸런스 조절 용이:** 향후 VIP 시스템이나 특수 버프로 효율 계수를 올릴 수 있는 성장 축을 제공한다.

### 4.4 효율 계수 보너스 시스템 (향후)

기본 50%에 아래 보너스가 가산된다 (최대 80%, 100% 초과 불가).

| 보너스 출처 | 추가 효율 | 비고 |
|------------|-----------|------|
| 전생 레벨 1~5 | +2% per level (최대 +10%) | 전생 보상 |
| VIP 등급 | +5% ~ +20% | 과금 보상 |
| 이벤트 버프 | +10% ~ +30% | 기간 한정 |
| 펫 보너스 | +5% | 향후 펫 시스템 연계 |

---

## 5. 오프라인 보상 종류

### 5.1 보상 매트릭스

| 보상 종류 | 오프라인 지급 여부 | 효율 | 근거 |
|-----------|-------------------|------|------|
| **골드** | O (주요 보상) | 50% | 기본 재화, 방치형의 핵심 |
| **구슬 조각** | O (부분 지급) | 30% | 희귀 재화이므로 온라인 플레이 인센티브 강화 |
| **경험치** | O (부분 지급) | 40% | 레벨업 진행감 제공, 단 온라인보다 느리게 |
| **장비 아이템** | X | 0% | 드랍 확률/등급 시스템은 직접 플레이 보상으로 예약 |
| **보석 (프리미엄)** | X | 0% | 프리미엄 재화는 오프라인 지급 불가 |
| **스킬 경험치** | X | 0% | 스킬 사용 기반이므로 오프라인 지급 부적절 |
| **업적 진행도** | X | 0% | 특정 행동 기반이므로 오프라인 불가 |

### 5.2 보상별 상세 설계

#### 골드 (주요 보상)

```csharp
float offlineGold = goldPerSecond * clampedSeconds * 0.5f;
```

- 소수점 이하 버림 처리
- 숫자 포맷팅: 1,000 이상은 약식 표기 (1.2K, 1.5M 등)
- 최소 지급량: 1 골드 (0 이하 방지)

#### 구슬 조각 (부분 보상)

```csharp
// 오프라인 동안 예상 스테이지 클리어 횟수 기반
float estimatedStageClears = clampedSeconds / averageStageClearTime;
int offlineOrbFragments = Mathf.FloorToInt(estimatedStageClears * orbFragmentsPerClear * 0.3f);
```

- 스테이지 클리어 시에만 획득하는 재화이므로, 예상 클리어 횟수 기반 산출
- 효율 30%: 희귀 재화이므로 온라인 플레이 인센티브를 강하게 유지
- 최소 0개 (짧은 오프라인에서는 0개일 수 있음)

#### 경험치 (부분 보상)

```csharp
float offlineExp = expPerSecond * clampedSeconds * 0.4f;
```

- 레벨업이 발생하는 경우 레벨업 처리 후 보상 팝업에 "레벨업!" 표시
- 한 번에 여러 레벨을 올라가는 경우 최종 레벨만 표시 (중간 과정 스킵)

### 5.3 보상 지급 순서

1. 경과 시간 계산
2. 골드 계산 및 지급
3. 구슬 조각 계산 및 지급
4. 경험치 계산 및 지급 (레벨업 처리 포함)
5. 복귀 팝업 UI 표시
6. (선택) 광고 시청 시 2배 보상 추가 지급

---

## 6. 복귀 팝업 UI 명세

### 6.1 팝업 레이아웃

```
┌──────────────────────────────────────────┐
│              ✦ 접속 보상 ✦               │
│──────────────────────────────────────────│
│                                          │
│     당신이 없는 동안 용사가 열심히        │
│         싸워서 보상을 모았습니다!         │
│                                          │
│     ⏱ 오프라인 시간: 8시간 23분          │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  💰 골드         +443,088         │  │
│  │  🔮 구슬 조각    +12              │  │
│  │  ⭐ 경험치       +28,500          │  │
│  │  📈 레벨업!      Lv.34 → Lv.35   │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  🎬 광고 보상 2배!                │  │
│  │  골드 443,088 → 886,176           │  │
│  │  구슬 12 → 24                     │  │
│  │                                    │  │
│  │     [ 광고 시청하기 (30초) ]       │  │
│  └────────────────────────────────────┘  │
│                                          │
│         [ 보상 받기 ]                    │
│                                          │
│  (광고 없이 기본 보상만 수령)            │
└──────────────────────────────────────────┘
```

### 6.2 UI 요소 상세

| 요소 | 사양 | 비고 |
|------|------|------|
| 배경 딤 | #000000, 알파 60% | 게임 화면 위에 반투명 오버레이 |
| 팝업 패널 | 화면 중앙, 너비 80%, 높이 자동 | 라운드 코너 16px |
| 제목 텍스트 | "접속 보상", 폰트 36pt, 골드 컬러 | 반짝이는 파티클 이펙트 |
| 오프라인 시간 | "8시간 23분" 형식 | 1시간 미만: "45분", 1일 이상: "1일 2시간" |
| 보상 목록 | 아이콘 + 이름 + 수량 | 획득 없는 항목은 표시하지 않음 |
| 광고 보상 영역 | 황금 테두리, 하이라이트 배경 | 2배 보상 강조 |
| 광고 버튼 | 크기: 너비 60%, 높이 56px | 녹색 배경, 흰색 텍스트 |
| 기본 수령 버튼 | 크기: 너비 40%, 높이 48px | 회색 배경, 텍스트 약간 작게 |
| 레벨업 표시 | 레벨업 발생 시에만 표시 | 별 이펙트 애니메이션 |

### 6.3 애니메이션/연출 시퀀스

1. **팝업 등장** (0.3초): Scale 0 → 1, EaseOutBack 애니메이션
2. **오프라인 시간 카운트업** (0.5초): 0 → 실제 시간까지 숫자 올라가는 애니메이션
3. **보상 항목 순차 등장** (각 0.2초 간격):
   - 골드: 동전 아이콘 바운스 + 숫자 카운트업
   - 구슬 조각: 보라색 빛 이펙트 + 숫자 카운트업
   - 경험치: 별 파티클 + 숫자 카운트업
4. **레벨업 연출** (조건부, 0.5초): 화면 플래시 + 레벨업 텍스트 펀치 스케일
5. **광고 보상 영역 슬라이드인** (0.3초): 아래에서 위로 슬라이드
6. **버튼 활성화** (0.2초): 모든 연출 완료 후 버튼 인터랙션 가능

총 연출 시간: 약 1.5~2초

### 6.4 팝업 표시 조건

| 조건 | 팝업 표시 |
|------|-----------|
| 오프라인 시간 5분 이상 | O |
| 오프라인 시간 5분 미만 | X (보상은 자동 지급, 토스트 메시지로 알림) |
| 오프라인 시간 0 또는 음수 | X (비정상 상태) |
| 총 보상이 0 | X (표시할 내용 없음) |

### 6.5 토스트 메시지 (5분 미만 오프라인)

짧은 오프라인에서는 팝업 대신 화면 상단에 토스트 메시지를 표시한다.

```
"잠시 동안 +1,234 골드를 획득했습니다"
```

- 표시 시간: 3초
- 위치: 화면 상단 중앙
- 페이드 인/아웃: 0.3초

---

## 7. 광고 보상 설계

### 7.1 2배 보상 메커니즘

광고 시청 시 오프라인 보상 전체에 2배 승수를 적용한다.

```csharp
void ApplyAdBonus()
{
    // 이미 지급된 기본 보상과 동일한 양을 추가 지급
    playerData.gold += offlineGoldBase;           // 기존 50% + 추가 50% = 100%
    playerData.orbFragments += offlineOrbBase;     // 기존 30% + 추가 30% = 60%
    playerData.exp += offlineExpBase;              // 기존 40% + 추가 40% = 80%
}
```

> **핵심:** 광고 시청 시 오프라인 효율이 골드 기준 50% → 100%로 올라가, 온라인 플레이와 동등한 수준이 된다. 이는 "광고를 보면 내가 직접 플레이한 것과 같다"는 강력한 인센티브가 된다.

### 7.2 광고 빈도 제한

| 제한 항목 | 값 | 근거 |
|-----------|------|------|
| 복귀 보상 광고 | 복귀 시 1회 | 자연스러운 시점 |
| 일일 광고 시청 상한 | 10회 | 과도한 광고 노출 방지 |
| 광고 간 최소 간격 | 3분 | 연속 시청 방지 |
| 광고 쿨타임 표시 | 남은 시간 카운트다운 | UX 명확성 |

### 7.3 광고 시청 패턴별 시나리오 분석

#### 시나리오 A: 매번 광고를 시청하는 유저

```
하루 2회 복귀, 매번 광고 시청
일일 오프라인 보상 = goldPerSecond * 43,200 * 0.5 * 2 = goldPerSecond * 43,200
→ 온라인 플레이와 동일한 보상 수준
→ 광고 수익 발생, 유저 만족도 높음
→ 문제 없음: 직접 플레이 유저와의 격차 없음 (의도된 설계)
```

#### 시나리오 B: 절대 광고를 시청하지 않는 유저

```
하루 2회 복귀, 광고 안 봄
일일 오프라인 보상 = goldPerSecond * 43,200 * 0.5
→ 온라인의 50% 수준
→ 광고 유저 대비 50%의 보상을 받음
→ 직접 플레이로 보충 가능하므로 불공정하지 않음
→ 게임 진행이 느리지만 불가능하지는 않음
```

#### 시나리오 C: 가끔 광고를 시청하는 유저 (대부분의 유저)

```
하루 2회 복귀, 50% 확률로 광고 시청
일일 오프라인 보상 = goldPerSecond * 43,200 * 0.5 * 1.5 (평균)
→ 온라인의 75% 수준
→ 가장 일반적인 패턴, 밸런스 기준점
```

### 7.4 광고 실패 처리

| 상황 | 처리 |
|------|------|
| 광고 로드 실패 (네트워크 오류) | "광고를 불러올 수 없습니다" 토스트, 기본 보상 지급 |
| 광고 시청 중 이탈 | 보상 미지급, 재시청 가능 |
| 광고 SDK 미초기화 | 광고 버튼 숨김, 기본 보상만 표시 |
| 광고 캐싱 | 앱 시작 시 광고 사전 로드 (복귀 팝업 즉시 표시를 위해) |

### 7.5 광고 SDK 연동 (AdMob)

```csharp
// 광고 사전 로드 (앱 시작 시)
private void PreloadRewardedAd()
{
    var request = new AdRequest.Builder().Build();
    RewardedAd.Load(adUnitId, request, OnAdLoaded);
}

// 복귀 팝업에서 광고 버튼 클릭 시
public void OnWatchAdButtonClicked()
{
    if (rewardedAd != null && rewardedAd.CanShowAd())
    {
        rewardedAd.Show(OnAdRewarded);
    }
    else
    {
        ShowToast("광고를 불러오는 중입니다. 잠시 후 다시 시도해주세요.");
        PreloadRewardedAd(); // 재로드 시도
    }
}

// 광고 시청 완료 콜백
private void OnAdRewarded(Reward reward)
{
    ApplyAdBonus();
    SaveGameData(); // 보너스 즉시 저장
    PreloadRewardedAd(); // 다음 광고 사전 로드
}
```

---

## 8. 자동 전투 최적화

### 8.1 시뮬레이션 모드 개요

앱이 최소화 상태일 때, 실제 전투를 렌더링하지 않고 수학적으로 시뮬레이션한다.

```
[활성 모드]                     [최소화 시뮬레이션 모드]
실제 충돌 판정           →      DPS 기반 HP 감소 계산
물리 연산               →      생략
애니메이션/파티클        →      생략
카메라 추적             →      생략
UI 업데이트             →      생략
오디오                  →      음소거
```

### 8.2 간소화 전투 시뮬레이션 로직

```csharp
public class SimplifiedCombatSimulator
{
    /// <summary>
    /// 백그라운드에서 간소화된 전투를 시뮬레이션한다.
    /// 실제 물리/충돌 없이 DPS 기반으로 몬스터 처치와 스테이지 진행을 계산한다.
    /// </summary>
    public SimulationResult Simulate(float deltaTime, PlayerStats stats, StageData stage)
    {
        var result = new SimulationResult();
        float remainingTime = deltaTime;

        while (remainingTime > 0)
        {
            // 현재 방의 몬스터 총 HP
            float roomHP = CalculateRoomTotalHP(stage);

            // 방 클리어 소요 시간
            float clearTime = roomHP / stats.DPS;

            // 이동 시간
            float moveTime = 2f; // 방 사이 이동 시간

            float totalTime = clearTime + moveTime;

            if (remainingTime >= totalTime)
            {
                // 방 클리어 완료
                result.goldEarned += CalculateRoomGold(stage);
                result.expEarned += CalculateRoomExp(stage);
                result.roomsCleared++;

                remainingTime -= totalTime;

                // 마지막 방이면 스테이지 클리어
                if (IsLastRoom(stage))
                {
                    result.orbFragments += stage.orbFragmentsReward;
                    result.stagesCleared++;
                    AdvanceStage(stage);
                }
                else
                {
                    AdvanceRoom(stage);
                }
            }
            else
            {
                // 남은 시간으로 부분 진행 (비례 보상)
                float progress = remainingTime / totalTime;
                result.goldEarned += CalculateRoomGold(stage) * progress;
                result.expEarned += CalculateRoomExp(stage) * progress;
                remainingTime = 0;
            }
        }

        // 최소화 모드 효율 적용
        result.goldEarned *= 0.8f;
        result.expEarned *= 0.8f;

        return result;
    }
}
```

### 8.3 렌더링 스킵 로직

```csharp
void OnApplicationPause(bool isPaused)
{
    if (isPaused)
    {
        // === 최소화 진입 ===

        // 1. 현재 시간 즉시 저장 (OS 강제 종료 대비)
        SaveLastPlayTime();

        // 2. 렌더링 비활성화
        Camera.main.enabled = false;

        // 3. 파티클 시스템 모두 정지
        foreach (var ps in activeParticleSystems)
            ps.Pause();

        // 4. 오디오 음소거
        AudioListener.pause = true;

        // 5. 불필요한 MonoBehaviour 비활성화
        DisableNonEssentialComponents();

        // 6. 간소화 시뮬레이션 시작
        StartSimplifiedSimulation();

        // 7. 프레임레이트 최소화 (OS가 허용하는 한)
        Application.targetFrameRate = 1;
    }
    else
    {
        // === 최소화 복귀 ===

        // 1. 시뮬레이션 결과 수집
        var simResult = StopSimplifiedSimulation();

        // 2. 보상 지급
        ApplySimulationRewards(simResult);

        // 3. 렌더링 복원
        Camera.main.enabled = true;

        // 4. 파티클 재개
        foreach (var ps in activeParticleSystems)
            ps.Play();

        // 5. 오디오 복원
        AudioListener.pause = false;

        // 6. 컴포넌트 재활성화
        EnableNonEssentialComponents();

        // 7. 프레임레이트 복원
        Application.targetFrameRate = GetTargetFrameRate();

        // 8. 복귀 팝업 표시 (5분 이상 백그라운드였던 경우)
        if (simResult.elapsedTime >= 300f)
            ShowReturnPopup(simResult);
    }
}
```

### 8.4 시뮬레이션 vs 오프라인 계산 비교

| 항목 | 최소화 시뮬레이션 | 오프라인 계산 |
|------|-------------------|---------------|
| 실행 주체 | 앱 프로세스 (살아있음) | 복귀 시 일괄 계산 |
| 정확도 | 높음 (실시간 DPS 반영) | 중간 (마지막 상태 기준) |
| 스테이지 진행 | 실제로 진행됨 | 진행 안 됨 (보상만 지급) |
| 레벨업 반영 | 즉시 반영 (DPS 증가) | 미반영 (최종 일괄 처리) |
| 효율 계수 | 80% | 50% |
| 보상 종류 | 골드, 구슬, 경험치, 아이템 드랍 | 골드, 구슬, 경험치 (아이템 X) |

### 8.5 DPS 파워 게이트 (진행 제한)

시뮬레이션 중 DPS가 현재 스테이지 몬스터를 처치하기에 부족한 경우를 처리한다.

```csharp
// DPS가 방 클리어에 60초 이상 걸리면 "막힌 스테이지"로 판정
const float MAX_ROOM_CLEAR_TIME = 60f;

if (clearTime > MAX_ROOM_CLEAR_TIME)
{
    // 더 이상 스테이지 진행 불가
    // 현재 스테이지에서 골드/경험치만 획득 (반복 파밍)
    isStuck = true;
}
```

---

## 9. 배터리 절약 모드

### 9.1 설계 목표

방치형 게임의 특성상 장시간 화면을 켜둔 채로 방치하는 유저가 많다. 배터리 소모를 줄여 유저 경험을 개선한다.

### 9.2 모드 사양

| 항목 | 일반 모드 | 배터리 절약 모드 |
|------|-----------|-----------------|
| 프레임레이트 | 60fps | 30fps |
| 파티클 이펙트 | 전체 | 50% 감소 (최대 동시 파티클 수 제한) |
| 히트스톱 | 활성화 | 비활성화 |
| 카메라 셰이크 | 활성화 | 비활성화 |
| 데미지 텍스트 | 전체 표시 | 치명타만 표시 |
| 배경 스크롤링 | 멀티 레이어 패럴럭스 | 단일 레이어 |
| 그림자 | 활성화 | 비활성화 |
| 음질 | 고품질 | 저품질 (모노) |
| 예상 배터리 절약 | 기준 | 약 30~40% 감소 |

### 9.3 자동 제안 시스템

배터리 절약 모드를 다음 조건에서 자동으로 제안한다.

```csharp
void CheckBatterySavingSuggestion()
{
    float batteryLevel = SystemInfo.batteryLevel; // 0.0 ~ 1.0
    BatteryStatus status = SystemInfo.batteryStatus;

    // 배터리 20% 이하 + 충전 중이 아닌 경우
    if (batteryLevel <= 0.2f && status == BatteryStatus.Discharging)
    {
        if (!hasShownBatterySuggestion)
        {
            ShowBatterySavingPopup();
            hasShownBatterySuggestion = true;
        }
    }

    // 연속 플레이 30분 이상 + 배터리 50% 이하
    if (continuousPlayTime >= 1800f && batteryLevel <= 0.5f)
    {
        if (!hasShownPlaytimeSuggestion)
        {
            ShowBatterySavingToast("배터리 절약 모드를 켜시겠어요?");
            hasShownPlaytimeSuggestion = true;
        }
    }
}
```

### 9.4 제안 팝업

```
┌────────────────────────────────────┐
│       배터리가 부족합니다!         │
│                                    │
│  🔋 현재 배터리: 18%              │
│                                    │
│  배터리 절약 모드를 켜면           │
│  배터리 소모가 30~40% 줄어듭니다.  │
│                                    │
│  • 프레임: 60fps → 30fps          │
│  • 이펙트 감소                     │
│  • 게임 진행에는 영향 없음         │
│                                    │
│   [ 켜기 ]        [ 괜찮아요 ]     │
└────────────────────────────────────┘
```

### 9.5 구현 코드

```csharp
public class BatterySavingManager : MonoBehaviour
{
    [SerializeField] private bool isEnabled = false;

    public void SetBatterySavingMode(bool enabled)
    {
        isEnabled = enabled;

        // 프레임레이트
        Application.targetFrameRate = enabled ? 30 : 60;

        // 파티클 제한
        ParticleManager.Instance.SetMaxParticles(enabled ? 20 : 50);

        // 히트스톱
        HitStopManager.Instance.SetEnabled(!enabled);

        // 카메라 셰이크
        CameraShakeManager.Instance.SetEnabled(!enabled);

        // 데미지 텍스트 필터
        DamageTextManager.Instance.SetFilter(
            enabled ? DamageTextFilter.CritOnly : DamageTextFilter.All
        );

        // 배경 레이어
        BackgroundScroller.Instance.SetParallaxLayers(enabled ? 1 : 3);

        // 그림자
        QualitySettings.shadows = enabled ? ShadowQuality.Disable : ShadowQuality.All;

        // 저장
        PlayerPrefs.SetInt("BatterySavingMode", enabled ? 1 : 0);
    }
}
```

### 9.6 설정 메뉴 연동

설정 화면에 배터리 절약 모드 토글을 배치한다.

```
설정
├── 사운드
│   ├── BGM 볼륨: ████████░░ 80%
│   └── SFX 볼륨: ██████████ 100%
├── 화면
│   ├── 배터리 절약 모드: [ OFF / ON ]      ← 여기
│   └── 화면 꺼짐 방지: [ OFF / ON ]
└── 알림
    └── 푸시 알림: [ OFF / ON ]
```

---

## 10. 푸시 알림 시스템

### 10.1 알림 종류

| ID | 트리거 | 제목 | 내용 | 발송 시점 |
|----|--------|------|------|-----------|
| `REWARD_FULL` | 오프라인 보상 상한 도달 | "보상이 가득 찼습니다!" | "용사가 모은 보상이 가득 찼어요. 지금 수령하세요!" | 마지막 접속 + 12시간 |
| `REWARD_REMIND` | 오프라인 중간 리마인드 | "보상이 쌓이고 있어요" | "현재까지 {goldAmount} 골드가 쌓였습니다. 확인해보세요!" | 마지막 접속 + 4시간 |
| `DAILY_REMIND` | 24시간 미접속 | "용사가 기다리고 있어요!" | "오른쪽으로 달려야 할 시간이에요!" | 마지막 접속 + 24시간 |
| `COMEBACK` | 3일 미접속 | "돌아와 주세요!" | "특별 복귀 보상을 준비했어요. 지금 접속하세요!" | 마지막 접속 + 72시간 |
| `WEEKLY` | 7일 미접속 | "용사님, 보고 싶었어요" | "7일간의 특별 복귀 패키지가 기다리고 있습니다!" | 마지막 접속 + 168시간 |

### 10.2 알림 스케줄링

앱 종료 또는 최소화 시점에 로컬 푸시 알림을 스케줄링한다. (서버 불필요)

```csharp
public class PushNotificationScheduler
{
    public void ScheduleNotifications()
    {
        // 기존 알림 모두 취소 (중복 방지)
        CancelAllScheduledNotifications();

        DateTime now = DateTime.UtcNow;

        // 4시간 후: 중간 리마인드
        ScheduleLocalNotification(
            id: "REWARD_REMIND",
            title: "보상이 쌓이고 있어요",
            body: $"현재까지 {EstimateGold(4)} 골드가 쌓였습니다. 확인해보세요!",
            fireTime: now.AddHours(4),
            channelId: "idle_rewards"
        );

        // 12시간 후: 보상 가득
        ScheduleLocalNotification(
            id: "REWARD_FULL",
            title: "보상이 가득 찼습니다!",
            body: "용사가 모은 보상이 가득 찼어요. 지금 수령하세요!",
            fireTime: now.AddHours(12),
            channelId: "idle_rewards"
        );

        // 24시간 후: 일일 리마인드
        ScheduleLocalNotification(
            id: "DAILY_REMIND",
            title: "용사가 기다리고 있어요!",
            body: "오른쪽으로 달려야 할 시간이에요!",
            fireTime: now.AddHours(24),
            channelId: "daily_remind"
        );

        // 72시간 후: 복귀 유도
        ScheduleLocalNotification(
            id: "COMEBACK",
            title: "돌아와 주세요!",
            body: "특별 복귀 보상을 준비했어요. 지금 접속하세요!",
            fireTime: now.AddHours(72),
            channelId: "comeback"
        );

        // 168시간 후: 주간 복귀
        ScheduleLocalNotification(
            id: "WEEKLY",
            title: "용사님, 보고 싶었어요",
            body: "7일간의 특별 복귀 패키지가 기다리고 있습니다!",
            fireTime: now.AddHours(168),
            channelId: "comeback"
        );
    }

    // 앱 복귀 시 예약된 알림 취소
    public void OnAppResumed()
    {
        CancelAllScheduledNotifications();
    }
}
```

### 10.3 알림 빈도 제한

| 규칙 | 설명 |
|------|------|
| 야간 발송 금지 | 22:00~08:00 (로컬 시간) 사이에는 알림 미발송 (Android 알림 채널 설정) |
| 일일 최대 횟수 | 하루 최대 2건 |
| 동일 ID 중복 방지 | 같은 종류의 알림은 하나만 유지 |
| 앱 접속 시 자동 취소 | 앱 복귀 시 모든 예약 알림 취소 후 재스케줄링 |
| 사용자 설정 존중 | 설정에서 알림 OFF 시 스케줄링하지 않음 |

### 10.4 Android 알림 채널 설정

```csharp
// Android 8.0+ 알림 채널 생성
void CreateNotificationChannels()
{
    // 방치 보상 채널 (중요도: 높음)
    CreateChannel(
        id: "idle_rewards",
        name: "방치 보상 알림",
        description: "오프라인 보상이 쌓였을 때 알림",
        importance: Importance.High
    );

    // 일일 리마인드 채널 (중요도: 기본)
    CreateChannel(
        id: "daily_remind",
        name: "일일 알림",
        description: "매일 게임 접속 리마인드",
        importance: Importance.Default
    );

    // 복귀 유도 채널 (중요도: 낮음)
    CreateChannel(
        id: "comeback",
        name: "복귀 알림",
        description: "장기 미접속 시 복귀 유도 알림",
        importance: Importance.Low
    );
}
```

### 10.5 알림 텍스트 다양화

같은 종류의 알림이라도 반복 시 지루해지지 않도록 텍스트를 랜덤 선택한다.

```csharp
// REWARD_FULL 알림 텍스트 풀
private string[] rewardFullMessages = {
    "용사가 모은 보상이 가득 찼어요. 지금 수령하세요!",
    "창고가 터지기 직전이에요! 보상을 확인해주세요!",
    "12시간 동안 열심히 싸운 보상이 기다리고 있어요!",
    "보상 주머니가 꽉 찼습니다. 어서 열어보세요!",
    "용사의 금고가 넘치기 직전! 빨리 와주세요!"
};
```

---

## 11. 저장/로드 시스템

### 11.1 데이터 저장 전략

게임 데이터는 두 가지 저장소를 사용한다.

| 저장소 | 용도 | 데이터 |
|--------|------|--------|
| **PlayerPrefs** | 빠른 접근, 시간 기록 | lastPlayTime, 설정값 |
| **JSON 파일** | 전체 게임 상태 | 캐릭터, 인벤토리, 스테이지, 재화 등 |

### 11.2 PlayerPrefs 필드

| 키 | 타입 | 설명 | 예시 값 |
|----|------|------|---------|
| `LastPlayTime` | string (ISO 8601 UTC) | 마지막 플레이 시각 | `"2026-03-31T14:30:00Z"` |
| `LastPlayTimeTicks` | string (long) | 마지막 플레이 시각 (Ticks, 백업) | `"638789658000000000"` |
| `LastSaveVersion` | int | 저장 데이터 버전 | `1` |
| `BatterySavingMode` | int | 배터리 절약 모드 (0/1) | `0` |
| `PushNotificationEnabled` | int | 푸시 알림 활성화 (0/1) | `1` |
| `BGMVolume` | float | BGM 볼륨 | `0.8` |
| `SFXVolume` | float | SFX 볼륨 | `1.0` |
| `TotalPlayTimeSeconds` | float | 누적 플레이 시간 (초) | `36000` |
| `SessionCount` | int | 총 접속 횟수 | `42` |
| `AdWatchCount` | int | 오늘 광고 시청 횟수 | `3` |
| `AdWatchDate` | string | 광고 횟수 초기화 기준 날짜 | `"2026-03-31"` |

### 11.3 JSON 저장 구조

```json
{
    "saveVersion": 1,
    "saveTimestamp": "2026-03-31T14:30:00Z",
    "saveTimestampTicks": 638789658000000000,
    "checksum": "a3f2b7c9d1e4...",

    "player": {
        "level": 35,
        "currentExp": 12500,
        "expToNextLevel": 28000,
        "totalPlayTimeSeconds": 36000
    },

    "stats": {
        "atk": 150,
        "atkLevel": 12,
        "atkSpeed": 1.2,
        "atkSpeedLevel": 5,
        "critRate": 0.15,
        "critRateLevel": 3,
        "critDmg": 2.0,
        "critDmgLevel": 2,
        "moveSpeed": 5.0,
        "moveSpeedLevel": 4,
        "hp": 1000,
        "hpLevel": 8
    },

    "currency": {
        "gold": 1234567,
        "orbFragments": 89,
        "gems": 150
    },

    "stage": {
        "currentStage": 127,
        "currentRoom": 3,
        "roomsPerStage": 6,
        "highestStage": 127,
        "totalStagesCleared": 542
    },

    "skills": [
        {
            "id": "basic_combo",
            "level": 5,
            "isEquipped": true,
            "slotIndex": 0
        },
        {
            "id": "area_slash",
            "level": 3,
            "isEquipped": true,
            "slotIndex": 1
        },
        {
            "id": "ultimate_fury",
            "level": 2,
            "isEquipped": true,
            "slotIndex": 2
        }
    ],

    "equipment": [
        {
            "id": "sword_001",
            "grade": "rare",
            "level": 10,
            "isEquipped": true
        }
    ],

    "prestige": {
        "prestigeCount": 2,
        "permanentBonusAtk": 0.1,
        "permanentBonusGold": 0.15,
        "offlineEfficiencyBonus": 0.04
    },

    "idle": {
        "lastCalculatedGoldPerSecond": 30.77,
        "offlineMaxSeconds": 43200,
        "offlineEfficiency": 0.54,
        "totalOfflineGoldEarned": 5678900,
        "totalAdWatched": 28
    },

    "achievements": {
        "completed": ["first_kill", "stage_10", "stage_50", "stage_100"],
        "progress": {
            "kill_1000": 856,
            "gold_1m": 890000
        }
    },

    "settings": {
        "batterySaving": false,
        "pushNotification": true,
        "screenAlwaysOn": true
    }
}
```

### 11.4 저장 빈도

| 트리거 | 저장 대상 | 비고 |
|--------|-----------|------|
| 스테이지 클리어 시 | JSON 전체 | 주요 진행 저장점 |
| 방 클리어 시 | PlayerPrefs (LastPlayTime만) | 경량 저장 |
| 강화/구매 시 | JSON 전체 | 재화 변동 즉시 반영 |
| 앱 최소화 시 | JSON 전체 + PlayerPrefs | OS 종료 대비 |
| 앱 종료 시 | JSON 전체 + PlayerPrefs | 최종 상태 보존 |
| 주기적 자동 저장 | JSON 전체 | 60초 간격 |
| 광고 보상 수령 시 | JSON 전체 | 보상 손실 방지 |

### 11.5 저장/로드 코드

```csharp
public class SaveManager : MonoBehaviour
{
    private const string SAVE_FILE_NAME = "save_data.json";
    private const string BACKUP_FILE_NAME = "save_data_backup.json";
    private const string SAVE_KEY = "RUNNING_RIGHT_SAVE_V1"; // 암호화 키

    /// <summary>
    /// 게임 데이터를 JSON 파일로 저장한다.
    /// </summary>
    public void SaveGame(GameData data)
    {
        // 1. 타임스탬프 갱신
        data.saveTimestamp = DateTime.UtcNow.ToString("o");
        data.saveTimestampTicks = DateTime.UtcNow.Ticks;

        // 2. JSON 직렬화
        string json = JsonUtility.ToJson(data, prettyPrint: false);

        // 3. 체크섬 생성
        data.checksum = GenerateChecksum(json);
        json = JsonUtility.ToJson(data, prettyPrint: false);

        // 4. 기존 저장 파일을 백업으로 복사
        string savePath = GetSavePath(SAVE_FILE_NAME);
        string backupPath = GetSavePath(BACKUP_FILE_NAME);
        if (File.Exists(savePath))
        {
            File.Copy(savePath, backupPath, overwrite: true);
        }

        // 5. 새 저장 파일 쓰기
        File.WriteAllText(savePath, json);

        // 6. PlayerPrefs 업데이트
        PlayerPrefs.SetString("LastPlayTime", data.saveTimestamp);
        PlayerPrefs.SetString("LastPlayTimeTicks", data.saveTimestampTicks.ToString());
        PlayerPrefs.Save();
    }

    /// <summary>
    /// 저장된 게임 데이터를 로드한다.
    /// </summary>
    public GameData LoadGame()
    {
        string savePath = GetSavePath(SAVE_FILE_NAME);
        string backupPath = GetSavePath(BACKUP_FILE_NAME);

        // 1. 메인 저장 파일 로드 시도
        GameData data = TryLoadFromFile(savePath);

        // 2. 실패 시 백업 파일 로드
        if (data == null)
        {
            Debug.LogWarning("메인 저장 파일 로드 실패, 백업에서 복구 시도");
            data = TryLoadFromFile(backupPath);
        }

        // 3. 백업도 실패 시 신규 데이터 생성
        if (data == null)
        {
            Debug.LogWarning("백업 파일도 로드 실패, 신규 게임 시작");
            data = CreateNewGameData();
        }

        return data;
    }

    private GameData TryLoadFromFile(string path)
    {
        if (!File.Exists(path))
            return null;

        try
        {
            string json = File.ReadAllText(path);
            GameData data = JsonUtility.FromJson<GameData>(json);

            // 체크섬 검증
            if (!ValidateChecksum(data, json))
            {
                Debug.LogError("체크섬 불일치 - 데이터 변조 의심");
                return null;
            }

            // 데이터 유효성 검증
            if (!ValidateData(data))
            {
                Debug.LogError("데이터 유효성 검증 실패");
                return null;
            }

            return data;
        }
        catch (Exception e)
        {
            Debug.LogError($"저장 파일 파싱 오류: {e.Message}");
            return null;
        }
    }

    private string GetSavePath(string fileName)
    {
        return Path.Combine(Application.persistentDataPath, fileName);
    }
}
```

### 11.6 데이터 유효성 검증

로드 시 다음 항목을 검증하여 비정상 데이터를 방지한다.

```csharp
private bool ValidateData(GameData data)
{
    // 필수 필드 존재 확인
    if (data.player == null || data.stats == null || data.currency == null)
        return false;

    // 수치 범위 검증
    if (data.player.level < 1 || data.player.level > 99999)
        return false;
    if (data.currency.gold < 0)
        return false;
    if (data.currency.orbFragments < 0)
        return false;
    if (data.currency.gems < 0)
        return false;

    // 스테이지 범위 검증
    if (data.stage.currentStage < 1)
        return false;
    if (data.stage.currentRoom < 0 || data.stage.currentRoom >= data.stage.roomsPerStage)
        return false;

    // 스탯 레벨 비정상 검증
    if (data.stats.atkLevel < 0 || data.stats.atkLevel > 99999)
        return false;

    // 저장 버전 호환성 검증
    if (data.saveVersion > CURRENT_SAVE_VERSION)
    {
        Debug.LogError("미래 버전의 저장 데이터 - 다운그레이드 불가");
        return false;
    }

    return true;
}
```

### 11.7 시간 조작 방지 (Anti-Cheat)

#### 위협 모델

| 조작 방법 | 설명 | 위험도 |
|-----------|------|--------|
| 기기 시간 앞당기기 | 시스템 시간을 미래로 변경하여 오프라인 시간을 늘림 | 높음 |
| 기기 시간 되돌리기 | 보상 수령 후 시간을 과거로 되돌리고 재수령 | 중간 |
| 저장 파일 수정 | JSON 파일을 직접 편집하여 재화/스탯 변경 | 중간 |
| 메모리 수정 | 게임 실행 중 메모리 값 변경 (GameGuardian 등) | 높음 |

#### 시간 조작 감지 로직

```csharp
public class AntiCheatManager
{
    // 서버 시간 검증이 불가능한 오프라인 게임이므로
    // 복수의 시간 소스를 교차 검증한다.

    public TimeValidationResult ValidateOfflineTime(GameData savedData)
    {
        DateTime savedTime;

        // 1. PlayerPrefs의 ISO 8601 시간
        string savedTimeStr = PlayerPrefs.GetString("LastPlayTime", "");
        if (!DateTime.TryParse(savedTimeStr, out savedTime))
        {
            // 파싱 실패 시 Ticks로 복구 시도
            string ticksStr = PlayerPrefs.GetString("LastPlayTimeTicks", "");
            if (long.TryParse(ticksStr, out long ticks))
            {
                savedTime = new DateTime(ticks, DateTimeKind.Utc);
            }
            else
            {
                return TimeValidationResult.DataCorrupted;
            }
        }

        DateTime now = DateTime.UtcNow;
        TimeSpan elapsed = now - savedTime;

        // 2. 미래 시간 감지 (저장 시간이 현재보다 미래)
        if (elapsed.TotalSeconds < -60) // 1분 오차 허용
        {
            Debug.LogWarning($"시간 조작 의심: 저장 시간이 {elapsed.TotalSeconds}초 미래");
            return TimeValidationResult.FutureTimeDetected;
        }

        // 3. 비현실적 경과 시간 감지 (30일 이상)
        if (elapsed.TotalDays > 30)
        {
            Debug.LogWarning($"비현실적 경과 시간: {elapsed.TotalDays}일");
            return TimeValidationResult.UnrealisticDuration;
        }

        // 4. 누적 플레이 시간과 교차 검증
        float expectedMinPlayTime = savedData.player.level * 60f; // 레벨당 최소 1분
        if (savedData.player.totalPlayTimeSeconds < expectedMinPlayTime * 0.1f)
        {
            Debug.LogWarning("플레이 시간 대비 레벨이 비정상적으로 높음");
            return TimeValidationResult.ProgressMismatch;
        }

        // 5. 세션 카운터 검증
        // 앱 시작 시마다 1씩 증가하는 카운터. 시간 조작과 무관하게 증가.
        int sessionCount = PlayerPrefs.GetInt("SessionCount", 0);
        PlayerPrefs.SetInt("SessionCount", sessionCount + 1);

        return TimeValidationResult.Valid;
    }

    // 시간 조작 감지 시 처리
    public float GetSafeOfflineSeconds(TimeValidationResult result, float rawSeconds)
    {
        switch (result)
        {
            case TimeValidationResult.Valid:
                return Mathf.Min(rawSeconds, MAX_OFFLINE_SECONDS);

            case TimeValidationResult.FutureTimeDetected:
                // 미래 시간: 보상 0
                return 0f;

            case TimeValidationResult.UnrealisticDuration:
                // 30일 이상: 상한(12시간)만 지급
                return MAX_OFFLINE_SECONDS;

            case TimeValidationResult.ProgressMismatch:
                // 진행도 불일치: 50% 페널티
                return Mathf.Min(rawSeconds, MAX_OFFLINE_SECONDS) * 0.5f;

            case TimeValidationResult.DataCorrupted:
                // 데이터 손상: 보상 0, 로그 기록
                return 0f;

            default:
                return 0f;
        }
    }
}

public enum TimeValidationResult
{
    Valid,
    FutureTimeDetected,
    UnrealisticDuration,
    ProgressMismatch,
    DataCorrupted
}
```

#### 체크섬 생성/검증

```csharp
private string GenerateChecksum(string jsonWithoutChecksum)
{
    // 체크섬 필드를 제외한 JSON에 대해 HMAC-SHA256 생성
    // SAVE_KEY는 코드에 하드코딩 (완벽한 보안은 불가, 캐주얼 치팅 방지 목적)
    using (var hmac = new System.Security.Cryptography.HMACSHA256(
        System.Text.Encoding.UTF8.GetBytes(SAVE_KEY)))
    {
        byte[] hash = hmac.ComputeHash(
            System.Text.Encoding.UTF8.GetBytes(jsonWithoutChecksum));
        return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
    }
}

private bool ValidateChecksum(GameData data, string fullJson)
{
    string savedChecksum = data.checksum;

    // 체크섬 필드를 초기화한 상태로 재계산
    data.checksum = "";
    string jsonWithoutChecksum = JsonUtility.ToJson(data, prettyPrint: false);
    string calculatedChecksum = GenerateChecksum(jsonWithoutChecksum);

    // 복원
    data.checksum = savedChecksum;

    return savedChecksum == calculatedChecksum;
}
```

### 11.8 저장 데이터 마이그레이션

게임 업데이트로 저장 구조가 변경될 때를 대비한 마이그레이션 시스템이다.

```csharp
public class SaveMigrator
{
    private const int CURRENT_VERSION = 1;

    public GameData Migrate(GameData data)
    {
        if (data.saveVersion == CURRENT_VERSION)
            return data;

        // 버전별 순차 마이그레이션
        if (data.saveVersion < 1)
        {
            data = MigrateV0ToV1(data);
        }
        // 향후 추가:
        // if (data.saveVersion < 2)
        //     data = MigrateV1ToV2(data);

        data.saveVersion = CURRENT_VERSION;
        return data;
    }

    private GameData MigrateV0ToV1(GameData data)
    {
        // 예: prestige 필드 추가
        if (data.prestige == null)
        {
            data.prestige = new PrestigeData
            {
                prestigeCount = 0,
                permanentBonusAtk = 0,
                permanentBonusGold = 0,
                offlineEfficiencyBonus = 0
            };
        }
        return data;
    }
}
```

### 11.9 저장 실패 복구 전략

| 상황 | 복구 전략 |
|------|-----------|
| 메인 저장 파일 손상 | 백업 파일에서 복구 |
| 백업 파일도 손상 | PlayerPrefs에서 최소 정보 복구 (시간, 설정) + 신규 게임 |
| 저장 공간 부족 | 저장 시도 전 여유 공간 확인, 부족 시 경고 팝업 |
| 쓰기 도중 앱 종료 | 임시 파일에 먼저 쓰고 완료 후 이름 변경 (atomic write) |
| JSON 파싱 오류 | try-catch로 잡아서 백업 파일 사용 |

#### Atomic Write 구현

```csharp
public void SafeWriteFile(string targetPath, string content)
{
    string tempPath = targetPath + ".tmp";

    try
    {
        // 1. 임시 파일에 쓰기
        File.WriteAllText(tempPath, content);

        // 2. 기존 파일을 백업으로 이동
        if (File.Exists(targetPath))
        {
            string backupPath = targetPath.Replace(".json", "_backup.json");
            File.Copy(targetPath, backupPath, overwrite: true);
        }

        // 3. 임시 파일을 실제 파일로 이동 (atomic operation)
        if (File.Exists(targetPath))
            File.Delete(targetPath);
        File.Move(tempPath, targetPath);
    }
    catch (Exception e)
    {
        Debug.LogError($"저장 실패: {e.Message}");
        // 임시 파일 정리
        if (File.Exists(tempPath))
            File.Delete(tempPath);
    }
}
```

---

## 부록: 전체 시스템 흐름도

```
[앱 시작]
    │
    ├─ SaveManager.LoadGame()
    │   ├─ JSON 파일 로드
    │   ├─ 체크섬 검증
    │   ├─ 데이터 유효성 검증
    │   └─ 버전 마이그레이션
    │
    ├─ AntiCheatManager.ValidateOfflineTime()
    │   ├─ 경과 시간 계산
    │   ├─ 시간 조작 감지
    │   └─ 안전한 오프라인 시간 산출
    │
    ├─ OfflineRewardCalculator.Calculate()
    │   ├─ goldPerSecond 산출
    │   ├─ 골드 = gps * seconds * 0.5
    │   ├─ 구슬 조각 = 예상 클리어 * 0.3
    │   ├─ 경험치 = eps * seconds * 0.4
    │   └─ 레벨업 처리
    │
    ├─ [오프라인 5분 이상?]
    │   ├─ YES → ReturnPopupUI 표시
    │   │          ├─ 보상 요약
    │   │          ├─ 광고 시청 버튼 (2배)
    │   │          └─ 기본 수령 버튼
    │   └─ NO  → 토스트 메시지 (자동 수령)
    │
    ├─ PushNotificationScheduler.OnAppResumed()
    │   └─ 기존 예약 알림 모두 취소
    │
    └─ [게임 플레이 시작]
        │
        ├─ [60초마다] AutoSave
        ├─ [방 클리어] SaveLastPlayTime
        ├─ [스테이지 클리어] SaveGame (전체)
        │
        ├─ [앱 최소화]
        │   ├─ SaveGame (전체)
        │   ├─ 렌더링 비활성화
        │   ├─ 간소화 시뮬레이션 시작
        │   └─ PushNotificationScheduler.Schedule()
        │
        └─ [앱 종료]
            ├─ SaveGame (전체)
            └─ PushNotificationScheduler.Schedule()
```

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| 1.0 | 2026-03-31 | 초기 설계 문서 작성 |
