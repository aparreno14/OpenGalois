from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import pytest

from opengalois import analyze, verify

INPUT_REF = "$input"


@dataclass(frozen=True)
class DummitPaperExample:
    """Just for ruff to shut up."""
    name: str
    coeffs: tuple[int, ...]
    discriminant: int
    theta: Fraction
    group: str
    resolvent: tuple[int, ...]
    quadratics: frozenset[tuple[Fraction, Fraction, Fraction]] | None


DUMMIT_PAPER_EXAMPLES: tuple[DummitPaperExample, ...] = (
    DummitPaperExample(
        name="Dummit example 1: F20, x^5 + 15x + 12",
        coeffs=(1, 0, 0, 0, 15, 12),
        discriminant=2**10 * 3**4 * 5**5,
        theta=Fraction(0),
        group="F20",
        resolvent=(
            1,
            120,
            9000,
            540000,
            20250000,
            324000000,
            0,
        ),
        quadratics=None,
    ),
    DummitPaperExample(
        name="Dummit example 2: D5, x^5 - 5x + 12",
        coeffs=(1, 0, 0, 0, -5, 12),
        discriminant=2**12 * 5**6,
        theta=Fraction(40),
        group="D5",
        resolvent=(
            1,
            -40,
            1000,
            -20000,
            250000,
            -66400000,
            976000000,
        ),
        quadratics=frozenset(
            {
                (Fraction(1), Fraction(1250), Fraction(6015625)),
                (Fraction(1), Fraction(-3750), Fraction(4921875)),
            }
        ),
    ),
    DummitPaperExample(
        name="Dummit example 3: C5, x^5 - 110x^3 - 55x^2 + 2310x + 979",
        coeffs=(1, 0, -110, -55, 2310, 979),
        discriminant=5**20 * 11**4,
        theta=Fraction(-9955),
        group="C5",
        resolvent=(
            1,
            18480,
            47764750,
            -580262760000,
            -1796651418959375,
            2980357148316659375,
            -360260685644469671875,
        ),
        quadratics=frozenset(
            {
                # (x - 797500)(x + 61875)
                (Fraction(1), Fraction(-735625), Fraction(-49345312500)),
                # (x - 281875)(x + 405625)
                (Fraction(1), Fraction(123750), Fraction(-114335546875)),
            }
        ),
    ),
)


def _parse_q(s: str) -> Fraction:
    return Fraction(s)


def _proof_facts(cert: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    proof = cert.get("proof")
    if isinstance(proof, Mapping):
        facts = proof.get("facts")
    else:
        facts = proof
    if not isinstance(facts, list):
        raise AssertionError("certificate proof facts not found")
    out: list[Mapping[str, Any]] = []
    for fact in facts:
        if not isinstance(fact, Mapping):
            raise AssertionError(f"malformed proof fact: {fact!r}")
        out.append(fact)
    return out


def _objects(cert: Mapping[str, Any]) -> Mapping[str, Any]:
    objs = cert.get("objects")
    if not isinstance(objs, Mapping):
        raise AssertionError("certificate objects not found")
    return objs


def _input_coeffs(cert: Mapping[str, Any]) -> list[Fraction]:
    inp = cert.get("input")
    if not isinstance(inp, Mapping):
        raise AssertionError("certificate input not found")
    coeffs = inp.get("coeffs_qq")
    if not isinstance(coeffs, list) or not all(isinstance(c, str) for c in coeffs):
        raise AssertionError("certificate input.coeffs_qq not found")
    return [_parse_q(c) for c in coeffs]


def _ref(arg: Any) -> str | None:
    if not isinstance(arg, Mapping):
        return None
    value = arg.get("ref")
    return value if isinstance(value, str) else None


def _claim(fact: Mapping[str, Any]) -> Mapping[str, Any]:
    claim = fact.get("claim", fact)
    if not isinstance(claim, Mapping):
        raise AssertionError(f"malformed claim in fact {fact!r}")
    return claim


def _claim_args(fact: Mapping[str, Any]) -> list[Any]:
    args = _claim(fact).get("args")
    if not isinstance(args, list):
        raise AssertionError(f"malformed claim args in fact {fact!r}")
    return args


def _pred(fact: Mapping[str, Any]) -> str | None:
    pred = _claim(fact).get("pred")
    return pred if isinstance(pred, str) else None


def _poly(cert: Mapping[str, Any], ref: str) -> list[Fraction]:
    if ref == INPUT_REF:
        return _input_coeffs(cert)
    obj = _objects(cert).get(ref)
    if not isinstance(obj, Mapping):
        raise AssertionError(f"missing object {ref!r}")
    coeffs = obj.get("coeffs_qq")
    if not isinstance(coeffs, list) or not all(isinstance(c, str) for c in coeffs):
        raise AssertionError(f"object {ref!r} is not a PolyQQ object: {obj!r}")
    return [_parse_q(c) for c in coeffs]


def _rat(cert: Mapping[str, Any], ref: str) -> Fraction:
    obj = _objects(cert).get(ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "RatQQ":
        raise AssertionError(f"object {ref!r} is not a RatQQ object: {obj!r}")
    value = obj.get("value")
    if not isinstance(value, str):
        raise AssertionError(f"object {ref!r} has malformed RatQQ value: {obj!r}")
    return _parse_q(value)


def _intz(cert: Mapping[str, Any], ref: str) -> int:
    obj = _objects(cert).get(ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "IntZ":
        raise AssertionError(f"object {ref!r} is not an IntZ object: {obj!r}")
    value = obj.get("value")
    if not isinstance(value, str):
        raise AssertionError(f"object {ref!r} has malformed IntZ value: {obj!r}")
    return int(value)


def _polyqqlist_items(cert: Mapping[str, Any], ref: str) -> list[str]:
    obj = _objects(cert).get(ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "PolyQQList":
        raise AssertionError(f"object {ref!r} is not a PolyQQList object: {obj!r}")
    items = obj.get("items")
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise AssertionError(f"object {ref!r} has malformed items: {obj!r}")
    return list(items)


def _group_alias(cert: Mapping[str, Any]) -> str:
    summary = cert.get("summary")
    if isinstance(summary, Mapping):
        group = summary.get("galois_group")
        if isinstance(group, str):
            return group
    raise AssertionError("certificate summary.galois_group not found")


def _discriminant_of(cert: Mapping[str, Any], poly_ref: str) -> Fraction:
    for fact in _proof_facts(cert):
        if _pred(fact) != "Discriminant":
            continue
        args = _claim_args(fact)
        if len(args) != 2:
            continue
        if _ref(args[0]) == poly_ref:
            rat_ref = _ref(args[1])
            if rat_ref is None:
                raise AssertionError("malformed Discriminant fact")
            return _rat(cert, rat_ref)
    raise AssertionError(f"Discriminant({poly_ref}, D) not found")


def _resolvent_ref_for(cert: Mapping[str, Any], poly_ref: str) -> str:
    for fact in _proof_facts(cert):
        if _pred(fact) != "ResolventQQ":
            continue
        args = _claim_args(fact)
        if len(args) != 3:
            continue
        if _ref(args[1]) == poly_ref:
            r_ref = _ref(args[0])
            if r_ref is None:
                raise AssertionError("malformed ResolventQQ fact")
            return r_ref
    raise AssertionError(f"ResolventQQ(R, {poly_ref}, p) not found")


def _linear_factor_ref_of_resolvent(cert: Mapping[str, Any], resolvent_ref: str) -> str:
    factors_ref: str | None = None
    for fact in _proof_facts(cert):
        if _pred(fact) != "FactorizationMonicQQ":
            continue
        args = _claim_args(fact)
        if len(args) != 3:
            continue
        if _ref(args[0]) == resolvent_ref:
            factors_ref = _ref(args[1])
            break
    if factors_ref is None:
        raise AssertionError(f"FactorizationMonicQQ({resolvent_ref}, factors, unit) not found")

    factor_items = set(_polyqqlist_items(cert, factors_ref))
    for fact in _proof_facts(cert):
        if _pred(fact) != "Degree":
            continue
        args = _claim_args(fact)
        if len(args) != 2:
            continue
        factor_ref = _ref(args[0])
        degree_ref = _ref(args[1])
        if factor_ref in factor_items and degree_ref is not None and _intz(cert, degree_ref) == 1:
            return factor_ref
    raise AssertionError(f"linear factor of {resolvent_ref} not found")


def _theta_from_monic_linear_factor(cert: Mapping[str, Any], factor_ref: str) -> Fraction:
    coeffs = _poly(cert, factor_ref)
    if len(coeffs) != 2:
        raise AssertionError(f"factor {factor_ref!r} is not linear: {coeffs!r}")
    a, b = coeffs
    if a == 0:
        raise AssertionError(f"factor {factor_ref!r} has zero leading coefficient")
    return -b / a


def _degree2_polys(cert: Mapping[str, Any]) -> set[tuple[Fraction, Fraction, Fraction]]:
    out: set[tuple[Fraction, Fraction, Fraction]] = set()
    for _ref_id, obj in _objects(cert).items():
        if not isinstance(obj, Mapping) or obj.get("kind") != "PolyQQ":
            continue
        coeffs = obj.get("coeffs_qq")
        if not isinstance(coeffs, list) or len(coeffs) != 3:
            continue
        parsed = tuple(_parse_q(c) for c in coeffs)
        if len(parsed) == 3:
            out.add(parsed)  
    return out


@pytest.mark.parametrize("example", DUMMIT_PAPER_EXAMPLES, ids=lambda e: e.name)
def test_dummit_paper_examples_match_resolvent_theta_group_and_quadratics(
    example: DummitPaperExample,
) -> None:
    result = analyze(list(example.coeffs), explain=False)
    cert = result.certificate

    verification = verify(cert)
    assert verification.verified, [
        (check.name, check.details) for check in verification.checks if not check.ok
    ]

    assert _group_alias(cert) == example.group
    assert _discriminant_of(cert, INPUT_REF) == Fraction(example.discriminant)

    resolvent_ref = _resolvent_ref_for(cert, INPUT_REF)
    assert _poly(cert, resolvent_ref) == [Fraction(c) for c in example.resolvent]

    linear_ref = _linear_factor_ref_of_resolvent(cert, resolvent_ref)
    assert _theta_from_monic_linear_factor(cert, linear_ref) == example.theta

    if example.quadratics is not None:
        emitted_quadratics = _degree2_polys(cert)
        assert emitted_quadratics & example.quadratics, {
            "expected_one_of": sorted(example.quadratics),
            "emitted_quadratics": sorted(emitted_quadratics),
        }
