from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.config import ENABLE_HARDCASE_OCR
from backend.parking_service import vehicle_entry, vehicle_exit
from backend.validators import ValidationError, validate_plate_text, validate_ticket_id

ROOT_DIR = Path(__file__).resolve().parents[1]
EXTERNAL_MODELS_DIR = ROOT_DIR / "models" / "external"


@dataclass(frozen=True)
class ProcessedPlate:
    ocr: dict[str, Any]
    plate_text: str


def process_plate_image(
    image_path: str,
    detector_model: str | None = None,
    ocr_engine: str = "auto",
    use_hardcase: bool | None = None,
    alpr_runner=None,
) -> ProcessedPlate:
    if alpr_runner is None:
        from backend.alpr_service import run_alpr

        alpr_runner = run_alpr

    try:
        ocr = alpr_runner(image_path, detector_model=detector_model, ocr_engine=ocr_engine)
    except TypeError:
        ocr = alpr_runner(image_path, detector_model=detector_model)
    plate_text = (ocr.get("text") or "").strip()

    hardcase_enabled = ENABLE_HARDCASE_OCR if use_hardcase is None else use_hardcase
    if hardcase_enabled and not detector_model and not ocr.get("ai_analysis") and not ocr.get("ai_status") and (not ocr.get("is_usable") or len(plate_text) < 7):
        from backend.hardcase_ocr import run_hardcase_alpr

        hardcase = run_hardcase_alpr(image_path, EXTERNAL_MODELS_DIR)
        hardcase_text = (hardcase.get("text") or "").strip()
        if hardcase.get("is_usable") or len(hardcase_text) > len(plate_text):
            ocr = hardcase
            plate_text = hardcase_text

    return ProcessedPlate(ocr=ocr, plate_text=plate_text)


def confirm_vehicle_entry(
    plate_text: str,
    *,
    image_path: str | None = None,
    detected_path: str | None = None,
    plate_path: str | None = None,
    ocr_confidence: float | None = None,
    ocr_engine: str | None = None,
    ocr_text: str | None = None,
    manual_override: bool = False,
    ocr_review_required: bool | None = None,
    actor=None,
    card_id: str | None = None,
    gate_entry: str | None = "GATE_1",
    lane_entry: str | None = "LANE_1",
    zone_assigned: str | None = None,
):
    validated_plate = validate_plate_text(plate_text)
    if ocr_review_required is None:
        ocr_review_required = ocr_engine == "openai-vision"
    return vehicle_entry(
        validated_plate,
        image_path=image_path,
        detected_path=detected_path,
        plate_path=plate_path,
        ocr_confidence=ocr_confidence,
        ocr_engine=ocr_engine,
        ocr_text=ocr_text,
        manual_override=manual_override,
        ocr_review_required=bool(ocr_review_required),
        actor=actor,
        card_id=card_id,
        gate_entry=gate_entry,
        lane_entry=lane_entry,
        zone_assigned=zone_assigned,
    )


def confirm_vehicle_exit(
    ticket_id: str | None = None,
    plate_text: str = "",
    *,
    image_path: str | None = None,
    detected_path: str | None = None,
    plate_path: str | None = None,
    ocr_confidence: float | None = None,
    ocr_engine: str | None = None,
    ocr_text: str | None = None,
    manual_override: bool = False,
    ocr_review_required: bool | None = None,
    actor=None,
    card_id: str | None = None,
    gate_exit: str | None = None,
    lane_exit: str | None = None,
    payment_method: str = "CASH",
    payment_status: str = "PAID",
):
    clean_ticket = (ticket_id or "").strip()
    clean_card = (card_id or "").strip()
    if not clean_ticket and not clean_card:
        raise ValidationError("Ticket ID or Card ID is required")
    validated_ticket = validate_ticket_id(clean_ticket) if clean_ticket else ""
    validated_plate = validate_plate_text(plate_text)
    if ocr_review_required is None:
        ocr_review_required = ocr_engine == "openai-vision"
    return vehicle_exit(
        validated_ticket or None,
        validated_plate,
        image_path=image_path,
        detected_path=detected_path,
        plate_path=plate_path,
        ocr_confidence=ocr_confidence,
        ocr_engine=ocr_engine,
        ocr_text=ocr_text,
        manual_override=manual_override,
        ocr_review_required=bool(ocr_review_required),
        actor=actor,
        card_id=clean_card or None,
        gate_exit=gate_exit,
        lane_exit=lane_exit,
        payment_method=payment_method,
        payment_status=payment_status,
    )
