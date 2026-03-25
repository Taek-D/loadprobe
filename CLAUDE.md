# LoadProbe - Development Workflow

## Context7 (Required)
- 라이브러리/프레임워크(FastAPI, Locust, Pydantic, pytest, Docker 등) 사용 시 **반드시 Context7 MCP로 최신 공식 문서를 조회**한 후 구현한다.
- 순서: `resolve-library-id`로 라이브러리 식별 → `query-docs`로 관련 문서 조회 → 조회 결과 기반 구현
- User MCP(`mcp__context7__*`) 우선 사용. 실패 시 `mcp__claude_ai_Context7__*` 폴백.

## Project Overview
Locust 기반 성능 부하 테스트 자동화 도구. FastAPI 타깃 서버에 1,000 VUser 동시 접속 시뮬레이션 후 SLA 자동 판정 및 HTML 리포트 생성.

## Package Manager
- **항상 `uv` 사용** (`pip`, `poetry`, `conda` 사용 금지)
- 의존성 관리: `pyproject.toml` + `uv.lock`
- 의존성 동기화: `uv sync`
- 패키지 추가: `uv add <package>`
- dev 패키지 추가: `uv add --group dev <package>`
- Docker 빌드: `uv sync --locked --no-dev`

## Development Flow
1. 코드 변경 작성
2. 포맷팅: `ruff format .`
3. 린트: `ruff check . --fix`
4. 타입체크: `mypy --strict <module>`
5. 테스트: `pytest -v`
6. Docker 빌드: `docker compose build`

## Project Structure
```
loadprobe/
├── server/                  # FastAPI 타깃 서버
│   ├── main.py              # 앱 엔트리포인트
│   ├── database.py          # SQLite 연동
│   └── requirements.txt
├── locust/                  # 부하 테스트 시나리오
│   ├── locustfile.py        # 시나리오 3종 정의
│   └── config/              # 테스트 설정 파일
├── monitor/                 # 시스템 모니터링
│   └── system_monitor.py    # psutil CPU/메모리 수집
├── report/                  # 결과 분석 및 리포트
│   ├── generate_report.py   # SLA 판정 + HTML 생성
│   ├── templates/           # Jinja2 템플릿
│   └── results/             # 결과 CSV, HTML 리포트
├── tests/                   # 테스트 코드
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Coding Conventions

### Python Style
- Python 3.11+ 사용
- Type hints 필수 (모든 함수 파라미터, 반환값)
- `ruff`로 포맷팅 + 린트 통합
- docstring: Google style
- f-string 사용 (`.format()`, `%` 금지)

### Naming
- 변수/함수: `snake_case`
- 클래스: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`
- private: `_leading_underscore`

### Imports
- 표준 라이브러리 → 서드파티 → 로컬 순서
- `isort` 규칙 (ruff에 포함)
- 와일드카드 import (`from x import *`) 금지

### Error Handling
- 구체적인 예외 타입 사용 (`except Exception` 지양)
- FastAPI: `HTTPException`으로 에러 응답
- 로깅: `logging` 모듈 사용 (`print` 금지)

## SLA Criteria (Core Business Logic)
```
응답시간 < 3,000ms        → PASS
응답시간 3,000~5,000ms    → WARNING
응답시간 > 5,000ms        → FAIL

CPU 사용률 < 70%          → PASS
CPU 사용률 > 70%          → WARNING

메모리 사용률 < 90%        → PASS
메모리 사용률 > 90%        → CRITICAL

에러율 < 1%               → PASS
에러율 1~5%               → WARNING
에러율 > 5%               → FAIL
```

## Testing
- 프레임워크: `pytest`
- 비동기 테스트: `pytest-asyncio`
- FastAPI 테스트: `httpx.AsyncClient`
- 커버리지: `pytest-cov`
- 테스트 파일: `tests/test_<module>.py`

## Docker
- 멀티 스테이지 빌드 사용
- `.dockerignore` 필수 관리
- `docker compose up` 한 명령으로 전체 실행 가능해야 함

## Prohibited
- `any` 타입 사용 금지 (type: ignore 최소화)
- `print()` 대신 `logging` 사용
- 하드코딩된 설정값 → 환경변수 또는 config 파일로 관리
- `requirements.txt`에 버전 미고정 금지 (항상 `==` 사용)
- 테스트 없는 핵심 로직 커밋 금지
