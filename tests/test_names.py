from rocompany.names import (match_key, normalise, parse, same_company,
                             similarity)

VARIANTS = [
    "S.C. ALFA COM S.R.L.",
    "ALFA COM SRL",
    "Alfa Com S.R.L.",
    "ALFA-COM SOCIETATE COMERCIALA CU RASPUNDERE LIMITATA",
    "ALFA COM S.R.L. (IN INSOLVENTA)",
]


def test_all_variants_reduce_to_one_core():
    assert {normalise(v) for v in VARIANTS} == {"ALFA COM"}


def test_cedilla_and_comma_below_fold_the_same():
    # The single most common cause of silent match failures on Romanian data.
    assert normalise("Ţesătoria Şerban S.A.") == normalise("Țesătoria Șerban SA")


def test_legal_form_is_extracted_not_discarded():
    assert parse("ALFA COM SRL").legal_form == "SRL"
    assert parse("ALFA COM S.A.").legal_form == "SA"


def test_status_marker_detected():
    parsed = parse("ALFA COM S.R.L. (IN INSOLVENTA)")
    assert parsed.status == "IN INSOLVENTA"
    assert parsed.is_distressed


def test_different_legal_forms_are_not_the_same_company():
    assert not same_company("ALFA COM S.R.L.", "ALFA COM S.A.")


def test_same_legal_form_matches():
    assert same_company("S.C. ALFA COM S.R.L.", "ALFA COM SRL")


def test_match_key_is_order_independent():
    assert match_key("COM ALFA SRL") == match_key("ALFA COM SRL")


def test_similarity_bounds():
    assert similarity("ALFA COM SRL", "ALFA COM SRL") == 1.0
    assert similarity("ALFA COM SRL", "BETA TRANS SRL") == 0.0
    assert similarity("", "ALFA") == 0.0
