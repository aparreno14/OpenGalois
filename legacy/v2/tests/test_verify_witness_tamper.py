import copy
import json
from pathlib import Path
from typing import Any, cast

from opengalois import verify


def _load_fixture(name: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    p = root / "examples" / "certificates" / "v2.0.0" / name
    return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8")))


def test_verify_factorization_witness_tamper_unit_zero():
    """Tamper factorization unit -> must fail."""
    cert = _load_fixture("ok-factorization-x2-1.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    node = tampered["proof"]["root"]["children"][0]
    assert node["kind"] == "factorization.QQ.monic"
    node["witness"]["unit"] = "0"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name in {"lemma.factorization.unit.nonzero", "lemma.factorization"} and c.ok is False for c in v.checks)


def test_verify_factorization_coeff_tamper():
    """Tamper factor coefficients -> product check must fail."""
    cert = _load_fixture("ok-factorization-x2-1.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    # Flip leading coefficient of factor poly.f1 (break monic)
    tampered["objects"]["poly.f1"]["coeffs_qq"][0] = "-1"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name in {"lemma.factorization.factor.monic", "lemma.factorization.soundness"} and c.ok is False for c in v.checks)


def test_verify_factorization_multiplicity_tamper():
    """Tamper multiplicity -> product check must fail."""
    cert = _load_fixture("ok-factorization-x2-1.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    node = tampered["proof"]["root"]["children"][0]
    node["witness"]["factors"][0]["multiplicity"] = 2

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "lemma.factorization.soundness" and c.ok is False for c in v.checks)


def test_verify_factorization_order_insensitive():
    """Reordering factors must still verify (commutativity)."""
    cert = _load_fixture("ok-factorization-x2-1.json")

    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    node = tampered["proof"]["root"]["children"][0]
    factors = node["witness"]["factors"]
    node["witness"]["factors"] = list(reversed(factors))

    v = verify(tampered)
    assert v.verified is True
