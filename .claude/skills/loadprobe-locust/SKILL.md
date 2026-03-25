---
name: loadprobe-locust
description: Locust 부하 테스트 시나리오 작성 규칙. Use when working with locust/, load test scenarios, or VUser configuration.
---

# LoadProbe Locust Module

## Overview
Locust 기반 부하 테스트 시나리오 3종. 1,000 VUser까지 단계별 램프업.

## Key Files
```
locust/
├── locustfile.py          # 시나리오 3종 정의
├── config/
│   ├── normal_load.conf   # 100~1,000 VUser 램프업
│   ├── spike.conf         # 0→1,000 스파이크
│   └── sustained.conf     # 500 VUser x 10분
└── requirements.txt
```

## Scenarios

### 1. Normal Load (단계별 램프업)
- 100 → 300 → 500 → 1,000 VUser
- 각 단계 2분 유지
- Spawn rate: 50 users/sec

### 2. Spike Test
- 0 → 1,000 VUser 급격 증가
- Spawn rate: 200 users/sec
- 5분 유지 후 종료

### 3. Sustained Load
- 500 VUser x 10분 지속
- Spawn rate: 50 users/sec
- 안정성 검증 목적

## Collected Metrics
- 응답시간: p50, p90, p95, p99
- TPS (Transactions Per Second)
- Error rate
- Server CPU/Memory (psutil 연동)

## Locust Task Pattern
```python
class LoadProbeUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_health(self):
        self.client.get("/api/health")

    @task(5)
    def get_reports(self):
        self.client.get("/api/reports")

    @task(2)
    def submit_data(self):
        self.client.post("/api/submit", json={...})
```

## Commands
```bash
# Web UI 모드
locust -f locust/locustfile.py --host http://localhost:8000

# Headless 모드 (CI용)
locust -f locust/locustfile.py --headless \
  -u 1000 -r 50 -t 5m \
  --host http://localhost:8000 \
  --csv report/results/result

# 설정 파일 사용
locust -f locust/locustfile.py --config locust/config/normal_load.conf
```
