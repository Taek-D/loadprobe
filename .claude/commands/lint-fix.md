# Lint and Auto-fix

프로젝트 전체 린트 검사 후 자동 수정합니다.

## Steps
1. `ruff check . --statistics` - 현재 린트 상태 요약
2. `ruff check . --fix` - 자동 수정 가능한 항목 수정
3. `ruff format .` - 코드 포맷팅
4. 자동 수정 불가한 항목 목록 출력
5. 수동 수정이 필요한 항목에 대해 수정 제안

## Ruff Rules
- E: pycodestyle errors
- F: pyflakes
- I: isort
- UP: pyupgrade
- B: flake8-bugbear
- SIM: flake8-simplify
