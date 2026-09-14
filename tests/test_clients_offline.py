"""Client tests that never touch the network.

The live services are exercised by ``examples/verify_live.py``, which is not
part of the test suite on purpose: a test suite that depends on a government
endpoint being up is a test suite that fails for reasons you cannot fix.
"""
from xml.etree import ElementTree

from rocompany.eori import build_eori
from rocompany.vies import _clean


def test_build_eori():
    assert build_eori(43825150) == "RO43825150"
    assert build_eori("RO 43825150") == "RO43825150"


def test_vies_placeholder_values_become_none():
    assert _clean("---") is None
    assert _clean("  ") is None
    assert _clean(" WEBHUNT  S.R.L. ") == "WEBHUNT S.R.L."


def test_eori_response_shape_is_parseable():
    sample = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        '<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">'
        "<S:Body><ns0:validateEORIResponse"
        ' xmlns:ns0="http://eori.ws.eos.dds.s/"><return>'
        "<result><eori>RO12345678</eori><status>0</status>"
        "<statusDescr>Valid</statusDescr></result></return>"
        "</ns0:validateEORIResponse></S:Body></S:Envelope>"
    )
    root = ElementTree.fromstring(sample)
    assert root.find(".//status").text == "0"
    assert root.find(".//statusDescr").text == "Valid"
