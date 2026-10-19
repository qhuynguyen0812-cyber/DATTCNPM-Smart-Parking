"""Persist AI settings and atomically activate an immutable snapshot for this process."""
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit


@dataclass(frozen=True)
class AISettings:
    enabled: bool
    in_auto: bool
    api_key: str = field(repr=False)
    base_url: str
    model: str
    api_mode: str
    timeout: float = 45.0


_runtime: AISettings | None = None


def runtime_ai_settings() -> AISettings | None:
    return _runtime


def _stored_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def save_ai_config(path: Path, *, api_key: str, base_url: str, model: str,
                   api_mode: str, activate: bool = False) -> AISettings:
    global _runtime
    stored = _stored_values(path)
    # A blank password field keeps the stored key; never send it back to the browser.
    key = api_key or stored.get("ITS_OPENAI_API_KEY") or os.getenv("ITS_OPENAI_API_KEY", "")
    if not key or any(ch.isspace() for ch in key) or any(ch in key for ch in "\"'#"):
        raise ValueError("Khóa API trống hoặc có ký tự không hợp lệ")
    if any(ch.isspace() for ch in base_url):
        raise ValueError("Base URL không được chứa khoảng trắng hoặc xuống dòng")
    try:
        url = urlsplit(base_url)
        port = url.port
    except ValueError:
        raise ValueError("Base URL không hợp lệ") from None
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Base URL không hợp lệ; không đặt khóa API trong URL")
    if not re.fullmatch(r"[A-Za-z0-9/_.:-]+", model) or api_mode not in {"responses", "chat"}:
        raise ValueError("Model hoặc loại API không hợp lệ")
    settings = AISettings(True, True, key, base_url.rstrip("/"), model, api_mode)
    values = {"ITS_ENABLE_OPENAI_VISION": "true", "ITS_ENABLE_VISION_IN_AUTO": "true",
              "ITS_OPENAI_API_KEY": key, "ITS_OPENAI_BASE_URL": settings.base_url,
              "ITS_OPENAI_VISION_MODEL": model, "ITS_OPENAI_API_MODE": api_mode,
              "ITS_OPENAI_TIMEOUT_SECONDS": "45"}
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    retained = [line for line in lines if line.split("=", 1)[0].strip() not in values]
    retained.extend(f"{name}={value}" for name, value in values.items())
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".ai-settings-", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write("\n".join(retained) + "\n")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    if activate:
        _runtime = settings
    return settings
