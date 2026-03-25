"""System monitor for LoadProbe server.

Collects CPU and memory usage of the server (uvicorn) process at 1-second
intervals using psutil.  Requires PID namespace sharing with the server
container (``pid: "service:server"`` in docker-compose.yml) so that
psutil can discover the target process.

Output: ``results/system_metrics.csv``
"""

import csv
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("system_monitor")

RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))
INTERVAL = float(os.getenv("MONITOR_INTERVAL", "1"))
TARGET_CMD = os.getenv("MONITOR_TARGET", "uvicorn")

_running = True


def _shutdown(signum: int, _frame: object) -> None:
    global _running  # noqa: PLW0603
    logger.info("Received signal %d, shutting down gracefully...", signum)
    _running = False


def find_target_process(keyword: str) -> psutil.Process | None:
    """Find the first process whose command line contains *keyword*."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if keyword in cmdline and proc.pid != os.getpid():
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def wait_for_target(keyword: str, timeout: int = 60) -> psutil.Process:
    """Block until the target process appears, or raise after *timeout* seconds."""
    logger.info("Waiting for target process containing '%s'...", keyword)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        proc = find_target_process(keyword)
        if proc is not None:
            logger.info("Found target: PID %d (%s)", proc.pid, proc.name())
            return proc
        time.sleep(1)
    logger.error("Target process '%s' not found within %ds", keyword, timeout)
    sys.exit(1)


def collect(target: psutil.Process, output: Path) -> None:
    """Sample CPU / memory at *INTERVAL* and write rows to *output*."""
    output.parent.mkdir(parents=True, exist_ok=True)

    # Prime cpu_percent (first call always returns 0)
    try:
        target.cpu_percent()
    except psutil.NoSuchProcess:
        logger.error("Target process disappeared before monitoring started")
        sys.exit(1)

    rows_written = 0

    with output.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "cpu_percent", "memory_percent"])
        f.flush()

        logger.info("Monitoring started -> %s (interval=%.1fs)", output, INTERVAL)

        while _running:
            try:
                cpu = target.cpu_percent(interval=INTERVAL)
                mem = target.memory_percent()
            except psutil.NoSuchProcess:
                logger.warning("Target process terminated, stopping monitor")
                break

            ts = datetime.now(timezone.utc).isoformat()
            writer.writerow([ts, f"{cpu:.1f}", f"{mem:.2f}"])
            rows_written += 1

            # Flush every 10 rows to balance I/O and data safety
            if rows_written % 10 == 0:
                f.flush()

    logger.info("Monitoring stopped. %d rows written to %s", rows_written, output)


def main() -> None:
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    target = wait_for_target(TARGET_CMD)
    output = RESULTS_DIR / "system_metrics.csv"
    collect(target, output)


if __name__ == "__main__":
    main()
