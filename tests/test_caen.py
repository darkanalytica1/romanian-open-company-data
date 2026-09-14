import pytest

from rocompany.caen import SECTIONS, normalise, parse, section_of


def test_section_boundaries_are_contiguous_where_they_should_be():
    assert section_of("01") == "A"
    assert section_of("33") == "C"
    assert section_of("35") == "D"
    assert section_of("47") == "G"
    assert section_of("99") == "U"


def test_gaps_in_the_nomenclature_are_respected():
    # Division 34 does not exist in NACE Rev. 2.
    assert section_of("34") is None
    assert normalise("3400") is None


def test_leading_zero_recovered_from_spreadsheet():
    assert normalise("111") == "0111"
    assert parse("111").section == "A"


def test_float_formatting_recovered():
    assert normalise("4941.0") == "4941"


def test_code_parts():
    code = parse(4941)
    assert code.division == 49
    assert code.group == "494"
    assert code.section == "H"
    assert "Transport" in code.section_label


def test_rejects_non_codes():
    for value in ["", "abc", "12345"]:
        assert normalise(value) is None
    with pytest.raises(ValueError):
        parse("nope")


def test_every_section_label_is_populated():
    for letter, (low, high, label) in SECTIONS.items():
        assert low <= high and label
