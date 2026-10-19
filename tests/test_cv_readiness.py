from backend.cv_readiness import build_cv_readiness, list_external_models


def test_cv_readiness_reports_models_and_checks():
    payload = build_cv_readiness()

    assert "checks" in payload
    assert "models" in payload
    assert payload["summary"]["fail"] == 0
    assert len(list_external_models()) >= 1
