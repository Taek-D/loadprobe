# Test Runner Agent

테스트를 실행하고 결과를 분석합니다.

## Test Execution Strategy

### Unit Tests
```bash
pytest tests/ -v --tb=long --cov=. --cov-report=term-missing
```

### Integration Tests (Docker required)
```bash
docker compose up -d
pytest tests/integration/ -v --tb=long
docker compose down
```

### Load Test Verification
```bash
# Locust headless 모드로 짧은 테스트 실행
locust -f locust/locustfile.py --headless -u 10 -r 2 -t 30s --host http://localhost:8000
```

## Analysis
1. 실패한 테스트 원인 분석
2. 커버리지가 낮은 모듈 식별
3. 느린 테스트 (>1s) 최적화 제안
4. Flaky test 패턴 탐지

## Target Coverage
- server/: >= 80%
- report/: >= 90% (SLA 판정 로직은 100%)
- monitor/: >= 70%
- locust/: >= 60%
