"""LoadProbe target server.

Simulates a safety-and-health management platform with three endpoints.
The ``?slow=true`` query parameter on ``/api/reports`` injects an artificial
delay (3-6 s) to reproduce bottleneck conditions for Locust testing.
"""

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Query

from server.config import LOG_LEVEL
from server.database import (
    add_indexes,
    drop_indexes,
    explain_slow_queries,
    fetch_reports,
    init_db,
    insert_submission,
)
from server.models import (
    HealthResponse,
    ReportsResponse,
    SubmitRequest,
    SubmitResponse,
)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing database...")
    init_db()
    logger.info("Database ready")
    yield


app = FastAPI(
    title="LoadProbe Target Server",
    description="Safety-and-health management platform simulator for load testing",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Lightweight health check — returns 200 immediately."""
    return HealthResponse(timestamp=datetime.now(timezone.utc))


@app.get("/api/reports", response_model=ReportsResponse)
async def get_reports(
    slow: bool = Query(default=False, description="Enable bottleneck simulation (3-6s delay)"),
    category: str | None = Query(default=None, description="Filter by inspection category"),
    limit: int = Query(default=100, ge=1, le=500, description="Number of reports to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> ReportsResponse:
    """Fetch inspection reports from SQLite.

    When ``slow=true``, an artificial 3-6 second delay is injected before the
    query to simulate a bottleneck condition.  Locust can detect this as an
    SLA violation.
    """
    if slow:
        delay = random.uniform(3.0, 6.0)
        logger.warning("Bottleneck simulation: sleeping %.2fs", delay)
        await asyncio.sleep(delay)

    reports = fetch_reports(category=category, limit=limit, offset=offset)
    return ReportsResponse(count=len(reports), reports=reports)


@app.post("/api/submit", response_model=SubmitResponse, status_code=201)
async def submit_inspection(body: SubmitRequest) -> SubmitResponse:
    """Record a safety inspection submission."""
    row_id = insert_submission(
        inspector_name=body.inspector_name,
        location=body.location,
        category=body.category,
        check_items=body.check_items,
        notes=body.notes,
    )
    return SubmitResponse(
        id=row_id,
        submitted_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Tuning endpoints (used by before/after scripts)
# ---------------------------------------------------------------------------


@app.get("/api/tuning/explain")
async def explain() -> list[dict[str, str]]:
    """Run EXPLAIN QUERY PLAN on slow queries."""
    return explain_slow_queries()


@app.post("/api/tuning/add-indexes")
async def apply_indexes() -> dict[str, str]:
    """Add indexes to fix slow queries (after tuning)."""
    add_indexes()
    return {"status": "indexes_created"}


@app.post("/api/tuning/drop-indexes")
async def remove_indexes() -> dict[str, str]:
    """Drop indexes to restore baseline (before tuning)."""
    drop_indexes()
    return {"status": "indexes_dropped"}
