# License Plate Recognition Parking App

A Streamlit-based smart parking demo for Vietnamese motorbike license plates, with ALPR/OCR processing, vehicle entry/exit logging, and a compact dashboard UI.

## Features

- Vehicle entry and exit flow
- Vietnamese plate post-processing and formatting
- fast-alpr + EasyOCR based OCR pipeline
- SQLite parking log storage
- Optional external detector models (`.pt`)
- Compact dashboard UI with image preview

## Project Structure

```text
plate-app-final/
├── backend/
│   ├── alpr_service.py
│   ├── config.py
│   ├── db.py
│   ├── parking_service.py
│   ├── plate_format.py
│   └── storage.py
├── frontend/
│   ├── app.py
│   ├── ui.py
│   └── assets/
├── models/
│   └── external/
├── integrations/
│   └── person1/
├── docs/
├── tests/
├── requirements_streamlit.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.11+
- Streamlit
- OpenCV
- EasyOCR
- fast-alpr
- pandas

Install dependencies:

```bash
pip install -r requirements_streamlit.txt
```

## Run

```bash
streamlit run frontend/app.py
```

## Notes

- `frontend/app.py` is the Streamlit entry point.
- `backend/` contains app logic separated from the UI.
- `models/external/` stores optional detector checkpoints.
- `tests/` currently contains lightweight formatter smoke tests.
- `.venv/` is intentionally ignored and not included in source structure.

## Current Status

This project has been cleaned up and reorganized into a clearer frontend/backend structure while preserving the current app flow.
