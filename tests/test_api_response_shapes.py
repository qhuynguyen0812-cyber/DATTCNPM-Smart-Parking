import pytest

pytestmark = pytest.mark.api


import api.main as api_main


def test_ok_helper_wraps_payload():
    response = api_main.ok({"items": [1, 2], "count": 2}, status_code=201)

    assert response.status_code == 201
    assert b'"ok":true' in response.body
    assert b'"count":2' in response.body


def test_validation_error_handler_shape():
    assert api_main.ValidationError in api_main.app.exception_handlers


def test_require_token_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(api_main, "API_TOKEN", "configured-token")
    try:
        api_main.require_token("wrong-token")
        assert False, "Expected HTTPException"
    except api_main.HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Unauthorized"


def test_require_token_fails_when_not_configured(monkeypatch):
    monkeypatch.setattr(api_main, "API_TOKEN", "")
    try:
        api_main.require_token("")
        assert False, "Expected HTTPException"
    except api_main.HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "API token is not configured"
