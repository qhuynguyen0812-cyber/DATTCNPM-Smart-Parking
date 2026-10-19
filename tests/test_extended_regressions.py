"""Edge cases found while exercising the web app and its AI pipeline."""
import json
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import api.main as api
from backend import openai_vision_adapter as vision
from backend.ai_settings import AISettings
from backend.validators import validate_image_extension


@pytest.fixture
def viewer_headers():
    token = api.create_session_token(api.AuthUser(username="regression-viewer", role="viewer"))
    return {"Authorization": "Bearer " + token}


@pytest.mark.parametrize("query", ["[", "(", ".*", "T+1", "a|b", "\\"])
def test_ticket_search_treats_user_text_as_literal(monkeypatch, viewer_headers, query):
    monkeypatch.setattr(api, "fetch_logs", lambda: pd.DataFrame([
        {"ticket_id": "prefix" + query + "suffix"}, {"ticket_id": "unrelated"}]))
    client = TestClient(api.app, raise_server_exceptions=False)
    response = client.get("/logs", params={"ticket_id": query}, headers=viewer_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["ticket_id"] == "prefix" + query + "suffix"


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 501}, {"offset": -1}, {"limit": "abc"}])
def test_invalid_pagination_is_rejected(viewer_headers, params):
    response = TestClient(api.app).get("/logs", params=params, headers=viewer_headers)
    assert response.status_code == 422


@pytest.mark.parametrize("filename", ["plate.webp", "PLATE.WEBP", "plate.jpeg", "plate.PNG"])
def test_formats_advertised_by_upload_ui_are_supported(filename):
    assert validate_image_extension(filename) == "." + filename.rsplit(".", 1)[1].lower()


@pytest.mark.parametrize("raw", [
    {"annotated_path": "C:/internal/plate.jpg", "text": "59B106999"},
    {"candidates": [{"annotated_path": "C:/internal/plate.jpg", "text": "59B106999"}]},
    {"extra": {"source_path": "C:/internal/original.jpg"}, "text": "59B106999"},
])
def test_ocr_response_removes_paths_at_all_depths(monkeypatch, raw):
    monkeypatch.setattr(api, "API_EXPOSE_INTERNAL_PATHS", False)
    cleaned = api._sanitize_ocr_payload(raw)
    assert "C:/internal/" not in json.dumps(cleaned)
    assert "59B106999" in json.dumps(cleaned)
    assert "C:/internal/" in json.dumps(raw), "Sanitizing must not mutate pipeline data"


def test_ocr_debug_opt_in_preserves_nested_paths(monkeypatch):
    monkeypatch.setattr(api, "API_EXPOSE_INTERNAL_PATHS", True)
    payload = {"candidates": [{"annotated_path": "C:/internal/plate.jpg"}]}
    assert api._sanitize_ocr_payload(payload) == payload


@pytest.mark.parametrize("field,value", [
    ("plate_count", True), ("readable", "yes"), ("plate_visible", 1),
    ("uncertain_characters", "8 or 9"), ("image_issues", [1]), ("notes", ["unknown"]),
])
def test_ai_output_invalid_types_are_rejected(field, value):
    payload = dict(plate_visible=True, plate_count=1, plate_text="59B106999", readable=True,
                   layout="two_line", vehicle_type="motorcycle", uncertain_characters=[],
                   image_issues=[], notes="")
    payload[field] = value
    with pytest.raises(ValueError):
        vision.parse_plate_analysis(json.dumps(payload))


def test_ai_uncertainty_overrides_readable_flag():
    payload = dict(plate_visible=True, plate_count=1, plate_text="59B106999", readable=True,
                   layout="two_line", vehicle_type="motorcycle", uncertain_characters=["last digit 8 or 9"],
                   image_issues=["blur"], notes="")
    result = vision.parse_plate_analysis(json.dumps(payload))
    assert result["text"] == ""
    assert not result["is_usable"]
    assert result["review_required"]


def test_active_ai_snapshot_controls_key_endpoint_model_and_protocol(monkeypatch, tmp_path):
    settings = AISettings(True, True, "runtime-test-key", "http://127.0.0.1:9999/v1", "cx/gpt-6-sol", "chat", 17)
    monkeypatch.setattr(vision, "active_ai_settings", lambda: settings)
    monkeypatch.setattr(vision, "ENABLE_OPENAI_VISION", False)
    monkeypatch.setattr(vision, "OPENAI_API_KEY", "old-test-key")
    captured = {}
    payload = dict(plate_visible=True, plate_count=1, plate_text="59B106999", readable=True,
                   layout="two_line", vehicle_type="motorcycle", uncertain_characters=[], image_issues=[], notes="")
    def create(**kwargs):
        captured["request"] = kwargs
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=json.dumps(payload), refusal=None))])
    def client(**kwargs):
        captured["client"] = kwargs
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)), close=lambda: None)
    monkeypatch.setattr(vision, "OpenAI", client)
    image = tmp_path / "plate.png"
    Image.new("RGB", (100, 80), "white").save(image)
    assert vision.run_openai_vision(str(image))["text"] == "59-B1 069.99"
    assert captured["client"]["api_key"] == "runtime-test-key"
    assert captured["client"]["base_url"] == settings.base_url
    assert captured["request"]["model"] == settings.model
    assert captured["request"]["timeout"] == 17


def test_active_ai_key_is_redacted_from_provider_errors(monkeypatch):
    monkeypatch.setattr(vision, "active_ai_settings", lambda: AISettings(True, True, "runtime-secret-value", "http://127.0.0.1:9999/v1", "cx/gpt-6-sol", "responses"))
    assert "runtime-secret-value" not in vision._redact_secrets("failed runtime-secret-value")


def test_write_limit_resets_and_isolated_users_do_not_share_bucket(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(api.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(api, "_WRITE_BUCKETS", __import__('collections').defaultdict(__import__('collections').deque))
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    user = api.AuthUser(username="load-test-1", role="operator")
    for _ in range(30):
        api.enforce_write_rate_limit(request, user)
    with pytest.raises(api.HTTPException) as error:
        api.enforce_write_rate_limit(request, user)
    assert error.value.status_code == 429
    api.enforce_write_rate_limit(request, api.AuthUser(username="load-test-2", role="operator"))
    now[0] += 61
    api.enforce_write_rate_limit(request, user)
