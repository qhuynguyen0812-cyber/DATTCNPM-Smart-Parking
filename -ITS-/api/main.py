from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.app_service import confirm_vehicle_entry, confirm_vehicle_exit, process_plate_image
from backend.config import API_TOKEN, APP_TITLE, LOG_LEVEL, SCHEMA_VERSION
from backend.db import fetch_logs, get_active_tickets, init_db
from backend.logging_config import get_logger, setup_logging
from backend.storage import save_uploaded_file
from backend.validators import ValidationError

setup_logging(LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(title=APP_TITLE, version=f"schema-{SCHEMA_VERSION}")


def require_token(x_api_token: str = Header(default="")):
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("API started")


@app.get("/health")
def health():
    return {"status": "ok", "schema_version": SCHEMA_VERSION}


@app.get("/logs", dependencies=[Depends(require_token)])
def logs():
    df = fetch_logs()
    return JSONResponse(content=df.to_dict(orient="records"))


@app.get("/tickets/active", dependencies=[Depends(require_token)])
def active_tickets():
    df = get_active_tickets()
    return JSONResponse(content=df.to_dict(orient="records"))


@app.post("/ocr", dependencies=[Depends(require_token)])
def ocr_image(file: UploadFile):
    try:
        saved_path = save_uploaded_file(file, "api_ocr")
        processed = process_plate_image(saved_path)
        return processed.ocr
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/vehicle/entry", dependencies=[Depends(require_token)])
def vehicle_entry(file: UploadFile, plate_text: str | None = None):
    try:
        saved_path = save_uploaded_file(file, "api_entry")
        processed = process_plate_image(saved_path)
        final_plate = (plate_text or processed.plate_text).strip()
        result = confirm_vehicle_entry(
            final_plate,
            image_path=saved_path,
            detected_path=processed.ocr.get("annotated_path"),
            ocr_confidence=processed.ocr.get("confidence"),
        )
        return {"ocr": processed.ocr, "result": result}
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/vehicle/exit", dependencies=[Depends(require_token)])
def vehicle_exit(ticket_id: str, file: UploadFile, plate_text: str | None = None):
    try:
        saved_path = save_uploaded_file(file, "api_exit")
        processed = process_plate_image(saved_path)
        final_plate = (plate_text or processed.plate_text).strip()
        result = confirm_vehicle_exit(
            ticket_id,
            final_plate,
            image_path=saved_path,
            detected_path=processed.ocr.get("annotated_path"),
            ocr_confidence=processed.ocr.get("confidence"),
        )
        return {"ocr": processed.ocr, "result": result}
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
