import copy

from opengalois import analyze, verify


def test_verify_detects_tampered_coefficients():
    """Test verify detects tampered coefficients."""
    cert = analyze([1, 0, 0, 0, -1, -1]).certificate
    tampered = copy.deepcopy(cert)
    tampered["input"]["coeffs_qq"][0] = "2"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "input.hash.match" and c.ok is False for c in v.checks)


def test_verify_hash_scope_does_not_include_hash_metadata_fields():
    """Test verify hash scope does not include hash metadata fields."""
    cert = analyze([1, 0, 0, 0, -1, -1]).certificate
    tampered = copy.deepcopy(cert)
    tampered["input"]["hash_alg"] = "sha512"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "input.hash_alg" and c.ok is False for c in v.checks)
    assert any(c.name == "input.hash.match" and c.ok is True for c in v.checks)
