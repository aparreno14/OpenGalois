from __future__ import annotations

import hashlib
import itertools
import os
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import pytest

if (
    os.getenv("OPENGALOIS_RUN_SYMPY_CROSSCHECK") != "1"
    or os.getenv("OPENGALOIS_RUN_SYMPY_DEG5") != "1"
    or os.getenv("OPENGALOIS_RUN_LINTON97") != "1"
):
    pytest.skip(
        "local Linton §9.7 generated-solvable degree-5 cross-check disabled; set "
        "OPENGALOIS_RUN_SYMPY_CROSSCHECK=1, OPENGALOIS_RUN_SYMPY_DEG5=1, "
        "and OPENGALOIS_RUN_LINTON97=1",
        allow_module_level=True,
    )

sp = pytest.importorskip("sympy")
from sympy.polys.numberfields import galois_group  # type: ignore[import-untyped]

from opengalois import analyze, verify  # noqa: E402

PARAM_BOUND = int(os.getenv("OPENGALOIS_LINTON97_PARAM_BOUND", "2"))
DEN_BOUND = int(os.getenv("OPENGALOIS_LINTON97_DEN_BOUND", "1"))
MAX_CASES_PER_FAMILY = int(os.getenv("OPENGALOIS_LINTON97_MAX_CASES_PER_FAMILY", "25"))
HEIGHT_BOUND = int(os.getenv("OPENGALOIS_LINTON97_HEIGHT_BOUND", "1000000"))
SHARDS = int(os.getenv("OPENGALOIS_LINTON97_SHARDS", "1"))
SHARD_INDEX = int(os.getenv("OPENGALOIS_LINTON97_SHARD_INDEX", "0"))
CHECK_ROOTS = os.getenv("OPENGALOIS_LINTON97_CHECK_ROOTS", "sample").strip().lower()
ROOT_SAMPLE_RATE = int(os.getenv("OPENGALOIS_LINTON97_ROOT_SAMPLE_RATE", "25"))
ROOT_PRECISION = int(os.getenv("OPENGALOIS_SYMPY_ROOT_PRECISION", "120"))
ROOT_TOL = sp.Float(os.getenv("OPENGALOIS_SYMPY_ROOT_TOL", "1e-25"), ROOT_PRECISION)
FAMILIES_RAW = os.getenv(
    "OPENGALOIS_LINTON97_FAMILIES",
    "general,s_eq_0,s_eq_t_eq_0,s2_eq_c2",
)

SOLVABLE_DEG5_GROUPS = {"C5", "D5", "F20"}
SUPPORTED_ROOT_CHECK_MODES = {"all", "sample", "off"}
SUPPORTED_FAMILIES = {"general", "s_eq_0", "s_eq_t_eq_0", "s2_eq_c2"}

if CHECK_ROOTS not in SUPPORTED_ROOT_CHECK_MODES:
    raise ValueError(
        "OPENGALOIS_LINTON97_CHECK_ROOTS must be one of "
        f"{sorted(SUPPORTED_ROOT_CHECK_MODES)}, got {CHECK_ROOTS!r}."
    )
if ROOT_SAMPLE_RATE <= 0:
    raise ValueError("OPENGALOIS_LINTON97_ROOT_SAMPLE_RATE must be positive.")
if DEN_BOUND <= 0:
    raise ValueError("OPENGALOIS_LINTON97_DEN_BOUND must be positive.")
if SHARDS <= 0:
    raise ValueError("OPENGALOIS_LINTON97_SHARDS must be positive.")
if not 0 <= SHARD_INDEX < SHARDS:
    raise ValueError("OPENGALOIS_LINTON97_SHARD_INDEX must satisfy 0 <= index < shards.")

REQUESTED_FAMILIES = tuple(
    family.strip() for family in FAMILIES_RAW.split(",") if family.strip()
)
unknown_families = set(REQUESTED_FAMILIES) - SUPPORTED_FAMILIES
if unknown_families:
    raise ValueError(
        "OPENGALOIS_LINTON97_FAMILIES contains unsupported family names: "
        f"{sorted(unknown_families)}. Supported families are {sorted(SUPPORTED_FAMILIES)}."
    )
if not REQUESTED_FAMILIES:
    raise ValueError("OPENGALOIS_LINTON97_FAMILIES selected no families.")


@dataclass(frozen=True)
class LintonCase:
    """One exact quintic generated from Linton §9.7."""

    family: str
    label: str
    coeffs: tuple[Any, ...]
    params: Mapping[str, Any]


# ---------------------------------------------------------------------------
# Exact rational utilities
# ---------------------------------------------------------------------------


def _small_rationals(*, param_bound: int, den_bound: int) -> tuple[Any, ...]:
    """Return a deterministic small rational box as SymPy rationals."""
    values: list[Any] = []
    seen: set[Any] = set()
    for den in range(1, den_bound + 1):
        for num in range(-param_bound, param_bound + 1):
            q = sp.Rational(num, den)
            if q not in seen:
                seen.add(q)
                values.append(q)
    return tuple(values)


def _sp_rat_to_fraction(q: Any) -> Fraction:
    q = sp.Rational(q)
    return Fraction(int(q.p), int(q.q))


def _coeffs_to_fractions(coeffs: Sequence[Any]) -> tuple[Fraction, ...]:
    return tuple(_sp_rat_to_fraction(c) for c in coeffs)


def _coeff_height(coeffs: Sequence[Any]) -> int:
    height = 0
    for coeff in coeffs:
        q = sp.Rational(coeff)
        height = max(height, abs(int(q.p)), abs(int(q.q)))
    return height


def _coeffs(C: Any, D: Any, E: Any, f0: Any) -> tuple[Any, ...]:
    return (
        sp.Rational(1),
        sp.Rational(0),
        sp.cancel(10 * C),
        sp.cancel(10 * D),
        sp.cancel(5 * E),
        sp.cancel(f0),
    )


def _canonical_coeffs_string(coeffs: Sequence[Any]) -> str:
    return ";".join(str(sp.Rational(c)) for c in coeffs)


def _stable_int_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def _belongs_to_current_shard(coeffs: Sequence[Any]) -> bool:
    if SHARDS == 1:
        return True
    return _stable_int_hash(_canonical_coeffs_string(coeffs)) % SHARDS == SHARD_INDEX


def _should_check_roots(coeffs: Sequence[Any]) -> bool:
    if CHECK_ROOTS == "all":
        return True
    if CHECK_ROOTS == "off":
        return False
    return _stable_int_hash("roots:" + _canonical_coeffs_string(coeffs)) % ROOT_SAMPLE_RATE == 0


# ---------------------------------------------------------------------------
# Linton §9.7 generators
# ---------------------------------------------------------------------------


def _iter_linton_97_general(params: Sequence[Any]) -> Iterator[LintonCase]:
    """Generate the main §9.7 family with S != 0 and S^2 != C^2."""
    for Theta, Gamma, Lambda, Omega in itertools.product(params, repeat=4):
        w2 = Omega**2 + 1
        den = 4 * (Theta + 1) * (Theta**2 * w2 - 1)
        if den == 0:
            continue

        chi = sp.cancel((Lambda**2 * Omega**2 - Gamma**2 * w2) / den)
        if chi == 0:
            continue

        S2 = sp.cancel(chi**2 / w2)
        C = sp.cancel(Theta * chi)
        D = sp.cancel((Gamma + Lambda) * chi)
        if S2 == C**2:
            continue

        E = sp.cancel(
            C**2
            + S2 * (3 + 4 * Omega)
            + (C * (Lambda**2 * S2 - D**2) + 2 * D * Omega * Lambda * S2)
            / (S2 - C**2)
        )
        f0 = sp.cancel(
            (
                (Lambda**2 * S2 - D**2) * (C * Lambda - D)
                + E * (Lambda * (S2 + C**2) - 2 * C * D)
                - Lambda * (C**2 - 5 * S2) ** 2
            )
            / (S2 - C**2)
        )

        yield LintonCase(
            family="general",
            label=f"general Θ={Theta}, Γ={Gamma}, Λ={Lambda}, Ω={Omega}",
            params={"Theta": Theta, "Gamma": Gamma, "Lambda": Lambda, "Omega": Omega},
            coeffs=_coeffs(C, D, E, f0),
        )


def _iter_linton_97_s_eq_0(params: Sequence[Any]) -> Iterator[LintonCase]:
    """Generate the alternative §9.7 family with S = 0, T != 0, C != 0."""
    for mu, lam, gamma in itertools.product(params, repeat=3):
        # The condition (gamma^2 + mu^2)(1 + lambda)^2 != 0 over QQ.
        if mu == 0 and gamma == 0:
            continue
        if lam == -1:
            continue

        C = sp.cancel((mu**2 - lam**2 * (gamma**2 + mu**2)) / 4)
        if C == 0:
            continue

        D = sp.cancel(gamma * C)
        E = sp.cancel(5 * C**2 - 2 * mu**2 * C - 2 * C * lam * (gamma**2 + mu**2))
        f0 = sp.cancel(gamma * (C**2 + E) - 2 * mu * (C**2 + C * gamma**2 - E))

        yield LintonCase(
            family="s_eq_0",
            label=f"S=0 μ={mu}, λ={lam}, γ={gamma}",
            params={"mu": mu, "lambda": lam, "gamma": gamma},
            coeffs=_coeffs(C, D, E, f0),
        )


def _iter_linton_97_s_eq_t_eq_0(params: Sequence[Any]) -> Iterator[LintonCase]:
    """Generate the §9.7 family with S = T = 0 and C != 0."""
    for C, D in itertools.product(params, repeat=2):
        if C == 0 or D == 0:
            continue

        E = sp.cancel(C**2 + D**2 / C)
        f0 = sp.cancel(D**3 / C**2 + 2 * C * D)

        yield LintonCase(
            family="s_eq_t_eq_0",
            label=f"S=T=0 C={C}, D={D}",
            params={"C": C, "D": D},
            coeffs=_coeffs(C, D, E, f0),
        )


def _iter_linton_97_s2_eq_c2(params: Sequence[Any]) -> Iterator[LintonCase]:
    """Generate the §9.7 family with S^2 = C^2 != 0 in the non-De-Moivre subcase."""
    for C, D, Lambda in itertools.product(params, repeat=3):
        if C == 0:
            continue

        xi = sp.cancel(C * Lambda - D)
        eta = sp.cancel(C * Lambda + D)
        if xi == 0 or eta == 0:
            continue

        E = sp.cancel(4 * C**2 + (4 * C**2 * eta) / xi - (eta * xi) / (2 * C))
        f0 = sp.cancel(
            (16 * C**4 * eta) / xi**2
            - (2 * C * xi**2) / eta
            - (eta**2 * xi) / (4 * C**2)
            - 20 * C**2 * Lambda
        )

        yield LintonCase(
            family="s2_eq_c2",
            label=f"S^2=C^2 C={C}, D={D}, Λ={Lambda}",
            params={"C": C, "D": D, "Lambda": Lambda},
            coeffs=_coeffs(C, D, E, f0),
        )


def _iter_family_cases(family: str, params: Sequence[Any]) -> Iterator[LintonCase]:
    if family == "general":
        yield from _iter_linton_97_general(params)
    elif family == "s_eq_0":
        yield from _iter_linton_97_s_eq_0(params)
    elif family == "s_eq_t_eq_0":
        yield from _iter_linton_97_s_eq_t_eq_0(params)
    elif family == "s2_eq_c2":
        yield from _iter_linton_97_s2_eq_c2(params)
    else:  # pragma: no cover - guarded at module import.
        raise AssertionError(f"unsupported Linton §9.7 family: {family}")


# ---------------------------------------------------------------------------
# SymPy / OpenGalois cross-check helpers
# ---------------------------------------------------------------------------


def _sympy_poly_from_coeffs(coeffs: Sequence[Any]) -> Any:
    x = sp.Symbol("x")
    degree = len(coeffs) - 1
    expr = sum(sp.Rational(c) * x ** (degree - i) for i, c in enumerate(coeffs))
    return sp.Poly(expr, x, domain=sp.QQ)


def _is_irreducible_quintic(poly: Any) -> bool:
    # Over QQ, irreducible implies separable, so discriminant != 0 is automatic.
    return bool(poly.degree() == 5 and poly.is_irreducible)


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


def _case_payload(case: LintonCase) -> dict[str, Any]:
    return {
        "family": case.family,
        "label": case.label,
        "params": {key: str(value) for key, value in case.params.items()},
        "coeffs": [str(sp.Rational(c)) for c in case.coeffs],
        "height": _coeff_height(case.coeffs),
    }


def _assert_case_matches(case: LintonCase) -> str:
    coeffs_for_opengalois = _coeffs_to_fractions(case.coeffs)
    try:
        result = analyze(list(coeffs_for_opengalois), explain=False)
    except Exception as exc:  # noqa: BLE001
        raise AssertionError({
            **_case_payload(case),
            "stage": "opengalois.analyze",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }) from exc

    cert = result.certificate

    verification = verify(cert)
    assert verification.verified, {
        **_case_payload(case),
        "failed_checks": [
            (check.name, check.details) for check in verification.checks if not check.ok
        ],
    }

    poly = _sympy_poly_from_coeffs(case.coeffs)
    og_group = _opengalois_group_alias(cert)
    sp_group = _sympy_deg5_group_alias(poly)

    assert sp_group in SOLVABLE_DEG5_GROUPS, {
        **_case_payload(case),
        "sympy_group": sp_group,
        "reason": "Linton §9.7 generated an irreducible quintic outside C5/D5/F20.",
    }

    assert og_group == sp_group, {
        **_case_payload(case),
        "opengalois_group": og_group,
        "sympy_group": sp_group,
        "certificate_summary": cert.get("summary"),
    }

    if _should_check_roots(case.coeffs):
        og_roots = [sp.N(root, ROOT_PRECISION) for root in _opengalois_final_root_exprs(cert)]
        sympy_roots = [sp.N(root, ROOT_PRECISION) for root in poly.nroots(n=ROOT_PRECISION)]
        distance = _root_multiset_distance(og_roots, sympy_roots)
        assert distance < ROOT_TOL, {
            **_case_payload(case),
            "opengalois_group": og_group,
            "sympy_group": sp_group,
            "root_distance": str(distance),
            "root_tolerance": str(ROOT_TOL),
            "opengalois_roots": [str(root) for root in og_roots],
            "sympy_roots": [str(root) for root in sympy_roots],
        }

    return og_group


def test_linton_section_9_7_generated_solvable_quintics_match_sympy() -> None:
    params = _small_rationals(param_bound=PARAM_BOUND, den_bound=DEN_BOUND)

    checked_by_family = {family: 0 for family in REQUESTED_FAMILIES}
    generated_by_family = {family: 0 for family in REQUESTED_FAMILIES}
    skipped_height_by_family = {family: 0 for family in REQUESTED_FAMILIES}
    skipped_reducible_by_family = {family: 0 for family in REQUESTED_FAMILIES}
    seen_groups: set[str] = set()
    seen_coeffs: set[str] = set()

    for family in REQUESTED_FAMILIES:
        for case in _iter_family_cases(family, params):
            generated_by_family[family] += 1

            if not _belongs_to_current_shard(case.coeffs):
                continue

            coeff_key = _canonical_coeffs_string(case.coeffs)
            if coeff_key in seen_coeffs:
                continue
            seen_coeffs.add(coeff_key)

            if _coeff_height(case.coeffs) > HEIGHT_BOUND:
                skipped_height_by_family[family] += 1
                continue

            poly = _sympy_poly_from_coeffs(case.coeffs)
            if not _is_irreducible_quintic(poly):
                skipped_reducible_by_family[family] += 1
                continue

            seen_groups.add(_assert_case_matches(case))
            checked_by_family[family] += 1

            if MAX_CASES_PER_FAMILY > 0 and checked_by_family[family] >= MAX_CASES_PER_FAMILY:
                break

    total_checked = sum(checked_by_family.values())
    assert total_checked > 0, {
        "params": [str(q) for q in params],
        "requested_families": REQUESTED_FAMILIES,
        "generated_by_family": generated_by_family,
        "skipped_height_by_family": skipped_height_by_family,
        "skipped_reducible_by_family": skipped_reducible_by_family,
        "height_bound": HEIGHT_BOUND,
        "shards": SHARDS,
        "shard_index": SHARD_INDEX,
    }

    if SHARDS == 1:
        missing_families = [
            family for family, checked in checked_by_family.items() if checked == 0
        ]
        assert not missing_families, {
            "missing_families": missing_families,
            "checked_by_family": checked_by_family,
            "generated_by_family": generated_by_family,
            "skipped_height_by_family": skipped_height_by_family,
            "skipped_reducible_by_family": skipped_reducible_by_family,
            "height_bound": HEIGHT_BOUND,
        }

    assert seen_groups <= SOLVABLE_DEG5_GROUPS, {
        "seen_groups": sorted(seen_groups),
        "checked_by_family": checked_by_family,
    }
