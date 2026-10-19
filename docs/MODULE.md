# Docs Module

## Responsibility

The `docs/` module contains project requirements, business rules, production reports, hardware instructions, OCR plans, and archived historical references.

## Key Documents

| Document | Purpose |
|---|---|
| `BUSINESS_RULES.md` | Domain rules for ticket lifecycle and roles |
| `ITS_APPLICATION_REQUIREMENTS.md` | Functional requirements |
| `PRODUCTION_AUDIT.md` | Production/security/business audit |
| `HARDWARE_CONFIGURATION.md` | Real device endpoint setup |
| `LOCAL_HARDWARE_DISCOVERY.md` | Safe local hardware discovery notes |
| `OCR_COMPARISON_PLAN.md` | OCR strategy notes |
| `FIELD_BENCHMARK_PROTOCOL.md` | Field benchmark process |

## Archive Policy

Historical references and old mockups should go under:

```text
docs/archive/
```

Do not delete historical files unless the user explicitly requests deletion.

## Rules

- Update docs when architecture, business rules, OCR policy, or production readiness changes.
- Keep secrets out of documentation.
- Use placeholders for credentials.
