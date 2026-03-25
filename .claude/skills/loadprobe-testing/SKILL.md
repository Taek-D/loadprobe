---
name: loadprobe-testing
description: LoadProbe 테스트 전략, 패턴, 실행 방법. Use when writing tests, debugging test failures, or checking coverage.
---

# LoadProbe Testing Guide

## Test Framework
- **pytest** + pytest-asyncio + pytest-cov
- **httpx.AsyncClient** for FastAPI integration tests

## Test Structure
```
tests/
├── conftest.py              # 공통 fixtures
├── test_server.py           # FastAPI 엔드포인트 테스트
├── test_database.py         # SQLite 연동 테스트
├── test_sla_engine.py       # SLA 판정 로직 테스트 (가장 중요)
├── test_report_generator.py # 리포트 생성 테스트
├── test_system_monitor.py   # 모니터링 수집 테스트
└── integration/
    └── test_e2e.py          # Docker 기반 E2E 테스트
```

## Test Patterns

### FastAPI Endpoint Test
```python
import pytest
from httpx import AsyncClient, ASGITransport
from server.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
```

### SLA Judgment Test (Critical)
```python
def test_sla_pass():
    result = evaluate_sla(avg_response_ms=2500, cpu_pct=65, mem_pct=80, error_rate=0.5)
    assert result.response_time == "PASS"
    assert result.cpu == "PASS"
    assert result.memory == "PASS"
    assert result.error_rate == "PASS"

def test_sla_fail():
    result = evaluate_sla(avg_response_ms=6000, cpu_pct=85, mem_pct=95, error_rate=7.0)
    assert result.response_time == "FAIL"
    assert result.cpu == "WARNING"
    assert result.memory == "CRITICAL"
    assert result.error_rate == "FAIL"
```

## Running Tests
```bash
# 전체 테스트
pytest -v

# 특정 모듈
pytest tests/test_sla_engine.py -v

# 커버리지 포함
pytest -v --cov=. --cov-report=term-missing

# 비동기 테스트만
pytest -v -m asyncio
```

## Coverage Targets
| Module | Target | Priority |
|--------|--------|----------|
| SLA 판정 엔진 | 100% | Critical |
| server/ | 80% | High |
| report/ | 90% | High |
| monitor/ | 70% | Medium |
| locust/ | 60% | Low |
