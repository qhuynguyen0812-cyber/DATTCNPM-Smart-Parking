from backend.production_readiness import check_production_readiness, summarize_findings


def test_production_readiness_demo_mode_has_no_failures():
    findings = check_production_readiness(demo_ok=True)
    summary = summarize_findings(findings)

    assert summary["fail"] == 0
    assert summary["pass"] >= 4


def test_production_readiness_flags_short_jwt_secret(monkeypatch):
    from backend import production_readiness
    monkeypatch.setattr(production_readiness, "API_JWT_SECRET", "short-secret")
    findings = check_production_readiness(demo_ok=False)
    jwt = next(f for f in findings if f.name == "jwt_secret")
    assert jwt.status == "fail"


def test_production_readiness_accepts_strong_jwt_secret(monkeypatch):
    from backend import production_readiness
    monkeypatch.setattr(production_readiness, "API_JWT_SECRET", "x" * 40)
    findings = check_production_readiness(demo_ok=False)
    jwt = next(f for f in findings if f.name == "jwt_secret")
    assert jwt.status == "pass"
