from __future__ import annotations

import copy
from fractions import Fraction
from typing import Any

from tests_helpers import (
    assert_schema_valid,
    lemma_factorization,
    load_schema_validator,
    make_cert,
    poly_obj,
)

from opengalois import verify


def test_factorization_repeated_linear_multiplicity_ok_and_tamper():
    """Factorization lemma must accept correct multiplicity and reject tampered multiplicity."""
    v = load_schema_validator()

    # (x - 1)^3 = x^3 - 3x^2 + 3x - 1
    f = [Fraction(1), Fraction(-3), Fraction(3), Fraction(-1)]
    factor = [Fraction(1), Fraction(-1)]  # x - 1 (monic)

    objects: dict[str, Any] = {"poly.f1": poly_obj(factor)}

    cert = make_cert(
        coeffs=f,
        objects=objects,
        children=[lemma_factorization("$input", unit=Fraction(1), factors=[("poly.f1", 3)], outputs=["poly.f1"])],
    )
    assert_schema_valid(v, cert)
    assert verify(cert).verified is True

    tampered = copy.deepcopy(cert)
    tampered["proof"]["root"]["children"][0]["witness"]["factors"][0]["multiplicity"] = 2
    assert_schema_valid(v, tampered)
    out = verify(tampered)
    assert out.verified is False
    assert any(c.name == "lemma.factorization.soundness" and c.ok is False for c in out.checks)


def test_factorization_repeated_quadratic_ok_and_tamper_unit():
    """Repeated quadratic factors must verify; tampering unit must fail."""
    v = load_schema_validator()

    # (x^2 + 1)^2 = x^4 + 2x^2 + 1
    f = [Fraction(1), Fraction(0), Fraction(2), Fraction(0), Fraction(1)]
    q = [Fraction(1), Fraction(0), Fraction(1)]  # x^2 + 1 (monic)

    objects: dict[str, Any] = {"poly.q": poly_obj(q)}
    cert = make_cert(
        coeffs=f,
        objects=objects,
        children=[lemma_factorization("$input", unit=Fraction(1), factors=[("poly.q", 2)], outputs=["poly.q"])],
    )
    assert_schema_valid(v, cert)
    assert verify(cert).verified is True

    tampered = copy.deepcopy(cert)
    tampered["proof"]["root"]["children"][0]["witness"]["unit"] = "2"
    assert_schema_valid(v, tampered)
    out = verify(tampered)
    assert out.verified is False
    assert any(c.name == "lemma.factorization.soundness" and c.ok is False for c in out.checks)


def test_factorization_rational_unit_ok():
    """Factorization lemma must support non-trivial rational units."""
    v = load_schema_validator()

    # (1/2)(x-1)(x+1) = 1/2 x^2 - 1/2
    f = [Fraction(1, 2), Fraction(0), Fraction(-1, 2)]
    f1 = [Fraction(1), Fraction(-1)]
    f2 = [Fraction(1), Fraction(1)]

    objects: dict[str, Any] = {"poly.f1": poly_obj(f1), "poly.f2": poly_obj(f2)}
    cert = make_cert(
        coeffs=f,
        objects=objects,
        children=[
            lemma_factorization(
                "$input",
                unit=Fraction(1, 2),
                factors=[("poly.f1", 1), ("poly.f2", 1)],
                outputs=["poly.f1", "poly.f2"],
            )
        ],
    )
    assert_schema_valid(v, cert)
    assert verify(cert).verified is True


def test_factorization_rejects_nonmonic_factor():
    """Factor objects must be monic; otherwise verification must fail."""
    v = load_schema_validator()

    f = [Fraction(1), Fraction(0), Fraction(-1)]  # x^2 - 1
    bad_factor = [Fraction(2), Fraction(-2)]  # 2x - 2 (NOT monic)

    objects: dict[str, Any] = {"poly.bad": poly_obj(bad_factor)}
    cert = make_cert(
        coeffs=f,
        objects=objects,
        children=[lemma_factorization("$input", unit=Fraction(1), factors=[("poly.bad", 1)])],
    )
    assert_schema_valid(v, cert)
    out = verify(cert)
    assert out.verified is False
    assert any(c.name == "lemma.factorization.factor.monic" and c.ok is False for c in out.checks)


def test_factorization_missing_object_ref_fails_ref_integrity():
    """Missing factor object id must be detected by reference integrity checks."""
    v = load_schema_validator()

    f = [Fraction(1), Fraction(0), Fraction(-1)]  # x^2 - 1
    cert = make_cert(
        coeffs=f,
        objects={},  # missing poly.f1
        children=[lemma_factorization("$input", unit=Fraction(1), factors=[("poly.f1", 1)])],
    )
    assert_schema_valid(v, cert)
    out = verify(cert)
    assert out.verified is False
    assert any(("factor.resolve" in c.name or "resolve" in c.name) and c.ok is False for c in out.checks)


def test_factorization_order_insensitive():
    """Reordering factors must still verify (commutativity)."""
    v = load_schema_validator()

    f = [Fraction(1), Fraction(0), Fraction(-1)]  # x^2 - 1
    f1 = [Fraction(1), Fraction(-1)]
    f2 = [Fraction(1), Fraction(1)]

    objects: dict[str, Any] = {"poly.f1": poly_obj(f1), "poly.f2": poly_obj(f2)}
    cert = make_cert(
        coeffs=f,
        objects=objects,
        children=[
            lemma_factorization("$input", unit=Fraction(1), factors=[("poly.f1", 1), ("poly.f2", 1)]),
        ],
    )
    assert_schema_valid(v, cert)

    # Reverse order in witness.factors (still valid).
    swapped = copy.deepcopy(cert)
    w = swapped["proof"]["root"]["children"][0]["witness"]["factors"]
    swapped["proof"]["root"]["children"][0]["witness"]["factors"] = list(reversed(w))

    out = verify(swapped)
    assert out.verified is True
