"""SLA judgment engine.

Pure functions that evaluate metrics against the safety-and-health
management platform's SLA criteria.  No side effects — only data in, verdict out.
"""

from dataclasses import dataclass

PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"
CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class SLAResult:
    metric: str
    value: float
    unit: str
    threshold_info: str
    verdict: str


def judge_response_time(avg_ms: float) -> SLAResult:
    if avg_ms < 3000:
        verdict = PASS
    elif avg_ms <= 5000:
        verdict = WARNING
    else:
        verdict = FAIL
    return SLAResult(
        metric="Average Response Time",
        value=round(avg_ms, 1),
        unit="ms",
        threshold_info="<3,000ms PASS / 3,000-5,000ms WARNING / >5,000ms FAIL",
        verdict=verdict,
    )


def judge_cpu(cpu_percent: float) -> SLAResult:
    verdict = PASS if cpu_percent < 70 else WARNING
    return SLAResult(
        metric="CPU Usage",
        value=round(cpu_percent, 1),
        unit="%",
        threshold_info="<70% PASS / >=70% WARNING",
        verdict=verdict,
    )


def judge_memory(mem_percent: float) -> SLAResult:
    verdict = PASS if mem_percent < 90 else CRITICAL
    return SLAResult(
        metric="Memory Usage",
        value=round(mem_percent, 1),
        unit="%",
        threshold_info="<90% PASS / >=90% CRITICAL",
        verdict=verdict,
    )


def judge_error_rate(error_rate_percent: float) -> SLAResult:
    if error_rate_percent < 1:
        verdict = PASS
    elif error_rate_percent <= 5:
        verdict = WARNING
    else:
        verdict = FAIL
    return SLAResult(
        metric="Error Rate",
        value=round(error_rate_percent, 2),
        unit="%",
        threshold_info="<1% PASS / 1-5% WARNING / >5% FAIL",
        verdict=verdict,
    )


def evaluate_all(
    avg_response_ms: float,
    cpu_percent: float,
    memory_percent: float,
    error_rate_percent: float,
) -> list[SLAResult]:
    return [
        judge_response_time(avg_response_ms),
        judge_cpu(cpu_percent),
        judge_memory(memory_percent),
        judge_error_rate(error_rate_percent),
    ]


def overall_verdict(results: list[SLAResult]) -> str:
    verdicts = {r.verdict for r in results}
    if FAIL in verdicts or CRITICAL in verdicts:
        return FAIL
    if WARNING in verdicts:
        return WARNING
    return PASS
