---
name: loadprobe-report
description: SLA 판정 엔진 및 HTML 리포트 생성 규칙. Use when working with report/, SLA criteria, charts, or Jinja2 templates.
---

# LoadProbe Report Module

## Overview
Locust 결과 CSV를 파싱하여 SLA 자동 판정 후 HTML 리포트를 생성.

## Key Files
```
report/
├── generate_report.py     # 메인 리포트 생성 스크립트
├── sla_engine.py          # SLA 판정 엔진 (핵심 로직)
├── chart_generator.py     # matplotlib 차트 생성
├── templates/
│   └── report.html        # Jinja2 리포트 템플릿
└── results/               # CSV 입력 + HTML 출력
```

## SLA Criteria (Immutable Business Rules)
```python
SLA_CRITERIA = {
    "response_time": {
        "pass": 3000,      # < 3,000ms → PASS
        "warning": 5000,   # 3,000~5,000ms → WARNING
        # > 5,000ms → FAIL
    },
    "cpu": {
        "pass": 70,        # < 70% → PASS
        # > 70% → WARNING
    },
    "memory": {
        "pass": 90,        # < 90% → PASS
        # > 90% → CRITICAL
    },
    "error_rate": {
        "pass": 1,         # < 1% → PASS
        "warning": 5,      # 1~5% → WARNING
        # > 5% → FAIL
    }
}
```

## Charts (matplotlib)
1. 응답시간 분포 차트 (p50/p90/p99 라인)
2. TPS 추이 차트
3. CPU/메모리 부하 추이
4. 병목 구간 자동 강조

## HTML Report Structure
```html
<!-- Jinja2 Template -->
<h1>LoadProbe Performance Report</h1>
<section id="sla-summary">  <!-- PASS/WARNING/FAIL 컬러 테이블 --></section>
<section id="response-time"> <!-- 응답시간 차트 --></section>
<section id="tps">           <!-- TPS 추이 차트 --></section>
<section id="system-load">   <!-- CPU/메모리 차트 --></section>
<section id="bottleneck">    <!-- 병목 구간 분석 --></section>
```

## Rules
- SLA 기준값은 상수로 관리 (하드코딩 금지 → config)
- 판정 로직은 순수 함수로 작성 (side effect 없음)
- 차트는 PNG로 저장 후 HTML에 base64 인코딩 삽입
- 리포트는 외부 의존성 없이 단일 HTML로 열 수 있어야 함

## Commands
```bash
# 리포트 생성
python report/generate_report.py --input report/results/ --output report/results/report.html
```
