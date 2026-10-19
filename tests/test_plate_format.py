import pytest

from backend.plate_format import (
    classify_plate_type,
    combine_vn_two_line,
    format_vn_plate,
    is_top_only_plate,
    looks_like_vn_bottom,
    normalize_vn_top,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("65X17953", "65-X1 7953"),
        ("94E105025", "94-E1 050.25"),
        ("66B1\n069.99", "66-B1 069.99"),
        ("66B106999", "66-B1 069.99"),
        ("66FH9296", "66-FH 9296"),
        ("30AB12345", "30-AB 123.45"),
        ("66-FH 9296", "66-FH 9296"),
    ],
)
def test_format_vn_plate_cases(raw, expected):
    assert format_vn_plate(raw) == expected


@pytest.mark.parametrize(
    "raw, expected_type",
    [
        ("66B1", "vn_partial_top"),
        ("06999", "vn_partial_bottom"),
        ("66B106999", "vn_bike_5_one_line"),
        ("66FH9296", "vn_car_4"),
        ("30AB12345", "vn_car_5_one_line"),
        ("ABC123XYZ", "generic_unknown"),
    ],
)
def test_classify_plate_type_cases(raw, expected_type):
    assert classify_plate_type(raw) == expected_type


def test_normalize_vn_top_keeps_two_letter_series():
    assert normalize_vn_top("66FH") == "66FH"


def test_combine_vn_two_line_supports_two_letter_series():
    assert combine_vn_two_line("66FH", "9296") == "66-FH 9296"


@pytest.mark.parametrize("raw", ["66B1", "66-B1", "66FH", "30AB"])
def test_top_only_detection(raw):
    assert is_top_only_plate(raw) is True


@pytest.mark.parametrize("raw", ["0699", "06999", "069.99"])
def test_bottom_detection(raw):
    assert looks_like_vn_bottom(raw) is True
