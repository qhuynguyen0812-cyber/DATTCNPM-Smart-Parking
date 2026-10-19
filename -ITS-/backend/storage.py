import base64
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from backend.config import UPLOAD_DIR
from backend.validators import validate_image_extension, validate_upload_size


def _timestamped_path(prefix: str, suffix: str) -> Path:
    safe_prefix = (prefix or "file").strip().replace(" ", "_")[:20]
    return UPLOAD_DIR / f"{safe_prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}{suffix}"


def save_uploaded_file(uploaded_file, prefix: str):
    suffix = validate_image_extension(getattr(uploaded_file, "name", ""))
    buffer = uploaded_file.getbuffer()
    validate_upload_size(len(buffer))
    output_path = _timestamped_path(prefix, suffix)
    output_path.write_bytes(buffer)
    return str(output_path)


def save_annotated_image(cv2_module, image, prefix: str):
    output_path = _timestamped_path(prefix, ".jpg")
    cv2_module.imwrite(str(output_path), image)
    return str(output_path)


def image_to_base64(path: Path):
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")

