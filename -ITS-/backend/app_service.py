from dataclasses import dataclass
from typing import Any

from backend.alpr_service import run_alpr
from backend.parking_service import vehicle_entry, vehicle_exit
from backend.validators import validate_plate_text, validate_ticket_id


@dataclass(frozen=True)
class ProcessedPlate:
    ocr: dict[str, Any]
    plate_text: str


def process_plate_image(image_path: str, detector_model: str | None = None) -> ProcessedPlate:
    ocr = run_alpr(image_path, detector_model=detector_model)
    plate_text = (ocr.get("text") or "").strip()
    return ProcessedPlate(ocr=ocr, plate_text=plate_text)


def confirm_vehicle_entry(plate_text: str, *, image_path: str | None = None, detected_path: str | None = None, plate_path: str | None = None, ocr_confidence: float | None = None):
    validated_plate = validate_plate_text(plate_text)
    return vehicle_entry(
        validated_plate,
        image_path=image_path,
        detected_path=detected_path,
        plate_path=plate_path,
        ocr_confidence=ocr_confidence,
    )


def confirm_vehicle_exit(ticket_id: str, plate_text: str, *, image_path: str | None = None, detected_path: str | None = None, plate_path: str | None = None, ocr_confidence: float | None = None):
    validated_ticket = validate_ticket_id(ticket_id)
    validated_plate = validate_plate_text(plate_text)
    return vehicle_exit(
        validated_ticket,
        validated_plate,
        image_path=image_path,
        detected_path=detected_path,
        plate_path=plate_path,
        ocr_confidence=ocr_confidence,
    )
