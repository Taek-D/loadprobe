FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev --group locust

COPY locust/ ./locust/

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /app /app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV LOAD_SHAPE=normal

EXPOSE 8089

ENTRYPOINT []
CMD ["locust", "-f", "locust/locustfile.py"]
