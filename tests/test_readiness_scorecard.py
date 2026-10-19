from fastapi.testclient import TestClient

from api.main import app


def test_readiness_and_scorecard_endpoints():
    client = TestClient(app)

    readiness = client.get("/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "ready"
    assert any(check["name"] == "api_parity" for check in readiness.json()["checks"])

    scorecard = client.get("/system/scorecard")
    assert scorecard.status_code == 200
    payload = scorecard.json()
    assert payload["overall_score"] >= 9.7
    assert any(item["criterion"] == "Security" for item in payload["items"])


def test_openapi_contains_response_models():
    client = TestClient(app)
    schema = client.get("/openapi.json").json()

    assert "HealthResponse" in schema["components"]["schemas"]
    assert "ReadinessResponse" in schema["components"]["schemas"]
    assert "ScorecardResponse" in schema["components"]["schemas"]
