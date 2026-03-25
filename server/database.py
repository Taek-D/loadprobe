"""SQLite database layer.

Intentionally starts WITHOUT indexes on the reports table
so that the 'before tuning' state can be benchmarked by Locust.
After measuring the slow baseline, indexes can be added to demonstrate
the performance improvement.
"""

import json
import logging
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Generator

from server.config import DB_PATH, SEED_REPORT_COUNT

logger = logging.getLogger(__name__)

_CATEGORIES = [
    "화학물질 안전점검",
    "전기 설비 점검",
    "소방 시설 점검",
    "보호구 착용 점검",
    "작업환경 측정",
    "안전교육 이수 확인",
    "위험성 평가",
    "MSDS 비치 확인",
]

_LOCATIONS = [
    "본관 1층", "본관 2층", "본관 3층",
    "제1공장 A동", "제1공장 B동",
    "제2공장 A동", "제2공장 B동",
    "물류창고", "화학물질 저장소", "옥외 작업장",
]

_INSPECTORS = [
    "김안전", "이점검", "박관리", "최보건", "정평가",
    "강진단", "조감독", "윤검사", "임측정", "한모니터",
]


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and seed data if empty. No indexes by design."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                inspector TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspector_name TEXT NOT NULL,
                location TEXT NOT NULL,
                category TEXT NOT NULL,
                check_items TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                submitted_at TEXT NOT NULL
            )
        """)

        row = conn.execute("SELECT COUNT(*) AS cnt FROM reports").fetchone()
        if row["cnt"] == 0:
            _seed_reports(conn, SEED_REPORT_COUNT)
            logger.info("Seeded %d reports into database", SEED_REPORT_COUNT)


def _seed_reports(conn: sqlite3.Connection, count: int) -> None:
    """Insert realistic sample reports for load testing."""
    rng = random.Random(42)
    base_date = datetime(2025, 1, 1)
    rows: list[tuple[str, str, str, str, str, str]] = []

    for i in range(count):
        category = rng.choice(_CATEGORIES)
        location = rng.choice(_LOCATIONS)
        inspector = rng.choice(_INSPECTORS)
        created = base_date + timedelta(
            days=rng.randint(0, 365),
            hours=rng.randint(8, 18),
            minutes=rng.randint(0, 59),
        )
        title = f"{category} - {location} ({created.strftime('%Y-%m')})"
        description = (
            f"{inspector} 담당자가 {location}에서 수행한 {category} 결과입니다. "
            f"점검 항목 {rng.randint(5, 20)}건 중 {rng.randint(0, 3)}건 지적사항 발견."
        )
        rows.append((
            title,
            category,
            location,
            inspector,
            description,
            created.isoformat(),
        ))

    conn.executemany(
        "INSERT INTO reports (title, category, location, inspector, description, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )


def fetch_reports(
    category: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Fetch reports with optional category filter. No index = full table scan."""
    with get_db() as conn:
        if category:
            cursor = conn.execute(
                "SELECT * FROM reports WHERE category = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (category, limit, offset),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM reports ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        return [dict(row) for row in cursor.fetchall()]


def explain_slow_queries() -> list[dict[str, str]]:
    """Run EXPLAIN QUERY PLAN on the main queries to diagnose bottlenecks.

    Returns a list of dicts with ``query`` and ``plan`` keys showing
    that category-filtered and ORDER BY queries hit full table scans
    when no indexes exist.
    """
    queries = [
        (
            "Category filter (WHERE category = ?)",
            "EXPLAIN QUERY PLAN SELECT * FROM reports WHERE category = ? "
            "ORDER BY created_at DESC LIMIT 100",
            ("화학물질 안전점검",),
        ),
        (
            "Order by created_at",
            "EXPLAIN QUERY PLAN SELECT * FROM reports ORDER BY created_at DESC LIMIT 100",
            (),
        ),
    ]
    results: list[dict[str, str]] = []
    with get_db() as conn:
        for label, sql, params in queries:
            rows = conn.execute(sql, params).fetchall()
            plan = " | ".join(dict(r)["detail"] for r in rows)
            results.append({"query": label, "plan": plan})
            logger.info("EXPLAIN [%s]: %s", label, plan)
    return results


def add_indexes() -> None:
    """Add indexes to fix the slow queries identified by explain_slow_queries().

    - ``idx_reports_category`` eliminates full table scan on WHERE category = ?
    - ``idx_reports_created_at`` speeds up ORDER BY created_at DESC

    This is the 'after tuning' step.  Running explain_slow_queries() again
    after this call will show INDEX scans instead of SCAN TABLE.
    """
    with get_db() as conn:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reports_category ON reports (category)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports (created_at DESC)"
        )
        logger.info("Indexes created: idx_reports_category, idx_reports_created_at")


def drop_indexes() -> None:
    """Remove indexes to restore the 'before tuning' baseline state."""
    with get_db() as conn:
        conn.execute("DROP INDEX IF EXISTS idx_reports_category")
        conn.execute("DROP INDEX IF EXISTS idx_reports_created_at")
        logger.info("Indexes dropped: idx_reports_category, idx_reports_created_at")


def insert_submission(
    inspector_name: str,
    location: str,
    category: str,
    check_items: list[str],
    notes: str,
) -> int:
    """Insert a new safety check submission. Returns the new row id."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO submissions (inspector_name, location, category, check_items, notes, submitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                inspector_name,
                location,
                category,
                json.dumps(check_items, ensure_ascii=False),
                notes,
                datetime.now().isoformat(),
            ),
        )
        return cursor.lastrowid or 0
