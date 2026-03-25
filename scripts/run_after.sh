#!/usr/bin/env bash
# =============================================================================
# LoadProbe — After Tuning (indexes added, slow mode off)
#
# Runs the full test pipeline:
#   1. Start server + monitor
#   2. Add indexes (tuning step)
#   3. Run identical Locust 1,000 VUser test (no ?slow=true)
#   4. Stop services, generate "after" HTML report
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

RESULTS_DIR="$PROJECT_DIR/results"
LABEL="after"
VUSERS="${VUSERS:-1000}"
DURATION="${DURATION:-5m}"
SPAWN_RATE="${SPAWN_RATE:-50}"

echo "============================================="
echo " LoadProbe — AFTER Tuning (Optimized)"
echo "============================================="
echo ""

# --- 1. Back up before results, clean locust/monitor files ---
echo "[1/6] Backing up 'before' results and cleaning..."
if [ -f "$RESULTS_DIR/locust_stats.csv" ]; then
  for f in "$RESULTS_DIR"/locust_*; do
    cp "$f" "${f%.csv}_before_backup.csv" 2>/dev/null || true
  done
fi
rm -f "$RESULTS_DIR"/locust_*.csv "$RESULTS_DIR"/system_metrics.csv
mkdir -p "$RESULTS_DIR"

# --- 2. Build & start server + monitor ---
echo "[2/6] Starting server + monitor..."
docker compose up -d --build server monitor
echo "       Waiting for server to be healthy..."
sleep 8

# --- 3. Add indexes (tuning step) ---
echo "[3/6] Adding indexes (tuning: category + created_at)..."
curl -sf -X POST http://localhost:8000/api/tuning/add-indexes | python -m json.tool
echo ""

echo "       Query plan AFTER tuning:"
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
echo " DONE — After Tuning"
echo " Report: $RESULTS_DIR/report_${LABEL}.html"
echo ""
echo " Compare:"
echo "   results/report_before.html  (baseline)"
echo "   results/report_after.html   (optimized)"
echo "============================================="
