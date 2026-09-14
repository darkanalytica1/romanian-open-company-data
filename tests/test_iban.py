import pytest

from rocompany.iban import is_romanian, is_valid, normalise, parse

VALID_RO = "RO49AAAA1B31007593840000"


def test_valid_romanian_iban():
    assert is_valid(VALID_RO)
    assert is_romanian(VALID_RO)


def test_spacing_is_irrelevant():
    assert is_valid("RO49 AAAA 1B31 0075 9384 0000")
    assert normalise("ro49-aaaa 1b31.0075 9384 0000") == VALID_RO


def test_single_character_typo_is_caught():
    broken = VALID_RO[:-1] + "1"
    assert not is_valid(broken)


def test_wrong_length_for_country():
    assert not is_valid("RO49AAAA1B310075938400")


def test_other_country_still_validates():
    assert is_valid("DE89370400440532013000")
    assert not is_romanian("DE89370400440532013000")


def test_parts():
    parsed = parse(VALID_RO)
    assert parsed.country == "RO"
    assert parsed.bank_code == "AAAA"
    assert parsed.formatted().startswith("RO49 AAAA")


def test_bank_code_only_for_romania():
    with pytest.raises(ValueError):
        parse("DE89370400440532013000").bank_code


def test_rejects_rubbish():
    for value in ["", "RO", "hello world", "1234"]:
        assert not is_valid(value)
