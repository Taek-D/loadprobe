---
name: loadprobe-architecture
description: LoadProbe 전체 아키텍처, 모듈 간 의존성, 데이터 흐름. Use when working with project structure, module boundaries, or data flow.
---

# LoadProbe Architecture

## System Overview
```
[Locust Client] → HTTP → [FastAPI Server] → [SQLite DB]
                              ↑
[System Monitor] → psutil → [CPU/Memory Metrics]
                              ↓
[Report Generator] ← CSV ← [Test Results]
         ↓
   [HTML Report + SLA Judgment]
```

## Module Responsibilities

### server/ - FastAPI Target Server
- HTTP 엔드포인트 3종 제공
- SQLite 데이터 레이어
- 병목 시뮬레이션 모드 (`?slow=true`)
- 독립 실행 가능 (Docker 컨테이너)

### locust/ - Load Test Scenarios
- 3가지 시나리오 (정상/스파이크/지속)
- VUser 단계별 램프업 설정
- 결과 CSV 자동 저장
- server/ 모듈에 의존 (테스트 대상)

### monitor/ - System Monitoring
- psutil 기반 CPU/메모리 수집
- 주기적 샘플링 (1초 간격)
- CSV 형식 메트릭 저장
- 독립 실행 가능

### report/ - Report Generation
- Locust CSV + Monitor CSV 파싱
- SLA 기준 자동 판정
- Jinja2 HTML 리포트 생성
- locust/, monitor/ 출력에 의존

## Data Flow
1. `docker compose up` → server, monitor 시작
2. `locust` 실행 → server에 부하 생성
3. monitor가 CPU/메모리 수집 → CSV 저장
4. locust 완료 → 결과 CSV 저장
5. `generate_report.py` → CSV 파싱 → SLA 판정 → HTML 생성

## Dependency Direction
```
report/ → locust/ (결과 CSV)
report/ → monitor/ (메트릭 CSV)
locust/ → server/ (HTTP 요청 대상)
monitor/ → server/ (모니터링 대상 프로세스)
```

## Key Design Decisions
- 모듈 간 통신은 파일(CSV)로만 진행 (느슨한 결합)
- 각 모듈은 독립된 requirements.txt 보유
- Docker Compose로 전체 오케스트레이션
