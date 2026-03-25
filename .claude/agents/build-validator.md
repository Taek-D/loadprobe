# Build Validator Agent

Docker Compose 빌드 및 서비스 실행 상태를 검증합니다.

## Responsibilities
1. `docker compose build` 성공 여부 확인
2. 모든 서비스가 healthy 상태인지 검증
3. 포트 충돌, 볼륨 마운트 오류 탐지
4. FastAPI `/api/health` 엔드포인트 응답 확인
5. Locust Web UI 접근 가능 여부 확인

## Validation Checklist
- [ ] docker-compose.yml 문법 유효성 (`docker compose config`)
- [ ] 모든 Dockerfile 빌드 성공
- [ ] 서비스 간 네트워크 연결 확인
- [ ] 환경변수 누락 검사
- [ ] 헬스체크 엔드포인트 응답 확인

## Commands
```bash
docker compose config --quiet        # 설정 검증
docker compose build                 # 빌드
docker compose up -d                 # 실행
docker compose ps                    # 상태 확인
docker compose logs --tail=50        # 최근 로그
```
