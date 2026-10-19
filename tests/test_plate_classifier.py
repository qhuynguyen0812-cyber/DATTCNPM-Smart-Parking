from backend.plate_format import classify_plate_type, format_plate_by_type
from backend.ocr_quality import assess_ocr_quality


def test_classify_vn_bike_4():
    assert classify_plate_type('65-X3 5505') == 'vn_bike_4'


def test_classify_vn_bike_4_two_line():
    assert classify_plate_type('65-X3\n5505') == 'vn_bike_4_two_line'


def test_classify_vn_bike_5():
    assert classify_plate_type('66-B1 069.99') == 'vn_bike_5'


def test_classify_vn_bike_5_two_line():
    assert classify_plate_type('66-B1\n069.99') == 'vn_bike_5_two_line'


def test_classify_vn_car_4_one_line():
    assert classify_plate_type('51A1234') == 'vn_car_4_one_line'


def test_classify_vn_car_5_one_line():
    assert classify_plate_type('30AB12345') == 'vn_car_5_one_line'


def test_classify_generic_unknown_when_not_matching_vn_rules():
    assert classify_plate_type('AB123XYZ') == 'generic_unknown'


def test_format_plate_by_type_keeps_generic_unknown_as_normalized_raw():
    assert format_plate_by_type('AB-123.XYZ', 'generic_unknown') == 'AB123XYZ'


def test_assess_ocr_quality_exposes_plate_type():
    assessment = assess_ocr_quality('65-X3 5505', 0.95)
    assert assessment.plate_type == 'vn_bike_4'
    assert assessment.formatted_text == '65-X3 5505'
