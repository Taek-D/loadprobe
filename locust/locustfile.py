"""LoadProbe load test scenarios.

Three scenarios controlled by the ``LOAD_SHAPE`` environment variable:

- ``normal``    : 100 -> 300 -> 500 -> 1,000 VUser stepped ramp-up (default)
- ``spike``     : 0 -> 1,000 VUser in 30 seconds, hold 5 min
- ``sustained`` : 500 VUser held for 10 minutes

When ``LOAD_SHAPE`` is unset or empty, Locust falls back to CLI flags
(``-u``, ``-r``, ``-t``), which is useful for quick ad-hoc tests.

Examples::

    # Use a predefined shape
    LOAD_SHAPE=spike locust -f locustfile.py --headless --host http://server:8000

    # Use CLI flags (no shape)
    locust -f locustfile.py --headless -u 100 -r 50 -t 30s --host http://server:8000
"""

import logging
import os
import random

from locust import HttpUser, LoadTestShape, between, task

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared User behaviour — task weights 7:2:1
# ---------------------------------------------------------------------------

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
    "본관 1층",
    "본관 2층",
    "제1공장 A동",
    "제2공장 B동",
    "물류창고",
]


class LoadProbeUser(HttpUser):
    """Virtual user that exercises the three server endpoints."""

    wait_time = between(1, 3)

    @task(7)
    def health_check(self) -> None:
        self.client.get("/api/health")

    @task(2)
    def get_reports(self) -> None:
        params: dict[str, str | int] = {"limit": random.randint(10, 100)}
        if random.random() < 0.3:
            params["category"] = random.choice(_CATEGORIES)
        self.client.get("/api/reports", params=params, name="/api/reports")

    @task(1)
    def submit_inspection(self) -> None:
        payload = {
            "inspector_name": f"inspector_{random.randint(1, 100)}",
            "location": random.choice(_LOCATIONS),
            "category": random.choice(_CATEGORIES),
            "check_items": random.sample(
                ["접지 상태", "절연 저항", "누전 차단기", "소화기 비치", "비상구 확보"],
                k=random.randint(1, 3),
            ),
            "notes": "",
        }
        self.client.post(
            "/api/submit",
            json=payload,
            name="/api/submit",
        )


# ---------------------------------------------------------------------------
# Load shape definitions
# ---------------------------------------------------------------------------

_SHAPES: dict[str, list[dict[str, int | float]]] = {
    "normal": [
        {"duration": 120, "users": 100, "spawn_rate": 50},
        {"duration": 240, "users": 300, "spawn_rate": 50},
        {"duration": 360, "users": 500, "spawn_rate": 50},
        {"duration": 480, "users": 1000, "spawn_rate": 50},
    ],
    "spike": [
        {"duration": 30, "users": 1000, "spawn_rate": 200},
        {"duration": 330, "users": 1000, "spawn_rate": 200},
    ],
    "sustained": [
        {"duration": 600, "users": 500, "spawn_rate": 50},
    ],
}

_SHAPE_NAME = os.getenv("LOAD_SHAPE", "").lower().strip()


# Only register the shape class when a valid LOAD_SHAPE is set.
# When empty/unset, Locust falls back to CLI flags (-u, -r, -t).
if _SHAPE_NAME in _SHAPES:

    class LoadProbeShape(LoadTestShape):
        """Single shape class that dispatches to the selected stage config."""

        stages = _SHAPES[_SHAPE_NAME]

        def tick(self) -> tuple[int, float] | None:
            run_time = self.get_run_time()
            for stage in self.stages:
                if run_time < stage["duration"]:
                    return (int(stage["users"]), float(stage["spawn_rate"]))
            return None
