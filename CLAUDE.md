# 오른쪽 달리기 (Running Right)

## 프로젝트 개요
- DNF(던전앤파이터) 패러디 방치형 2D 횡스크롤 액션 게임
- 플랫폼: Android
- 엔진: Unity 2022 LTS+, C#

## 게임 핵심 루프
캐릭터 자동 오른쪽 달리기 → 몬스터 무리 처치 → 마지막 방 개 얼굴 구슬 파괴 → 스테이지 반복 (무한)

## 프로젝트 구조
```
Assets/
├── Scripts/
│   ├── Core/          # GameManager, StageManager
│   ├── Character/     # Player, Stats, Skills
│   ├── Monster/       # Monster, Spawner
│   ├── Stage/         # Room, DungeonGenerator
│   ├── UI/            # HUD, Popup, Inventory
│   ├── Idle/          # OfflineReward, AutoCombat
│   └── Data/          # ScriptableObjects, SaveData
├── Prefabs/
├── Sprites/
├── Animations/
├── ScriptableObjects/
├── Scenes/
└── Audio/
```

## 개발 규칙
- 데이터 관리: ScriptableObject 기반
- 저장: JSON + PlayerPrefs
- 카메라: Cinemachine 2D
- 커밋 메시지: Conventional Commits (feat, fix, refactor, docs, test, chore)
- 언어: 코드는 영어, 주석/문서는 한국어 허용

## 개발 단계
전체 계획은 [MASTER_PLAN.md](MASTER_PLAN.md) 참조

| Phase | 내용 | 기간 |
|-------|------|------|
| 0 | 프로젝트 셋업 | 1주 |
| 1 | 코어 루프 프로토타입 | 2주 |
| 2 | 전투 시스템 고도화 | 2주 |
| 3 | 성장 시스템 | 2주 |
| 4 | 방치형 시스템 | 1.5주 |
| 5 | UI/UX | 2주 |
| 6 | 아트/사운드 | 2주 |
| 7 | 폴리시/최적화 | 1.5주 |
| 8 | 빌드/출시 | 1주 |

## 핵심 설계
- 몬스터 스케일링: `BaseHP * (1 + stage * 0.15)`
- 오프라인 보상: 경과시간 기반, 효율 계수 적용
- 스킬: ScriptableObject 정의, 쿨타임 기반 자동 시전
- 성능: 오브젝트 풀링 필수 (몬스터, 데미지 텍스트, 이펙트)
