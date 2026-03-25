FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY server/ ./server/
RUN uv sync --locked --no-dev

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /app /app

RUN useradd -m appuser && mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV DB_PATH=/app/data/loadprobe.db
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8000

EXPOSE 8000

ENTRYPOINT []
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
