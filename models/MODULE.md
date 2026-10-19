# Models Module

## Responsibility

The `models/` module stores local/external computer vision model weights and model documentation.

## Current External Detector Models

```text
models/external/sourudra-model2.pt
models/external/sourudra-model1.pt
models/external/sourudra-another_model.pt
```

## Detector Priority

The app currently prefers:

1. `sourudra-model2.pt`
2. `sourudra-model1.pt`
3. `sourudra-another_model.pt`
4. baseline detector fallback

## Rules

- Do not commit model files without documenting source and purpose.
- Do not replace detector priority without running OCR/CV regression tests.
- Keep OCR separate from detector model responsibility.
- Detector output should feed OCR but not decide business lifecycle directly.
