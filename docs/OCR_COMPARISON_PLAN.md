# OCR Comparison Plan

## Current status
- EasyOCR: available and integrated
- PaddleOCR: optional, disabled by default via `ITS_ENABLE_PADDLE_OCR=false`

## Goal
Compare OCR engines on the same benchmark dataset and decide whether to keep EasyOCR or switch to PaddleOCR.

## Evaluation criteria
1. Exact plate match rate
2. Usable rate
3. Failure pattern quality
4. Runtime stability
5. Integration complexity

## Proposed workflow
1. Curate `data/benchmark/datasets/benchmark_dataset.csv` with labeled representative images.
2. Run `python scripts/run_benchmark_dataset.py` for current EasyOCR baseline.
3. Run `python scripts/compare_ocr_engines.py` and save report output to `data/benchmark/results/`.
4. Only enable PaddleOCR when dependencies are ready and benchmark environment is stable.
5. Compare exact-match, usable-rate, bad-case behavior, and failure notes.
6. Keep the simpler engine unless the gain is materially clear.

## Recommendation logic
- Keep EasyOCR if PaddleOCR gives no clear gain and adds integration risk.
- Switch to PaddleOCR if it improves medium/hard samples materially.
- Consider dual-engine fallback only if complexity remains acceptable.
