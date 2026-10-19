from backend.plate_format import combine_vn_two_line, format_vn_plate, normalize_vn_top


def test_format_vn_plate_4_digits():
    assert format_vn_plate("65X17953") == "65-X1 7953"


def test_format_vn_plate_5_digits_with_dot():
    assert format_vn_plate("94E105025") == "94-E1 050.25"


def test_format_vn_plate_preserves_two_line_shape():
    assert format_vn_plate("66B1\n069.99") == "66-B1 069.99"


def test_normalize_vn_top_keeps_two_letter_series():
    assert normalize_vn_top("66FH") == "66FH"


def test_combine_vn_two_line_supports_two_letter_series():
    assert combine_vn_two_line("66FH", "9296") == "66-FH 9296"

