---
name: loadprobe-server
description: FastAPI 타깃 서버 개발 규칙. Use when working with server/, endpoints, database, or API logic.
---

# LoadProbe Server Module

## Overview
안전보건관리플랫폼을 모사한 FastAPI 타깃 서버. Locust 부하 테스트의 대상.

## Key Files
```
server/
├── main.py          # FastAPI app, 라우터 등록
├── database.py      # SQLite 연결, 테이블 생성
├── models.py        # Pydantic 요청/응답 모델
├── config.py        # 서버 설정 (환경변수)
└── requirements.txt # 서버 의존성
```

## Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | 헬스체크 (경량) |
| GET | `/api/reports` | 대량 데이터 조회 (DB 쿼리) |
| POST | `/api/submit` | 점검 데이터 제출 (쓰기) |

## Rules
- 모든 엔드포인트는 `async def` 사용
- 응답 모델은 Pydantic `BaseModel`로 정의
- DB 연결은 `database.py`에서 관리 (lifespan 패턴)
- 병목 시뮬레이션: `?slow=true` 쿼리 파라미터로 3~6초 지연
- 에러 응답은 `HTTPException`으로 통일
- SQL은 파라미터 바인딩 필수 (injection 방지)

## Bottleneck Simulation
```python
@app.get("/api/reports")
async def get_reports(slow: bool = False):
    if slow:
        await asyncio.sleep(random.uniform(3.0, 6.0))  # 병목 시뮬레이션
    # ... 실제 쿼리
```

## Commands
```bash
# 개발 서버 실행
uvicorn server.main:app --reload --port 8000

# OpenAPI 문서 확인
# http://localhost:8000/docs
```
