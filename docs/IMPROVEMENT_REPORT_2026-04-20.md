# ITS Improvement Report — 2026-04-20

## Summary of repo architecture

### Current structure
- `frontend/app.py`: Streamlit UI orchestration for entry / exit / logs / admin flow
- `frontend/ui.py`: rendering helpers and Streamlit HTML/CSS fragments
- `backend/app_service.py`: app-facing orchestration layer between OCR and parking services
- `backend/parking_service.py`: parking ticket business rules and persistence calls
- `backend/db.py`: SQLite schema, migrations, query helpers
- `backend/alpr_service.py`: primary ALPR pipeline, OCR scoring and VN plate formatting
- `backend/hardcase_ocr.py`: fallback strategy for hard cases via rotations and detector variants
- `backend/plate_format.py`: VN plate normalization / formatting / top-bottom heuristics
- `backend/ocr_quality.py`: OCR quality assessment and usability gating
- `backend/auth.py`: Streamlit login + static bearer parsing + user password hashing
- `api/main.py`: FastAPI surface for health, logs, OCR, vehicle entry/exit
- `scripts/*`: doctor, benchmark, OCR comparison, bootstrap helpers
- `tests/*`: unit and API contract tests

### Effective business flow
1. Image upload enters Streamlit or FastAPI.
2. `process_plate_image()` runs baseline `run_alpr()`.
3. If baseline is weak and no explicit detector override is used, `run_hardcase_alpr()` may try rotations / external detectors.
4. OCR result is shown to operator; operator may manually correct plate text.
5. Confirmation endpoints/services write entry/exit records through `parking_service` into SQLite.

This is still prototype-oriented, but the separation between UI, orchestration, OCR/domain logic, and persistence is real and worth preserving.

---

## Confirmed issues

### 1. Plate validation was too weak — confirmed
**Evidence:** `backend/validators.py` previously only checked blank / max length. That meant manual input like `66B1` could pass validation and rely on lower layers, which only rejected completely empty normalized values.

**Impact:** incomplete / malformed manual plate input could reach business flow and possibly persistence.

### 2. API success/error semantics were wrong — confirmed
**Evidence:** `api/main.py` previously returned:
- `201` from `/vehicle/entry` even when business logic returned `{success: False}`
- `200` from `/vehicle/exit` even when business logic returned `{success: False}`

**Impact:** clients could not trust HTTP status codes and had to inspect nested result bodies manually.

### 3. Hardcase OCR fallback was overly restricted — confirmed
**Evidence:** `backend/hardcase_ocr.py::_candidate_is_safe_upgrade()` required `variant.startswith("rot")`, so `detector:<model>` candidates from external detector fallback were never eligible.

**Impact:** the external detector fallback path existed but was effectively disabled for upgrades.

### 4. Admin user creation flow in Streamlit was broken — confirmed
**Evidence:** `frontend/app.py` called `register_streamlit_user(...)` in admin flow without importing it.

**Impact:** admin create-user action would raise runtime failure when executed.

### 5. Authentication model was inconsistent — confirmed, partially improved
**Evidence:**
- Streamlit used username/password
- logs/tickets endpoints used `x-api-token`
- whoami/entry/exit used bearer token role auth

**Impact:** multiple auth models remain, but role enforcement is now more coherent than before. Full unification would require a bigger auth redesign.

### 6. Benchmark flow was inconsistent — confirmed
**Evidence:** benchmark scripts measured different things and some were hardcoded to machine-specific Windows paths. Production app flow uses `process_plate_image()`, but benchmark scripts used `run_alpr()` directly.

**Impact:** benchmark results did not reliably represent the operator-facing production flow.

### 7. Scripts were not portable — confirmed
**Evidence:** scripts used hardcoded paths such as `C:\Users\huy81\plate_demo_data\uploads`.

**Impact:** scripts failed or silently measured the wrong dataset on other machines.

### 8. Logs endpoint lacked pagination — confirmed
**Evidence:** `/logs` returned the full dataset every time.

**Impact:** unnecessary payload growth and poor API ergonomics.

---

## Fixes implemented

### A. Strengthened manual plate validation
Updated `backend/validators.py`:
- validation now formats the plate and evaluates it with `assess_ocr_quality(..., confidence=1.0)`
- rejects incomplete / malformed manual input like `66B1`
- returns normalized formatted VN plate text for valid input

Result:
- **valid recognized plate** → accepted and normalized
- **uncertain OCR** → stays uncertain in OCR flow, but invalid manual input is rejected
- **invalid manual input** → rejected before business write

### B. Fixed API business-failure semantics
Updated `api/main.py`:
- added machine-friendly error envelope helper
- added business failure mapping:
  - `404` for not found
  - `409` for ticket conflict / already checked out / duplicate active ticket
  - `400` for validation-type business failures
- `/vehicle/entry` now only returns `201` on actual success
- `/vehicle/exit` now only returns `200` on actual success

### C. Enabled meaningful hardcase detector fallback
Updated `backend/hardcase_ocr.py`:
- detector variants (`detector:<model>`) are now eligible as safe upgrades
- rotation variants still require stricter confidence
- detector variants are accepted with a slightly lower but still conservative threshold

This keeps fallback useful without opening the door to reckless false positives.

### D. Fixed admin create-user import/runtime failure
Updated `frontend/app.py`:
- imported `register_streamlit_user`

Admin create-user flow no longer crashes due to missing symbol.

### E. Improved logs API ergonomics
Updated `api/main.py`:
- `/logs` now supports `limit` and `offset`
- response includes `count`, `total`, `limit`, `offset`

### F. Standardized benchmark methodology
Added `scripts/benchmark_common.py` and updated scripts:
- `run_benchmark_dataset.py` now evaluates `process_plate_image()` instead of raw `run_alpr()`
- `benchmark_recent_samples.py` also evaluates `process_plate_image()`
- `compare_ocr_engines.py` remains engine-comparison-oriented and explicitly documents that it measures `run_alpr()`
- upload directory now comes from config (`BENCHMARK_UPLOADS_DIR`) instead of hardcoded machine paths

### G. Improved portability
Benchmark scripts now resolve paths from repo/config instead of hardcoded local machine paths.

### H. Second-pass hardening updates
- `scripts/benchmark_bad_cases.py` was aligned with the shared benchmark helpers and no longer uses machine-specific paths.
- `scripts/benchmark_with_ground_truth.py` now uses config-driven benchmark uploads instead of a hardcoded local Windows path.
- `scripts/generate_benchmark_candidates.py` now uses config-driven uploads and repo-relative output instead of hardcoded local Windows paths.
- API OCR/path exposure is now gated by config via `ITS_API_EXPOSE_INTERNAL_PATHS` and defaults to hidden.
- Read-only API routes (`/logs`, `/tickets/active`, `/ocr`) can now use bearer read access in addition to static token access, improving auth coherence without a full rewrite.
- `/logs` now supports lightweight filtering by `status` and `ticket_id`.
- `tests/test_admin_flow.py` now uses `pytest.importorskip("streamlit")`, making collection robust on clean environments where Streamlit is not installed.

---

## Remaining risks

1. **Auth is still mixed-model**
   - Streamlit auth, API token auth, and bearer auth coexist.
   - This is more coherent than before but still not a single source of truth.

2. **Filesystem paths can still appear in API OCR payloads only when explicitly enabled**
   - Default behavior now hides `annotated_path` / `image_path`.
   - This is safer for internal prototype use, but a proper media abstraction would still be better for a stable external contract.

3. **Streamlit is still not a production multi-user UI**
   - stateful rerun model remains acceptable for demo/internal tooling only.

4. **SQLite remains concurrency-limited**
   - improved correctness, but not enough for serious concurrent workload.

5. **Hardcase fallback is still heuristic-heavy**
   - safer and more usable now, but requires real benchmark validation on hard datasets.

---

## Recommended next steps

### Near-term
1. Unify auth around a single token/session model for API routes.
2. Add explicit API schemas/models for success and error payloads.
3. Hide internal file paths behind media IDs or download endpoints.
4. Extend `/logs` filtering beyond basic `status` and `ticket_id` to date/time ranges and structured sort options.
5. Add tests for admin UI actions beyond import/runtime sanity.

### Medium-term
1. Move to PostgreSQL + Alembic.
2. Make API the clear source of truth for all business operations.
3. Add structured audit events for entry/exit/mismatch/manual override.
4. Benchmark hardcase fallback separately from baseline ALPR.

---

## Final checklist

### Files changed
- `api/main.py`
- `backend/hardcase_ocr.py`
- `backend/validators.py`
- `frontend/app.py`
- `scripts/benchmark_common.py`
- `scripts/benchmark_recent_samples.py`
- `scripts/run_benchmark_dataset.py`
- `scripts/compare_ocr_engines.py`
- `scripts/benchmark_bad_cases.py`
- `scripts/benchmark_with_ground_truth.py`
- `scripts/generate_benchmark_candidates.py`
- `tests/test_validators.py`
- `tests/test_app_service.py`
- `tests/test_api_contract.py`
- `tests/test_hardcase_ocr.py`
- `tests/test_benchmark_common.py`
- `tests/test_benchmark_bad_cases.py`
- `tests/test_benchmark_with_ground_truth.py`
- `tests/test_generate_benchmark_candidates.py`
- `tests/test_admin_flow.py`
- `docs/IMPROVEMENT_REPORT_2026-04-20.md`

### Tests run
- `python -m compileall api backend frontend scripts tests`
- `python -m pytest tests/test_api_contract.py tests/test_api_response_shapes.py tests/test_benchmark_common.py tests/test_benchmark_bad_cases.py tests/test_admin_flow.py -q`
- `python -m pytest tests/test_benchmark_common.py tests/test_benchmark_bad_cases.py tests/test_benchmark_with_ground_truth.py tests/test_generate_benchmark_candidates.py tests/test_admin_flow.py tests/test_api_contract.py tests/test_hardcase_ocr.py tests/test_validators.py -q`
- `python -m pytest tests/test_validators.py tests/test_app_service.py tests/test_api_contract.py tests/test_api_response_shapes.py tests/test_hardcase_ocr.py tests/test_benchmark_common.py tests/test_benchmark_bad_cases.py tests/test_benchmark_with_ground_truth.py tests/test_generate_benchmark_candidates.py tests/test_admin_flow.py tests/test_parking_service.py tests/test_db_schema.py tests/test_alpr_quality.py -q`

### Test result
- **44 passed**
- **0 failed**

### Unresolved items
- Full auth unification not done (intentional scope limit)
- Full frontend behavioral tests not added
- API still uses file-based storage internally; path exposure is now gated but media abstraction is still missing
- Full repo test suite beyond targeted scope was not rerun in this pass
- Auth is still intentionally mixed-model rather than fully unified
- Benchmark methodology is now clearer, but ground-truth quality still dominates result trustworthiness
