import copy
import json
from pathlib import Path
from typing import Any, cast

from opengalois import verify


def _load_fixture(name: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    p = root / "examples" / "certificates" / "v1.1.0" / name
    return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8")))


def test_verify_discriminant_sqrt_witness_tamper():
    """Test verify discriminant sqrt witness tamper."""
    # A5 implies square discriminant; this fixture should contain sqrt_witness.
    cert = _load_fixture("ok-5T4-A5-modp_113.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    tampered["invariants"]["discriminant"]["sqrt_witness"] = "0"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "invariants.discriminant.witness" and c.ok is False for c in v.checks)


def test_verify_reducible_factorization_coeff_tamper():
    """Reducible: tamper factor coefficients -> product check must fail."""
    cert = _load_fixture("reducible.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    # Flip sign of the leading coefficient of the first factor.
    # This changes the leading coefficient of the product, so verification must fail.
    tampered["checks"]["factorization_QQ"]["factors"][0]["coeffs_qq"][0] = "-1"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "checks.factorization_QQ.product" and c.ok is False for c in v.checks)


def test_verify_reducible_factorization_multiplicity_tamper():
    """Reducible: tamper factor multiplicity -> product check must fail."""
    cert = _load_fixture("reducible.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    # Changing multiplicity changes the reconstructed product polynomial.
    tampered["checks"]["factorization_QQ"]["factors"][0]["multiplicity"] = 2

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "checks.factorization_QQ.product" and c.ok is False for c in v.checks)


def test_verify_reducible_factorization_order_insensitive():
    """Reducible: factor order is not normative; reordering must still verify."""
    cert = _load_fixture("reducible.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)

    factors = tampered["checks"]["factorization_QQ"]["factors"]
    tampered["checks"]["factorization_QQ"]["factors"] = list(reversed(factors))

    # Keep the certificate internally consistent: factor_results are an envelope only.
    # Reordering factors would otherwise make factor_index mapping meaningless.
    tampered["result"]["factor_results"] = []

    v = verify(tampered)
    assert v.verified is True
    assert all(c.ok is True for c in v.checks if c.name == "checks.factorization_QQ.product")


def test_verify_dummit_quadratic_sqrt_discriminant_witness_tamper():
    """Test verify dummit quadratic sqrt discriminant witness tamper."""
    cert = _load_fixture("ok-5T1-C5-dummit_quads_reducible.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    tampered["dummit_quadratics"]["quad1"]["sqrt_discriminant_witness"] = "0"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "dummit_quadratics.witness" and c.ok is False for c in v.checks)
