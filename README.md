# LoadProbe

**안전보건관리플랫폼 성능 검증 기준(동시접속 1,000명, 응답시간 3초 SLA, CPU 70% / 메모리 90% 임계값)을 기반으로 설계된 부하 테스트 자동화 환경**

Locust 기반 1,000 VUser 동시 접속 시뮬레이션 → SLA 자동 판정 → HTML 리포트 생성까지의 End-to-End 파이프라인을 제공합니다. 슬로우 쿼리 탐지 → 인덱스 튜닝 → 재측정의 Before/After 흐름을 코드와 리포트로 증명합니다.

---

## 기술 스택

| 레이어 | 기술 | 역할 |
|--------|------|------|
| 부하 생성 | Locust (Python) | 1,000 VUser 시나리오 3종 |
| 타깃 서버 | FastAPI (Python) | 안전보건 플랫폼 모사 API |
| 모니터링 | psutil | 서버 CPU/메모리 실시간 수집 |
| 리포트 | Jinja2 + Chart.js | SLA 판정 + 시각화 HTML |
| 컨테이너 | Docker Compose | 환경 재현성 보장 |
| 패키지 관리 | uv | 고속 Python 의존성 관리 |

---

## 빠른 시작 (3단계)

### 사전 요구사항

- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) (리포트 생성 시 필요)

### 1단계: 전체 환경 실행

```bash
docker compose up -d --build
```

3개 서비스가 시작됩니다:
- **server** (`:8000`) — FastAPI 타깃 서버
- **locust** (`:8089`) — Locust Web UI
- **monitor** — 서버 CPU/메모리 수집 → `results/system_metrics.csv`

### 2단계: 부하 테스트 실행

**방법 A: Locust Web UI** — http://localhost:8089 에서 VUser 수/시나리오 설정 후 시작

**방법 B: 헤드리스 모드** (CLI)

```bash
# 100 VUser 빠른 테스트 (30초)
docker run --rm --network loadprobe_default \
  -v ./results:/app/results \
  -e LOAD_SHAPE="" \
  loadprobe-locust \
  locust -f locust/locustfile.py \
    --headless -u 100 -r 50 -t 30s \
    --host http://server:8000 \
    --csv /app/results/locust
```

**방법 C: 시나리오별 Shape 사용**

```bash
# 단계별 램프업 (100→300→500→1,000 VUser, 8분)
LOAD_SHAPE=normal docker compose up locust

# 스파이크 (0→1,000 VUser 30초, 5.5분)
LOAD_SHAPE=spike docker compose up locust

# 지속 부하 (500 VUser, 10분)
LOAD_SHAPE=sustained docker compose up locust
```

### 3단계: 리포트 생성

```bash
uv run python -m report.generate_report \
  --input results/locust_stats.csv \
  --label before
```

`results/report_before.html`을 브라우저에서 열면 SLA 판정 결과와 차트를 확인할 수 있습니다.

---

## Before/After 튜닝 흐름

성능 저하 원인 탐지 → 쿼리 튜닝 → 개선 확인까지의 End-to-End 흐름:

```
1. Before (baseline)          2. 원인 분석               3. After (optimized)
┌─────────────────┐          ┌─────────────────┐         ┌─────────────────┐
│ 인덱스 없음      │    →     │ EXPLAIN QUERY   │    →    │ 인덱스 추가      │
│ ?slow=true 포함  │          │ PLAN → SCAN     │         │ INDEX scan      │
│ SLA: FAIL/WARN  │          │ TABLE 확인       │         │ SLA: PASS       │
└─────────────────┘          └─────────────────┘         └─────────────────┘
```

### 자동 실행

```bash
# Before 테스트 (인덱스 없음 → 리포트 생성)
bash scripts/run_before.sh

# After 테스트 (인덱스 추가 → 동일 테스트 → 리포트 생성)
bash scripts/run_after.sh
```

### 수동 실행

```bash
# 1. 서버 시작
docker compose up -d server monitor

# 2. 슬로우 쿼리 분석 (SCAN TABLE 확인)
curl http://localhost:8000/api/tuning/explain

# 3. 인덱스 추가
curl -X POST http://localhost:8000/api/tuning/add-indexes

# 4. 개선 확인 (USING INDEX 확인)
curl http://localhost:8000/api/tuning/explain

# 5. 인덱스 제거 (원복)
curl -X POST http://localhost:8000/api/tuning/drop-indexes
```

---

## SLA 판정 기준

공고의 성능 요구사항을 그대로 판정 기준으로 사용합니다:

| 항목 | PASS | WARNING | FAIL / CRITICAL |
|------|------|---------|-----------------|
| 평균 응답시간 | < 3,000ms | 3,000 ~ 5,000ms | > 5,000ms (FAIL) |
| CPU 사용률 | < 70% | >= 70% | - |
| 메모리 사용률 | < 90% | - | >= 90% (CRITICAL) |
| 에러율 | < 1% | 1 ~ 5% | > 5% (FAIL) |

---

## Before/After 결과 비교

> 아래 표는 실제 테스트 실행 후 수치를 채워 넣는 placeholder입니다.

| 항목 | Before (baseline) | After (optimized) | 개선율 |
|------|-------------------|-------------------|--------|
| 평균 응답시간 | ___ ms | ___ ms | ___% |
| p99 응답시간 | ___ ms | ___ ms | ___% |
| TPS | ___ req/s | ___ req/s | ___% |
| 에러율 | ___% | ___% | - |
| CPU 사용률 (avg) | ___% | ___% | ___% |
| CPU 사용률 (max) | ___% | ___% | ___% |
| 메모리 사용률 | ___% | ___% | - |
| **SLA 판정** | **___** | **___** | - |

---

## Locust 시나리오

| 시나리오 | LOAD_SHAPE | VUser | 동작 | 시간 |
|----------|------------|-------|------|------|
| Normal Load | `normal` | 100→300→500→1,000 | 단계별 램프업 (2분 유지) | 8분 |
| Spike Test | `spike` | 0→1,000 | 30초 안에 급증 후 유지 | 5.5분 |
| Sustained | `sustained` | 500 | 일정 부하 지속 | 10분 |

Task 비율: `/api/health`(7) : `/api/reports`(2) : `/api/submit`(1)

---

## 디렉토리 구조

```
loadprobe/
├── server/                      # FastAPI 타깃 서버
│   ├── main.py                  #   앱 엔트리포인트 + API 엔드포인트
│   ├── database.py              #   SQLite 연동 + 인덱스 관리
│   ├── models.py                #   Pydantic 요청/응답 모델
│   ├── config.py                #   환경변수 기반 설정
│   └── Dockerfile
│
├── locust/                      # Locust 부하 테스트
│   ├── locustfile.py            #   시나리오 3종 + LoadTestShape
│   └── Dockerfile
│
├── monitor/                     # 시스템 모니터링
│   ├── system_monitor.py        #   psutil CPU/메모리 1초 간격 수집
│   └── Dockerfile
│
├── report/                      # SLA 판정 + 리포트 생성
│   ├── sla_engine.py            #   SLA 판정 순수 함수
│   ├── generate_report.py       #   CSV 파싱 → HTML 리포트 생성
│   └── templates/
│       └── report.html          #   Jinja2 + Chart.js 템플릿
│
├── scripts/                     # 자동화 스크립트
│   ├── run_before.sh            #   Before 튜닝 테스트 파이프라인
│   └── run_after.sh             #   After 튜닝 테스트 파이프라인
│
├── results/                     # 테스트 결과 (gitignore)
│   ├── locust_stats.csv         #   Locust 요약 통계
│   ├── locust_stats_history.csv #   Locust 시계열 데이터
│   ├── system_metrics.csv       #   CPU/메모리 수집 데이터
│   └── report_*.html            #   생성된 HTML 리포트
│
├── docker-compose.yml           # 3서비스 오케스트레이션
├── pyproject.toml               # uv 프로젝트 설정
├── uv.lock                      # 의존성 lock 파일
└── README.md
```

---

## API 엔드포인트

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | 헬스체크 (경량, 즉시 응답) |
| GET | `/api/reports` | 점검 보고서 조회 (`?slow=true`로 병목 시뮬레이션) |
| POST | `/api/submit` | 점검 데이터 제출 |
| GET | `/api/tuning/explain` | EXPLAIN QUERY PLAN 실행 |
| POST | `/api/tuning/add-indexes` | 인덱스 추가 (after 튜닝) |
| POST | `/api/tuning/drop-indexes` | 인덱스 제거 (before 복원) |

---

## 라이선스

MIT
