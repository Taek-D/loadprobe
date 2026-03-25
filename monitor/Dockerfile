FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev --group monitor

COPY monitor/ ./monitor/

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /app /app

RUN mkdir -p /app/results && chown -R nobody:nogroup /app/results
USER nobody

ENV PATH="/app/.venv/bin:$PATH"
ENV RESULTS_DIR=/app/results
ENV MONITOR_INTERVAL=1
ENV MONITOR_TARGET=uvicorn

CMD ["python", "monitor/system_monitor.py"]
