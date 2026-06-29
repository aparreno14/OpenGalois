from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from opengalois import analyze, verify


def _objects(cert: Mapping[str, Any]) -> Mapping[str, Any]:
    objects = cert.get("objects")
    if not isinstance(objects, Mapping):
        raise AssertionError("certificate objects not found")
    return objects


def _poly(cert: Mapping[str, Any], ref: str) -> list[Fraction]:
    obj = _objects(cert).get(ref)
    if not isinstance(obj, Mapping):
        raise AssertionError(f"missing object {ref!r}")
    coeffs = obj.get("coeffs_qq")
    if not isinstance(coeffs, list) or not all(isinstance(c, str) for c in coeffs):
        raise AssertionError(f"object {ref!r} is not a PolyQQ object: {obj!r}")
    return [Fraction(c) for c in coeffs]


def _single_ref_with_prefix(cert: Mapping[str, Any], prefix: str) -> str:
    refs = [ref for ref in _objects(cert) if ref.startswith(prefix)]
    if len(refs) != 1:
        raise AssertionError(f"expected one object with prefix {prefix!r}, got {refs!r}")
    return refs[0]


def _group_alias(cert: Mapping[str, Any]) -> str:
    summary = cert.get("summary")
    if isinstance(summary, Mapping):
        group = summary.get("galois_group")
        if isinstance(group, str):
            return group
    raise AssertionError("certificate summary.galois_group not found")


def _disc_monic_quadratic(q: list[Fraction]) -> Fraction:
    if len(q) != 3 or q[0] != 1:
        raise AssertionError(f"expected monic quadratic, got {q!r}")
    return q[1] * q[1] - 4 * q[2]


def test_deg5_mixed_dummit_quadratic_degeneracy_is_d5() -> None:
    """Regression for the case q+ splits doubly but q- is irreducible.

    The old one-quadratic C5/D5 gate only inspected q+ and therefore
    misclassified this polynomial as C5 because disc(q+) = 0.  The second
    Dummit quadratic has non-square discriminant -17900, so the correct group
    is D5.
    """
    coeffs = [1, -2, -1, 4, 3, 2]
    cert = analyze(coeffs, explain=False).certificate

    verification = verify(cert)
    assert verification.verified, [
        (check.name, check.details) for check in verification.checks if not check.ok
    ]
    assert _group_alias(cert) == "D5"

    q1 = _poly(cert, _single_ref_with_prefix(cert, "poly.dummit.q1."))
    q2 = _poly(cert, _single_ref_with_prefix(cert, "poly.dummit.q2."))

    assert q1 == [Fraction(1), Fraction(2214, 5), Fraction(1225449, 25)]
    assert q2 == [Fraction(1), Fraction(-5086, 5), Fraction(6578724, 25)]
    assert _disc_monic_quadratic(q1) == 0
    assert _disc_monic_quadratic(q2) == -17900
