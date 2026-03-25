# Commit, Push, and Create PR

## Steps
1. `ruff format .` 로 포맷팅
2. `ruff check . --fix` 로 린트 수정
3. `pytest -v --tb=short` 로 테스트 실행
4. 테스트 통과 시 변경사항 스테이징
5. 컨벤셔널 커밋 메시지 작성 (feat/fix/refactor/test/docs)
6. 현재 브랜치에 push
7. main 브랜치 대상 PR 생성

## Commit Message Format
```
<type>(<scope>): <description>

<body>
```

Types: feat, fix, refactor, test, docs, chore, perf
Scopes: server, locust, monitor, report, docker, ci

## Rules
- 테스트 실패 시 커밋하지 않음
- PR 본문에 변경 요약과 테스트 계획 포함
- 린트 에러 0개 확인 후 커밋
