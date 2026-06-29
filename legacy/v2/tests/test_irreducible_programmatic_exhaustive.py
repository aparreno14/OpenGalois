from __future__ import annotations

import copy
from fractions import Fraction
from typing import Any

import pytest
from tests_helpers import (
    assert_schema_valid,
    lemma_irreducible,
    load_schema_validator,
    make_cert,
    poly_obj,
)

from opengalois import verify


@pytest.mark.parametrize(
    "coeffs",
    [
        # x^2 + 1
        [Fraction(1), Fraction(0), Fraction(1)],
        # x^3 - x - 1
        [Fraction(1), Fraction(0), Fraction(-1), Fraction(-1)],
        # x^4 + 1
        [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(1)],
        # x^5 - x - 1
        [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(-1), Fraction(-1)],
    ],
)
def test_irreducible_ok_on_known_irreducibles(coeffs: list[Fraction]):
    """irreducible.QQ must verify for polynomials irreducible over Q under glassbox_le5."""
    v = load_schema_validator()
    cert = make_cert(coeffs=coeffs, children=[lemma_irreducible("$input")])
    assert_schema_valid(v, cert)
    out = verify(cert)
    assert out.verified is True


@pytest.mark.parametrize(
    "coeffs",
    [
        # x^2 - 1 = (x-1)(x+1)
        [Fraction(1), Fraction(0), Fraction(-1)],
        # x^4 - 1 reducible
        [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(-1)],
        # x^5 - x^4 = x^4(x-1)
        [Fraction(1), Fraction(-1), Fraction(0), Fraction(0), Fraction(0), Fraction(0)],
    ],
)
def test_irreducible_rejects_reducible_poly(coeffs: list[Fraction]):
    """irreducible.QQ must fail if a non-trivial factorization exists."""
    v = load_schema_validator()
    cert = make_cert(coeffs=coeffs, children=[lemma_irreducible("$input")])
    assert_schema_valid(v, cert)
    out = verify(cert)
    assert out.verified is False
    assert any(c.name == "lemma.irreducible.soundness" and c.ok is False for c in out.checks)


def test_irreducible_rejects_unknown_method():
    """Unsupported method identifiers must be rejected."""
    v = load_schema_validator()
    f = [Fraction(1), Fraction(0), Fraction(1)]  # x^2 + 1
    cert = make_cert(coeffs=f, children=[lemma_irreducible("$input", method="glassbox_le5_TYPO")])
    assert_schema_valid(v, cert)
    out = verify(cert)
    assert out.verified is False
    assert any(c.name == "lemma.irreducible.witness.method" and c.ok is False for c in out.checks)


def test_irreducible_supports_object_refs():
    """irreducible.QQ must support inputs referencing poly_qq_desc objects."""
    v = load_schema_validator()

    # Input is x^4 + 1, but lemma consumes objects['poly.p1'].
    f = [Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(1)]
    objects: dict[str, Any] = {"poly.p1": poly_obj(f)}
    cert = make_cert(coeffs=f, objects=objects, children=[lemma_irreducible("poly.p1")])
    assert_schema_valid(v, cert)
    out = verify(cert)
    assert out.verified is True

    # Tamper object to x^4 - 1 (reducible) while leaving input hash intact.
    bad = copy.deepcopy(cert)
    bad["objects"]["poly.p1"]["coeffs_qq"][-1] = "-1"
    assert_schema_valid(v, bad)
    out2 = verify(bad)
    assert out2.verified is False
