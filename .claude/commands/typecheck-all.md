# Type Check All Modules

모든 Python 모듈에 대해 mypy 타입체크를 실행합니다.

## Steps
1. `mypy server/ --strict` - FastAPI 서버 타입체크
2. `mypy locust/ --strict` - Locust 시나리오 타입체크
3. `mypy monitor/ --strict` - 모니터링 모듈 타입체크
4. `mypy report/ --strict` - 리포트 생성 모듈 타입체크
5. 각 모듈별 에러 요약 출력

## Error Handling
- 에러 발견 시 파일/라인/에러 코드 목록 정리
- 수정 우선순위: server > report > locust > monitor
- `type: ignore` 사용 시 반드시 이유 주석 추가
