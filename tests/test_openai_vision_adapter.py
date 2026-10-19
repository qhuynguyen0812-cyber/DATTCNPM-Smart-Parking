from PIL import Image

from backend import openai_vision_adapter as adapter


class FakeResponse:
    output_text = "66B106999"


class FakeResponses:
    def create(self, **kwargs):
        # Responses requires a named structured-output schema; the live router
        # rejects requests missing this field before it can analyze the image.
        assert kwargs["text"]["format"]["name"] == "plate_analysis"
        schema = kwargs["text"]["format"]["schema"]
        assert set(schema["required"]) == set(schema["properties"])
        return FakeResponse()


class FakeClient:
    def __init__(self, api_key, base_url=None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.responses = FakeResponses()

    def close(self):
        pass


def test_openai_vision_adapter_predicts_and_formats(monkeypatch, tmp_path):
    image_path = tmp_path / "plate.jpg"
    Image.new("RGB", (60, 40), "white").save(image_path)

    monkeypatch.setattr(adapter, "ENABLE_OPENAI_VISION", True)
    monkeypatch.setattr(adapter, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(adapter, "OPENAI_VISION_MODEL", "gpt-test")
    monkeypatch.setattr(adapter, "OpenAI", FakeClient)

    result = adapter.run_openai_vision(str(image_path))

    assert result["engine"] == "openai-vision"
    assert result["text"] == "66-B1 069.99"
    assert result["raw_text"] == "66B106999"
