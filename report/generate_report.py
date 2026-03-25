"""LoadProbe HTML report generator.

Parses Locust CSV output and system_metrics.csv, runs SLA judgments,
and renders a self-contained HTML report with Chart.js charts.

Usage::

    python report/generate_report.py \\
        --input  results/locust_stats.csv \\
        --output results/report.html \\
        --label  before
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from report.sla_engine import evaluate_all, overall_verdict

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# CSV parsers
# ---------------------------------------------------------------------------

def parse_locust_stats(path: Path) -> dict:
    """Parse locust_stats.csv (summary row = 'Aggregated')."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] == "Aggregated":
                total_reqs = int(row["Request Count"])
                total_fails = int(row["Failure Count"])
                return {
                    "total_requests": total_reqs,
                    "total_failures": total_fails,
                    "error_rate": (total_fails / total_reqs * 100) if total_reqs else 0,
                    "avg_response_ms": float(row["Average Response Time"]),
                    "min_response_ms": float(row["Min Response Time"]),
                    "max_response_ms": float(row["Max Response Time"]),
                    "median_response_ms": float(row["Median Response Time"]),
                    "rps": float(row["Requests/s"]),
                    "p50": float(row["50%"]),
                    "p66": float(row["66%"]),
                    "p75": float(row["75%"]),
                    "p80": float(row["80%"]),
                    "p90": float(row["90%"]),
                    "p95": float(row["95%"]),
                    "p98": float(row["98%"]),
                    "p99": float(row["99%"]),
                }
    logger.error("No 'Aggregated' row found in %s", path)
    sys.exit(1)


def parse_locust_history(path: Path) -> dict:
    """Parse locust_stats_history.csv for time-series charts."""
    timestamps: list[str] = []
    user_counts: list[int] = []
    rps_values: list[float] = []
    p50_values: list[float] = []
    p90_values: list[float] = []
    p99_values: list[float] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] != "Aggregated":
                continue
            ts = int(row["Timestamp"])
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            timestamps.append(dt.strftime("%H:%M:%S"))
            user_counts.append(int(row["User Count"]))
            rps_values.append(round(float(row["Requests/s"]), 1))

            def _safe_pct(val: str) -> float:
                return 0.0 if val == "N/A" else float(val)

            p50_values.append(_safe_pct(row["50%"]))
            p90_values.append(_safe_pct(row["90%"]))
            p99_values.append(_safe_pct(row["99%"]))

    return {
        "timestamps": timestamps,
        "user_counts": user_counts,
        "rps": rps_values,
        "p50": p50_values,
        "p90": p90_values,
        "p99": p99_values,
    }


def parse_system_metrics(path: Path) -> dict:
    """Parse system_metrics.csv from monitor."""
    timestamps: list[str] = []
    cpu_values: list[float] = []
    mem_values: list[float] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_raw = row["timestamp"]
            try:
                dt = datetime.fromisoformat(ts_raw)
                timestamps.append(dt.strftime("%H:%M:%S"))
            except ValueError:
                timestamps.append(ts_raw)
            cpu_values.append(float(row["cpu_percent"]))
            mem_values.append(float(row["memory_percent"]))

    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
    max_cpu = max(cpu_values) if cpu_values else 0.0
    avg_mem = sum(mem_values) / len(mem_values) if mem_values else 0.0
    max_mem = max(mem_values) if mem_values else 0.0

    return {
        "timestamps": timestamps,
        "cpu": cpu_values,
        "memory": mem_values,
        "avg_cpu": avg_cpu,
        "max_cpu": max_cpu,
        "avg_mem": avg_mem,
        "max_mem": max_mem,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate(
    stats_path: Path,
    output_path: Path,
    label: str,
    results_dir: Path | None = None,
) -> None:
    """Generate an HTML report from Locust + monitor CSVs."""
    if results_dir is None:
        results_dir = stats_path.parent

    history_path = results_dir / stats_path.name.replace("_stats.csv", "_stats_history.csv")
    metrics_path = results_dir / "system_metrics.csv"

    # Parse sources
    stats = parse_locust_stats(stats_path)
    history = parse_locust_history(history_path) if history_path.exists() else None
    system = parse_system_metrics(metrics_path) if metrics_path.exists() else None

    # SLA judgment
    avg_cpu = system["avg_cpu"] if system else 0.0
    avg_mem = system["avg_mem"] if system else 0.0
    sla_results = evaluate_all(
        avg_response_ms=stats["avg_response_ms"],
        cpu_percent=avg_cpu,
        memory_percent=avg_mem,
        error_rate_percent=stats["error_rate"],
    )
    verdict = overall_verdict(sla_results)

    # Render
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html")
    html = template.render(
        label=label,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        stats=stats,
        sla_results=sla_results,
        overall_verdict=verdict,
        history_json=Markup(json.dumps(history)) if history else Markup("null"),
        system_json=Markup(json.dumps(system)) if system else Markup("null"),
        system=system,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    logger.info("Report written to %s (%d bytes)", output_path, len(html))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LoadProbe HTML report")
    parser.add_argument(
        "--input", required=True, type=Path,
        help="Path to locust_stats.csv",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output HTML path (default: results/report.html or results/report_{label}.html)",
    )
    parser.add_argument(
        "--label", default="",
        help="Report label (e.g. 'before', 'after') — appended to filename",
    )
    args = parser.parse_args()

    if args.output is None:
        suffix = f"_{args.label}" if args.label else ""
        args.output = args.input.parent / f"report{suffix}.html"

    generate(
        stats_path=args.input,
        output_path=args.output,
        label=args.label,
    )


if __name__ == "__main__":
    main()
