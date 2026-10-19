# Scripts Guide

This directory contains operational and development utilities. Keep importable helpers stable because several scripts are covered by tests.

## Production and Runtime Checks

- `production_check.py` — production readiness smoke checks.
- `doctor.py` — general project health summary.
- `cv_doctor.py` — computer-vision/OCR readiness diagnostics.
- `validate_runtime_db.py` — checks the runtime SQLite schema/data state.
- `backup_runtime.py` — creates runtime data backups.
- `restore_runtime.py` — restores a runtime backup.
- `operational_report.py` — daily operational CSV report.

## OCR and Benchmarking

- `benchmark_openai_vision.py` — Vision OCR benchmark helper.
- `compare_ocr_engines.py` — compares OCR engines through `run_alpr()`.
- `run_benchmark_dataset.py` — runs benchmark datasets.
- `benchmark_with_ground_truth.py` — evaluates against ground-truth labels.
- `benchmark_bad_cases.py` — focuses on difficult OCR samples.
- `run_image_dir_ocr.py` — OCR over image directories.
- `quick_ocr_probe.py` / `run_alpr_check.py` — quick local OCR probes.

## Dataset Preparation

- `prepare_ground_truth_dataset.py`
- `generate_benchmark_candidates.py`
- `prefill_ground_truth.py`
- `prefill_bike_back_ctu_ground_truth.py`
- `make_bike_back_ctu_ground_truth_template.py`
- `export_weak_ocr_cases.py`

## API and Demo Utilities

- `smoke_api.py` — HTTP API smoke test.
- `seed_demo_users.py` — creates demo users for local/staging environments.
- `bootstrap.py` — project bootstrap helper.

## Maintenance Rule

Do not place one-off scratch experiments here. Put temporary files in the conversation scratch/artifacts area or under `docs/archive/` if they are historical references.
