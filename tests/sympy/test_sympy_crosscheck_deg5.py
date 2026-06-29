from __future__ import annotations

import itertools
import os
import random
from collections.abc import Iterator, Sequence
from typing import Any

import pytest

if (
    os.getenv("OPENGALOIS_RUN_SYMPY_CROSSCHECK") != "1"
    or os.getenv("OPENGALOIS_RUN_SYMPY_DEG5") != "1"
):
    pytest.skip(
        "local SymPy degree-5 cross-check disabled; set "
        "OPENGALOIS_RUN_SYMPY_CROSSCHECK=1 and OPENGALOIS_RUN_SYMPY_DEG5=1",
        allow_module_level=True,
    )

sp = pytest.importorskip("sympy")
from sympy.polys.numberfields import galois_group  # type: ignore[import-untyped]

from opengalois import analyze, verify  # noqa: E402

EXHAUSTIVE_DEG5_BOUND = int(os.getenv("OPENGALOIS_SYMPY_DEG5_BOUND", "2"))
RANDOM_DEG5_CASES = int(os.getenv("OPENGALOIS_SYMPY_DEG5_RANDOM_CASES", "200"))
RANDOM_DEG5_BOUND = int(os.getenv("OPENGALOIS_SYMPY_DEG5_RANDOM_BOUND", "50"))
RANDOM_DEG5_SEED = int(os.getenv("OPENGALOIS_SYMPY_DEG5_RANDOM_SEED", "20260624"))
ROOT_PRECISION = int(os.getenv("OPENGALOIS_SYMPY_ROOT_PRECISION", "120"))
ROOT_TOL = sp.Float(os.getenv("OPENGALOIS_SYMPY_ROOT_TOL", "1e-25"), ROOT_PRECISION)

SOLVABLE_DEG5_GROUPS = {"C5", "D5", "F20"}

# One small irreducible representative for each transitive degree-5 group.
# The expected labels are checked against SymPy before OpenGalois is tested.
FIXED_DEG5_CASES: tuple[tuple[tuple[int, ...], str], ...] = (
    ((1, -3, -3, 4, 1, -1), "C5"),       # x^5 - 3*x^4 - 3*x^3 + 4*x^2 + x - 1
    ((1, -4, -2, -1, -2, -1), "D5"),     # x^5 - 4*x^4 - 2*x^3 - x^2 - 2*x - 1
    ((1, -4, -3, 2, -2, -3), "F20"),     # x^5 - 4*x^4 - 3*x^3 + 2*x^2 - 2*x - 3
    ((1, -4, 1, 3, 0, -3), "A5"),        # x^5 - 4*x^4 + x^3 + 3*x^2 - 3
    ((1, -4, -4, -4, -4, -4), "S5"),     # x^5 - 4*x^4 - 4*x^3 - 4*x^2 - 4*x - 4
)


def _sympy_poly_from_coeffs(coeffs: Sequence[int]) -> Any:
    x = sp.Symbol("x")
    degree = len(coeffs) - 1
    expr = sum(sp.Integer(c) * x ** (degree - i) for i, c in enumerate(coeffs))
    return sp.Poly(expr, x, domain=sp.QQ)


def _is_valid_irreducible_quintic(coeffs: Sequence[int]) -> bool:
    poly = _sympy_poly_from_coeffs(coeffs)
    return bool(poly.degree() == 5 and poly.is_irreducible and poly.discriminant() != 0)


def _monic_integer_quintics(*, bound: int) -> Iterator[tuple[int, ...]]:
    for tail in itertools.product(range(-bound, bound + 1), repeat=5):
        yield (1, *tail)


def _random_irreducible_quintics(
    *,
    count: int,
    bound: int,
    seed: int,
) -> list[tuple[int, ...]]:
    rng = random.Random(seed)
    cases: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    attempts = 0
    max_attempts = max(1000, count * 100)

    while len(cases) < count and attempts < max_attempts:
        attempts += 1
        coeffs = (1, *(rng.randint(-bound, bound) for _ in range(5)))
        if coeffs in seen:
            continue
        seen.add(coeffs)
        if _is_valid_irreducible_quintic(coeffs):
            cases.append(coeffs)

    if len(cases) < count:
        raise AssertionError(
            f"Could only generate {len(cases)} irreducible degree-5 cases "
            f"after {attempts} attempts; requested {count}."
        )
    return cases


def _opengalois_group_alias(cert: dict[str, Any]) -> str:
    objects = cert["objects"]
    facts = cert["proof"]["facts"]

    for fact in reversed(facts):
        if not isinstance(fact, dict):
            continue
        claim = fact.get("claim")
        if not isinstance(claim, dict) or claim.get("pred") != "GaloisGroup":
            continue
        args = claim.get("args")
        if not isinstance(args, list) or len(args) != 2:
            continue
        first_arg = args[0]
        if not isinstance(first_arg, dict) or first_arg.get("ref") != "$input":
            continue
        second_arg = args[1]
        if not isinstance(second_arg, dict):
            continue
        group_ref = second_arg.get("ref")
        if not isinstance(group_ref, str) or group_ref not in objects:
            continue
        group_obj = objects[group_ref]
        alias = group_obj.get("alias")
        if isinstance(alias, str):
            return alias
        order = group_obj.get("order")
        index = group_obj.get("index")
        return f"SmallGroup({order},{index})"

    raise AssertionError("missing final GaloisGroup($input,G) fact")


def _sympy_deg5_group_alias(poly: Any) -> str:
    group, _ = galois_group(poly)
    degree = int(poly.degree())
    order = int(group.order())

    if degree != 5:
        raise AssertionError(f"expected degree 5, got degree={degree}")

    aliases = {
        5: "C5",
        10: "D5",
        20: "F20",
        60: "A5",
        120: "S5",
    }
    try:
        return aliases[order]
    except KeyError as exc:
        raise AssertionError(f"unsupported degree-5 group order: {order}, group={group}") from exc


def _parse_qq(value: str) -> Any:
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return sp.Rational(int(numerator), int(denominator))
    return sp.Rational(int(value), 1)


def _rat_object_to_sympy(obj: dict[str, Any]) -> Any:
    if obj.get("kind") != "RatQQ":
        raise AssertionError(f"expected RatQQ object, got {obj!r}")
    value = obj.get("value")
    if not isinstance(value, str):
        raise AssertionError(f"RatQQ object missing canonical string value: {obj!r}")
    return _parse_qq(value)


def _expect_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AssertionError(f"expected mapping node, got {value!r}")
    return value


def _radical_expr_to_sympy(expr: dict[str, Any], objects: dict[str, Any]) -> Any:
    kind = expr.get("kind")

    if kind == "qq":
        value = expr.get("value_qq")
        if isinstance(value, str):
            return _parse_qq(value)
        ref = expr.get("ref")
        if isinstance(ref, str) and ref in objects:
            return _rat_object_to_sympy(objects[ref])
        raise AssertionError(f"invalid qq node: {expr!r}")

    if kind == "zeta":
        n = expr.get("n")
        k = expr.get("k")
        if not isinstance(n, int) or not isinstance(k, int):
            raise AssertionError(f"invalid zeta node: {expr!r}")
        return sp.exp(2 * sp.pi * sp.I * sp.Rational(k, n))

    if kind == "neg":
        return -_radical_expr_to_sympy(_expect_mapping(expr.get("arg")), objects)

    if kind in {"add", "sub", "mul", "div"}:
        left = _radical_expr_to_sympy(_expect_mapping(expr.get("left")), objects)
        right = _radical_expr_to_sympy(_expect_mapping(expr.get("right")), objects)
        if kind == "add":
            return left + right
        if kind == "sub":
            return left - right
        if kind == "mul":
            return left * right
        return left / right

    if kind == "pow_int":
        exp = expr.get("exp")
        if not isinstance(exp, int):
            raise AssertionError(f"invalid pow_int exponent: {expr!r}")
        return _radical_expr_to_sympy(_expect_mapping(expr.get("base")), objects) ** exp

    if kind == "root":
        n = expr.get("n")
        if not isinstance(n, int) or n < 2:
            raise AssertionError(f"invalid root index: {expr!r}")
        arg = _radical_expr_to_sympy(_expect_mapping(expr.get("arg")), objects)
        return arg ** sp.Rational(1, n)

    raise AssertionError(f"unknown RadicalExpr node kind: {kind!r}")


def _opengalois_final_root_exprs(cert: dict[str, Any]) -> list[Any]:
    objects = cert["objects"]

    for fact in reversed(cert["proof"]["facts"]):
        if not isinstance(fact, dict):
            continue
        claim = fact.get("claim")
        if not isinstance(claim, dict) or claim.get("pred") != "RadicalRoots":
            continue
        args = claim.get("args")
        if not isinstance(args, list) or len(args) != 2:
            continue
        first_arg = args[0]
        if not isinstance(first_arg, dict) or first_arg.get("ref") != "$input":
            continue
        second_arg = args[1]
        if not isinstance(second_arg, dict):
            continue
        roots_ref = second_arg.get("ref")
        if not isinstance(roots_ref, str) or roots_ref not in objects:
            continue

        roots_obj = objects[roots_ref]
        if roots_obj.get("kind") != "RadicalExprList":
            raise AssertionError(f"expected RadicalExprList object, got {roots_obj!r}")
        items = roots_obj.get("items")
        if not isinstance(items, list):
            raise AssertionError(f"RadicalExprList.items must be a list: {roots_obj!r}")

        values: list[Any] = []
        for item_ref in items:
            if not isinstance(item_ref, str) or item_ref not in objects:
                raise AssertionError(f"missing RadicalExpr object: {item_ref!r}")
            expr_obj = objects[item_ref]
            if expr_obj.get("kind") != "RadicalExpr":
                raise AssertionError(f"expected RadicalExpr object, got {expr_obj!r}")
            values.append(_radical_expr_to_sympy(_expect_mapping(expr_obj.get("expr")), objects))
        return values

    raise AssertionError("missing final RadicalRoots($input,R) fact")


def _root_multiset_distance(left: Sequence[Any], right: Sequence[Any]) -> Any:
    if len(left) != len(right):
        raise AssertionError(f"root count mismatch: {len(left)} != {len(right)}")

    best = None
    for perm in itertools.permutations(right):
        current = max(
            sp.Abs(sp.N(a - b, ROOT_PRECISION))
            for a, b in zip(left, perm, strict=True)
        )
        if best is None or current < best:
            best = current
    if best is None:
        return sp.Integer(0)
    return sp.N(best, ROOT_PRECISION)


def _assert_matches_sympy(coeffs: Sequence[int]) -> str:
    result = analyze(list(coeffs), explain=False)
    cert = result.certificate
    verification = verify(cert)
    assert verification.verified, {
        "coeffs": tuple(coeffs),
        "failed_checks": [
            (check.name, check.details) for check in verification.checks if not check.ok
        ],
    }

    poly = _sympy_poly_from_coeffs(coeffs)
    og_group = _opengalois_group_alias(cert)
    sp_group = _sympy_deg5_group_alias(poly)
    assert og_group == sp_group, {
        "coeffs": tuple(coeffs),
        "opengalois_group": og_group,
        "sympy_group": sp_group,
        "certificate_summary": cert.get("summary"),
    }

    if og_group in SOLVABLE_DEG5_GROUPS:
        og_roots = [sp.N(root, ROOT_PRECISION) for root in _opengalois_final_root_exprs(cert)]
        sympy_roots = [sp.N(root, ROOT_PRECISION) for root in poly.nroots(n=ROOT_PRECISION)]
        distance = _root_multiset_distance(og_roots, sympy_roots)
        assert distance < ROOT_TOL, {
            "coeffs": tuple(coeffs),
            "opengalois_group": og_group,
            "sympy_group": sp_group,
            "root_distance": str(distance),
            "root_tolerance": str(ROOT_TOL),
            "opengalois_roots": [str(root) for root in og_roots],
            "sympy_roots": [str(root) for root in sympy_roots],
        }

    return og_group


def test_deg5_fixed_cases_match_sympy_group_and_solvable_roots() -> None:
    seen_groups: set[str] = set()

    for coeffs, expected_group in FIXED_DEG5_CASES:
        poly = _sympy_poly_from_coeffs(coeffs)
        assert poly.is_irreducible, {"coeffs": coeffs, "reason": "fixed case is reducible"}
        assert _sympy_deg5_group_alias(poly) == expected_group
        seen_groups.add(_assert_matches_sympy(coeffs))

    assert seen_groups == {"C5", "D5", "F20", "A5", "S5"}


def test_deg5_exhaustive_small_box_matches_sympy_group_and_solvable_roots() -> None:
    checked = 0
    seen_groups: set[str] = set()

    for coeffs in _monic_integer_quintics(bound=EXHAUSTIVE_DEG5_BOUND):
        if _is_valid_irreducible_quintic(coeffs):
            seen_groups.add(_assert_matches_sympy(coeffs))
            checked += 1

    assert checked > 0
    assert seen_groups


def test_deg5_random_matches_sympy_group_and_solvable_roots() -> None:
    cases = _random_irreducible_quintics(
        count=RANDOM_DEG5_CASES,
        bound=RANDOM_DEG5_BOUND,
        seed=RANDOM_DEG5_SEED,
    )

    seen_groups: set[str] = set()
    for coeffs in cases:
        seen_groups.add(_assert_matches_sympy(coeffs))

    assert seen_groups
