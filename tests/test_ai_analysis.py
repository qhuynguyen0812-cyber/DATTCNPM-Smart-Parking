import base64
import io
import json
from types import SimpleNamespace

import pytest
from PIL import Image

from backend import openai_vision_adapter as adapter
from backend import alpr_service, app_service, parking_service, db


def analysis(**updates):
    data = dict(plate_visible=True, plate_count=1, plate_text="66B106999", readable=True,
                layout="two_line", vehicle_type="motorcycle", image_issues=[],
                uncertain_characters=[], notes="Biển số nhìn rõ trên ảnh.")
    data.update(updates)
    return json.dumps(data, ensure_ascii=False)


@pytest.fixture
def configured(monkeypatch, tmp_path):
    monkeypatch.setattr(adapter, "ENABLE_OPENAI_VISION", True)
    monkeypatch.setattr(adapter, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(adapter, "OPENAI_API_MODE", "responses")
    monkeypatch.setattr(adapter, "OPENAI_VISION_MODEL", "cx/gpt-5.5")
    path = tmp_path / "plate.png"
    Image.new("RGBA", (80, 60), "white").save(path)
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(status="completed", output_text=analysis())
    monkeypatch.setattr(adapter, "OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=create)))
    return path, calls


def test_structured_request_and_real_image_encoding(configured):
    path, calls = configured
    result = adapter.run_openai_vision(str(path))
    assert result["text"] == "66-B1 069.99"
    assert result["confidence"] is None
    assert result["review_required"] is True
    assert result["is_usable"] is True
    assert result["ai_analysis"]["layout"] == "two_line"
    request = calls[0]
    assert request["store"] is False
    assert request["text"]["format"]["strict"] is True
    url = request["input"][0]["content"][1]["image_url"]
    with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as image:
        assert image.format == "JPEG"


@pytest.mark.parametrize("plate,expected", [("30F51315", "30F51315"), ("60A99999", "60A99999")])
def test_does_not_invent_motorcycle_series_digit(plate, expected):
    from backend.plate_format import normalize_generic_plate_text
    result = adapter.parse_plate_analysis(analysis(plate_text=plate, vehicle_type="car"))
    assert normalize_generic_plate_text(result["text"]) == expected


def test_uncertain_character_is_not_silently_deleted():
    result = adapter.parse_plate_analysis(analysis(plate_text="66B1069?9", readable=False, uncertain_characters=["Ký tự thứ 8 bị che"]))
    assert result["text"] == ""
    assert "?" in result["raw_text"]
    assert not result["is_usable"]
    assert result["review_required"]


@pytest.mark.parametrize("updates", [
    {"plate_visible": False, "plate_count": 0},
    {"plate_count": 2},
    {"image_issues": ["multiple_plates"]},
])
def test_no_single_target_never_returns_a_selected_plate(updates):
    result = adapter.parse_plate_analysis(analysis(**updates))
    assert result["text"] == ""
    assert not result["is_usable"]


@pytest.mark.parametrize("raw", ["I cannot read this image", '{"plate_text":"66B106999"}', '[]', analysis(plate_count="1"), analysis(readable="true")])
def test_malformed_or_refused_output_is_not_a_plate(raw):
    with pytest.raises(ValueError):
        adapter.parse_plate_analysis(raw)


def test_legacy_output_requires_review_without_fake_confidence():
    result = adapter.parse_plate_analysis("66B106999")
    assert result["ai_status"] == "legacy_response"
    assert result["confidence"] is None
    assert result["review_required"]
    assert not result["is_usable"]


def test_invalid_image_does_not_send_api_request(configured):
    path, calls = configured
    path.write_bytes(b"not an image")
    with pytest.raises(ValueError):
        adapter.run_openai_vision(str(path))
    assert calls == []


def test_provider_error_never_echoes_key_or_url(configured, monkeypatch):
    path, _ = configured
    def fail(**kwargs):
        raise RuntimeError("secret-test-key https://private-provider.invalid/request")
    monkeypatch.setattr(adapter, "OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=fail)))
    with pytest.raises(RuntimeError) as exc:
        adapter.run_openai_vision(str(path))
    assert "secret-test-key" not in str(exc.value)
    assert "private-provider" not in str(exc.value)


def test_incomplete_response_is_rejected(configured, monkeypatch):
    path, _ = configured
    monkeypatch.setattr(adapter, "OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=lambda **kw: SimpleNamespace(status="incomplete", output_text=analysis()))))
    with pytest.raises(RuntimeError):
        adapter.run_openai_vision(str(path))


def test_chat_protocol(configured, monkeypatch):
    path, calls = configured
    monkeypatch.setattr(adapter, "OPENAI_API_MODE", "chat")
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=analysis(), refusal=None))])
    monkeypatch.setattr(adapter, "OpenAI", lambda **kwargs: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    assert adapter.run_openai_vision(str(path))["ai_status"] == "analyzed"
    assert calls[0]["response_format"]["json_schema"]["strict"]


def test_vision_runs_before_local_detector_or_opencv(monkeypatch):
    monkeypatch.setattr(alpr_service, "ENABLE_OPENAI_VISION", True)
    monkeypatch.setattr(alpr_service, "ENABLE_VISION_IN_AUTO", True)
    monkeypatch.setattr(alpr_service, "cv2", None)
    monkeypatch.setattr(alpr_service, "run_openai_vision", lambda path: adapter.parse_plate_analysis(analysis()))
    monkeypatch.setattr(alpr_service, "load_fast_alpr", lambda *a: pytest.fail("Local detector must not run for structured AI"))
    result = alpr_service.run_alpr("plate.png", ocr_engine="auto")
    assert result["ocr_engine"] == "openai-vision"
    assert result["text"] == "66-B1 069.99"


def test_unavailable_ai_keeps_local_fallback_explicit(monkeypatch):
    monkeypatch.setattr(alpr_service, "ENABLE_OPENAI_VISION", True)
    monkeypatch.setattr(alpr_service, "ENABLE_VISION_IN_AUTO", True)
    monkeypatch.setattr(alpr_service, "run_openai_vision", lambda path: (_ for _ in ()).throw(RuntimeError("private")))
    monkeypatch.setattr(alpr_service, "cv2", None)
    result = alpr_service.run_alpr("plate.png")
    assert result["ai_status"] == "unavailable"
    assert result["review_required"]
    assert "private" not in result["ai_error"]


def test_hardcase_cannot_override_ai_abstention(monkeypatch):
    from backend import hardcase_ocr
    monkeypatch.setattr(hardcase_ocr, "run_hardcase_alpr", lambda *args: pytest.fail("Must retain AI abstention"))
    payload = adapter.parse_plate_analysis(analysis(plate_visible=False, plate_count=0, plate_text=""))
    result = app_service.process_plate_image("sample.png", use_hardcase=True, alpr_runner=lambda *args, **kw: payload)
    assert result.plate_text == ""
    assert result.ocr["ai_analysis"]


def test_ai_review_persists_and_blocks_unconfirmed_matching_exit(tmp_path, monkeypatch):
    path = tmp_path / "parking.db"
    db.init_db(path)
    monkeypatch.setattr(parking_service, "DB_PATH", path)
    entry = app_service.confirm_vehicle_entry("66B106999", ocr_engine="openai-vision")
    assert entry["review_required"]
    result = app_service.confirm_vehicle_exit(entry["ticket_id"], "66B106999", ocr_confidence=0.99)
    assert result["status"] == "NEEDS_REVIEW"
    assert "OCR_REVIEW_REQUIRED" in result["review_reason"]


def test_human_confirmed_ai_result_can_complete(tmp_path, monkeypatch):
    path = tmp_path / "parking.db"
    db.init_db(path)
    monkeypatch.setattr(parking_service, "DB_PATH", path)
    entry = app_service.confirm_vehicle_entry("66B106999", ocr_engine="openai-vision", manual_override=True)
    result = app_service.confirm_vehicle_exit(entry["ticket_id"], "66B106999", ocr_engine="openai-vision", manual_override=True)
    assert result["status"] == "COMPLETED"


def test_config_writer_preserves_unrelated_settings(tmp_path):
    from scripts.configure_ai import save_ai_config
    path = tmp_path / ".env"
    path.write_text("ITS_BASE_DIR=runtime\nITS_OPENAI_API_KEY=old\n", encoding="utf-8")
    save_ai_config(path, api_key="new-key", base_url="http://localhost:20128/v1", model="cx/gpt-5.5", api_mode="responses")
    text = path.read_text(encoding="utf-8")
    assert "ITS_BASE_DIR=runtime" in text
    assert text.count("ITS_OPENAI_API_KEY=") == 1
    assert "ITS_ENABLE_OPENAI_VISION=true" in text

def test_real_sdk_serializes_request_to_local_test_server(configured, monkeypatch):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from openai import OpenAI
    path, _ = configured
    received = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            body = json.dumps({"id": "resp-local-test", "object": "response", "created_at": 1,
                "model": "cx/gpt-5.5", "status": "completed", "output": [{"id": "msg-local-test",
                "type": "message", "role": "assistant", "status": "completed",
                "content": [{"type": "output_text", "text": analysis(), "annotations": []}]}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setattr(adapter, "OpenAI", OpenAI)
        monkeypatch.setattr(adapter, "OPENAI_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
        result = adapter.run_openai_vision(str(path))
        assert result["text"] == "66-B1 069.99"
        assert received[0]["model"] == "cx/gpt-5.5"
        assert received[0]["text"]["format"]["type"] == "json_schema"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("endpoint", ["entry", "exit"])
@pytest.mark.parametrize("confirmed", [False, True])
def test_api_carries_ai_analysis_and_operator_confirmation(monkeypatch, endpoint, confirmed):
    import api.main as api_main
    from fastapi.testclient import TestClient
    payload = adapter.parse_plate_analysis(analysis())
    payload["ocr_engine"] = "openai-vision"
    processed = app_service.ProcessedPlate(ocr=payload, plate_text=payload["text"])
    monkeypatch.setattr(api_main, "verify_session_token", lambda token: api_main.AuthUser("ai-test-op", "operator"))
    monkeypatch.setattr(api_main, "save_uploaded_file", lambda *args: "test.png")
    monkeypatch.setattr(api_main, "process_plate_image", lambda *args: processed)
    calls = []
    def confirm(*args, **kwargs):
        calls.append(kwargs)
        return {"success": True, "ticket_id": "T-AI"}
    monkeypatch.setattr(api_main, "confirm_vehicle_" + endpoint, confirm)
    api_main._WRITE_BUCKETS.clear()
    with TestClient(api_main.app) as client:
        response = client.post("/vehicle/" + endpoint, headers={"Authorization": "Bearer ai-test"},
            data={"ticket_id": "T-AI", "ai_review_confirmed": str(confirmed).lower()},
            files={"file": ("plate.png", b"test", "image/png")})
    assert response.status_code in {200, 201}
    assert response.json()["ocr"]["ai_analysis"]["plate_text"] == "66B106999"
    assert response.json()["ocr"]["confidence"] is None
    assert calls[0]["ocr_review_required"] is True
    assert calls[0]["manual_override"] is confirmed


def test_ai_status_does_not_expose_credentials(configured):
    status = adapter.vision_configuration_status()
    assert status["configured"]
    assert not status["connection_verified"]
    assert "test-key" not in json.dumps(status)


def test_ai_status_requires_authentication():
    from api.main import app
    from fastapi.testclient import TestClient
    assert TestClient(app).get("/ai/status").status_code == 401

def test_runtime_settings_are_applied_atomically(tmp_path, monkeypatch):
    from backend import ai_settings
    monkeypatch.setattr(ai_settings, "_runtime", None)
    before = adapter.active_ai_settings()
    path = tmp_path / ".env"
    saved = ai_settings.save_ai_config(path, api_key="new-key", base_url="http://localhost:20128/v1",
                                      model="cx/gpt-5.5", api_mode="chat", activate=True)
    assert adapter.active_ai_settings() is saved
    assert "new-key" not in repr(saved)
    assert alpr_service._vision_enabled(auto=True)
    assert adapter.vision_configuration_status()["api_mode"] == "chat"


def test_blank_key_preserves_stored_key(tmp_path):
    from backend.ai_settings import save_ai_config
    path = tmp_path / ".env"
    path.write_text("ITS_OPENAI_API_KEY=stored-secret\nOTHER_SETTING=preserved\n", encoding="utf-8")
    result = save_ai_config(path, api_key="", base_url="http://localhost:20128/v1", model="cx/gpt-5.5", api_mode="responses")
    assert result.api_key == "stored-secret"
    assert "OTHER_SETTING=preserved" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("url", ["http://localhost:20128/v1\nOTHER=bad", "http://user:password@localhost/v1", "http://localhost:invalid/v1", "http://localhost/v1?key=secret"])
def test_invalid_configuration_does_not_overwrite_existing_file(tmp_path, url):
    from backend.ai_settings import save_ai_config
    path = tmp_path / ".env"
    path.write_text("KEEP=original\n", encoding="utf-8")
    with pytest.raises(ValueError):
        save_ai_config(path, api_key="test", base_url=url, model="cx/gpt-5.5", api_mode="responses")
    assert path.read_text(encoding="utf-8") == "KEEP=original\n"


def test_failed_atomic_save_does_not_activate_or_truncate_config(tmp_path, monkeypatch):
    from backend import ai_settings
    path = tmp_path / ".env"
    path.write_text("KEEP=original\n", encoding="utf-8")
    monkeypatch.setattr(ai_settings, "_runtime", None)
    monkeypatch.setattr(ai_settings.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("disk error")))
    with pytest.raises(OSError):
        ai_settings.save_ai_config(path, api_key="new-key", base_url="http://localhost:20128/v1", model="cx/gpt-5.5", api_mode="chat", activate=True)
    assert ai_settings.runtime_ai_settings() is None
    assert path.read_text(encoding="utf-8") == "KEEP=original\n"
    assert list(tmp_path.glob(".ai-settings-*.tmp")) == []


def test_probe_success_does_not_claim_image_accuracy(configured, monkeypatch):
    seen = []
    client = SimpleNamespace(models=SimpleNamespace(list=lambda: SimpleNamespace(data=[SimpleNamespace(id="cx/gpt-5.5")])), close=lambda: seen.append("closed"))
    monkeypatch.setattr(adapter, "OpenAI", lambda **kwargs: client)
    result = adapter.probe_vision_connection()
    assert result["connected"] and result["model_listed"]
    assert not result["analysis_verified"]
    assert seen == ["closed"]


def test_probe_failure_sanitizes_provider_error(configured, monkeypatch):
    def fail():
        raise RuntimeError("private secret-test-key")
    client = SimpleNamespace(models=SimpleNamespace(list=fail), close=lambda: None)
    monkeypatch.setattr(adapter, "OpenAI", lambda **kwargs: client)
    result = adapter.probe_vision_connection()
    assert not result["connected"]
    assert "private" not in result["message"]
    assert "secret-test-key" not in result["message"]
