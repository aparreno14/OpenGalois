# tests/test_verify_normalization.py
from __future__ import annotations

import copy
from fractions import Fraction
from typing import Any

from opengalois import analyze, verify
from opengalois.certificate import compute_input_hash


def _recompute_input_hash(cert: dict[str, Any]) -> None:
    """Recompute input.hash for input_v1 scope (used to isolate non-hash checks)."""
    inp = cert["input"]
    scope = {
        "domain": inp["domain"],
        "variable": inp["variable"],
        "ordering": inp["ordering"],
        "degree": inp["degree"],
        "coeffs_qq": inp["coeffs_qq"],
    }
    inp["hash"] = compute_input_hash(scope)


def test_verify_rejects_noncanonical_input_rational_even_if_hash_matches():
    """Determinism / canonicalization guard.

    - '2/4' is mathematically equal to '1/2' but NOT canonical.

    - Verifier must reject it even if the attacker recomputes input.hash consistently.
    """
    cert = analyze([Fraction(1, 2), 0, 0, 0, -1, -1], explain=False).certificate
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)

    # Replace a canonical "1/2" with a non-canonical equivalent "2/4"
    assert tampered["input"]["coeffs_qq"][0] == "1/2"
    tampered["input"]["coeffs_qq"][0] = "2/4"

    # Attacker recomputes hash to avoid hash mismatch checks
    _recompute_input_hash(tampered)

    v = verify(tampered)
    assert v.verified is False
    # Update the check name to whatever you added (examples):
    assert any(
        c.name in {"input.coeffs_qq.canonical", "input.coeffs_qq.canonical_form"} and c.ok is False
        for c in v.checks
    )


def test_verify_rejects_noncanonical_normalization_rational_strings():
    """Canonicalization must apply to normalization fields too..

    Here we tamper the shift with a non-canonical rational '2/4'.
    """
    cert = analyze([1, 5, 0, 0, 0, 0], explain=False).certificate  # shift=1 for x^5+5x^4
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    assert "normalization" in tampered
    # Canonical "1" -> non-canonical "2/2" or "2/4" depending on your patterns
    tampered["normalization"]["tschirnhaus_shift"] = "2/2"

    v = verify(tampered)
    assert v.verified is False
    assert any(
        c.name in {"normalization.canonical", "normalization.rationals.canonical"} and c.ok is False
        for c in v.checks
    )


def test_verify_detects_normalization_poly_coeffs_mismatch():
    """Soundness: normalization.poly_coeffs must match the polynomial obtained by applying.

    - tschirnhaus_shift

    - monic_scale

    to input polynomial (per your spec).
    """
    cert = analyze([1, 5, 0, 0, 0, 0], explain=False).certificate
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    # Flip one coefficient in the depressed monic polynomial
    pc = tampered["normalization"]["poly_coeffs"]
    assert isinstance(pc, list) and len(pc) == 6
    pc[-1] = "1" if pc[-1] != "1" else "2"

    v = verify(tampered)

    assert v.verified is False
    assert any(
        c.name in {"normalization.canonical", "normalization.witness"} and c.ok is False
        for c in v.checks
    )


def test_verify_rejects_nonmonic_normalization_header_coeffs():
    """Schema already enforces poly_coeffs[0]="1" and poly_coeffs[1]="0".

    But this test ensures verifier also rejects (defense in depth),

    especially if schema validation is bypassed in some integration.
    """
    cert = analyze([1, 5, 0, 0, 0, 0], explain=False).certificate
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    tampered["normalization"]["poly_coeffs"][0] = "2"  # break monic invariant

    v = verify(tampered)
    assert v.verified is False
    assert any(
        c.name in {"normalization.witness", "schema.conformance"} and c.ok is False
        for c in v.checks
    )

def test_analyze_canonicalizes_equivalent_inputs():
    """Test that analyze canonicalizes mathematically equivalent but non-canonical inputs to the same certificate.""" # noQA: E501
    cert = analyze([Fraction(1, 2), 0, 0, 0, -1, -1], explain=False).certificate
    cert2 = analyze([Fraction(2, 4), 0, 0, 0, -1, -1], explain=False).certificate
    
    assert cert["input"]["coeffs_qq"] == cert2["input"]["coeffs_qq"] == ["1/2", "0", "0",
                                                                         "0", "-1", "-1"]
    
    assert cert["input"]["hash"] == cert2["input"]["hash"]
