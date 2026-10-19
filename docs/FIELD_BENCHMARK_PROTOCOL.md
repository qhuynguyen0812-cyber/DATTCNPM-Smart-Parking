# Field Benchmark Protocol

Use this protocol to turn the current demo benchmark into field-grade ITS evidence.

## Dataset size

- Minimum: 100 real parking images.
- Recommended: 300+ images.

## Conditions

Capture samples across:

- daylight,
- night/low light,
- glare/backlight,
- rain/dirty plate,
- angled plates,
- motion blur,
- partial occlusion.

## CSV format

Use `data/benchmark/field_manifest_template.csv`.

Required columns:

- `image_path`
- `expected_plate`
- `condition`
- `camera_id`
- `captured_at`

Optional columns:

- `predicted_plate`
- `confidence`
- `latency_ms`
- `notes`

## Metrics

- Exact accuracy = exact string matches / total.
- Normalized accuracy = normalized plate matches / total.
- Unreadable rate = empty predictions / total.
- Average latency and P95 latency.

## Suggested thresholds

- Normalized accuracy >= 90% for demo acceptance.
- P95 latency <= 2000 ms for local demo.
- Unreadable rate <= 10% for unconstrained field images.

## Reporting

Run:

```powershell
python scripts/run_benchmark.py
```

Attach generated reports from the report directory to the final submission.
