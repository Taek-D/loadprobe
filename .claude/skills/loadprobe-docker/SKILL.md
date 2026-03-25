---
name: loadprobe-docker
description: Docker/Docker Compose 환경 구성 규칙. Use when working with Dockerfile, docker-compose.yml, or container configuration.
---

# LoadProbe Docker Module

## Overview
Docker Compose로 전체 서비스를 오케스트레이션. `docker compose up` 한 명령으로 실행 가능.

## Key Files
```
loadprobe/
├── docker-compose.yml      # 서비스 정의
├── server/
│   └── Dockerfile          # FastAPI 서버 이미지
├── locust/
│   └── Dockerfile          # Locust 워커 이미지
└── .dockerignore           # 빌드 제외 파일
```

## Docker Compose Services
```yaml
services:
  server:
    build: ./server
    ports: ["8000:8000"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  locust-master:
    build: ./locust
    ports: ["8089:8089"]
    depends_on:
      server:
        condition: service_healthy
    command: >
      locust -f /app/locustfile.py
      --master --host http://server:8000

  locust-worker:
    build: ./locust
    depends_on: [locust-master]
    command: >
      locust -f /app/locustfile.py
      --worker --master-host locust-master
    deploy:
      replicas: 4
```

## Dockerfile Rules
- Base image: `python:3.11-slim`
- 멀티 스테이지 빌드 사용
- `uv`로 의존성 설치
- non-root 유저로 실행
- `.dockerignore`에 `.venv/`, `__pycache__/`, `.git/` 포함

## Dockerfile Pattern
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
```

## Commands
```bash
# 전체 빌드 및 실행
docker compose up --build -d

# 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f server

# 정리
docker compose down -v

# 워커 스케일링
docker compose up -d --scale locust-worker=8
```

## Environment Variables
```yaml
# docker-compose.yml에서 관리
environment:
  - FASTAPI_HOST=0.0.0.0
  - FASTAPI_PORT=8000
  - DB_PATH=/app/data/loadprobe.db
  - LOG_LEVEL=INFO
```
