"""
Barcode & QR Code Detection Service for UTH Student & Faculty Cards.
Uses high-performance zxing-cpp to read Code 128, QR, EAN from card images.
"""

from pathlib import Path
from typing import Any
from PIL import Image
import zxingcpp


def decode_card_barcode(image_path_or_file: str | Path | Any) -> dict[str, Any]:
    """Decode 1D/2D barcodes (Code 128, QR, DataMatrix) from a card photo."""
    try:
        if isinstance(image_path_or_file, (str, Path)):
            img = Image.open(image_path_or_file)
        else:
            img = Image.open(image_path_or_file)

        results = zxingcpp.read_barcodes(img)
        if results:
            first = results[0]
            return {
                "success": True,
                "card_id": first.text.strip(),
                "format": str(first.format),
                "count": len(results),
            }
    except Exception as exc:
        return {"success": False, "error": str(exc), "card_id": None}

    return {"success": False, "card_id": None, "message": "No barcode detected"}
