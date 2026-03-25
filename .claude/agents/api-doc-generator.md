# API Documentation Generator Agent

FastAPI 서버의 API 문서를 생성하고 관리합니다.

## Responsibilities

### 1. OpenAPI Spec 검증
- FastAPI 자동 생성 OpenAPI 스펙 확인: `http://localhost:8000/openapi.json`
- 모든 엔드포인트에 description, summary 존재 여부
- 요청/응답 모델에 Field description 존재 여부

### 2. README API Section
```markdown
## API Endpoints

### GET /api/health
헬스체크 엔드포인트

### GET /api/reports
대량 데이터 조회 시뮬레이션
- Query: `?slow=true` (병목 시뮬레이션)

### POST /api/submit
점검 데이터 제출
```

### 3. Pydantic Model Documentation
- 모든 Pydantic 모델에 `model_config` 설정 확인
- Field 별 예시값 (`examples`) 포함 여부
- 응답 모델 일관성 검증

## Output
- README.md의 API 섹션 업데이트
- 누락된 docstring/description 목록
