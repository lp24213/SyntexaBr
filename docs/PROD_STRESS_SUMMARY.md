# Syntexa Production Stress Summary

Timestamp (UTC): 2026-04-20
Target: `https://syntexabr.com.br/v1/public-chat`
Model path: `DEFAULT_LLM=ollama` + `OLLAMA_MODEL=gpt-oss:20b`

## Artifacts created

- `scripts/stress_test_public_chat.py` - reusable stress tool for public chat.
- `docs/STRESS_TEST_REPORT.json` - baseline run (before retries).
- `docs/STRESS_TEST_REPORT_AFTER_RETRY.json` - run after LLM retry patch.
- `docs/STRESS_TEST_REPORT_FINAL.json` - final run after API retry patch.

## Results

1. Baseline:
   - success rate: 80.0% (24/30)
   - avg latency: 3.66s
   - p95 latency: 4.98s

2. After LLM retry in chat engine:
   - success rate: 93.33% (28/30)
   - avg latency: 3.60s
   - p95 latency: 4.74s

3. Final (LLM retry + public endpoint retry):
   - success rate: 96.67% (29/30)
   - avg latency: 3.66s
   - p95 latency: 4.85s

4. Extended run (110 requests, hard prompts):
   - success rate: 95.45% (105/110)
   - avg latency: 3.38s
   - p95 latency: 5.25s
   - report: `docs/STRESS_TEST_REPORT_110.json`

## Multimodal and download checks

- Smoke runner: `scripts/multimodal_smoke_test.py`
- Report: `docs/MULTIMODAL_SMOKE_REPORT.json`
- Summary:
  - Public chat: intermittent 503 observed.
  - OCR/analyze/export endpoints: reachable and responding.
  - Exports validated: PDF, DOCX, XLSX, JSON.
  - Download page validated with both keywords: `Windows` and `Linux`.
  - Some endpoints are authenticated (`401`) by design (`/v1/vision/image/basic`, `/v1/tools/image/analyze`).
  - STT endpoint currently responds as unavailable when transcription backend is not configured.

## Final state

- Public domain routing fixed to API origin.
- Runtime provider confirmed as `ollama`.
- Health reports LLM `up` with provider `ollama`.
- One intermittent 503 remains under stress; retries greatly reduced failure frequency.
