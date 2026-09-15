import pytest

from rocompany.cui import InvalidCUI, check_digit, filter_valid, is_valid, parse

# Real, public fiscal codes of Romanian companies, used here only as known
# good checksums. They are published in the national trade register.
KNOWN_VALID = [43825150, 14162177, 5661836, 9689910, 4885207]


@pytest.mark.parametrize("value", KNOWN_VALID)
def test_known_valid(value):
    assert is_valid(value)


@pytest.mark.parametrize("value", [43825151, 14162178, 0, 1, "", "abc", None])
def test_rejects_bad_input(value):
    assert not is_valid(value)


def test_accepts_messy_formatting():
    assert is_valid("RO 4382 5150")
    assert is_valid("CIF: 43825150")
    assert is_valid("43825150.0")          # spreadsheet float
    assert parse(" ro43825150 ").value == 43825150


def test_vat_form():
    assert parse(43825150).vat == "RO43825150"


def test_check_digit_matches_last_digit():
    for value in KNOWN_VALID:
        text = str(value)
        assert check_digit(text[:-1]) == int(text[-1])


def test_length_bounds():
    assert not is_valid("1" * 11)          # too long to be a CUI


def test_parse_raises():
    with pytest.raises(InvalidCUI):
        parse("not a cui")


def test_filter_valid_drops_junk():
    messy = ["43825150", "0722 123 456", "", "14162177", "not a code"]
    assert [c.value for c in filter_valid(messy)] == [43825150, 14162177]


def test_checksum_is_necessary_but_not_sufficient():
    """A short number can satisfy the checksum by coincidence.

    Roughly one in ten arbitrary numbers passes. The Romanian postcode
    010101 is a real example. Local validation is a cheap filter that removes
    most rubbish before you spend a network call, never a proof that the
    company exists. Confirm existence against a register.
    """
    assert is_valid("010101")
