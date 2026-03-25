# Build All (Docker Compose)

Docker Compose로 전체 서비스를 빌드하고 실행합니다.

## Steps
1. `docker compose build --no-cache` - 전체 이미지 빌드
2. `docker compose up -d` - 백그라운드 실행
3. `docker compose ps` - 서비스 상태 확인
4. 각 서비스 헬스체크:
   - FastAPI 서버: `curl http://localhost:8000/api/health`
   - Locust Web UI: `curl http://localhost:8089`
5. 문제 발견 시 `docker compose logs <service>` 로 로그 확인

## Cleanup
- `docker compose down` - 서비스 중지
- `docker compose down -v` - 볼륨 포함 정리
