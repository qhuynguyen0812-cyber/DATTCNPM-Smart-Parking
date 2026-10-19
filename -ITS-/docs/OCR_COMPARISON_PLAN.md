# OCR Comparison Plan

## Current status
- EasyOCR: available and integrated
- PaddleOCR: not installed yet

## Goal
Compare OCR engines on the same benchmark dataset and decide whether to keep EasyOCR or switch to PaddleOCR.

## Evaluation criteria
1. Exact plate match rate
2. Usable rate
3. Failure pattern quality
4. Runtime stability
5. Integration complexity

## Proposed workflow
1. Fill `benchmark_candidates.csv` into a curated labeled dataset (20 to 50 images).
2. Run current EasyOCR benchmark and save results.
3. Install PaddleOCR in a controlled branch or dependency update.
4. Implement a `PaddleOCRVNOCR` adapter without breaking current EasyOCR flow.
5. Run the same benchmark dataset with PaddleOCR.
6. Compare exact-match, usable-rate, and bad-case behavior.

## Recommendation logic
- Keep EasyOCR if PaddleOCR gives no clear gain and adds integration risk.
- Switch to PaddleOCR if it improves medium/hard samples materially.
- Consider dual-engine fallback only if complexity remains acceptable.
