from backend.ocr_analysis import analyze_ocr_rows


def test_ocr_analysis_reports_character_accuracy_and_confusions():
    analysis = analyze_ocr_rows([
        {"expected_plate": "66-B1 123.45", "predicted_plate": "66-B1 123.45", "confidence": 0.9},
        {"expected_plate": "59-C2 999.99", "predicted_plate": "59-C2 999.9S", "confidence": 0.6},
        {"expected_plate": "51-A1 000.01", "predicted_plate": "", "confidence": 0.0},
    ])

    assert analysis.total == 3
    assert analysis.exact_accuracy < 1.0
    assert analysis.character_accuracy > 0.0
    assert analysis.low_confidence_count == 2
    assert analysis.confusion_pairs
