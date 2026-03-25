# Test Specific Module

특정 모듈의 테스트를 실행합니다.

## Usage
`/test-module $ARGUMENTS`

$ARGUMENTS: server | locust | monitor | report | all

## Steps
1. 대상 모듈 확인
2. `pytest tests/test_<module>.py -v --tb=long --cov=<module>` 실행
3. 커버리지 리포트 출력
4. 실패한 테스트 분석 및 수정 제안

## Module Mapping
- `server` → `pytest tests/test_server.py -v --cov=server`
- `locust` → `pytest tests/test_locust.py -v --cov=locust`
- `monitor` → `pytest tests/test_monitor.py -v --cov=monitor`
- `report` → `pytest tests/test_report.py -v --cov=report`
- `all` → `pytest -v --cov=. --cov-report=html`
