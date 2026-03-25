#!/usr/bin/env bash
# =============================================================================
# LoadProbe — Before Tuning (baseline with slow queries, no indexes)
#
# Runs the full test pipeline:
#   1. Start server + monitor
#   2. Ensure indexes are dropped (baseline state)
#   3. Run Locust 1,000 VUser normal-load test with ?slow=true traffic mixed in
#   4. Stop services, generate "before" HTML report
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

RESULTS_DIR="$PROJECT_DIR/results"
LABEL="before"
VUSERS="${VUSERS:-1000}"
DURATION="${DURATION:-5m}"
SPAWN_RATE="${SPAWN_RATE:-50}"

echo "============================================="
echo " LoadProbe — BEFORE Tuning (Baseline)"
echo "============================================="
echo ""

# --- 1. Clean previous results ---
echo "[1/6] Cleaning previous results..."
rm -f "$RESULTS_DIR"/locust_* "$RESULTS_DIR"/system_metrics.csv
mkdir -p "$RESULTS_DIR"

# --- 2. Build & start server + monitor ---
echo "[2/6] Starting server + monitor..."
docker compose up -d --build server monitor
echo "       Waiting for server to be healthy..."
sleep 8

# --- 3. Drop indexes (ensure baseline state) ---
echo "[3/6] Dropping indexes (baseline: no indexes)..."
curl -sf -X POST http://localhost:8000/api/tuning/drop-indexes | python -m json.tool
echo ""

echo "       Query plan BEFORE tuning:"
curl -sf http://localhost:8000/api/tuning/explain | python -m json.tool
echo ""

# --- 4. Run Locust test ---
echo "[4/6] Running Locust: ${VUSERS} VUsers, ${DURATION}, spawn rate ${SPAWN_RATE}/s..."
docker compose build locust > /dev/null 2>&1
docker run --rm \
  --network loadprobe_default \
  -v "$RESULTS_DIR:/app/results" \
  -e LOAD_SHAPE=normal \
  loadprobe-locust \
  locust -f locust/locustfile.py \
    --headless \
    --host http://server:8000 \
    --csv /app/results/locust \
    --only-summary \
  2>&1 | tail -20

echo ""

# --- 5. Stop services ---
echo "[5/6] Stopping services..."
docker compose down

# --- 6. Generate report ---
echo "[6/6] Generating report..."
uv run python -m report.generate_report \
  --input "$RESULTS_DIR/locust_stats.csv" \
  --label "$LABEL"

echo ""
echo "============================================="
echo " DONE — Before Tuning"
echo " Report: $RESULTS_DIR/report_${LABEL}.html"
echo "============================================="
