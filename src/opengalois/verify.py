from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from math import gcd
from typing import Any, Literal, cast

from jsonschema import Draft202012Validator

from opengalois.algorithms.dummit_quintic_tables import eval_all
from opengalois.engine.procedures.irreducible.deg5 import (
    _find_rational_root_QQ_desc_resolvent_6_1plus5,
)
from opengalois.radicals.ast import (
    add as _ast_add,
)
from opengalois.radicals.ast import (
    div as _ast_div,
)
from opengalois.radicals.ast import (
    mul as _ast_mul,
)
from opengalois.radicals.ast import (
    neg as _ast_neg,
)
from opengalois.radicals.ast import (
    pow_int as _ast_pow_int,
)
from opengalois.radicals.ast import (
    qq as _ast_qq,
)
from opengalois.radicals.ast import (
    root as _ast_root,
)
from opengalois.radicals.ast import (
    sub as _ast_sub,
)
from opengalois.radicals.ast import (
    zeta as _ast_zeta,
)
from opengalois.radicals.schemes import deg2_quadratic_formula
from opengalois.radicals.schemes.deg5_mcclintock_depressed_monic import (
    build as _deg5_mcclintock_build,
)
from opengalois.rulesets import get_ruleset

from .algorithms.factorization import (
    _choose_zassenhaus_prime,
    _hensel_precision_from_bound,
    _modular_factorization_z,
    _zassenhaus_factor_bound_z,
    factorize_le5,
)
from .certificate import compute_input_hash
from .codec.rationals import _is_canonical_rational_str, _parse_fraction
from .models import CheckResult, VerifiedResult
from .polyops.desc_qx import _mul_desc, _mul_scalar_desc, _shift_desc, _trim_leading_zeros_desc
from .polyops.desc_zx import _primitive_integer_poly_from_QQ_desc, _trim_leading_zeros_desc_z

try:
    from importlib.resources import files as resource_files
except Exception:  # pragma: no cover
    resource_files = None  # type: ignore[assignment]


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_INT_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)$")
_INPUT_REF = "$input"

_SCHEMA_VERSION = "3.0.0"
_SCHEMA_RESOURCE = "schemas/certificate/3.0.0.json"


def _format_schema_error(err: Any) -> str:
    path = getattr(err, "absolute_path", [])
    if path:
        loc = "$" + "".join(f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in path)
    else:
        loc = "$"
    msg = getattr(err, "message", str(err))
    return f"{loc}: {msg}"


@lru_cache
def _load_schema_v300() -> dict[str, Any]:
    """Load the v3.0.0 JSON schema from package resources or repo checkout."""
    # 1) Packaged resource
    if resource_files is not None:
        try:
            p = resource_files("opengalois").joinpath(_SCHEMA_RESOURCE)
            if p.is_file():
                content = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(content, dict):
                    raise TypeError(f"The schema in {p} must be a JSON object, got {type(content)}")
                return content
        except (FileNotFoundError, ModuleNotFoundError):
            pass

    # 2) Repo checkout fallback
    from pathlib import Path  # local import
    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    p2 = repo_root / "schemas" / "certificate" / f"{_SCHEMA_VERSION}.json"
    if p2.is_file():
        content = json.loads(p2.read_text(encoding="utf-8"))
        if not isinstance(content, dict):
            raise TypeError(f"The schema in {p2} must be a JSON object, got {type(content)}")
        return content

    raise FileNotFoundError(f"Could not locate schemas/certificate/{_SCHEMA_VERSION}.json")


def _add(checks: list[CheckResult], name: str, ok: bool, details: str = "") -> None:
    checks.append(CheckResult(name, ok, details))


def _get_ref_id(x: Any) -> str | None:
    if not isinstance(x, Mapping):
        return None
    ref = x.get("ref")
    if not isinstance(ref, str) or not ref:
        return None
    return ref


def _build_scope_from_input(inp: Mapping[str, Any], coeffs_qq: list[str]) -> dict[str, Any]:
    return {
        "domain": inp["domain"],
        "variable": inp["variable"],
        "ordering": inp["ordering"],
        "degree": inp["degree"],
        "coeffs_qq": coeffs_qq,
    }


@dataclass(frozen=True)
class _V3Ctx:
    input_block: Mapping[str, Any]
    input_coeffs_qq: list[str]
    objects: Mapping[str, Any]
    checks: list[CheckResult]


def _validate_polyqq_block(
    checks: list[CheckResult],
    name_prefix: str,
    coeffs_qq: Any,
) -> tuple[bool, list[str]]:
    """Validate a PolyQQ coeff list (canonical QQ strings, len>=2, leading!=0)."""
    if not isinstance(coeffs_qq, list) or not all(isinstance(s, str) for s in coeffs_qq):
        _add(checks, f"{name_prefix}.shape", False, "coeffs_qq must be a list[str]")
        return False, []
    if len(coeffs_qq) < 2:
        _add(checks, f"{name_prefix}.len", False, "coeffs_qq must have at least 2 items")
        return False, []

    for i, s in enumerate(coeffs_qq):
        if not _is_canonical_rational_str(s):
            _add(checks, f"{name_prefix}.canonical", False,
                 f"Non-canonical rational at index {i}: {s!r}")
            return False, []
    # leading non-zero
    try:
        if _parse_fraction(coeffs_qq[0]) == 0:
            _add(checks, f"{name_prefix}.leading", False, "Leading coefficient must be non-zero")
            return False, []
    except Exception as e:  # noqa: BLE001
        _add(checks, f"{name_prefix}.parse", False, f"Failed to parse leading coefficient: {e}")
        return False, []
    return True, cast(list[str], coeffs_qq)


def _validate_mpolyqq_block(
    checks: list[CheckResult],
    name_prefix: str,
    obj: Any,
) -> bool:
    """Validate an MPolyQQ payload in canonical sparse form."""
    if not isinstance(obj, Mapping):
        _add(checks, f"{name_prefix}.shape", False, "MPolyQQ must be an object")
        return False

    nvars = obj.get("nvars")
    if not isinstance(nvars, int) or isinstance(nvars, bool) or nvars < 1:
        _add(checks, f"{name_prefix}.nvars", False, "MPolyQQ.nvars must be an int >= 1")
        return False

    terms = obj.get("terms")
    if not isinstance(terms, list):
        _add(checks, f"{name_prefix}.terms", False, "MPolyQQ.terms must be a list")
        return False

    seen: set[tuple[int, ...]] = set()
    prev_exp: tuple[int, ...] | None = None
    for i, term in enumerate(terms):
        if not isinstance(term, Mapping):
            _add(checks, f"{name_prefix}.terms[{i}]", False, "Each term must be an object")
            return False

        exp = term.get("exp")
        if not isinstance(exp, list) or len(exp) != nvars:
            _add(checks, f"{name_prefix}.terms[{i}].exp", False,
                 "Exponent vector must be a list[int] of length nvars")
            return False
        if any((not isinstance(e, int)) or isinstance(e, bool) or e < 0 for e in exp):
            _add(checks, f"{name_prefix}.terms[{i}].exp", False,
                 "Exponent entries must be ints >= 0")
            return False

        coeff = term.get("coeff_qq")
        if not isinstance(coeff, str) or not _is_canonical_rational_str(coeff):
            _add(checks, f"{name_prefix}.terms[{i}].coeff_qq", False,
                 "coeff_qq must be a canonical rational string")
            return False
        if _parse_fraction(coeff) == 0:
            _add(checks, f"{name_prefix}.terms[{i}].coeff_qq", False,
                 "Zero coefficients are not allowed in MPolyQQ terms")
            return False

        exp_t = tuple(cast(list[int], exp))
        if exp_t in seen:
            _add(checks, f"{name_prefix}.terms[{i}].exp_unique", False,
                 "Duplicate exponent vector in MPolyQQ")
            return False
        if prev_exp is not None and prev_exp <= exp_t:
            _add(checks, f"{name_prefix}.terms[{i}].order", False,
                 "MPolyQQ terms must be in descending lexicographic order")
            return False
        seen.add(exp_t)
        prev_exp = exp_t

    return True

def _validate_ratqq_value(checks: list[CheckResult], name_prefix: str, value: Any) -> bool:
    if not isinstance(value, str):
        _add(checks, f"{name_prefix}.shape", False, "value must be a string")
        return False
    if not _is_canonical_rational_str(value):
        _add(checks, f"{name_prefix}.canonical", False, f"Non-canonical rational: {value!r}")
        return False
    try:
        _parse_fraction(value)
    except Exception as e:  # noqa: BLE001
        _add(checks, f"{name_prefix}.parse", False, f"Failed to parse rational: {e}")
        return False
    return True

def _validate_intz_value(checks: list[CheckResult], name_prefix: str, value: Any) -> bool:
    if not isinstance(value, str):
        _add(checks, f"{name_prefix}.shape", False, "value must be a string")
        return False
    if not _INT_RE.fullmatch(value):
        _add(checks, f"{name_prefix}.canonical", False, f"Non-canonical integer: {value!r}")
        return False
    return True

def _validate_groupid_block(checks: list[CheckResult], name_prefix: str, obj: Any) -> bool:
    if not isinstance(obj, Mapping):
        _add(checks, f"{name_prefix}.shape", False, "GroupId must be an object")
        return False

    system = obj.get("system")
    if system != "smallgroup":
        _add(checks, f"{name_prefix}.system", False, "GroupId.system must be 'smallgroup'")
        return False

    order = obj.get("order")
    if not isinstance(order, int) or isinstance(order, bool) or order < 1:
        _add(checks, f"{name_prefix}.order", False, "GroupId.order must be an int >= 1")
        return False

    index = obj.get("index")
    if not isinstance(index, int) or isinstance(index, bool) or index < 1:
        _add(checks, f"{name_prefix}.index", False, "GroupId.index must be an int >= 1")
        return False

    alias = obj.get("alias", None)
    if alias is not None and (not isinstance(alias, str) or alias == ""):
        _add(checks, f"{name_prefix}.alias", False, 
             "GroupId.alias must be a non-empty string if present")
        return False

    return True



def _validate_radical_expr_node(
    checks: list[CheckResult],
    name_prefix: str,
    node: Any,
    *,
    ctx: _V3Ctx,
) -> bool:
    """Validate a RadicalExpr AST node (structural equality only)."""
    if not isinstance(node, Mapping):
        _add(checks, f"{name_prefix}.shape", False, "RadicalExpr AST node must be an object")
        return False

    kind = node.get("kind")
    if not isinstance(kind, str) or not kind:
        _add(checks, f"{name_prefix}.kind", False, 
             "RadicalExpr AST node must have a non-empty 'kind'")
        return False

    keys = set(node)

    if kind == "qq":
        allowed = {"kind", "value_qq", "ref"}
        extra = keys - allowed
        if extra:
            _add(checks, f"{name_prefix}.keys", False,
                 f"qq node contains unknown keys: {sorted(extra)!r}")
            return False
        has_value = "value_qq" in node
        has_ref = "ref" in node
        if has_value == has_ref:
            _add(checks, f"{name_prefix}.qq_form", False,
                 "qq node must contain exactly one of 'value_qq' or 'ref'")
            return False
        if has_value:
            return _validate_ratqq_value(checks, f"{name_prefix}.value_qq", node.get("value_qq"))
        ref = node.get("ref")
        if not isinstance(ref, str) or not ref:
            _add(checks, f"{name_prefix}.ref", False, "qq.ref must be a non-empty string")
            return False
        obj = ctx.objects.get(ref)
        if not isinstance(obj, Mapping):
            _add(checks, f"{name_prefix}.ref", False, f"qq.ref points to missing object: {ref!r}")
            return False
        if obj.get("kind") != "RatQQ":
            _add(checks, f"{name_prefix}.ref", False, "qq.ref must point to a RatQQ object")
            return False
        return _validate_ratqq_value(checks, f"objects[{ref}].value", obj.get("value"))

    if kind == "zeta":
        if keys != {"kind", "n", "k"}:
            _add(checks, f"{name_prefix}.keys", False,
                 "zeta node must contain exactly 'kind', 'n', and 'k'")
            return False
        n = node.get("n")
        k = node.get("k")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            _add(checks, f"{name_prefix}.n", False, "zeta.n must be an int >= 1")
            return False
        if not isinstance(k, int) or isinstance(k, bool) or not (0 <= k < n):
            _add(checks, f"{name_prefix}.k", False, "zeta.k must be an int with 0 <= k < n")
            return False
        return True

    if kind == "neg":
        if keys != {"kind", "arg"}:
            _add(checks, f"{name_prefix}.keys", False,
                 "neg node must contain exactly 'kind' and 'arg'")
            return False
        return _validate_radical_expr_node(checks, f"{name_prefix}.arg", node.get("arg"), ctx=ctx)

    if kind in {"add", "sub", "mul", "div"}:
        if keys != {"kind", "left", "right"}:
            _add(checks, f"{name_prefix}.keys", False,
                 f"{kind} node must contain exactly 'kind', 'left', and 'right'")
            return False
        ok_left = _validate_radical_expr_node(checks, 
                                              f"{name_prefix}.left", node.get("left"), ctx=ctx)
        ok_right = _validate_radical_expr_node(checks, 
                                               f"{name_prefix}.right", node.get("right"), ctx=ctx)
        return ok_left and ok_right

    if kind == "pow_int":
        if keys != {"kind", "base", "exp"}:
            _add(checks, f"{name_prefix}.keys", False,
                 "pow_int node must contain exactly 'kind', 'base', and 'exp'")
            return False
        exp = node.get("exp")
        if not isinstance(exp, int) or isinstance(exp, bool):
            _add(checks, f"{name_prefix}.exp", False, "pow_int.exp must be an int")
            return False
        return _validate_radical_expr_node(checks, f"{name_prefix}.base", node.get("base"), ctx=ctx)

    if kind == "root":
        if keys != {"kind", "n", "arg"}:
            _add(checks, f"{name_prefix}.keys", False,
                 "root node must contain exactly 'kind', 'n', and 'arg'")
            return False
        n = node.get("n")
        if not isinstance(n, int) or isinstance(n, bool) or n < 2:
            _add(checks, f"{name_prefix}.n", False, "root.n must be an int >= 2")
            return False
        return _validate_radical_expr_node(checks, f"{name_prefix}.arg", node.get("arg"), ctx=ctx)

    _add(checks, f"{name_prefix}.kind_known", False, f"Unknown RadicalExpr node kind: {kind!r}")
    return False


def _validate_radical_expr_block(
    checks: list[CheckResult],
    name_prefix: str,
    obj: Any,
    *,
    ctx: _V3Ctx,
) -> bool:
    if not isinstance(obj, Mapping):
        _add(checks, f"{name_prefix}.shape", False, "RadicalExpr must be an object")
        return False
    if set(obj) != {"kind", "expr"}:
        _add(checks, f"{name_prefix}.keys", False, 
             "RadicalExpr must contain exactly 'kind' and 'expr'")
        return False
    if obj.get("kind") != "RadicalExpr":
        _add(checks, f"{name_prefix}.kind", False, "RadicalExpr.kind must be 'RadicalExpr'")
        return False
    return _validate_radical_expr_node(checks, f"{name_prefix}.expr", obj.get("expr"), ctx=ctx)


def _validate_radical_expr_list_block(
    checks: list[CheckResult],
    name_prefix: str,
    obj: Any,
    *,
    ctx: _V3Ctx,
) -> bool:
    if not isinstance(obj, Mapping):
        _add(checks, f"{name_prefix}.shape", False, "RadicalExprList must be an object")
        return False
    if set(obj) != {"kind", "items"}:
        _add(checks, f"{name_prefix}.keys", False,
             "RadicalExprList must contain exactly 'kind' and 'items'")
        return False
    if obj.get("kind") != "RadicalExprList":
        _add(checks, f"{name_prefix}.kind", False,
             "RadicalExprList.kind must be 'RadicalExprList'")
        return False
    items = obj.get("items")
    if not isinstance(items, list) or not all(isinstance(x, str) and x for x in items):
        _add(checks, f"{name_prefix}.items.shape", False,
             "RadicalExprList.items must be a list[str] of non-empty ids")
        return False
    ok = True
    for j, item_id in enumerate(cast(list[str], items)):
        if item_id == _INPUT_REF:
            _add(checks, f"{name_prefix}.items[{j}]", False,
                 "RadicalExprList.items must not reference $input")
            ok = False
            continue
        item = ctx.objects.get(item_id)
        if not isinstance(item, Mapping):
            _add(checks, f"{name_prefix}.items[{j}]", False, f"Missing object id: {item_id!r}")
            ok = False
            continue
        if item.get("kind") != "RadicalExpr":
            _add(checks, f"{name_prefix}.items[{j}]", False,
                 f"Expected RadicalExpr item, got {item.get('kind')!r}")
            ok = False
            continue
        if not _validate_radical_expr_block(checks, f"objects[{item_id}]", item, ctx=ctx):
            ok = False
    return ok

def _decode_polyqq_to_fracs(ref_id: str, ctx : _V3Ctx) -> list[Fraction] | None:
    # $input
    if ref_id == _INPUT_REF:
        try:
            return [_parse_fraction(s) for s in ctx.input_coeffs_qq]
        except Exception:
            return None
    obj = ctx.objects.get(ref_id)
    if not isinstance(obj, Mapping):
        return None
    coeffs_any = obj.get("coeffs_qq")
    if not isinstance(coeffs_any, list) or not all(isinstance(x, str) for x in coeffs_any):
        return None
    try:
        return [_parse_fraction(s) for s in coeffs_any]
    except Exception:
        return None

def _decode_ratqq_to_frac(ref_id: str, ctx: _V3Ctx) -> Fraction | None:
    if ref_id == _INPUT_REF:
        return None
    obj = ctx.objects.get(ref_id)
    if not isinstance(obj, Mapping) or obj.get("kind") != "RatQQ":
        return None
    v = obj.get("value")
    if not isinstance(v, str) or not _is_canonical_rational_str(v):
        return None
    try:
        return _parse_fraction(v)
    except Exception:
        return None

def _decode_intz_to_int(ref_id: str | None, ctx: _V3Ctx) -> int | None:
    if ref_id is None:
        return None
    if ref_id == _INPUT_REF:
        return None
    obj = ctx.objects.get(ref_id)
    if not isinstance(obj, Mapping) or obj.get("kind") != "IntZ":
        return None
    v = obj.get("value")
    if not isinstance(v, str) or not _INT_RE.fullmatch(v):
        return None
    try:
        return int(v)
    except Exception:
        return None

def _decode_polyqqlist_items(ref_id: str, ctx: _V3Ctx) -> list[str] | None:
    if ref_id == _INPUT_REF:
        return None
    obj = ctx.objects.get(ref_id)
    if not isinstance(obj, Mapping) or obj.get("kind") != "PolyQQList":
        return None
    items = obj.get("items")
    if not isinstance(items, list) or not all(isinstance(x, str) and x for x in items):
        return None
    if any(x == _INPUT_REF for x in items):
        return None
    return items


def _decode_groupid_smallgroup(ref_id: str, ctx: _V3Ctx) -> tuple[int, int] | None:
    if ref_id == _INPUT_REF:
        return None
    obj = ctx.objects.get(ref_id)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return None
    if obj.get("system") != "smallgroup":
        return None
    order = obj.get("order")
    index = obj.get("index")
    if (not isinstance(order, int) or isinstance(order, bool) or order < 1 or
            not isinstance(index, int) or isinstance(index, bool) or index < 1):
        return None
    return order, index


_RESOLVABLE_SMALLGROUPS: frozenset[tuple[int, int]] = frozenset({
    (1, 1),    # Trivial
    (2, 1),    # C2
    (3, 1),    # C3
    (4, 1),    # C4
    (4, 2),    # V4
    (5, 1),    # C5
    (6, 1),    # C6
    (6, 2),    # S3
    (8, 3),    # D4
    (10, 2),   # D5
    (12, 3),   # A4
    (12, 4),   # D6
    (20, 3),   # F20
    (24, 12),  # S4
})

_NONSOLVABLE_SMALLGROUPS: frozenset[tuple[int, int]] = frozenset({
    (60, 5),   # A5
    (120, 34), # S5
})

def _require_degree_premise(
    *,
    premises: list[Mapping[str, Any]],
    poly_ref: str,
    ctx: _V3Ctx,
    expected: int | None = None,
    allowed: set[int] | None = None,
) -> tuple[int | None, str]:
    """Require and decode a matching Degree(poly_ref, n) premise.

    Premises are already verified facts (their own rule checker already passed).
    This helper only checks that the *right* premise is present for this rule.
    """
    degree_values: list[int] = []

    for prem in premises:
        if prem.get("pred") != "Degree":
            continue
        args_any = prem.get("args")
        if not isinstance(args_any, list) or len(args_any) != 2:
            continue
        p_ref = _get_ref_id(args_any[0])
        n_ref = _get_ref_id(args_any[1])
        if p_ref != poly_ref:
            continue
        if n_ref is None:
            return None, "E_PREMISE: malformed Degree premise (arg1 ref)"
        n = _decode_intz_to_int(n_ref, ctx)
        if n is None:
            return None, "E_PREMISE: cannot decode IntZ from Degree premise"
        degree_values.append(n)

    if not degree_values:
        return None, "E_PREMISE_MISSING: missing Degree premise for polynomial"

    # In a consistent proof there should not be conflicting Degree facts for same polynomial.
    uniq = sorted(set(degree_values))
    if len(uniq) != 1:
        return None, f"E_PREMISE_CONFLICT: multiple Degree premises for polynomial: {uniq}"

    n = uniq[0]
    if expected is not None and n != expected:
        return None, f"E_SIDE_CONDITION: Degree premise says {n}, expected {expected}"
    if allowed is not None and n not in allowed:
        return None, f"E_SIDE_CONDITION: Degree premise says {n}, allowed {sorted(allowed)}"
    return n, ""



def _require_irreducible_premise(
    *,
    premises: list[Mapping[str, Any]],
    poly_ref: str,
) -> tuple[bool, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        if _get_ref_id(p_args[0]) == poly_ref:
            return True, ""
    return False, "E_PREMISE_MISSING: missing IrreducibleQQ premise"


def _require_factorization_premise(
    *,
    premises: list[Mapping[str, Any]],
    poly_ref: str,
) -> tuple[tuple[str, str] | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return None, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        p_f = _get_ref_id(p_args[0])
        p_factors = _get_ref_id(p_args[1])
        p_unit = _get_ref_id(p_args[2])
        if p_f is None or p_factors is None or p_unit is None:
            return None, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise (refs)"
        if p_f == poly_ref:
            return (p_factors, p_unit), ""
    return None, "E_PREMISE_MISSING: missing FactorizationMonicQQ premise"


def _require_radical_roots_premise(
    *,
    premises: list[Mapping[str, Any]],
    poly_ref: str,
) -> tuple[str | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "RadicalRoots":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return None, "E_PREMISE_BINDING: malformed RadicalRoots premise"
        p_f = _get_ref_id(p_args[0])
        p_roots = _get_ref_id(p_args[1])
        if p_f is None or p_roots is None:
            return None, "E_PREMISE_BINDING: malformed RadicalRoots premise (refs)"
        if p_f == poly_ref:
            return p_roots, ""
    return None, "E_PREMISE_MISSING: missing RadicalRoots premise"


def _decode_radical_expr_list_payloads(
    ref_id: str,
    ctx: _V3Ctx,
) -> list[dict[str, Any]] | None:
    if ref_id == _INPUT_REF:
        return None
    obj = ctx.objects.get(ref_id)
    if not isinstance(obj, Mapping) or obj.get("kind") != "RadicalExprList":
        return None
    items = obj.get("items")
    if not isinstance(items, list) or not all(isinstance(x, str) and x for x in items):
        return None
    out: list[dict[str, Any]] = []
    for item_id in items:
        if item_id == _INPUT_REF:
            return None
        item = ctx.objects.get(item_id)
        if not isinstance(item, Mapping) or item.get("kind") != "RadicalExpr":
            return None
        out.append(dict(item))
    return out


def _qq_expr(q: Fraction) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_qq(q))


def _radical_expr_payload(expr: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "RadicalExpr", "expr": expr}


def _zeta_expr(n: int, k: int) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_zeta(n, k))


def _is_qq_zero(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "qq" and expr.get("value_qq") == "0"


def _is_qq_one(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "qq" and expr.get("value_qq") == "1"


def _neg_expr(expr: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_neg(expr))


def _add_expr(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_add(left, right))


def _sub_expr(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_sub(left, right))


def _mul_expr(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_mul(left, right))


def _div_expr(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_div(left, right))


def _root_expr(n: int, arg: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_root(n, arg))


def _pow_int_expr(base: dict[str, Any], exp: int) -> dict[str, Any]:
    return cast(dict[str, Any], _ast_pow_int(base, exp))


def _require_depressed_monic_target_premise(
    *,
    premises: list[Mapping[str, Any]],
    target_ref: str,
) -> tuple[tuple[str, Mapping[str, Any]] | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "DepressedMonicEq":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return None, "E_PREMISE_BINDING: malformed DepressedMonicEq premise"
        p_f = _get_ref_id(p_args[0])
        p_g = _get_ref_id(p_args[1])
        if p_f is None or p_g is None:
            return None, "E_PREMISE_BINDING: malformed DepressedMonicEq premise (refs)"
        if p_g == target_ref:
            return (p_f, prem), ""
    return None, "E_PREMISE_MISSING: missing DepressedMonicEq(_,g)"


def _require_depressed_monic_source_premise(
    *,
    premises: list[Mapping[str, Any]],
    source_ref: str,
) -> tuple[tuple[str, Mapping[str, Any]] | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "DepressedMonicEq":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return None, "E_PREMISE_BINDING: malformed DepressedMonicEq premise"
        p_f = _get_ref_id(p_args[0])
        p_g = _get_ref_id(p_args[1])
        if p_f is None or p_g is None:
            return None, "E_PREMISE_BINDING: malformed DepressedMonicEq premise (refs)"
        if p_f == source_ref:
            return (p_g, prem), ""
    return None, "E_PREMISE_MISSING: missing DepressedMonicEq(f,g)"


def _cardano_root_payloads_for_depressed_cubic(poly: list[Fraction]) -> list[dict[str, Any]] | None:
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 4 or poly[0] != 1 or poly[1] != 0:
        return None
    p = poly[2]
    q = poly[3]
    delta_c = q * q / 4 + p * p * p / 27

    minus_q_over_2 = _qq_expr(-q / 2)
    sqrt_delta = _root_expr(2, _qq_expr(delta_c))
    u = _root_expr(3, _add_expr(minus_q_over_2, sqrt_delta))
    v = _root_expr(3, _sub_expr(_qq_expr(-q / 2), _root_expr(2, _qq_expr(delta_c))))

    omega = _zeta_expr(3, 1)
    omega2 = _zeta_expr(3, 2)

    roots = [
        _radical_expr_payload(_add_expr(u, v)),
        _radical_expr_payload(_add_expr(_mul_expr(omega, u), _mul_expr(omega2, v))),
        _radical_expr_payload(_add_expr(_mul_expr(omega2, u), _mul_expr(omega, v))),
    ]
    return roots


def _expr_from_radical_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    expr = payload.get("expr")
    if not isinstance(expr, Mapping):
        return None
    return dict(expr)


def _quadratic_root_payloads_for_monic_coeff_exprs(
    b_expr: dict[str, Any],
    c_expr: dict[str, Any],
) -> list[dict[str, Any]]:
    disc = _sub_expr(
        _pow_int_expr(b_expr, 2),
        _mul_expr(_qq_expr(Fraction(4, 1)), c_expr),
    )
    sqrt_disc = _root_expr(2, disc)
    minus_b = _neg_expr(b_expr)
    two = _qq_expr(Fraction(2, 1))
    return [
        _radical_expr_payload(_div_expr(_add_expr(minus_b, sqrt_disc), two)),
        _radical_expr_payload(_div_expr(_sub_expr(minus_b, sqrt_disc), two)),
    ]



def _biquadratic_quartic_root_payloads(c: Fraction, e: Fraction) -> list[dict[str, Any]]:
    y_roots = _quadratic_root_payloads_for_monic_coeff_exprs(_qq_expr(c), _qq_expr(e))
    y1 = _expr_from_radical_payload(y_roots[0])
    y2 = _expr_from_radical_payload(y_roots[1])
    if y1 is None or y2 is None:
        raise ValueError("Malformed quadratic payload while building biquadratic quartic roots")
    s1 = _root_expr(2, y1)
    s2 = _root_expr(2, y2)
    return [
        _radical_expr_payload(s1),
        _radical_expr_payload(_neg_expr(s1)),
        _radical_expr_payload(s2),
        _radical_expr_payload(_neg_expr(s2)),
    ]


def _first_nonzero_resolvent_root_expr(
    resolvent_roots: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for payload in resolvent_roots:
        expr = _expr_from_radical_payload(payload)
        if expr is None:
            return None
        if not _is_qq_zero(expr):
            return expr
    return None


def _resolvent_root_exprs_zero_last(
    resolvent_roots: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    exprs: list[dict[str, Any]] = []
    for payload in resolvent_roots:
        expr = _expr_from_radical_payload(payload)
        if expr is None:
            return None
        exprs.append(expr)
    if len(exprs) != 3:
        return None
    nonzero = [expr for expr in exprs if not _is_qq_zero(expr)]
    zero = [expr for expr in exprs if _is_qq_zero(expr)]
    return nonzero + zero


def _quartic_root_payloads_ferrari_depressed(
    poly: list[Fraction],
    resolvent_roots: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 5 or poly[0] != 1 or poly[1] != 0:
        return None
    c = poly[2]
    d = poly[3]
    if len(resolvent_roots) != 3:
        return None

    if d == 0:
        s = _first_nonzero_resolvent_root_expr(resolvent_roots)
    else:
        s = _expr_from_radical_payload(resolvent_roots[0])
    if s is None:
        return None

    u = _root_expr(2, _neg_expr(s))
    c_minus_s = _sub_expr(_qq_expr(c), s)
    d_over_u = _div_expr(_qq_expr(d), u)
    alpha = _div_expr(_sub_expr(c_minus_s, d_over_u), _qq_expr(Fraction(2, 1)))
    beta = _div_expr(_add_expr(c_minus_s, d_over_u), _qq_expr(Fraction(2, 1)))

    roots1 = _quadratic_root_payloads_for_monic_coeff_exprs(_neg_expr(u), alpha)
    roots2 = _quadratic_root_payloads_for_monic_coeff_exprs(u, beta)
    return roots1 + roots2


def _quartic_root_payloads_ferrari_depressed_v2(
    poly: list[Fraction],
    resolvent_roots: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 5 or poly[0] != 1 or poly[1] != 0:
        return None
    c = poly[2]
    d = poly[3]
    e = poly[4]
    if len(resolvent_roots) != 3:
        return None

    two = _qq_expr(Fraction(2, 1))
    four = _qq_expr(Fraction(4, 1))

    if d == 0:
        disc = _sub_expr(
            _mul_expr(_qq_expr(c), _qq_expr(c)),
            _mul_expr(four, _qq_expr(e)),
        )
        sqrt_disc = _root_expr(2, disc)
        minus_c = _neg_expr(_qq_expr(c))
        y_plus = _div_expr(_add_expr(minus_c, sqrt_disc), two)
        y_minus = _div_expr(_sub_expr(minus_c, sqrt_disc), two)
        s1 = _root_expr(2, y_plus)
        s2 = _root_expr(2, y_minus)
        return [
            _radical_expr_payload(s1),
            _radical_expr_payload(_neg_expr(s1)),
            _radical_expr_payload(s2),
            _radical_expr_payload(_neg_expr(s2)),
        ]

    s = _expr_from_radical_payload(resolvent_roots[0])
    if s is None:
        return None

    u = _root_expr(2, _neg_expr(s))
    two_c = _mul_expr(two, _qq_expr(c))
    two_d_over_u = _div_expr(_mul_expr(two, _qq_expr(d)), u)
    delta1 = _sub_expr(_sub_expr(s, two_c), two_d_over_u)
    delta2 = _add_expr(_sub_expr(s, two_c), two_d_over_u)
    sqrt_delta1 = _root_expr(2, delta1)
    sqrt_delta2 = _root_expr(2, delta2)

    return [
        _radical_expr_payload(_div_expr(_add_expr(u, sqrt_delta1), two)),
        _radical_expr_payload(_div_expr(_sub_expr(u, sqrt_delta1), two)),
        _radical_expr_payload(_div_expr(_add_expr(_neg_expr(u), sqrt_delta2), two)),
        _radical_expr_payload(_div_expr(_sub_expr(_neg_expr(u), sqrt_delta2), two)),
    ]


def _quartic_root_payloads_resolvent_symmetric_depressed(
    poly: list[Fraction],
    resolvent_roots: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 5 or poly[0] != 1 or poly[1] != 0:
        return None
    d = poly[3]
    if len(resolvent_roots) != 3:
        return None

    if d == 0:
        exprs = _resolvent_root_exprs_zero_last(resolvent_roots)
        if exprs is None or len(exprs) != 3:
            return None
        s1, s2, s3 = exprs
        a = _root_expr(2, _neg_expr(s1))
        b = _root_expr(2, _neg_expr(s2))
        gamma = _root_expr(2, _neg_expr(s3))
    else:
        s1_n = _expr_from_radical_payload(resolvent_roots[0])
        s2_n = _expr_from_radical_payload(resolvent_roots[1])
        if s1_n is None or s2_n is None:
            return None
        s1, s2 = s1_n, s2_n
        a = _root_expr(2, _neg_expr(s1))
        b = _root_expr(2, _neg_expr(s2))
        gamma = _div_expr(_qq_expr(-d), _mul_expr(a, b))
    two = _qq_expr(Fraction(2, 1))

    return [
        _radical_expr_payload(_div_expr(_add_expr(_add_expr(a, b), gamma), two)),
        _radical_expr_payload(_div_expr(_sub_expr(_sub_expr(a, b), gamma), two)),
        _radical_expr_payload(_div_expr(_sub_expr(_sub_expr(b, a), gamma), two)),
        _radical_expr_payload(
            _div_expr(_sub_expr(_neg_expr(_add_expr(a, b)), _neg_expr(gamma)), two)),
    ]


def _distinct_refs_in_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for ref in items:
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _rule_radical_roots_QQ_deg1_trivial(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if f_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(premises=premises, poly_ref=f_ref, ctx=ctx, expected=1)
    if deg is None:
        return False, err

    poly = _decode_polyqq_to_fracs(f_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 2:
        return False, "E_SIDE_CONDITION: recomputed degree is not 1"
    a, b = poly
    if a == 0:
        return False, "E_SIDE_CONDITION: leading coefficient is zero"

    expected = [_radical_expr_payload(_qq_expr((-b) / a))]
    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, "E_MISMATCH: claimed root list does not match canonical degree-1 scheme"
    return True, ""


def _rule_radical_roots_QQ_deg2_quadratic_formula(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if f_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(premises=premises, poly_ref=f_ref, ctx=ctx, expected=2)
    if deg is None:
        return False, err
    ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=f_ref)
    if not ok_irred:
        return False, err

    poly = _decode_polyqq_to_fracs(f_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 3:
        return False, "E_SIDE_CONDITION: recomputed degree is not 2"
    a, b, c = poly
    if a == 0:
        return False, "E_SIDE_CONDITION: leading coefficient is zero"

    expected = [
        _radical_expr_payload(expr)
        for expr in deg2_quadratic_formula.build(a=a, b=b, c=c)
    ]

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, (
            "E_MISMATCH: claimed root list does not match "
            "canonical quadratic-formula scheme"
        )
    return True, ""



def _rule_radical_roots_QQ_reducible_compose(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if f_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    factorization, err = _require_factorization_premise(premises=premises, poly_ref=f_ref)
    if factorization is None:
        return False, err
    factors_ref, _unit_ref = factorization
    factor_items = _decode_polyqqlist_items(factors_ref, ctx)
    if factor_items is None:
        return False, "E_TYPE: cannot decode PolyQQList"
    if len(factor_items) < 2:
        return False, "E_SIDE_CONDITION: factorization is not reducible"

    distinct_factors = _distinct_refs_in_order(factor_items)
    roots_by_factor: dict[str, list[dict[str, Any]]] = {}
    for g_ref in distinct_factors:
        ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=g_ref)
        if not ok_irred:
            return False, err
        factor_roots_ref, err = _require_radical_roots_premise(premises=premises, poly_ref=g_ref)
        if factor_roots_ref is None:
            return False, err
        payloads = _decode_radical_expr_list_payloads(factor_roots_ref, ctx)
        if payloads is None:
            return False, f"E_TYPE: cannot decode factor RadicalExprList for {g_ref!r}"
        roots_by_factor[g_ref] = payloads

    expected: list[dict[str, Any]] = []
    for g_ref in factor_items:
        expected.extend(roots_by_factor[g_ref])

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, ("E_MISMATCH: claimed root list does not match "
                        "canonical reducible concatenation")
    return True, ""


def _rule_radical_roots_QQ_reducible_compose_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if f_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    factorization, err = _require_factorization_premise(premises=premises, poly_ref=f_ref)
    if factorization is None:
        return False, err
    factors_ref, _unit_ref = factorization
    factor_items = _decode_polyqqlist_items(factors_ref, ctx)
    if factor_items is None:
        return False, "E_TYPE: cannot decode PolyQQList"
    if len(factor_items) < 2:
        return False, "E_SIDE_CONDITION: factorization is not reducible"

    distinct_factors = _distinct_refs_in_order(factor_items)
    roots_by_factor: dict[str, list[dict[str, Any]]] = {}
    for g_ref in distinct_factors:
        factor_roots_ref, err = _require_radical_roots_premise(premises=premises, poly_ref=g_ref)
        if factor_roots_ref is None:
            return False, err
        payloads = _decode_radical_expr_list_payloads(factor_roots_ref, ctx)
        if payloads is None:
            return False, f"E_TYPE: cannot decode factor RadicalExprList for {g_ref!r}"
        roots_by_factor[g_ref] = payloads

    expected: list[dict[str, Any]] = []
    for g_ref in factor_items:
        expected.extend(roots_by_factor[g_ref])

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, (
            "E_MISMATCH: claimed root list does not match "
            "canonical reducible concatenation"
        )
    return True, ""

def _rule_radical_roots_QQ_deg3_cardano_depressed_monic(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    g_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if g_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(premises=premises, poly_ref=g_ref, ctx=ctx, expected=3)
    if deg is None:
        return False, err
    ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=g_ref)
    if not ok_irred:
        return False, err
    dep, err = _require_depressed_monic_target_premise(premises=premises, target_ref=g_ref)
    if dep is None:
        return False, err

    poly = _decode_polyqq_to_fracs(g_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 4 or poly[0] != 1 or poly[1] != 0:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed cubic"

    expected = _cardano_root_payloads_for_depressed_cubic(poly)
    if expected is None:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed cubic"
    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, "E_MISMATCH: claimed root list does not match canonical Cardano scheme"
    return True, ""

def _cardano_v2_root_payloads_for_depressed_cubic(
    poly: list[Fraction],
) -> list[dict[str, Any]] | None:
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 4 or poly[0] != 1 or poly[1] != 0:
        return None

    p = poly[2]
    q = poly[3]

    omega = _zeta_expr(3, 1)
    omega2 = _zeta_expr(3, 2)

    # Local special branch for x^3 + q.  Do not build div(0, u): for the fixed
    # Cardano choice of u, p = 0 can make u = 0, producing the undefined 0/0.
    if p == 0:
        w = _root_expr(3, _qq_expr(-q))
        return [
            _radical_expr_payload(w),
            _radical_expr_payload(_mul_expr(omega, w)),
            _radical_expr_payload(_mul_expr(omega2, w)),
        ]

    # Generic branch.  For this Cardano choice, u = 0 implies p = 0; therefore
    # the division by u is safe under the branch condition p != 0.
    delta_c = q * q / 4 + p * p * p / 27
    minus_q_over_2 = _qq_expr(-q / 2)
    sqrt_delta = _root_expr(2, _qq_expr(delta_c))
    u = _root_expr(3, _add_expr(minus_q_over_2, sqrt_delta))
    alpha_over_u = _div_expr(_qq_expr(-p / 3), u)

    return [
        _radical_expr_payload(_add_expr(u, alpha_over_u)),
        _radical_expr_payload(
            _add_expr(_mul_expr(omega, u), _mul_expr(omega2, alpha_over_u))
        ),
        _radical_expr_payload(
            _add_expr(_mul_expr(omega2, u), _mul_expr(omega, alpha_over_u))
        ),
    ]

def _rule_radical_roots_QQ_deg3_cardano_depressed_monic_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    g_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if g_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=g_ref,
        ctx=ctx,
        expected=3,
    )
    if deg is None:
        return False, err
    ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=g_ref)
    if not ok_irred:
        return False, err
    dep, err = _require_depressed_monic_target_premise(
        premises=premises,
        target_ref=g_ref,
    )
    if dep is None:
        return False, err

    poly = _decode_polyqq_to_fracs(g_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 4 or poly[0] != 1 or poly[1] != 0:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed cubic"

    expected = _cardano_v2_root_payloads_for_depressed_cubic(poly)
    if expected is None:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed cubic"
    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, "E_MISMATCH: claimed root list does not match canonical Cardano-v2 scheme"
    return True, ""

def _rule_radical_roots_QQ_lift_depressed_monic(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if f_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    dep, err = _require_depressed_monic_source_premise(premises=premises, source_ref=f_ref)
    if dep is None:
        return False, err
    g_ref, dep_fact = dep
    roots_g_ref, err = _require_radical_roots_premise(premises=premises, poly_ref=g_ref)
    if roots_g_ref is None:
        return False, err

    poly_f = _decode_polyqq_to_fracs(f_ref, ctx)
    poly_g = _decode_polyqq_to_fracs(g_ref, ctx)
    if poly_f is None or poly_g is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly_f = _trim_leading_zeros_desc(poly_f)
    poly_g = _trim_leading_zeros_desc(poly_g)
    if len(poly_f) < 2 or len(poly_g) < 2:
        return False, "E_TYPE: zero polynomial is not supported"
    if len(poly_f) != len(poly_g):
        return False, "E_PREMISE_BINDING: normalization degree mismatch"
    n = len(poly_f) - 1
    lc = poly_f[0]
    if lc == 0:
        return False, "E_TYPE: leading coefficient is zero"
    f_m = [c / lc for c in poly_f]
    t = f_m[1] / n

    roots_g = _decode_radical_expr_list_payloads(roots_g_ref, ctx)
    if roots_g is None:
        return False, "E_TYPE: cannot decode premise RadicalExprList"
    expected = []
    for payload in roots_g:
        expr = payload.get("expr")
        if not isinstance(expr, dict):
            return False, "E_TYPE: malformed RadicalExpr payload in premise"
        lifted = _sub_expr(dict(expr), _qq_expr(t))
        expected.append(_radical_expr_payload(lifted))

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, "E_MISMATCH: claimed root list does not match canonical depressed-monic lift"
    return True, ""

def _rule_irreducible_QQ_deg5_recompute(*, claim: Mapping[str, Any], evidence: Any, 
                                        fact_id: str, premises: list[Mapping[str, Any]],
                                        ctx: _V3Ctx) -> tuple[bool, str]:
    # Defensive checks (even though typing already passed)
    if claim.get("pred") != "IrreducibleQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    ref = _get_ref_id(args_any[0])
    if ref is None:
        return False, "E_TYPE: arg0 not an ObjectRef"

    p = _decode_polyqq_to_fracs(ref, ctx)
    if p is None:
        return False, "E_TYPE: cannot decode PolyQQ"

    p = _trim_leading_zeros_desc(p)
    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=ref,
        ctx=ctx,
        allowed={2, 3, 4, 5},
    )
    if deg is None:
        return False, err

    unit = p[0]
    if unit == 0:
        return False, "E_TYPE: leading coefficient is zero"
    monic_p = [c / unit for c in p]

    try:
        facs = factorize_le5(monic_p)
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: factorize_le5 raised: {e}"

    facs = [_trim_leading_zeros_desc(f) for f in facs if f]
    monic_p = _trim_leading_zeros_desc(monic_p)

    ok = (len(facs) == 1 and facs[0] == monic_p)
    if not ok:
        return False, "E_NOT_IRREDUCIBLE: non-trivial factorization found"
    return True, ""

def _rule_factorization_QQ_monic(*, claim: Mapping[str, Any], fact_id: str, evidence: Any,
                                 premises: list[Mapping[str, Any]],
                                 ctx: _V3Ctx) -> tuple[bool, str]:
    _ = premises
    if claim.get("pred") != "FactorizationMonicQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 3:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    factors_ref = _get_ref_id(args_any[1])
    unit_ref = _get_ref_id(args_any[2])
    if f_ref is None or factors_ref is None or unit_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    f = _decode_polyqq_to_fracs(f_ref, ctx)
    if f is None:
        return False, "E_TYPE: cannot decode f as PolyQQ"
    f = _trim_leading_zeros_desc(f)

    items = _decode_polyqqlist_items(factors_ref, ctx)
    if items is None:
        return False, "E_TYPE: cannot decode factors as PolyQQList"
    if len(items) == 0:
        return False, "E_EMPTY_FACTORS"

    unit = _decode_ratqq_to_frac(unit_ref, ctx)
    if unit is None:
        return False, "E_TYPE: cannot decode unit as RatQQ"
    if unit == 0:
        return False, "E_UNIT_ZERO"

    try:
        prod: list[Fraction] = [Fraction(1)]
        for idx, poly_id in enumerate(items):
            g = _decode_polyqq_to_fracs(poly_id, ctx)
            if g is None:
                return False, f"E_OBJECT_REF: cannot decode factor at index {idx}: {poly_id!r}"
            g = _trim_leading_zeros_desc(g)
            if len(g) < 2:
                return False, f"E_DEG0_FACTOR: factor at index {idx} is constant"
            if g[0] != 1:
                return False, f"E_NOT_MONIC: factor at index {idx} has leading coeff {g[0]!r}"
            prod = _mul_desc(prod, g)
            prod = _trim_leading_zeros_desc(prod)

        prod = _mul_scalar_desc(prod, unit)
        prod = _trim_leading_zeros_desc(prod)
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: multiply/compare raised: {e}"

    if prod != f:
        return False, "E_PRODUCT_MISMATCH"
    return True, ""

def _rule_normalize_depressed_monic_QQ(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    # Claim: DepressedMonicEq(f: PolyQQ, g: PolyQQ)
    if claim.get("pred") != "DepressedMonicEq":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    f = _decode_polyqq_to_fracs(f_ref, ctx)
    g = _decode_polyqq_to_fracs(g_ref, ctx)
    if f is None or g is None:
        return False, "E_TYPE: cannot decode PolyQQ args"
    f = _trim_leading_zeros_desc(f)
    g = _trim_leading_zeros_desc(g)

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        allowed={2, 3, 4, 5},
    )
    if n is None:
        return False, err

    if not isinstance(evidence, Mapping):
        return False, "E_EVIDENCE: evidence must be an object"
    t_s = evidence.get("tschirnhaus_shift")
    a_s = evidence.get("monic_scale")
    if not (isinstance(t_s, str) and isinstance(a_s, str)):
        return False, "E_EVIDENCE: missing tschirnhaus_shift / monic_scale"
    if not (_is_canonical_rational_str(t_s) and _is_canonical_rational_str(a_s)):
        return False, "E_EVIDENCE: non-canonical rational in evidence"

    try:
        t = _parse_fraction(t_s)
        a = _parse_fraction(a_s)
    except Exception as e:  # noqa: BLE001
        return False, f"E_EVIDENCE: parse failed: {e}"

    if not f or f[0] == 0:
        return False, "E_TYPE: leading coefficient is zero"

    a_n = f[0]
    if a != a_n:
        return False, f"E_EVIDENCE: monic_scale mismatch (expected {a_n}, got {a})"

    # monicize
    f_m = [c / a_n for c in f]
    # computed shift t = coeff of x^(n-1) / n
    # f_m is descending: f_m[1] is coeff of x^(n-1)
    t_expected = f_m[1] / n
    if t != t_expected:
        return False, f"E_EVIDENCE: tschirnhaus_shift mismatch (expected {t_expected}, got {t})"

    try:
        g_expected = _shift_desc(f_m, -t_expected)  # p(x - t)
        g_expected = _trim_leading_zeros_desc(g_expected)
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: shift/construct raised: {e}"

    if g != g_expected:
        return False, "E_CONSTRUCTION_MISMATCH"

    # invariants on g
    g = _trim_leading_zeros_desc(g)
    if not g or g[0] != 1:
        return False, "E_NOT_MONIC"
    if len(g) != n + 1:
        return False, "E_CONSTRUCTION_MISMATCH"
    if g[1] != 0:
        return False, "E_NOT_DEPRESSED"
    return True, ""

def _rule_irreducible_QQ_deg1_trivial(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    # Claim: IrreducibleQQ(f) with deg(f)==1
    if claim.get("pred") != "IrreducibleQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    ref = _get_ref_id(args_any[0])
    if ref is None:
        return False, "E_TYPE: arg0 not an ObjectRef"

    # We rely on the Degree premise for the side condition (premise itself is already verified).
    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=ref,
        ctx=ctx,
        expected=1,
    )
    if deg is None:
        return False, err

    # Any degree-1 polynomial over Q is irreducible in Q[x].
    return True, ""

def _rule_galois_group_QQ_deg1_trivial(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    # Claim: GaloisGroup(f: PolyQQ, G: GroupId)
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=1,
    )
    if deg is None:
        return False, err

    if g_ref == _INPUT_REF:
        return False, "E_TYPE: GroupId cannot be $input"
    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 1 or obj.get("index") != 1:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(1,1)"
    return True, ""


def _require_resolvent_premise_for_poly(
    *,
    premises: list[Mapping[str, Any]],
    poly_ref: str,
) -> tuple[tuple[str, str] | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "ResolventQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return None, "E_PREMISE_BINDING: malformed ResolventQQ premise"
        r_ref = _get_ref_id(p_args[0])
        f_ref = _get_ref_id(p_args[1])
        p_ref = _get_ref_id(p_args[2])
        if r_ref is None or f_ref is None or p_ref is None:
            return None, "E_PREMISE_BINDING: malformed ResolventQQ premise (refs)"
        if f_ref == poly_ref:
            return (r_ref, p_ref), ""
    return None, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"


def _rule_radical_roots_QQ_deg4_ferrari_depressed_monic(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    g_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if g_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(premises=premises, poly_ref=g_ref, ctx=ctx, expected=4)
    if deg is None:
        return False, err
    ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=g_ref)
    if not ok_irred:
        return False, err
    dep, err = _require_depressed_monic_target_premise(premises=premises, target_ref=g_ref)
    if dep is None:
        return False, err

    res_prem, err = _require_resolvent_premise_for_poly(premises=premises, poly_ref=g_ref)
    if res_prem is None:
        return False, err
    r_ref, p_ref = res_prem
    ok, err = _check_canonical_deg4_resolvent_family_alt(ctx, p_ref)
    if not ok:
        return False, err

    roots_r_ref, err = _require_radical_roots_premise(premises=premises, poly_ref=r_ref)
    if roots_r_ref is None:
        return False, err

    poly = _decode_polyqq_to_fracs(g_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 5 or poly[0] != 1 or poly[1] != 0:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed quartic"

    resolvent_roots = _decode_radical_expr_list_payloads(roots_r_ref, ctx)
    if resolvent_roots is None:
        return False, "E_TYPE: cannot decode RadicalExprList for resolvent roots"

    expected = _quartic_root_payloads_ferrari_depressed(poly, resolvent_roots)
    if expected is None:
        return False, (
            "E_SIDE_CONDITION: expected a monic depressed"
            " quartic and a cubic resolvent root list"
        )

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, (
            "E_MISMATCH: claimed root list"
            " does not match canonical quartic Ferrari scheme"
        )
    return True, ""


def _rule_radical_roots_QQ_deg4_ferrari_depressed_monic_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    g_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if g_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(premises=premises, poly_ref=g_ref, ctx=ctx, expected=4)
    if deg is None:
        return False, err
    ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=g_ref)
    if not ok_irred:
        return False, err
    dep, err = _require_depressed_monic_target_premise(premises=premises, target_ref=g_ref)
    if dep is None:
        return False, err

    res_prem, err = _require_resolvent_premise_for_poly(premises=premises, poly_ref=g_ref)
    if res_prem is None:
        return False, err
    r_ref, p_ref = res_prem
    ok, err = _check_canonical_deg4_resolvent_family_alt(ctx, p_ref)
    if not ok:
        return False, err

    roots_r_ref, err = _require_radical_roots_premise(premises=premises, poly_ref=r_ref)
    if roots_r_ref is None:
        return False, err

    poly = _decode_polyqq_to_fracs(g_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 5 or poly[0] != 1 or poly[1] != 0:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed quartic"

    resolvent_roots = _decode_radical_expr_list_payloads(roots_r_ref, ctx)
    if resolvent_roots is None:
        return False, "E_TYPE: cannot decode RadicalExprList for resolvent roots"

    expected = _quartic_root_payloads_ferrari_depressed_v2(poly, resolvent_roots)
    if expected is None:
        return False, (
            "E_SIDE_CONDITION: expected a monic depressed"
            " quartic and a cubic resolvent root list"
        )

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, (
            "E_MISMATCH: claimed root list"
            " does not match canonical quartic Ferrari-v2 scheme"
        )
    return True, ""


def _rule_radical_roots_QQ_deg4_resolvent_symmetric_depressed_monic(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    g_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if g_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(premises=premises, poly_ref=g_ref, ctx=ctx, expected=4)
    if deg is None:
        return False, err
    ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=g_ref)
    if not ok_irred:
        return False, err
    dep, err = _require_depressed_monic_target_premise(premises=premises, target_ref=g_ref)
    if dep is None:
        return False, err

    res_prem, err = _require_resolvent_premise_for_poly(premises=premises, poly_ref=g_ref)
    if res_prem is None:
        return False, err
    r_ref, p_ref = res_prem
    ok, err = _check_canonical_deg4_resolvent_family_alt(ctx, p_ref)
    if not ok:
        return False, err

    roots_r_ref, err = _require_radical_roots_premise(premises=premises, poly_ref=r_ref)
    if roots_r_ref is None:
        return False, err

    poly = _decode_polyqq_to_fracs(g_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 5 or poly[0] != 1 or poly[1] != 0:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed quartic"

    resolvent_roots = _decode_radical_expr_list_payloads(roots_r_ref, ctx)
    if resolvent_roots is None:
        return False, "E_TYPE: cannot decode RadicalExprList for resolvent roots"

    expected = _quartic_root_payloads_resolvent_symmetric_depressed(poly, resolvent_roots)
    if expected is None:
        return False, (
            "E_SIDE_CONDITION: expected a monic depressed quartic "
            "and a cubic resolvent root list"
        )

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, (
            "E_MISMATCH: claimed root list does not match canonical "
            "quartic symmetric-resolvent scheme"
        )
    return True, ""

def _rule_degree_QQ(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = premises
    # Claim: Degree(f: PolyQQ, n: IntZ)
    if claim.get("pred") != "Degree":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    n_ref = _get_ref_id(args_any[1])
    if f_ref is None or n_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    f = _decode_polyqq_to_fracs(f_ref, ctx)
    if f is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    f = _trim_leading_zeros_desc(f)
    deg = len(f) - 1

    n = _decode_intz_to_int(n_ref, ctx)
    if n is None:
        return False, "E_TYPE: cannot decode IntZ"
    if n < 0:
        return False, "E_TYPE: degree must be non-negative"

    if n != deg:
        return False, f"E_MISMATCH: claimed degree {n} != recomputed degree {deg}"
    return True, ""

def _rule_galois_group_QQ_deg2_C2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    # Claim: GaloisGroup(f: PolyQQ, G: GroupId)
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    # Premise 1: Degree(f, 2)
    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=2,
    )
    if deg is None:
        # _require_degree_premise ya devuelve errores estables
        return False, err

    # Premise 2: IrreducibleQQ(f)
    found_irred = False
    for prem in premises:
        if prem.get("pred") != "IrreducibleQQ":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_ref = _get_ref_id(p_args[0])
        if p_ref is None:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise (arg0 ref)"
        if p_ref == f_ref:
            found_irred = True
            break
    if not found_irred:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ premise for polynomial"

    # Decode/validate GroupId
    if g_ref == _INPUT_REF:
        return False, "E_TYPE: GroupId cannot be $input"
    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"

    # Must be SmallGroup(2,1) == C2
    if obj.get("order") != 2 or obj.get("index") != 1:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(2,1)"
    return True, ""

def _det_fraction_matrix(a: list[list[Fraction]]) -> Fraction:
    """Compute det(A) exactly over Q using Gaussian elimination with Fractions."""
    n = len(a)
    if n == 0:
        return Fraction(1)
    if any(len(row) != n for row in a):
        raise ValueError("det: matrix must be square")

    m = [row[:] for row in a]
    det = Fraction(1)
    sign = 1

    for i in range(n):
        piv = None
        for r in range(i, n):
            if m[r][i] != 0:
                piv = r
                break
        if piv is None:
            return Fraction(0)
        if piv != i:
            m[i], m[piv] = m[piv], m[i]
            sign *= -1
        pivot = m[i][i]
        det *= pivot
        for r in range(i + 1, n):
            if m[r][i] == 0:
                continue
            factor = m[r][i] / pivot
            for c in range(i, n):
                m[r][c] -= factor * m[i][c]
    return det * sign


def _poly_derivative_desc(p: list[Fraction]) -> list[Fraction]:
    """Derivative of a polynomial in descending-degree coefficient order."""
    p = _trim_leading_zeros_desc(p)
    deg = len(p) - 1
    if deg <= 0:
        return [Fraction(0)]
    out: list[Fraction] = []
    for i, a in enumerate(p[:-1]):
        out.append(a * (deg - i))
    return _trim_leading_zeros_desc(out) or [Fraction(0)]


def _resultant_sylvester_desc(f: list[Fraction], g: list[Fraction]) -> Fraction:
    """Compute Res(f,g) via Sylvester determinant (exact over Q)."""
    f = _trim_leading_zeros_desc(f)
    g = _trim_leading_zeros_desc(g)
    mdeg = len(f) - 1
    ndeg = len(g) - 1
    if mdeg < 0 or ndeg < 0:
        return Fraction(0)
    if (mdeg == 0 and f[0] == 0) or (ndeg == 0 and g[0] == 0):
        return Fraction(0)

    size = mdeg + ndeg
    S: list[list[Fraction]] = []
    for i in range(ndeg):
        row = [Fraction(0)] * size
        row[i : i + (mdeg + 1)] = f
        S.append(row)
    for i in range(mdeg):
        row = [Fraction(0)] * size
        row[i : i + (ndeg + 1)] = g
        S.append(row)

    return _det_fraction_matrix(S)


def _discriminant_QQ_desc(f: list[Fraction]) -> Fraction:
    """Compute Disc(f) in QQ via Disc = (-1)**(n*(n-1)/2) * Res(f,f') / lc(f).

    Convention: for deg(f)=1, return 1.
    """
    f = _trim_leading_zeros_desc(f)
    n = len(f) - 1
    if n < 0:
        raise ValueError("discriminant: zero polynomial")
    if n == 0:
        return Fraction(0)
    if n == 1:
        return Fraction(1)
    lc = f[0]
    if lc == 0:
        raise ValueError("discriminant: leading coefficient is zero")
    fp = _poly_derivative_desc(f)
    res = _resultant_sylvester_desc(f, fp)
    sgn = -1 if ((n * (n - 1) // 2) % 2) else 1
    return Fraction(sgn) * (res / lc)


def _rule_disc_QQ_compute(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    _ = premises

    # Claim: Discriminant(f: PolyQQ, D: RatQQ)
    if claim.get("pred") != "Discriminant":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"

    f_ref = _get_ref_id(args_any[0])
    d_ref = _get_ref_id(args_any[1])
    if f_ref is None or d_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    f = _decode_polyqq_to_fracs(f_ref, ctx)
    if f is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    f = _trim_leading_zeros_desc(f)
    n = len(f) - 1
    if n < 1:
        return False, "E_TYPE: expected deg(f) >= 1"
    
    # Hard-limit to avoid DoS
    if n > 5:
        return False, f"E_BOUNDS: degree {n} exceeds verifier limits (max 5) for disc_QQ_compute"

    d_claimed = _decode_ratqq_to_frac(d_ref, ctx)
    if d_claimed is None:
        return False, "E_TYPE: cannot decode RatQQ"

    try:
        d_expected = _discriminant_QQ_desc(f)
    except Exception as e:  # noqa: BLE001
        return False, "E_EXCEPTION: discriminant computation failed: " + str(e)

    if d_expected != d_claimed:
        return False, "E_MISMATCH: claimed " + str(d_claimed) + " != expected " + str(d_expected)
    return True, ""

def _rule_sqrt_QQ_check(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    _ = premises

    # Claim: SqrtQQ(q: RatQQ, k: RatQQ)
    if claim.get("pred") != "SqrtQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"

    q_ref = _get_ref_id(args_any[0])
    k_ref = _get_ref_id(args_any[1])
    if q_ref is None or k_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    q = _decode_ratqq_to_frac(q_ref, ctx)
    if q is None:
        return False, "E_TYPE: cannot decode q as RatQQ"
    k = _decode_ratqq_to_frac(k_ref, ctx)
    if k is None:
        return False, "E_TYPE: cannot decode k as RatQQ"

    if k * k != q:
        return False, "E_MISMATCH: k^2 != q"
    return True, ""


def _rule_is_square_QQ_lift(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    _ = ctx

    # Claim: IsSquareQQ(q: RatQQ)
    if claim.get("pred") != "IsSquareQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    q_ref = _get_ref_id(args_any[0])
    if q_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    found = False
    for prem in premises:
        if prem.get("pred") != "SqrtQQ":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed SqrtQQ premise"
        p_q = _get_ref_id(p_args[0])
        if p_q is None:
            return False, "E_PREMISE_BINDING: malformed SqrtQQ premise (q ref)"
        if p_q == q_ref:
            found = True
            break

    if not found:
        return False, "E_PREMISE_MISSING: missing SqrtQQ(q,k) premise"
    return True, ""

def _is_square_int(n: int) -> bool:
    """Return True iff n is a perfect square in Z."""
    if n < 0:
        return False
    import math
    r = math.isqrt(n)
    return r * r == n


def _rule_nonsquare_QQ_isqrt(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    _ = premises

    # Claim: NonSquareQQ(q: RatQQ)
    if claim.get("pred") != "NonSquareQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    q_ref = _get_ref_id(args_any[0])
    if q_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    q = _decode_ratqq_to_frac(q_ref, ctx)
    if q is None:
        return False, "E_TYPE: cannot decode RatQQ"

    # Fraction is reduced with positive denominator.
    a = q.numerator
    b = q.denominator
    if a < 0:
        return True, ""

    if _is_square_int(a) and _is_square_int(b):
        return False, "E_MISMATCH: q is a square in QQ"
    return True, ""

def _parse_evidence_int(value: Any, field: str) -> tuple[int | None, str]:
    if not isinstance(value, str) or not _INT_RE.fullmatch(value):
        return None, f"E_EVIDENCE: {field} must be a canonical integer string"
    try:
        return int(value), ""
    except Exception as exc:  # noqa: BLE001
        return None, f"E_EVIDENCE: could not parse {field}: {exc}"


def _rule_nonsquare_QQ_isqrt_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = premises

    if claim.get("pred") != "NonSquareQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    q_ref = _get_ref_id(args_any[0])
    if q_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    q = _decode_ratqq_to_frac(q_ref, ctx)
    if q is None:
        return False, "E_TYPE: cannot decode RatQQ"

    a = q.numerator
    b = q.denominator
    if a >= 0 and _is_square_int(a) and _is_square_int(b):
        return False, "E_MISMATCH: q is a square in QQ"

    if not isinstance(evidence, Mapping):
        return False, "E_EVIDENCE: evidence must be an object"
    obstruction = evidence.get("obstruction")
    if not isinstance(obstruction, Mapping):
        return False, "E_EVIDENCE: missing obstruction object"

    kind = obstruction.get("kind")

    if a < 0:
        if dict(obstruction) != {"kind": "negative"}:
            return False, "E_EVIDENCE: negative obstruction must be exactly {'kind': 'negative'}"
        return True, ""

    if kind != "integer_isqrt_interval":
        return False, "E_EVIDENCE: expected integer_isqrt_interval obstruction"

    allowed = {"kind", "side", "lower_root", "lower_square", "upper_root", "upper_square"}
    extra = set(obstruction) - allowed
    missing = allowed - set(obstruction)
    if extra or missing:
        return False, (
            "E_EVIDENCE: integer_isqrt_interval obstruction must contain exactly "
            "kind, side, lower_root, lower_square, upper_root, upper_square"
        )

    side = obstruction.get("side")
    if side == "numerator":
        n = a
    elif side == "denominator":
        n = b
    else:
        return False, "E_EVIDENCE: side must be 'numerator' or 'denominator'"

    if n < 0:
        return False, "E_EVIDENCE: interval obstruction expects a non-negative integer"

    lower_root, err = _parse_evidence_int(obstruction.get("lower_root"), "lower_root")
    if lower_root is None:
        return False, err
    lower_square, err = _parse_evidence_int(obstruction.get("lower_square"), "lower_square")
    if lower_square is None:
        return False, err
    upper_root, err = _parse_evidence_int(obstruction.get("upper_root"), "upper_root")
    if upper_root is None:
        return False, err
    upper_square, err = _parse_evidence_int(obstruction.get("upper_square"), "upper_square")
    if upper_square is None:
        return False, err

    import math
    r = math.isqrt(n)

    if lower_root != r:
        return False, "E_EVIDENCE: lower_root mismatch"
    if upper_root != r + 1:
        return False, "E_EVIDENCE: upper_root mismatch"
    if lower_square != r * r:
        return False, "E_EVIDENCE: lower_square mismatch"
    if upper_square != (r + 1) * (r + 1):
        return False, "E_EVIDENCE: upper_square mismatch"
    if not (lower_square < n < upper_square):
        return False, "E_EVIDENCE: interval does not prove non-squarehood"

    return True, ""


def _rule_disc_square_QQ_lift(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    _ = ctx

    # Claim: DiscSquareQQ(f: PolyQQ)
    if claim.get("pred") != "DiscSquareQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    if f_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    d_ref: str | None = None
    for prem in premises:
        if prem.get("pred") != "Discriminant":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed Discriminant premise"
        p_f = _get_ref_id(p_args[0])
        p_d = _get_ref_id(p_args[1])
        if p_f is None or p_d is None:
            return False, "E_PREMISE_BINDING: malformed Discriminant premise (refs)"
        if p_f == f_ref:
            d_ref = p_d
            break
    if d_ref is None:
        return False, "E_PREMISE_MISSING: missing Discriminant(f,D) premise"

    found_sq = False
    for prem in premises:
        if prem.get("pred") != "IsSquareQQ":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IsSquareQQ premise"
        p_q = _get_ref_id(p_args[0])
        if p_q is None:
            return False, "E_PREMISE_BINDING: malformed IsSquareQQ premise (ref)"
        if p_q == d_ref:
            found_sq = True
            break
    if not found_sq:
        return False, "E_PREMISE_MISSING: missing IsSquareQQ(D) premise for discriminant"
    return True, ""


def _rule_disc_nonsquare_QQ_lift(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    _ = ctx

    # Claim: DiscNonSquareQQ(f: PolyQQ)
    if claim.get("pred") != "DiscNonSquareQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    if f_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    d_ref: str | None = None
    for prem in premises:
        if prem.get("pred") != "Discriminant":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed Discriminant premise"
        p_f = _get_ref_id(p_args[0])
        p_d = _get_ref_id(p_args[1])
        if p_f is None or p_d is None:
            return False, "E_PREMISE_BINDING: malformed Discriminant premise (refs)"
        if p_f == f_ref:
            d_ref = p_d
            break
    if d_ref is None:
        return False, "E_PREMISE_MISSING: missing Discriminant(f,D) premise"

    found_ns = False
    for prem in premises:
        if prem.get("pred") != "NonSquareQQ":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed NonSquareQQ premise"
        p_q = _get_ref_id(p_args[0])
        if p_q is None:
            return False, "E_PREMISE_BINDING: malformed NonSquareQQ premise (ref)"
        if p_q == d_ref:
            found_ns = True
            break
    if not found_ns:
        return False, "E_PREMISE_MISSING: missing NonSquareQQ(D) premise for discriminant"
    return True, ""

def _rule_galois_group_QQ_deg3_C3(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    # Degree(f,3)
    found_deg = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "Degree":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed Degree premise"
        p_f = _get_ref_id(p_args[0])
        p_n = _get_ref_id(p_args[1])
        if p_f is None or p_n is None:
            return False, "E_PREMISE_BINDING: malformed Degree premise (refs)"
        if p_f != f_ref:
            continue
        obj = ctx.objects.get(p_n)
        if not isinstance(obj, Mapping) or obj.get("kind") != "IntZ" or obj.get("value") != "3":
            return False, "E_PREMISE_BINDING: Degree must be IntZ('3')"
        found_deg = True
        break
    if not found_deg:
        return False, "E_PREMISE_MISSING: missing Degree(f,3)"

    # IrreducibleQQ(f)
    found_irred = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_f = _get_ref_id(p_args[0])
        if p_f == f_ref:
            found_irred = True
            break
    if not found_irred:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"

    # DiscSquareQQ(f)
    found_disc = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "DiscSquareQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed DiscSquareQQ premise"
        p_f = _get_ref_id(p_args[0])
        if p_f == f_ref:
            found_disc = True
            break
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscSquareQQ(f)"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 3 or obj.get("index") != 1:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(3,1)"
    return True, ""


def _rule_galois_group_QQ_deg3_S3(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    # Degree(f,3)
    found_deg = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "Degree":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed Degree premise"
        p_f = _get_ref_id(p_args[0])
        p_n = _get_ref_id(p_args[1])
        if p_f is None or p_n is None:
            return False, "E_PREMISE_BINDING: malformed Degree premise (refs)"
        if p_f != f_ref:
            continue
        obj = ctx.objects.get(p_n)
        if not isinstance(obj, Mapping) or obj.get("kind") != "IntZ" or obj.get("value") != "3":
            return False, "E_PREMISE_BINDING: Degree must be IntZ('3')"
        found_deg = True
        break
    if not found_deg:
        return False, "E_PREMISE_MISSING: missing Degree(f,3)"

    # IrreducibleQQ(f)
    found_irred = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_f = _get_ref_id(p_args[0])
        if p_f == f_ref:
            found_irred = True
            break
    if not found_irred:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"

    # DiscNonSquareQQ(f)
    found_disc = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "DiscNonSquareQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed DiscNonSquareQQ premise"
        p_f = _get_ref_id(p_args[0])
        if p_f == f_ref:
            found_disc = True
            break
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscNonSquareQQ(f)"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 6 or obj.get("index") != 2:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(6,2)"
    return True, ""

def _is_fixed_mpolyqq_x1x2_plus_x3x4(ref: str, ctx: _V3Ctx) -> bool:
    """Return True iff ref resolves to the canonical MPolyQQ for x1*x2 + x3*x4."""
    if ref == _INPUT_REF:
        return False
    obj = ctx.objects.get(ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "MPolyQQ":
        return False
    if obj.get("nvars") != 4:
        return False
    terms = obj.get("terms")
    expected_terms = [
        {"exp": [1, 1, 0, 0], "coeff_qq": "1"},
        {"exp": [0, 0, 1, 1], "coeff_qq": "1"},
    ]
    return terms == expected_terms


def _is_fixed_mpolyqq_x1plusx2_times_x3plusx4(ref: str, ctx: _V3Ctx) -> bool:
    """Return True iff ref resolves to the canonical MPolyQQ for (x1+x2)(x3+x4)."""
    if ref == _INPUT_REF:
        return False
    obj = ctx.objects.get(ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "MPolyQQ":
        return False
    if obj.get("nvars") != 4:
        return False
    terms = obj.get("terms")
    expected_terms = [
        {"exp": [1, 0, 1, 0], "coeff_qq": "1"},
        {"exp": [1, 0, 0, 1], "coeff_qq": "1"},
        {"exp": [0, 1, 1, 0], "coeff_qq": "1"},
        {"exp": [0, 1, 0, 1], "coeff_qq": "1"},
    ]
    return terms == expected_terms


def _rule_resolvent_QQ_compute_deg4_cubic_x1x2_plus_x3x4(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "ResolventQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 3:
        return False, "E_TYPE: arity"
    r_ref = _get_ref_id(args_any[0])
    f_ref = _get_ref_id(args_any[1])
    p_ref = _get_ref_id(args_any[2])
    if r_ref is None or f_ref is None or p_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=4,
    )
    if deg is None:
        return False, err

    r_poly = _decode_polyqq_to_fracs(r_ref, ctx)
    f_poly = _decode_polyqq_to_fracs(f_ref, ctx)
    if r_poly is None or f_poly is None:
        return False, "E_TYPE: cannot decode PolyQQ args"
    r_poly = _trim_leading_zeros_desc(r_poly)
    f_poly = _trim_leading_zeros_desc(f_poly)
    if len(f_poly) != 5 or not f_poly or f_poly[0] == 0:
        return False, "E_SIDE_CONDITION: decoded polynomial is not quartic"

    if not _is_fixed_mpolyqq_x1x2_plus_x3x4(p_ref, ctx):
        return False, "E_P_MISMATCH: expected canonical MPolyQQ for x1*x2 + x3*x4"

    try:
        lc = f_poly[0]
        f_m = [c / lc for c in f_poly]
        a, b, c, d = f_m[1], f_m[2], f_m[3], f_m[4]
        r_expected = _trim_leading_zeros_desc(
            [Fraction(1), -b, a * c - Fraction(4) * d, -(a * a * d + c * c - Fraction(4) * b * d)]
        )
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: recomputation raised: {e}"

    if r_poly != r_expected:
        return False, "E_MISMATCH"
    return True, ""


def _rule_resolvent_QQ_compute_deg4_cubic_x1plusx2_times_x3plusx4(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "ResolventQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 3:
        return False, "E_TYPE: arity"
    r_ref = _get_ref_id(args_any[0])
    f_ref = _get_ref_id(args_any[1])
    p_ref = _get_ref_id(args_any[2])
    if r_ref is None or f_ref is None or p_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=4,
    )
    if deg is None:
        return False, err

    r_poly = _decode_polyqq_to_fracs(r_ref, ctx)
    f_poly = _decode_polyqq_to_fracs(f_ref, ctx)
    if r_poly is None or f_poly is None:
        return False, "E_TYPE: cannot decode PolyQQ args"
    r_poly = _trim_leading_zeros_desc(r_poly)
    f_poly = _trim_leading_zeros_desc(f_poly)
    if len(f_poly) != 5 or not f_poly or f_poly[0] == 0:
        return False, "E_SIDE_CONDITION: decoded polynomial is not quartic"

    if not _is_fixed_mpolyqq_x1plusx2_times_x3plusx4(p_ref, ctx):
        return False, "E_P_MISMATCH: expected canonical MPolyQQ for (x1+x2)(x3+x4)"

    try:
        lc = f_poly[0]
        f_m = [coeff / lc for coeff in f_poly]
        a, b, c, d = f_m[1], f_m[2], f_m[3], f_m[4]
        r_expected = _trim_leading_zeros_desc(
            [Fraction(1), Fraction(-2) * b, b * b + a * c - Fraction(4) * d,
             a * a * d - a * b * c + c * c]
        )
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: recomputation raised: {e}"

    if r_poly != r_expected:
        return False, "E_MISMATCH"
    return True, ""

_CANONICAL_DEG4_RESOLVENT_MPOLY = {
    "kind": "MPolyQQ",
    "nvars": 4,
    "terms": [
        {"exp": [1, 1, 0, 0], "coeff_qq": "1"},
        {"exp": [0, 0, 1, 1], "coeff_qq": "1"},
    ],
}

_CANONICAL_DEG4_RESOLVENT_MPOLY_ALT = {
    "kind": "MPolyQQ",
    "nvars": 4,
    "terms": [
        {"exp": [1, 0, 1, 0], "coeff_qq": "1"},
        {"exp": [1, 0, 0, 1], "coeff_qq": "1"},
        {"exp": [0, 1, 1, 0], "coeff_qq": "1"},
        {"exp": [0, 1, 0, 1], "coeff_qq": "1"},
    ],
}


def _check_canonical_deg4_resolvent_family(ctx: _V3Ctx, p_ref: str | None) -> tuple[bool, str]:
    if p_ref is None:
        return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
    p_obj = ctx.objects.get(p_ref)
    if not isinstance(p_obj, Mapping):
        return False, "E_TYPE: missing MPolyQQ object for resolvent family"
    if dict(p_obj) != _CANONICAL_DEG4_RESOLVENT_MPOLY:
        return False, "E_BAD_RESOLVENT_FAMILY: expected p = x1*x2 + x3*x4"
    return True, ""


def _check_canonical_deg4_resolvent_family_alt(ctx: _V3Ctx, p_ref: str | None) -> tuple[bool, str]:
    if p_ref is None:
        return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
    p_obj = ctx.objects.get(p_ref)
    if not isinstance(p_obj, Mapping):
        return False, "E_TYPE: missing MPolyQQ object for resolvent family"
    if dict(p_obj) != _CANONICAL_DEG4_RESOLVENT_MPOLY_ALT:
        return False, "E_BAD_RESOLVENT_FAMILY: expected p = (x1+x2)(x3+x4)"
    return True, ""


def _rule_galois_group_QQ_deg4_S4(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=4,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc = False
    resolvent_ref = None
    p_ref = None

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_irred_f = True
        elif pred == "DiscNonSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscNonSquareQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_disc = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            r_ref = _get_ref_id(p_args[0])
            f_ref_prem = _get_ref_id(p_args[1])
            p_candidate = _get_ref_id(p_args[2])
            if f_ref_prem == f_ref:
                resolvent_ref = r_ref
                p_ref = p_candidate

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscNonSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg4_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    found_irred_r = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_poly = _get_ref_id(p_args[0])
        if p_poly == resolvent_ref:
            found_irred_r = True
            break

    if not found_irred_r:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(R) for the same resolvent"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 24 or obj.get("index") != 12:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(24,12)"
    return True, ""


def _rule_galois_group_QQ_deg4_A4(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=4,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc = False
    resolvent_ref = None
    p_ref = None

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_irred_f = True
        elif pred == "DiscSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscSquareQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_disc = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            r_ref = _get_ref_id(p_args[0])
            f_ref_prem = _get_ref_id(p_args[1])
            p_candidate = _get_ref_id(p_args[2])
            if f_ref_prem == f_ref:
                resolvent_ref = r_ref
                p_ref = p_candidate

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg4_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    found_irred_r = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_poly = _get_ref_id(p_args[0])
        if p_poly == resolvent_ref:
            found_irred_r = True
            break

    if not found_irred_r:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(R) for the same resolvent"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 12 or obj.get("index") != 3:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(12,3)"
    return True, ""

def _rule_galois_group_QQ_deg4_V4(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=4,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc = False
    resolvent_ref = None
    p_ref = None
    factor_list_ref = None
    unit_ref = None

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_irred_f = True
        elif pred == "DiscSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscSquareQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_disc = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            r_ref = _get_ref_id(p_args[0])
            f_ref_prem = _get_ref_id(p_args[1])
            p_candidate = _get_ref_id(p_args[2])
            if f_ref_prem == f_ref:
                resolvent_ref = r_ref
                p_ref = p_candidate
        elif pred == "FactorizationMonicQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
            r_ref = _get_ref_id(p_args[0])
            factors_ref = _get_ref_id(p_args[1])
            unit_candidate = _get_ref_id(p_args[2])
            # binding to R is checked after R is known
            if r_ref is not None:
                factor_list_ref = factors_ref if factor_list_ref is None else factor_list_ref
                unit_ref = unit_candidate if unit_ref is None else unit_ref

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg4_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    # locate the factorization premise bound to the same R
    bound_factor_list_ref = None
    bound_unit_ref = None
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        r_ref = _get_ref_id(p_args[0])
        if r_ref == resolvent_ref:
            bound_factor_list_ref = _get_ref_id(p_args[1])
            bound_unit_ref = _get_ref_id(p_args[2])
            break

    if bound_factor_list_ref is None or bound_unit_ref is None:
        return False, (
            "E_PREMISE_MISSING: missing FactorizationMonicQQ(R, factors, unit) "
            "for the same resolvent"
        )

    list_obj = ctx.objects.get(bound_factor_list_ref)
    unit_obj = ctx.objects.get(bound_unit_ref)
    if not isinstance(list_obj, Mapping) or list_obj.get("kind") != "PolyQQList":
        return False, "E_TYPE: cannot decode PolyQQList"
    if not isinstance(unit_obj, Mapping) or unit_obj.get("kind") != "RatQQ":
        return False, "E_TYPE: cannot decode RatQQ unit"

    if unit_obj.get("value") != "1":
        return False, "E_BAD_FACTORIZATION: expected unit = 1"

    items = list_obj.get("items")
    if not isinstance(items, list) or len(items) != 3 or not all(isinstance(x, str) and x for 
                                                                 x in items):
        return False, "E_BAD_FACTORIZATION: expected exactly three factor refs"

    for ref in items:
        f_obj = ctx.objects.get(ref)
        if not isinstance(f_obj, Mapping) or f_obj.get("kind") != "PolyQQ":
            return False, "E_TYPE: factor is not a PolyQQ"
        coeffs = f_obj.get("coeffs_qq")
        if not isinstance(coeffs, list) or len(coeffs) != 2:
            return False, "E_BAD_FACTORIZATION: factor is not linear"
        if coeffs[0] != "1":
            return False, "E_BAD_FACTORIZATION: factor is not monic"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 4 or obj.get("index") != 2:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(4,2)"
    return True, ""

def _rule_galois_group_QQ_deg4_C4(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=4,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc_branch = False
    delta_ref = None
    resolvent_ref = None
    p_ref = None
    factor_list_ref = None
    unit_ref = None
    is_square_refs = []

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            if _get_ref_id(p_args[0]) == f_ref:
                found_irred_f = True
        elif pred == "Discriminant":
            if not isinstance(p_args, list) or len(p_args) != 2:
                return False, "E_PREMISE_BINDING: malformed Discriminant premise"
            if _get_ref_id(p_args[0]) == f_ref:
                delta_ref = _get_ref_id(p_args[1])
        elif pred == "DiscNonSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscNonSquareQQ premise"
            if _get_ref_id(p_args[0]) == f_ref:
                found_disc_branch = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            if _get_ref_id(p_args[1]) == f_ref:
                resolvent_ref = _get_ref_id(p_args[0])
                p_ref = _get_ref_id(p_args[2])
        elif pred == "FactorizationMonicQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
            if resolvent_ref is None:
                pass
            # binding checked later against R
        elif pred == "IsSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IsSquareQQ premise"
            rat_ref = _get_ref_id(p_args[0])
            if rat_ref is not None:
                is_square_refs.append(rat_ref)

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if delta_ref is None:
        return False, "E_PREMISE_MISSING: missing Discriminant(f,Δ)"
    if not found_disc_branch:
        return False, "E_PREMISE_MISSING: missing DiscNonSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg4_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    # recover factorization premise bound to the same resolvent
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        if _get_ref_id(p_args[0]) == resolvent_ref:
            factor_list_ref = _get_ref_id(p_args[1])
            unit_ref = _get_ref_id(p_args[2])
            break

    if factor_list_ref is None or unit_ref is None:
        return False, ("E_PREMISE_MISSING: missing FactorizationMonicQQ(R, factors, unit) "
                      "for the same resolvent")

    unit_val = _decode_ratqq_to_frac(unit_ref, ctx)
    if unit_val is None:
        return False, "E_TYPE: cannot decode RatQQ"
    if unit_val != 1:
        return False, "E_BAD_FACTORIZATION: expected unit = 1"

    list_obj = ctx.objects.get(factor_list_ref)
    if not isinstance(list_obj, Mapping) or list_obj.get("kind") != "PolyQQList":
        return False, "E_TYPE: cannot decode PolyQQList"
    items = list_obj.get("items")
    if not isinstance(items, list) or not items or not all(isinstance(x, str) and x for x in items):
        return False, "E_TYPE: invalid PolyQQList.items"

    linear_factors = []
    for ref in items:
        coeffs = _decode_polyqq_to_fracs(ref, ctx)
        if coeffs is None:
            return False, "E_TYPE: cannot decode PolyQQ"
        if len(coeffs) == 2:
            if coeffs[0] != 1:
                return False, "E_BAD_FACTORIZATION: linear factor must be monic"
            linear_factors.append(coeffs)

    if len(linear_factors) != 1:
        return False, "E_BAD_FACTORIZATION: expected exactly one monic linear factor"

    # x - r0 = [1, -r0]
    r0 = -linear_factors[0][1]

    f_coeffs = _decode_polyqq_to_fracs(f_ref, ctx)
    if f_coeffs is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    if len(f_coeffs) != 5:
        return False, "E_TYPE: expected quartic PolyQQ"
    lc = f_coeffs[0]
    if lc == 0:
        return False, "E_TYPE: leading coefficient is zero"
    fm = [c / lc for c in f_coeffs]
    _, a, b, c, d = fm

    delta = _decode_ratqq_to_frac(delta_ref, ctx)
    if delta is None:
        return False, "E_TYPE: cannot decode RatQQ"

    w1 = (a * a - Fraction(4, 1) * (b - r0)) * delta
    w2 = (r0 * r0 - Fraction(4, 1) * d) * delta

    matched = set()
    for rat_ref in is_square_refs:
        val = _decode_ratqq_to_frac(rat_ref, ctx)
        if val is None:
            return False, "E_TYPE: cannot decode RatQQ"
        if val == w1:
            matched.add("w1")
        if val == w2:
            matched.add("w2")

    if matched != {"w1", "w2"}:
        return False, ("E_BAD_AUXILIARY_SQUARES: expected IsSquareQQ "
                       "premises for both Kappe-Warren auxiliary values")

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 4 or obj.get("index") != 1:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(4,1)"
    return True, ""

def _rule_galois_group_QQ_deg4_D4_common(
    *,
    claim: Mapping[str, Any],
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
    which: str,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=4,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc_branch = False
    delta_ref = None
    resolvent_ref = None
    p_ref = None
    nonsquare_refs = []

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            if _get_ref_id(p_args[0]) == f_ref:
                found_irred_f = True
        elif pred == "Discriminant":
            if not isinstance(p_args, list) or len(p_args) != 2:
                return False, "E_PREMISE_BINDING: malformed Discriminant premise"
            if _get_ref_id(p_args[0]) == f_ref:
                delta_ref = _get_ref_id(p_args[1])
        elif pred == "DiscNonSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscNonSquareQQ premise"
            if _get_ref_id(p_args[0]) == f_ref:
                found_disc_branch = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            if _get_ref_id(p_args[1]) == f_ref:
                resolvent_ref = _get_ref_id(p_args[0])
                p_ref = _get_ref_id(p_args[2])
        elif pred == "NonSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed NonSquareQQ premise"
            rat_ref = _get_ref_id(p_args[0])
            if rat_ref is not None:
                nonsquare_refs.append(rat_ref)

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if delta_ref is None:
        return False, "E_PREMISE_MISSING: missing Discriminant(f,Δ)"
    if not found_disc_branch:
        return False, "E_PREMISE_MISSING: missing DiscNonSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg4_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    factor_list_ref = None
    unit_ref = None
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        if _get_ref_id(p_args[0]) == resolvent_ref:
            factor_list_ref = _get_ref_id(p_args[1])
            unit_ref = _get_ref_id(p_args[2])
            break

    if factor_list_ref is None or unit_ref is None:
        return False, ("E_PREMISE_MISSING: missing FactorizationMonicQQ(R, factors, unit) "
                       "for the same resolvent")

    unit_val = _decode_ratqq_to_frac(unit_ref, ctx)
    if unit_val is None:
        return False, "E_TYPE: cannot decode RatQQ"
    if unit_val != 1:
        return False, "E_BAD_FACTORIZATION: expected unit = 1"

    list_obj = ctx.objects.get(factor_list_ref)
    if not isinstance(list_obj, Mapping) or list_obj.get("kind") != "PolyQQList":
        return False, "E_TYPE: cannot decode PolyQQList"
    items = list_obj.get("items")
    if not isinstance(items, list) or not items or not all(isinstance(x, str) and x for x in items):
        return False, "E_TYPE: invalid PolyQQList.items"

    linear_factors = []
    for ref in items:
        coeffs = _decode_polyqq_to_fracs(ref, ctx)
        if coeffs is None:
            return False, "E_TYPE: cannot decode PolyQQ"
        if len(coeffs) == 2:
            if coeffs[0] != 1:
                return False, "E_BAD_FACTORIZATION: linear factor must be monic"
            linear_factors.append(coeffs)

    if len(linear_factors) != 1:
        return False, "E_BAD_FACTORIZATION: expected exactly one monic linear factor"

    r0 = -linear_factors[0][1]

    f_coeffs = _decode_polyqq_to_fracs(f_ref, ctx)
    if f_coeffs is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    if len(f_coeffs) != 5:
        return False, "E_TYPE: expected quartic PolyQQ"
    lc = f_coeffs[0]
    if lc == 0:
        return False, "E_TYPE: leading coefficient is zero"
    fm = [c / lc for c in f_coeffs]
    _, a, b, c, d = fm

    delta = _decode_ratqq_to_frac(delta_ref, ctx)
    if delta is None:
        return False, "E_TYPE: cannot decode RatQQ"

    if which == "w1":
        target = (a * a - Fraction(4, 1) * (b - r0)) * delta
    else:
        target = (r0 * r0 - Fraction(4, 1) * d) * delta

    matched = False
    for rat_ref in nonsquare_refs:
        val = _decode_ratqq_to_frac(rat_ref, ctx)
        if val is None:
            return False, "E_TYPE: cannot decode RatQQ"
        if val == target:
            matched = True
            break

    if not matched:
        return False, ("E_BAD_AUXILIARY_NONSQUARE: expected NonSquareQQ premise "
                       "for the required Kappe-Warren auxiliary value")

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 8 or obj.get("index") != 3:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(8,3)"
    return True, ""


def _rule_galois_group_QQ_deg4_D4_w1(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    return _rule_galois_group_QQ_deg4_D4_common(
        claim=claim,
        premises=premises,
        ctx=ctx,
        which="w1",
    )


def _rule_galois_group_QQ_deg4_D4_w2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    return _rule_galois_group_QQ_deg4_D4_common(
        claim=claim,
        premises=premises,
        ctx=ctx,
        which="w2",
    )
    
 
# --- Degree-4 pair-sums classification rules @2 ---------------------------------

def _decode_groupid_smallgroup_deg4_v2(
    ctx: _V3Ctx,
    group_ref: str,
    *,
    order: int,
    index: int,
) -> tuple[bool, str]:
    obj = ctx.objects.get(group_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != order or obj.get("index") != index:
        return False, f"E_GROUP_MISMATCH: expected (order,index)=({order},{index})"
    return True, ""


def _find_unary_premise_deg4_v2(
    premises: list[Mapping[str, Any]],
    *,
    pred: str,
    ref: str,
) -> tuple[bool, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != pred:
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, f"E_PREMISE_BINDING: malformed {pred} premise"
        if _get_ref_id(p_args[0]) == ref:
            return True, ""
    return False, f"E_PREMISE_MISSING: missing {pred} premise"


def _find_resolvent_for_poly_deg4_v2(
    premises: list[Mapping[str, Any]],
    *,
    poly_ref: str,
) -> tuple[str | None, str | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "ResolventQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return None, None, "E_PREMISE_BINDING: malformed ResolventQQ premise"
        r_ref = _get_ref_id(p_args[0])
        f_ref = _get_ref_id(p_args[1])
        p_ref = _get_ref_id(p_args[2])
        if f_ref == poly_ref:
            return r_ref, p_ref, ""
    return None, None, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"


def _require_pair_sums_resolvent_family_deg4_v2(
    ctx: _V3Ctx,
    p_ref: str | None,
) -> tuple[bool, str]:
    return _check_canonical_deg4_resolvent_family_alt(ctx, p_ref)


def _factor_refs_for_resolvent_deg4_v2(
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
    *,
    resolvent_ref: str,
) -> tuple[list[str] | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return None, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        if _get_ref_id(p_args[0]) != resolvent_ref:
            continue
        factors_ref = _get_ref_id(p_args[1])
        unit_ref = _get_ref_id(p_args[2])
        if factors_ref is None or unit_ref is None:
            return None, "E_PREMISE_BINDING: malformed FactorizationMonicQQ refs"
        unit = _decode_ratqq_to_frac(unit_ref, ctx)
        if unit is None:
            return None, "E_TYPE: cannot decode RatQQ unit"
        if unit != 1:
            return None, "E_BAD_FACTORIZATION: expected unit = 1"
        list_obj = ctx.objects.get(factors_ref)
        if not isinstance(list_obj, Mapping) or list_obj.get("kind") != "PolyQQList":
            return None, "E_TYPE: cannot decode PolyQQList"
        items = list_obj.get("items")
        if not isinstance(items, list) or not all(isinstance(x, str) and x for x in items):
            return None, "E_TYPE: invalid PolyQQList.items"
        return list(items), ""
    return None, "E_PREMISE_MISSING: missing FactorizationMonicQQ(R,factors,unit)"


def _all_linear_monic_deg4_v2(
    ctx: _V3Ctx,
    factor_refs: list[str],
    *,
    expected_count: int,
) -> tuple[bool, str]:
    if len(factor_refs) != expected_count:
        return False, f"E_BAD_FACTORIZATION: expected exactly {expected_count} factor refs"
    for ref in factor_refs:
        coeffs = _decode_polyqq_to_fracs(ref, ctx)
        if coeffs is None:
            return False, "E_TYPE: cannot decode PolyQQ"
        coeffs = _trim_leading_zeros_desc(coeffs)
        if len(coeffs) != 2:
            return False, "E_BAD_FACTORIZATION: factor is not linear"
        if coeffs[0] != 1:
            return False, "E_BAD_FACTORIZATION: factor is not monic"
    return True, ""


def _unique_linear_root_deg4_v2(
    ctx: _V3Ctx,
    factor_refs: list[str],
) -> tuple[Fraction | None, str]:
    roots: list[Fraction] = []
    for ref in factor_refs:
        coeffs = _decode_polyqq_to_fracs(ref, ctx)
        if coeffs is None:
            return None, "E_TYPE: cannot decode PolyQQ"
        coeffs = _trim_leading_zeros_desc(coeffs)
        if len(coeffs) == 2:
            if coeffs[0] != 1:
                return None, "E_BAD_FACTORIZATION: linear factor must be monic"
            roots.append(-coeffs[1])
    if len(roots) != 1:
        return None, "E_BAD_FACTORIZATION: expected exactly one monic linear factor"
    return roots[0], ""


def _monic_quartic_coeffs_deg4_v2(
    ctx: _V3Ctx,
    f_ref: str,
) -> tuple[tuple[Fraction, Fraction, Fraction, Fraction] | None, str]:
    f_coeffs = _decode_polyqq_to_fracs(f_ref, ctx)
    if f_coeffs is None:
        return None, "E_TYPE: cannot decode PolyQQ"
    f_coeffs = _trim_leading_zeros_desc(f_coeffs)
    if len(f_coeffs) != 5:
        return None, "E_TYPE: expected quartic PolyQQ"
    lc = f_coeffs[0]
    if lc == 0:
        return None, "E_TYPE: leading coefficient is zero"
    fm = [c / lc for c in f_coeffs]
    return (fm[1], fm[2], fm[3], fm[4]), ""


def _disc_ref_for_poly_deg4_v2(
    premises: list[Mapping[str, Any]],
    *,
    poly_ref: str,
) -> tuple[str | None, str]:
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "Discriminant":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return None, "E_PREMISE_BINDING: malformed Discriminant premise"
        if _get_ref_id(p_args[0]) == poly_ref:
            d_ref = _get_ref_id(p_args[1])
            if d_ref is None:
                return None, "E_PREMISE_BINDING: malformed Discriminant premise"
            return d_ref, ""
    return None, "E_PREMISE_MISSING: missing Discriminant(f,Δ)"


def _kw_pair_sums_values_deg4_v2(
    *,
    a: Fraction,
    b: Fraction,
    d: Fraction,
    delta: Fraction,
    s0: Fraction,
) -> tuple[Fraction, Fraction]:
    r0 = b - s0
    w1 = (a * a - Fraction(4, 1) * s0) * delta
    w2 = (r0 * r0 - Fraction(4, 1) * d) * delta
    return w1, w2


def _rule_galois_group_QQ_deg4_irred_pair_sums_common_v2(
    *,
    claim: Mapping[str, Any],
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
    disc_pred: str,
    group_order: int,
    group_index: int,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(premises=premises, poly_ref=f_ref, ctx=ctx, expected=4)
    if n is None:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred="IrreducibleQQ", ref=f_ref)
    if not ok:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred=disc_pred, ref=f_ref)
    if not ok:
        return False, err

    resolvent_ref, p_ref, err = _find_resolvent_for_poly_deg4_v2(premises, poly_ref=f_ref)
    if resolvent_ref is None:
        return False, err
    ok, err = _require_pair_sums_resolvent_family_deg4_v2(ctx, p_ref)
    if not ok:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred="IrreducibleQQ", ref=resolvent_ref)
    if not ok:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(R) for the same resolvent"
    return _decode_groupid_smallgroup_deg4_v2(ctx, g_ref, order=group_order, index=group_index)


def _rule_galois_group_QQ_deg4_S4_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    return _rule_galois_group_QQ_deg4_irred_pair_sums_common_v2(
        claim=claim,
        premises=premises,
        ctx=ctx,
        disc_pred="DiscNonSquareQQ",
        group_order=24,
        group_index=12,
    )


def _rule_galois_group_QQ_deg4_A4_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    return _rule_galois_group_QQ_deg4_irred_pair_sums_common_v2(
        claim=claim,
        premises=premises,
        ctx=ctx,
        disc_pred="DiscSquareQQ",
        group_order=12,
        group_index=3,
    )


def _rule_galois_group_QQ_deg4_V4_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"
    n, err = _require_degree_premise(premises=premises, poly_ref=f_ref, ctx=ctx, expected=4)
    if n is None:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred="IrreducibleQQ", ref=f_ref)
    if not ok:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred="DiscSquareQQ", ref=f_ref)
    if not ok:
        return False, err
    resolvent_ref, p_ref, err = _find_resolvent_for_poly_deg4_v2(premises, poly_ref=f_ref)
    if resolvent_ref is None:
        return False, err
    ok, err = _require_pair_sums_resolvent_family_deg4_v2(ctx, p_ref)
    if not ok:
        return False, err
    factors, err = _factor_refs_for_resolvent_deg4_v2(premises, ctx, resolvent_ref=resolvent_ref)
    if factors is None:
        return False, err
    ok, err = _all_linear_monic_deg4_v2(ctx, factors, expected_count=3)
    if not ok:
        return False, err
    return _decode_groupid_smallgroup_deg4_v2(ctx, g_ref, order=4, index=2)


def _rule_galois_group_QQ_deg4_V4_v3(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(premises=premises, poly_ref=f_ref, ctx=ctx, expected=4)
    if n is None:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred="IrreducibleQQ", ref=f_ref)
    if not ok:
        return False, err

    resolvent_ref, p_ref, err = _find_resolvent_for_poly_deg4_v2(premises, poly_ref=f_ref)
    if resolvent_ref is None:
        return False, err
    ok, err = _require_pair_sums_resolvent_family_deg4_v2(ctx, p_ref)
    if not ok:
        return False, err

    factors, err = _factor_refs_for_resolvent_deg4_v2(premises, ctx, resolvent_ref=resolvent_ref)
    if factors is None:
        return False, err
    ok, err = _all_linear_monic_deg4_v2(ctx, factors, expected_count=3)
    if not ok:
        return False, err

    for factor_ref in factors:
        deg, err = _require_degree_premise(
            premises=premises,
            poly_ref=factor_ref,
            ctx=ctx,
            expected=1,
        )
        if deg is None:
            return False, err

    return _decode_groupid_smallgroup_deg4_v2(ctx, g_ref, order=4, index=2)


def _rule_galois_group_QQ_deg4_KW_pair_sums_common_v2(
    *,
    claim: Mapping[str, Any],
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
    which: str,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"
    n, err = _require_degree_premise(premises=premises, poly_ref=f_ref, ctx=ctx, expected=4)
    if n is None:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred="IrreducibleQQ", ref=f_ref)
    if not ok:
        return False, err
    ok, err = _find_unary_premise_deg4_v2(premises, pred="DiscNonSquareQQ", ref=f_ref)
    if not ok:
        return False, err
    delta_ref, err = _disc_ref_for_poly_deg4_v2(premises, poly_ref=f_ref)
    if delta_ref is None:
        return False, err
    delta = _decode_ratqq_to_frac(delta_ref, ctx)
    if delta is None:
        return False, "E_TYPE: cannot decode RatQQ"
    resolvent_ref, p_ref, err = _find_resolvent_for_poly_deg4_v2(premises, poly_ref=f_ref)
    if resolvent_ref is None:
        return False, err
    ok, err = _require_pair_sums_resolvent_family_deg4_v2(ctx, p_ref)
    if not ok:
        return False, err
    factors, err = _factor_refs_for_resolvent_deg4_v2(premises, ctx, resolvent_ref=resolvent_ref)
    if factors is None:
        return False, err
    s0, err = _unique_linear_root_deg4_v2(ctx, factors)
    if s0 is None:
        return False, err
    coeffs, err = _monic_quartic_coeffs_deg4_v2(ctx, f_ref)
    if coeffs is None:
        return False, err
    a, b, _c, d = coeffs
    w1, w2 = _kw_pair_sums_values_deg4_v2(a=a, b=b, d=d, delta=delta, s0=s0)

    if which == "both_square":
        is_square_refs: list[str] = []
        for prem in premises:
            p = prem.get("claim", prem)
            if not isinstance(p, Mapping) or p.get("pred") != "IsSquareQQ":
                continue
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IsSquareQQ premise"
            rat_ref = _get_ref_id(p_args[0])
            if rat_ref is not None:
                is_square_refs.append(rat_ref)
        matched: set[str] = set()
        for rat_ref in is_square_refs:
            val = _decode_ratqq_to_frac(rat_ref, ctx)
            if val is None:
                return False, "E_TYPE: cannot decode RatQQ"
            if val == w1:
                matched.add("w1")
            if val == w2:
                matched.add("w2")
        if matched != {"w1", "w2"}:
            return False, (
                "E_BAD_AUXILIARY_SQUARES: expected IsSquareQQ premises for both "
                "pair-sums Kappe-Warren auxiliary values"
            )
        return _decode_groupid_smallgroup_deg4_v2(ctx, g_ref, order=4, index=1)

    target = w1 if which == "w1" else w2
    nonsquare_refs: list[str] = []
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "NonSquareQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed NonSquareQQ premise"
        rat_ref = _get_ref_id(p_args[0])
        if rat_ref is not None:
            nonsquare_refs.append(rat_ref)
    for rat_ref in nonsquare_refs:
        val = _decode_ratqq_to_frac(rat_ref, ctx)
        if val is None:
            return False, "E_TYPE: cannot decode RatQQ"
        if val == target:
            return _decode_groupid_smallgroup_deg4_v2(ctx, g_ref, order=8, index=3)
    return False, (
        "E_BAD_AUXILIARY_NONSQUARE: expected NonSquareQQ premise for the required "
        "pair-sums Kappe-Warren auxiliary value"
    )


def _rule_galois_group_QQ_deg4_C4_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    return _rule_galois_group_QQ_deg4_KW_pair_sums_common_v2(
        claim=claim,
        premises=premises,
        ctx=ctx,
        which="both_square",
    )


def _rule_galois_group_QQ_deg4_D4_w1_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    return _rule_galois_group_QQ_deg4_KW_pair_sums_common_v2(
        claim=claim,
        premises=premises,
        ctx=ctx,
        which="w1",
    )


def _rule_galois_group_QQ_deg4_D4_w2_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence
    return _rule_galois_group_QQ_deg4_KW_pair_sums_common_v2(
        claim=claim,
        premises=premises,
        ctx=ctx,
        which="w2",
    )
    
def _rule_galois_group_QQ_reducible_all_linear_trivial(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    factor_items: list[str] | None = None
    for prem in premises:
        if prem.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        p_f = _get_ref_id(p_args[0])
        p_factors = _get_ref_id(p_args[1])
        if p_f is None or p_factors is None:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        if p_f != f_ref:
            continue
        factor_items = _decode_polyqqlist_items(p_factors, ctx)
        if factor_items is None:
            return False, "E_TYPE: cannot decode PolyQQList from FactorizationMonicQQ premise"
        break
    if factor_items is None:
        return False, "E_PREMISE_MISSING: missing FactorizationMonicQQ(f, factors, unit)"
    if len(factor_items) < 2:
        return False, "E_SIDE_CONDITION: expected reducible factorization"

    distinct_items = list(dict.fromkeys(factor_items))
    for l_ref in distinct_items:
        deg, err = _require_degree_premise(
            premises=premises,
            poly_ref=l_ref,
            ctx=ctx,
            expected=1,
        )
        if deg is None:
            return False, err

    if g_ref == _INPUT_REF:
        return False, "E_TYPE: GroupId cannot be $input"
    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 1 or obj.get("index") != 1:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(1,1)"
    return True, ""

def _rule_galois_group_QQ_reducible_single_nonlinear_inherit(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    claim_g_ref = _get_ref_id(args_any[1])
    if f_ref is None or claim_g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    factor_items: list[str] | None = None
    for prem in premises:
        if prem.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        p_f = _get_ref_id(p_args[0])
        p_factors = _get_ref_id(p_args[1])
        if p_f is None or p_factors is None:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        if p_f != f_ref:
            continue
        factor_items = _decode_polyqqlist_items(p_factors, ctx)
        if factor_items is None:
            return False, "E_TYPE: cannot decode PolyQQList from FactorizationMonicQQ premise"
        break
    if factor_items is None:
        return False, "E_PREMISE_MISSING: missing FactorizationMonicQQ(f, factors, unit)"
    if len(factor_items) < 2:
        return False, "E_SIDE_CONDITION: expected reducible factorization"

    distinct_items = list(dict.fromkeys(factor_items))
    deg_map: dict[str, int] = {}
    for h_ref in distinct_items:
        deg, err = _require_degree_premise(
            premises=premises,
            poly_ref=h_ref,
            ctx=ctx,
        )
        if deg is None:
            return False, err
        deg_map[h_ref] = deg

    nonlinear = [ref for ref, n in deg_map.items() if n > 1]
    if len(nonlinear) != 1:
        return False, "E_SIDE_CONDITION: expected exactly one distinct non-linear factor"
    g_ref = nonlinear[0]
    for ref, n in deg_map.items():
        if ref == g_ref:
            continue
        if n != 1:
            return False, "E_SIDE_CONDITION: every remaining listed factor must satisfy Degree(l,1)"

    found_irred = False
    for prem in premises:
        if prem.get("pred") != "IrreducibleQQ":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_poly = _get_ref_id(p_args[0])
        if p_poly is None:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise (arg0 ref)"
        if p_poly == g_ref:
            found_irred = True
            break
    if not found_irred:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(g)"

    found_group = False
    for prem in premises:
        if prem.get("pred") != "GaloisGroup":
            continue
        p_args = prem.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed GaloisGroup premise"
        p_poly = _get_ref_id(p_args[0])
        p_group = _get_ref_id(p_args[1])
        if p_poly is None or p_group is None:
            return False, "E_PREMISE_BINDING: malformed GaloisGroup premise"
        if p_poly != g_ref:
            continue
        if p_group != claim_g_ref:
            return False, ("E_PREMISE_BINDING: GaloisGroup premise "
                           "must use same group object as claim")
        found_group = True
        break
    if not found_group:
        return False, "E_PREMISE_MISSING: missing GaloisGroup(g,G)"

    return True, ""

def _rule_galois_group_QQ_reducible_double_quadratic_C2(
     *,
     claim: Mapping[str, Any],
     fact_id: str,
     evidence: Any,
     premises: list[Mapping[str, Any]],
     ctx: _V3Ctx,
) -> tuple[bool, str]:
     _ = fact_id
     _ = evidence

     if claim.get("pred") != "GaloisGroup":
          return False, "E_TYPE: claim.pred mismatch"
     args_any = claim.get("args")
     if not isinstance(args_any, list) or len(args_any) != 2:
          return False, "E_TYPE: arity"
     f_ref = _get_ref_id(args_any[0])
     g_ref = _get_ref_id(args_any[1])
     if f_ref is None or g_ref is None:
          return False, "E_TYPE: args must be ObjectRef"

     factor_items: list[str] | None = None
     for prem in premises:
          p = prem.get("claim", prem)
          if p.get("pred") != "FactorizationMonicQQ":
               continue
          p_args = p.get("args")
          if not isinstance(p_args, list) or len(p_args) != 3:
               return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
          p_f = _get_ref_id(p_args[0])
          p_factors = _get_ref_id(p_args[1])
          if p_f != f_ref:
               continue
          if p_factors is None:
               return False, ("E_PREMISE_BINDING: malformed "
                              "FactorizationMonicQQ premise (factors ref)")
          factor_items = _decode_polyqqlist_items(p_factors, ctx)
          if factor_items is None:
               return False, "E_TYPE: cannot decode PolyQQList from FactorizationMonicQQ premise"
          break
     if factor_items is None:
          return False, "E_PREMISE_MISSING: missing FactorizationMonicQQ(f,factors,unit)"

     def _degree_value(poly_ref: str) -> int | None:
          for prem in premises:
               p = prem.get("claim", prem)
               if p.get("pred") != "Degree":
                    continue
               p_args = p.get("args")
               if not isinstance(p_args, list) or len(p_args) != 2:
                    return None
               p_f = _get_ref_id(p_args[0])
               p_n = _get_ref_id(p_args[1])
               if p_f != poly_ref or p_n is None:
                    continue
               obj = ctx.objects.get(p_n)
               if not isinstance(obj, Mapping) or obj.get("kind") != "IntZ":
                    return None
               value = obj.get("value")
               if not isinstance(value, str):
                    return None
               try:
                    return int(value)
               except Exception:
                    return None
          return None

     def _has_irred(poly_ref: str) -> bool:
          for prem in premises:
               p = prem.get("claim", prem)
               if p.get("pred") != "IrreducibleQQ":
                    continue
               p_args = p.get("args")
               if not isinstance(p_args, list) or len(p_args) != 1:
                    return False
               if _get_ref_id(p_args[0]) == poly_ref:
                    return True
          return False

     distinct_items = list(dict.fromkeys(factor_items))
     quad_refs: list[str] = []
     for ref in distinct_items:
          deg = _degree_value(ref)
          if deg is None:
               return False, "E_PREMISE_MISSING: missing Degree premise for factor in factorization"
          if deg == 1:
               continue
          if deg != 2:
               return False, "E_SIDE_CONDITION: non-quadratic non-linear factor present"
          if not _has_irred(ref):
               return False, "E_PREMISE_MISSING: missing IrreducibleQQ(q)"
          quad_refs.append(ref)

     if len(quad_refs) != 2:
          return False, (
               "E_SIDE_CONDITION: expected exactly two distinct irreducible quadratic factors "
               "after ignoring linear factors and multiplicities"
          )
     q1_ref, q2_ref = quad_refs[0], quad_refs[1]

     def _require_disc(poly_ref: str) -> tuple[Fraction | None, str]:
          for prem in premises:
               p = prem.get("claim", prem)
               if p.get("pred") != "Discriminant":
                    continue
               p_args = p.get("args")
               if not isinstance(p_args, list) or len(p_args) != 2:
                    return None, "E_PREMISE_BINDING: malformed Discriminant premise"
               if _get_ref_id(p_args[0]) != poly_ref:
                    continue
               d_ref = _get_ref_id(p_args[1])
               if d_ref is None:
                    return None, "E_PREMISE_BINDING: malformed Discriminant premise (D ref)"
               d_val = _decode_ratqq_to_frac(d_ref, ctx)
               if d_val is None:
                    return None, "E_TYPE: cannot decode discriminant RatQQ"
               return d_val, ""
          return None, "E_PREMISE_MISSING: missing Discriminant(q,d)"

     d1, err = _require_disc(q1_ref)
     if d1 is None:
          return False, err
     d2, err = _require_disc(q2_ref)
     if d2 is None:
          return False, err
     expected = d1 * d2

     found_square = False
     for prem in premises:
          p = prem.get("claim", prem)
          if p.get("pred") != "IsSquareQQ":
               continue
          p_args = p.get("args")
          if not isinstance(p_args, list) or len(p_args) != 1:
               return False, "E_PREMISE_BINDING: malformed IsSquareQQ premise"
          c_ref = _get_ref_id(p_args[0])
          if c_ref is None:
               return False, "E_PREMISE_BINDING: malformed IsSquareQQ premise (arg ref)"
          c_val = _decode_ratqq_to_frac(c_ref, ctx)
          if c_val is None:
               return False, "E_TYPE: cannot decode IsSquareQQ argument as RatQQ"
          if c_val == expected:
               found_square = True
               break
     if not found_square:
          return False, "E_PREMISE_MISSING: missing IsSquareQQ(d1*d2)"

     obj = ctx.objects.get(g_ref)
     if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
          return False, "E_TYPE: cannot decode GroupId"
     if obj.get("system") != "smallgroup":
          return False, "E_TYPE: GroupId.system must be 'smallgroup'"
     if obj.get("order") != 2 or obj.get("index") != 1:
          return False, "E_GROUP_MISMATCH: expected (order,index)=(2,1)"
     return True, ""

def _rule_galois_group_QQ_reducible_double_quadratic_V4(
     *,
     claim: Mapping[str, Any],
     fact_id: str,
     evidence: Any,
     premises: list[Mapping[str, Any]],
     ctx: _V3Ctx,
) -> tuple[bool, str]:
     _ = fact_id
     _ = evidence

     if claim.get("pred") != "GaloisGroup":
          return False, "E_TYPE: claim.pred mismatch"
     args_any = claim.get("args")
     if not isinstance(args_any, list) or len(args_any) != 2:
          return False, "E_TYPE: arity"
     f_ref = _get_ref_id(args_any[0])
     g_ref = _get_ref_id(args_any[1])
     if f_ref is None or g_ref is None:
          return False, "E_TYPE: args must be ObjectRef"

     factor_items: list[str] | None = None
     for prem in premises:
          p = prem.get("claim", prem)
          if p.get("pred") != "FactorizationMonicQQ":
               continue
          p_args = p.get("args")
          if not isinstance(p_args, list) or len(p_args) != 3:
               return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
          p_f = _get_ref_id(p_args[0])
          p_factors = _get_ref_id(p_args[1])
          if p_f != f_ref:
               continue
          if p_factors is None:
               return False, ("E_PREMISE_BINDING: malformed "
                              "FactorizationMonicQQ premise (factors ref)")
          factor_items = _decode_polyqqlist_items(p_factors, ctx)
          if factor_items is None:
               return False, "E_TYPE: cannot decode PolyQQList from FactorizationMonicQQ premise"
          break
     if factor_items is None:
          return False, "E_PREMISE_MISSING: missing FactorizationMonicQQ(f,factors,unit)"

     def _degree_value(poly_ref: str) -> int | None:
          for prem in premises:
               p = prem.get("claim", prem)
               if p.get("pred") != "Degree":
                    continue
               p_args = p.get("args")
               if not isinstance(p_args, list) or len(p_args) != 2:
                    return None
               p_f = _get_ref_id(p_args[0])
               p_n = _get_ref_id(p_args[1])
               if p_f != poly_ref or p_n is None:
                    continue
               obj = ctx.objects.get(p_n)
               if not isinstance(obj, Mapping) or obj.get("kind") != "IntZ":
                    return None
               value = obj.get("value")
               if not isinstance(value, str):
                    return None
               try:
                    return int(value)
               except Exception:
                    return None
          return None

     def _has_irred(poly_ref: str) -> bool:
          for prem in premises:
               p = prem.get("claim", prem)
               if p.get("pred") != "IrreducibleQQ":
                    continue
               p_args = p.get("args")
               if not isinstance(p_args, list) or len(p_args) != 1:
                    return False
               if _get_ref_id(p_args[0]) == poly_ref:
                    return True
          return False

     distinct_items = list(dict.fromkeys(factor_items))
     quad_refs: list[str] = []
     for ref in distinct_items:
          deg = _degree_value(ref)
          if deg is None:
               return False, "E_PREMISE_MISSING: missing Degree premise for factor in factorization"
          if deg == 1:
               continue
          if deg != 2:
               return False, "E_SIDE_CONDITION: non-quadratic non-linear factor present"
          if not _has_irred(ref):
               return False, "E_PREMISE_MISSING: missing IrreducibleQQ(q)"
          quad_refs.append(ref)

     if len(quad_refs) != 2:
          return False, (
               "E_SIDE_CONDITION: expected exactly two distinct irreducible quadratic factors "
               "after ignoring linear factors and multiplicities"
          )
     q1_ref, q2_ref = quad_refs[0], quad_refs[1]

     def _require_disc(poly_ref: str) -> tuple[Fraction | None, str]:
          for prem in premises:
               p = prem.get("claim", prem)
               if p.get("pred") != "Discriminant":
                    continue
               p_args = p.get("args")
               if not isinstance(p_args, list) or len(p_args) != 2:
                    return None, "E_PREMISE_BINDING: malformed Discriminant premise"
               if _get_ref_id(p_args[0]) != poly_ref:
                    continue
               d_ref = _get_ref_id(p_args[1])
               if d_ref is None:
                    return None, "E_PREMISE_BINDING: malformed Discriminant premise (D ref)"
               d_val = _decode_ratqq_to_frac(d_ref, ctx)
               if d_val is None:
                    return None, "E_TYPE: cannot decode discriminant RatQQ"
               return d_val, ""
          return None, "E_PREMISE_MISSING: missing Discriminant(q,d)"

     d1, err = _require_disc(q1_ref)
     if d1 is None:
          return False, err
     d2, err = _require_disc(q2_ref)
     if d2 is None:
          return False, err
     expected = d1 * d2

     found_nonsquare = False
     for prem in premises:
          p = prem.get("claim", prem)
          if p.get("pred") != "NonSquareQQ":
               continue
          p_args = p.get("args")
          if not isinstance(p_args, list) or len(p_args) != 1:
               return False, "E_PREMISE_BINDING: malformed NonSquareQQ premise"
          c_ref = _get_ref_id(p_args[0])
          if c_ref is None:
               return False, "E_PREMISE_BINDING: malformed NonSquareQQ premise (arg ref)"
          c_val = _decode_ratqq_to_frac(c_ref, ctx)
          if c_val is None:
               return False, "E_TYPE: cannot decode NonSquareQQ argument as RatQQ"
          if c_val == expected:
               found_nonsquare = True
               break
     if not found_nonsquare:
          return False, "E_PREMISE_MISSING: missing NonSquareQQ(d1*d2)"

     obj = ctx.objects.get(g_ref)
     if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
          return False, "E_TYPE: cannot decode GroupId"
     if obj.get("system") != "smallgroup":
          return False, "E_TYPE: GroupId.system must be 'smallgroup'"
     if obj.get("order") != 4 or obj.get("index") != 2:
          return False, "E_GROUP_MISMATCH: expected (order,index)=(4,2)"
     return True, ""
 
def _rule_galois_group_QQ_reducible_quadratic_cubic_C6(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    return _rule_galois_group_QQ_reducible_quadratic_cubic_common(
        claim=claim, fact_id=fact_id, evidence=evidence, premises=premises, ctx=ctx, which="C6"
    )

def _rule_galois_group_QQ_reducible_quadratic_cubic_S3(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    return _rule_galois_group_QQ_reducible_quadratic_cubic_common(
        claim=claim, fact_id=fact_id, evidence=evidence, premises=premises, ctx=ctx, which="S3"
    )


def _rule_galois_group_QQ_reducible_quadratic_cubic_S3_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    return _rule_galois_group_QQ_reducible_quadratic_cubic_common(
        claim=claim,
        fact_id=fact_id,
        evidence=evidence,
        premises=premises,
        ctx=ctx,
        which="S3",
        cubic_disc_mode="explicit_nonsquare",
    )

def _rule_galois_group_QQ_reducible_quadratic_cubic_D6(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    return _rule_galois_group_QQ_reducible_quadratic_cubic_common(
        claim=claim, fact_id=fact_id, evidence=evidence, premises=premises, ctx=ctx, which="D6"
    )


def _rule_galois_group_QQ_reducible_quadratic_cubic_D6_v2(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    return _rule_galois_group_QQ_reducible_quadratic_cubic_common(
        claim=claim,
        fact_id=fact_id,
        evidence=evidence,
        premises=premises,
        ctx=ctx,
        which="D6",
        cubic_disc_mode="explicit_nonsquare",
    )


def _rule_galois_group_QQ_reducible_quadratic_cubic_common(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
    which: str,
    cubic_disc_mode: Literal["lifted_nonsquare", "explicit_nonsquare", "square"] =
    "lifted_nonsquare",
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    factor_items: list[str] | None = None
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        p_f = _get_ref_id(p_args[0])
        p_factors = _get_ref_id(p_args[1])
        if p_f != f_ref:
            continue
        if p_factors is None:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise (factors ref)"
        factor_items = _decode_polyqqlist_items(p_factors, ctx)
        if factor_items is None:
            return False, "E_TYPE: cannot decode PolyQQList from FactorizationMonicQQ premise"
        break
    if factor_items is None:
        return False, "E_PREMISE_MISSING: missing FactorizationMonicQQ(f,factors,unit)"

    def _degree_value(poly_ref: str) -> tuple[int | None, str]:
        for prem in premises:
            p = prem.get("claim", prem)
            if p.get("pred") != "Degree":
                continue
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 2:
                return None, "E_PREMISE_BINDING: malformed Degree premise"
            p_f = _get_ref_id(p_args[0])
            p_n = _get_ref_id(p_args[1])
            if p_f is None or p_n is None:
                return None, "E_PREMISE_BINDING: malformed Degree premise (refs)"
            if p_f != poly_ref:
                continue
            obj = ctx.objects.get(p_n)
            if not isinstance(obj, Mapping) or obj.get("kind") != "IntZ":
                return None, "E_PREMISE_BINDING: Degree object must be IntZ"
            value = obj.get("value")
            if not isinstance(value, str):
                return None, "E_PREMISE_BINDING: Degree IntZ.value must be string"
            try:
                return int(value), ""
            except Exception:
                return None, "E_PREMISE_BINDING: Degree IntZ.value must parse as integer"
        return None, f"E_PREMISE_MISSING: missing Degree({poly_ref},n)"

    def _has_irreducible(poly_ref: str) -> bool:
        for prem in premises:
            p = prem.get("claim", prem)
            if p.get("pred") != "IrreducibleQQ":
                continue
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False
            if _get_ref_id(p_args[0]) == poly_ref:
                return True
        return False

    def _disc_ref(poly_ref: str) -> tuple[str | None, str]:
        for prem in premises:
            p = prem.get("claim", prem)
            if p.get("pred") != "Discriminant":
                continue
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 2:
                return None, "E_PREMISE_BINDING: malformed Discriminant premise"
            p_f = _get_ref_id(p_args[0])
            p_d = _get_ref_id(p_args[1])
            if p_f != poly_ref:
                continue
            if p_d is None:
                return None, "E_PREMISE_BINDING: malformed Discriminant premise (disc ref)"
            return p_d, ""
        return None, "E_PREMISE_MISSING: missing Discriminant premise"

    def _has_pred_bound(pred: str, poly_ref: str) -> bool:
        for prem in premises:
            p = prem.get("claim", prem)
            if p.get("pred") != pred:
                continue
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False
            if _get_ref_id(p_args[0]) == poly_ref:
                return True
        return False

    # Determine q_ref / c_ref from the factorization itself, using the DISTINCT
    # non-linear factors after ignoring multiplicities. This aligns the reducible
    # [2,3] branch with the splitting-field semantics used by the dispatcher:
    # repeated occurrences of the same irreducible non-linear factor do not change
    # the core non-linear pattern.
    q_ref: str | None = None
    c_ref: str | None = None
    q_count = 0
    c_count = 0

    distinct_items = list(dict.fromkeys(factor_items))
    for ref in distinct_items:
        deg, err = _degree_value(ref)
        if deg is None:
            return False, f"{err}: factor in factorization"
        if deg == 2:
            q_count += 1
            if q_ref is None:
                q_ref = ref
        elif deg == 3:
            c_count += 1
            if c_ref is None:
                c_ref = ref
        elif deg == 1:
            continue
        else:
            return False, "E_SIDE_CONDITION: extra non-linear factor present in factorization"

    if q_count != 1 or c_count != 1 or q_ref is None or c_ref is None:
        return False, (
            "E_SIDE_CONDITION: expected exactly one distinct quadratic factor, "
            "exactly one distinct cubic factor, and all remaining distinct factors linear "
            "(after ignoring multiplicities)"
        )
    if q_ref == c_ref:
        return False, "E_PREMISE_BINDING: quadratic and cubic factors must be distinct"

    if not _has_irreducible(q_ref):
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(q)"
    if not _has_irreducible(c_ref):
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(c)"

    if which == "C6":
        if not _has_pred_bound("DiscSquareQQ", c_ref):
            return False, "E_PREMISE_MISSING: missing DiscSquareQQ(c)"
        obj = ctx.objects.get(g_ref)
        if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
            return False, "E_TYPE: cannot decode GroupId"
        if obj.get("system") != "smallgroup":
            return False, "E_TYPE: GroupId.system must be 'smallgroup'"
        if obj.get("order") != 6 or obj.get("index") != 1:
            return False, "E_GROUP_MISMATCH: expected (order,index)=(6,1)"
        return True, ""

    q_disc_ref, err = _disc_ref(q_ref)
    if q_disc_ref is None:
        return False, err.replace("premise", "premise for q")
    c_disc_ref, err = _disc_ref(c_ref)
    if c_disc_ref is None:
        return False, err.replace("premise", "premise for c")

    if cubic_disc_mode == "square":
        if not _has_pred_bound("DiscSquareQQ", c_ref):
            return False, "E_PREMISE_MISSING: missing DiscSquareQQ(c)"
    elif cubic_disc_mode == "lifted_nonsquare":
        if not _has_pred_bound("DiscNonSquareQQ", c_ref):
            return False, "E_PREMISE_MISSING: missing DiscNonSquareQQ(c)"
    else:
        if not _has_pred_bound("NonSquareQQ", c_disc_ref):
            return False, "E_PREMISE_MISSING: missing NonSquareQQ(d2)"

    d1 = _decode_ratqq_to_frac(q_disc_ref, ctx)
    d2 = _decode_ratqq_to_frac(c_disc_ref, ctx)
    if d1 is None or d2 is None:
        return False, "E_TYPE: cannot decode RatQQ discriminant objects"
    expected_product = d1 * d2

    aux_pred = "IsSquareQQ" if which == "S3" else "NonSquareQQ"
    found_aux_pred = False
    found_matching_aux = False

    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != aux_pred:
            continue
        found_aux_pred = True

        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, f"E_PREMISE_BINDING: malformed {aux_pred} premise"
        aux_ref = _get_ref_id(p_args[0])
        if aux_ref is None:
            return False, f"E_PREMISE_BINDING: malformed {aux_pred} premise (arg ref)"

        w = _decode_ratqq_to_frac(aux_ref, ctx)
        if w is None:
            return False, f"E_TYPE: cannot decode RatQQ object for {aux_pred}"

        if w == expected_product:
            found_matching_aux = True
            break

    if not found_aux_pred:
        return False, f"E_PREMISE_MISSING: missing {aux_pred}(w)"
    if not found_matching_aux:
        code = "E_BAD_AUXILIARY_SQUARE" if which == "S3" else "E_BAD_AUXILIARY_NONSQUARE"
        return False, f"{code}: missing witness for d1*d2"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"

    expected = (6, 2) if which == "S3" else (12, 4)
    if obj.get("order") != expected[0] or obj.get("index") != expected[1]:
        return False, f"E_GROUP_MISMATCH: expected (order,index)={expected}"
    return True, ""

# ---------------------------------------------------------------------------
# Dummit degree-5 sextic resolvent family (F20 stabilizer)
# ---------------------------------------------------------------------------

_CANONICAL_DEG5_RESOLVENT_MPOLY = {
    "kind": "MPolyQQ",
    "nvars": 5,
    "terms": [
        {"exp": [2, 1, 0, 0, 1], "coeff_qq": "1"},
        {"exp": [2, 0, 1, 1, 0], "coeff_qq": "1"},
        {"exp": [1, 2, 1, 0, 0], "coeff_qq": "1"},
        {"exp": [1, 1, 0, 2, 0], "coeff_qq": "1"},
        {"exp": [1, 0, 2, 0, 1], "coeff_qq": "1"},
        {"exp": [1, 0, 0, 1, 2], "coeff_qq": "1"},
        {"exp": [0, 2, 0, 1, 1], "coeff_qq": "1"},
        {"exp": [0, 1, 2, 1, 0], "coeff_qq": "1"},
        {"exp": [0, 1, 1, 0, 2], "coeff_qq": "1"},
        {"exp": [0, 0, 1, 2, 1], "coeff_qq": "1"},
    ],
}


def _is_fixed_mpolyqq_deg5_sextic_dummit_F20(p_ref: str, ctx: _V3Ctx) -> bool:
    p_obj = ctx.objects.get(p_ref)
    return isinstance(p_obj, Mapping) and dict(p_obj) == _CANONICAL_DEG5_RESOLVENT_MPOLY


def _rule_resolvent_QQ_compute_deg5_sextic_dummit_F20(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "ResolventQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 3:
        return False, "E_TYPE: arity"

    r_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    p_ref = _get_ref_id(args_any[2])
    if r_ref is None or g_ref is None or p_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=g_ref,
        ctx=ctx,
        expected=5,
    )
    if deg is None:
        return False, err

    r_poly = _decode_polyqq_to_fracs(r_ref, ctx)
    g_poly = _decode_polyqq_to_fracs(g_ref, ctx)
    if r_poly is None or g_poly is None:
        return False, "E_TYPE: cannot decode PolyQQ args"

    r_poly = _trim_leading_zeros_desc(r_poly)
    g_poly = _trim_leading_zeros_desc(g_poly)

    if not _is_fixed_mpolyqq_deg5_sextic_dummit_F20(p_ref, ctx):
        return False, (
            "E_P_MISMATCH: expected canonical MPolyQQ for Dummit's degree-5 F20 sextic family"
        )

    if not g_poly or g_poly[0] != Fraction(1):
        return False, "E_NOT_MONIC: expected depressed monic quintic"

    try:
        _, a4, p, q, r, s = g_poly
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: coefficient unpack failed: {e}"

    if a4 != 0:
        return False, "E_NOT_DEPRESSED: x^4 coefficient must be 0"

    try:
        r_expected = _trim_leading_zeros_desc(
            [
                Fraction(1),
                8 * r,
                2 * p * q * q - 6 * p * p * r + 40 * r * r - 50 * q * s,
                (
                    -2 * q**4
                    + 21 * p * q * q * r
                    - 40 * p * p * r * r
                    + 160 * r**3
                    - 15 * p * p * q * s
                    - 400 * q * r * s
                    + 125 * p * s * s
                ),
                (
                    p * p * q**4
                    - 6 * p**3 * q * q * r
                    - 8 * q**4 * r
                    + 9 * p**4 * r * r
                    + 76 * p * q * q * r * r
                    - 136 * p * p * r**3
                    + 400 * r**4
                    - 50 * p * q**3 * s
                    + 90 * p * p * q * r * s
                    - 1400 * q * r * r * s
                    + 625 * q * q * s * s
                    + 500 * p * r * s * s
                ),
                (
                    -2 * p * q**6
                    + 19 * p * p * q**4 * r
                    - 51 * p**3 * q * q * r * r
                    + 3 * q**4 * r * r
                    + 32 * p**4 * r**3
                    + 76 * p * q * q * r**3
                    - 256 * p * p * r**4
                    + 512 * r**5
                    - 31 * p**3 * q**3 * s
                    - 58 * q**5 * s
                    + 117 * p**4 * q * r * s
                    + 105 * p * q**3 * r * s
                    + 260 * p * p * q * r * r * s
                    - 2400 * q * r**3 * s
                    - 108 * p**5 * s * s
                    - 325 * p * p * q * q * s * s
                    + 525 * p**3 * r * s * s
                    + 2750 * q * q * r * s * s
                    - 500 * p * r * r * s * s
                    + 625 * p * q * s**3
                    - 3125 * s**4
                ),
                (
                    q**8
                    - 13 * p * q**6 * r
                    + p**5 * q * q * r * r
                    + 65 * p * p * q**4 * r * r
                    - 4 * p**6 * r**3
                    - 128 * p**3 * q * q * r**3
                    + 17 * q**4 * r**3
                    + 48 * p**4 * r**4
                    - 16 * p * q * q * r**4
                    - 192 * p * p * r**5
                    + 256 * r**6
                    - 4 * p**5 * q**3 * s
                    - 12 * p * p * q**5 * s
                    + 18 * p**6 * q * r * s
                    + 12 * p**3 * q**3 * r * s
                    - 124 * q**5 * r * s
                    + 196 * p**4 * q * r * r * s
                    + 590 * p * q**3 * r * r * s
                    - 160 * p * p * q * r**3 * s
                    - 1600 * q * r**4 * s
                    - 27 * p**7 * s * s
                    - 150 * p**4 * q * q * s * s
                    - 125 * p * q**4 * s * s
                    - 99 * p**5 * r * s * s
                    - 725 * p * p * q * q * r * s * s
                    + 1200 * p**3 * r * r * s * s
                    + 3250 * q * q * r * r * s * s
                    - 2000 * p * r**3 * s * s
                    - 1250 * p * q * r * s**3
                    + 3125 * p * p * s**4
                    - 9375 * r * s**4
                ),
            ]
        )
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: recomputation raised: {e}"

    if r_poly != r_expected:
        return False, "E_MISMATCH"
    return True, ""

def _check_canonical_deg5_f20_resolvent_family(ctx: _V3Ctx, p_ref: str | None) -> tuple[bool, str]:
    if p_ref is None:
        return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
    p_obj = ctx.objects.get(p_ref)
    if not isinstance(p_obj, Mapping):
        return False, "E_TYPE: missing MPolyQQ object for resolvent family"
    if dict(p_obj) != _CANONICAL_DEG5_RESOLVENT_MPOLY:
        return False, "E_BAD_RESOLVENT_FAMILY: expected Dummit F20 sextic resolvent family"
    return True, ""

def _rule_galois_group_QQ_deg5_S5(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=5,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc = False
    resolvent_ref = None
    p_ref = None

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_irred_f = True
        elif pred == "DiscNonSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscNonSquareQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_disc = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            r_ref = _get_ref_id(p_args[0])
            f_ref_prem = _get_ref_id(p_args[1])
            p_candidate = _get_ref_id(p_args[2])
            if f_ref_prem == f_ref:
                resolvent_ref = r_ref
                p_ref = p_candidate

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscNonSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg5_f20_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    found_irred_r = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_poly = _get_ref_id(p_args[0])
        if p_poly == resolvent_ref:
            found_irred_r = True
            break

    if not found_irred_r:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(R) for the same resolvent"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 120 or obj.get("index") != 34:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(120,34)"
    return True, ""

def _rule_galois_group_QQ_deg5_A5(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=5,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc = False
    resolvent_ref = None
    p_ref = None

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_irred_f = True
        elif pred == "DiscSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscSquareQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_disc = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            r_ref = _get_ref_id(p_args[0])
            f_ref_prem = _get_ref_id(p_args[1])
            p_candidate = _get_ref_id(p_args[2])
            if f_ref_prem == f_ref:
                resolvent_ref = r_ref
                p_ref = p_candidate

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg5_f20_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    found_irred_r = False
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_poly = _get_ref_id(p_args[0])
        if p_poly == resolvent_ref:
            found_irred_r = True
            break

    if not found_irred_r:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(R) for the same resolvent"

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 60 or obj.get("index") != 5:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(60,5)"
    return True, ""

def _rule_galois_group_QQ_deg5_F20(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=5,
    )
    if n is None:
        return False, err

    found_irred_f = False
    found_disc = False
    resolvent_ref = None
    p_ref = None

    for prem in premises:
        p = prem.get("claim", prem)
        pred = p.get("pred")
        p_args = p.get("args")
        if pred == "IrreducibleQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_irred_f = True
        elif pred == "DiscNonSquareQQ":
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed DiscNonSquareQQ premise"
            p_poly = _get_ref_id(p_args[0])
            if p_poly == f_ref:
                found_disc = True
        elif pred == "ResolventQQ":
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            r_ref = _get_ref_id(p_args[0])
            f_ref_prem = _get_ref_id(p_args[1])
            p_candidate = _get_ref_id(p_args[2])
            if f_ref_prem == f_ref:
                resolvent_ref = r_ref
                p_ref = p_candidate

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if not found_disc:
        return False, "E_PREMISE_MISSING: missing DiscNonSquareQQ(f)"
    if resolvent_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"

    ok, err = _check_canonical_deg5_f20_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    factor_items: list[str] | None = None
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "FactorizationMonicQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
        p_poly = _get_ref_id(p_args[0])
        p_factors = _get_ref_id(p_args[1])
        if p_poly != resolvent_ref:
            continue
        if p_factors is None:
            return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise (factors ref)"
        factor_items = _decode_polyqqlist_items(p_factors, ctx)
        if factor_items is None:
            return False, "E_TYPE: cannot decode PolyQQList from FactorizationMonicQQ premise"
        break

    if factor_items is None:
        return False, ("E_PREMISE_MISSING: missing FactorizationMonicQQ(R,factors,unit)"
                            " for the same resolvent")

    linear_factor_ref: str | None = None
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "Degree":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed Degree premise"
        factor_ref = _get_ref_id(p_args[0])
        deg_obj = _decode_intz_to_int(_get_ref_id(p_args[1]), ctx)
        if factor_ref is None or deg_obj is None:
            return False, "E_PREMISE_BINDING: malformed Degree premise"
        if deg_obj != 1:
            continue
        if factor_ref in factor_items:
            linear_factor_ref = factor_ref
            break

    if linear_factor_ref is None:
        return False, ("E_PREMISE_MISSING: missing Degree(l,1) for a factor listed"
                            " in FactorizationMonicQQ(R,factors,unit)")

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != 20 or obj.get("index") != 3:
        return False, "E_GROUP_MISMATCH: expected (order,index)=(20,3)"
    return True, ""

def _disc_quadratic_monic_desc(coeffs: list[Fraction]) -> Fraction:
    if len(coeffs) != 3 or coeffs[0] != 1:
        raise ValueError("Expected monic quadratic in descending coefficients [1,b,c].")
    _, b, c = coeffs
    return b * b - 4 * c


def _extract_theta_from_linear_factor(ctx: _V3Ctx, l_ref: str) -> tuple[Fraction | None, str]:
    coeffs = _decode_polyqq_to_fracs(l_ref, ctx)
    if coeffs is None:
        return None, "E_TYPE: cannot decode linear factor polynomial"
    if len(coeffs) != 2:
        return None, "E_PREMISE_BINDING: factor l is not linear in descending coefficients"
    a, b = coeffs
    if a == 0:
        return None, "E_TYPE: malformed linear factor with zero leading coefficient"
    return -b / a, ""


def _extract_depressed_quintic_pqrs(
    ctx: _V3Ctx, f_ref: str
) -> tuple[tuple[Fraction, Fraction, Fraction, Fraction] | None, str]:
    coeffs = _decode_polyqq_to_fracs(f_ref, ctx)
    if coeffs is None:
        return None, "E_TYPE: cannot decode quintic polynomial"
    if len(coeffs) != 6:
        return None, "E_SIDE_CONDITION: expected degree-5 polynomial with 6 descending coefficients"
    if coeffs[0] != 1:
        return None, "E_SIDE_CONDITION: Dummit quadratic formulas expect a monic quintic"
    if coeffs[1] != 0:
        return None, "E_SIDE_CONDITION: Dummit quadratic formulas expect a depressed quintic"
    return (coeffs[2], coeffs[3], coeffs[4], coeffs[5]), ""


def _rule_galois_group_QQ_deg5_D5_or_C5(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
    expect_all_square: bool,
    expected_order: int,
    expected_index: int,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    g_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    n, err = _require_degree_premise(premises=premises, poly_ref=f_ref, ctx=ctx, expected=5)
    if n is None:
        return False, err

    found_irred_f = False
    d_ref: str | None = None
    sqrt_a_ref: str | None = None
    resolvent_ref: str | None = None
    p20_ref: str | None = None
    factors_ref: str | None = None
    linear_ref: str | None = None
    quadratic_disc_premises: list[tuple[str, str]] = []

    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping):
            continue
        pred = p.get("pred")
        p_args = p.get("args")
        if not isinstance(p_args, list):
            continue

        if pred == "IrreducibleQQ":
            if len(p_args) != 1:
                return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
            if _get_ref_id(p_args[0]) == f_ref:
                found_irred_f = True

        elif pred == "Discriminant":
            if len(p_args) != 2:
                return False, "E_PREMISE_BINDING: malformed Discriminant premise"
            poly_ref = _get_ref_id(p_args[0])
            rat_ref = _get_ref_id(p_args[1])
            if poly_ref == f_ref:
                d_ref = rat_ref
            elif poly_ref is not None and rat_ref is not None:
                quadratic_disc_premises.append((poly_ref, rat_ref))

        elif pred == "ResolventQQ":
            if len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
            r_ref = _get_ref_id(p_args[0])
            f_ref_prem = _get_ref_id(p_args[1])
            p_candidate = _get_ref_id(p_args[2])
            if f_ref_prem == f_ref:
                resolvent_ref = r_ref
                p20_ref = p_candidate

        elif pred == "FactorizationMonicQQ":
            if len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
            r_ref = _get_ref_id(p_args[0])
            cand_factors_ref = _get_ref_id(p_args[1])
            if resolvent_ref is not None and r_ref == resolvent_ref:
                factors_ref = cand_factors_ref

        elif pred == "Degree":
            if len(p_args) != 2:
                return False, "E_PREMISE_BINDING: malformed Degree premise"
            poly_ref = _get_ref_id(p_args[0])
            n_ref = _get_ref_id(p_args[1])
            if poly_ref is None or n_ref is None:
                return False, "E_PREMISE_BINDING: malformed Degree premise refs"
            n_val = _decode_intz_to_int(n_ref, ctx)
            if n_val is None:
                return False, "E_PREMISE_BINDING: cannot decode Degree value"
            if n_val == 1:
                linear_ref = poly_ref

    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"
    if d_ref is None:
        return False, "E_PREMISE_MISSING: missing Discriminant(f,D)"

    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "SqrtQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed SqrtQQ premise"
        if _get_ref_id(p_args[0]) == d_ref:
            sqrt_a_ref = _get_ref_id(p_args[1])
            break
    if sqrt_a_ref is None:
        return False, "E_PREMISE_MISSING: missing SqrtQQ(D,A)"

    if resolvent_ref is None or p20_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p)"
    ok, err = _check_canonical_deg5_f20_resolvent_family(ctx, p20_ref)
    if not ok:
        return False, err

    if factors_ref is None:
        for prem in premises:
            p = prem.get("claim", prem)
            if not isinstance(p, Mapping) or p.get("pred") != "FactorizationMonicQQ":
                continue
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 3:
                return False, "E_PREMISE_BINDING: malformed FactorizationMonicQQ premise"
            if _get_ref_id(p_args[0]) == resolvent_ref:
                factors_ref = _get_ref_id(p_args[1])
                break
    if factors_ref is None:
        return False, "E_PREMISE_MISSING: missing FactorizationMonicQQ(R,factors,unit)"

    if linear_ref is None:
        return False, "E_PREMISE_MISSING: missing Degree(l,1)"

    factor_items = _decode_polyqqlist_items(factors_ref, ctx)
    if factor_items is None:
        return False, "E_TYPE: cannot decode factors as PolyQQList"
    if linear_ref not in factor_items:
        return False, "E_PREMISE_BINDING: l from Degree(l,1) is not listed in factors.items"

    theta, err = _extract_theta_from_linear_factor(ctx, linear_ref)
    if theta is None:
        return False, err

    pqrs, err = _extract_depressed_quintic_pqrs(ctx, f_ref)
    if pqrs is None:
        return False, err
    p_coef, q_coef, r_coef, s_coef = pqrs

    d_val = _decode_ratqq_to_frac(d_ref, ctx)
    if d_val is None:
        return False, "E_TYPE: cannot decode discriminant witness D"
    a_val = _decode_ratqq_to_frac(sqrt_a_ref, ctx)
    if a_val is None:
        return False, "E_TYPE: cannot decode square-root witness A"

    vals = eval_all(p=p_coef, q=q_coef, r=r_coef, s=s_coef, theta=theta, D=d_val)
    expected_quadratics = [
        [
            Fraction(1, 1),
            vals["T1"] + vals["T2"] * a_val,
            vals["T3"] + vals["T4"] * a_val,
        ],
        [
            Fraction(1, 1),
            vals["T1"] - vals["T2"] * a_val,
            vals["T3"] - vals["T4"] * a_val,
        ],
    ]
    expected_entries = [
        {"poly": q, "disc": _disc_quadratic_monic_desc(q)}
        for q in expected_quadratics
    ]

    matched_entries: list[dict[str, Any]] = []
    remaining = expected_entries.copy()
    for poly_ref, disc_ref in quadratic_disc_premises:
        q_actual = _decode_polyqq_to_fracs(poly_ref, ctx)
        if q_actual is None:
            return False, "E_TYPE: cannot decode candidate Dummit quadratic"
        for i, entry in enumerate(remaining):
            if q_actual == entry["poly"]:
                d_actual = _decode_ratqq_to_frac(disc_ref, ctx)
                if d_actual is None:
                    return False, "E_TYPE: cannot decode Dummit quadratic discriminant"
                if d_actual != entry["disc"]:
                    return False, (
                        "E_DUMMIT_D_MISMATCH: discriminant premise is not the "
                        "exact discriminant of its Dummit quadratic"
                    )
                matched = dict(entry)
                matched["poly_ref"] = poly_ref
                matched["disc_ref"] = disc_ref
                matched_entries.append(matched)
                remaining.pop(i)
                break

    if remaining:
        return False, (
            "E_DUMMIT_QUADRATICS_MISMATCH: missing Discriminant premises for "
            "the two canonical Dummit quadratics"
        )

    def _has_unary_gate(pred: str, rat_ref: str) -> tuple[bool, str]:
        for prem in premises:
            p = prem.get("claim", prem)
            if not isinstance(p, Mapping) or p.get("pred") != pred:
                continue
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 1:
                return False, f"E_PREMISE_BINDING: malformed {pred} premise"
            if _get_ref_id(p_args[0]) == rat_ref:
                return True, ""
        return False, ""

    if expect_all_square:
        for entry in matched_entries:
            found, err = _has_unary_gate("IsSquareQQ", str(entry["disc_ref"]))
            if err:
                return False, err
            if not found:
                return False, "E_PREMISE_MISSING: missing IsSquareQQ for both Dummit"
            " quadratic discriminants"
    else:
        found_nonsquare = False
        for entry in matched_entries:
            found, err = _has_unary_gate("NonSquareQQ", str(entry["disc_ref"]))
            if err:
                return False, err
            found_nonsquare = found_nonsquare or found
        if not found_nonsquare:
            return False, (
                "E_PREMISE_MISSING: expected NonSquareQQ for at least one "
                "Dummit quadratic discriminant"
            )

    obj = ctx.objects.get(g_ref)
    if not isinstance(obj, Mapping) or obj.get("kind") != "GroupId":
        return False, "E_TYPE: cannot decode GroupId"
    if obj.get("system") != "smallgroup":
        return False, "E_TYPE: GroupId.system must be 'smallgroup'"
    if obj.get("order") != expected_order or obj.get("index") != expected_index:
        return False, (f"E_GROUP_MISMATCH: expected"
                        f" (order,index)=({expected_order},{expected_index})")
    return True, ""


def _rule_galois_group_QQ_deg5_D5(*, claim: Mapping[str, Any],
                                  fact_id: str,
                                  evidence: Any,
                                  premises: list[Mapping[str, Any]],
                                  ctx: _V3Ctx) -> tuple[bool, str]:
    return _rule_galois_group_QQ_deg5_D5_or_C5(claim=claim, fact_id=fact_id,
                                               evidence=evidence, premises=premises, ctx=ctx,
                                               expect_all_square=False,
                                               expected_order=10, expected_index=2)


def _rule_galois_group_QQ_deg5_C5(*, claim: Mapping[str, Any],
                                  fact_id: str,
                                  evidence: Any, premises: list[Mapping[str, Any]],
                                  ctx: _V3Ctx) -> tuple[bool, str]:
    return _rule_galois_group_QQ_deg5_D5_or_C5(claim=claim, fact_id=fact_id,
                                               evidence=evidence, premises=premises, ctx=ctx,
                                               expect_all_square=True,
                                               expected_order=5, expected_index=1)

def _rule_galois_group_QQ_lift_depressed_monic(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    if claim.get("pred") != "GaloisGroup":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"

    f_ref = _get_ref_id(args_any[0])
    g_claim_ref = _get_ref_id(args_any[1])
    if f_ref is None or g_claim_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    normalized_ref: str | None = None
    found_group_on_g = False

    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping):
            continue
        pred = p.get("pred")
        p_args = p.get("args")
        if not isinstance(p_args, list):
            continue

        if pred == "DepressedMonicEq":
            if len(p_args) != 2:
                return False, "E_PREMISE_BINDING: malformed DepressedMonicEq premise"
            if _get_ref_id(p_args[0]) == f_ref:
                normalized_ref = _get_ref_id(p_args[1])

    if normalized_ref is None:
        return False, "E_PREMISE_MISSING: missing DepressedMonicEq(f,g)"

    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "GaloisGroup":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed GaloisGroup premise"
        if _get_ref_id(p_args[0]) == normalized_ref and _get_ref_id(p_args[1]) == g_claim_ref:
            found_group_on_g = True
            break

    if not found_group_on_g:
        return False, "E_PREMISE_MISSING: missing GaloisGroup(g,G) matching DepressedMonicEq(f,g)"

    return True, ""

def _lcm_nonneg(a: int, b: int) -> int:
    if a == 0:
        return abs(b)
    if b == 0:
        return abs(a)
    return abs(a * b) // gcd(a, b)


def _int_divisors(n: int) -> list[int]:
    n = abs(n)
    if n == 0:
        return [0]
    out: list[int] = []
    d = 1
    while d * d <= n:
        if n % d == 0:
            out.append(d)
            if d * d != n:
                out.append(n // d)
        d += 1
    return sorted(out)


def _poly_eval_desc(coeffs: list[Fraction], x: Fraction) -> Fraction:
    total = Fraction(0)
    for c in coeffs:
        total = total * x + c
    return total


def _has_rational_root_QQ_desc(coeffs: list[Fraction]) -> bool:
    if not coeffs or coeffs[0] == 0:
        raise ValueError("Malformed polynomial for rational-root test.")

    den_lcm = 1
    for c in coeffs:
        den_lcm = _lcm_nonneg(den_lcm, c.denominator)

    ints = [int(c * den_lcm) for c in coeffs]
    common = 0
    for n in ints:
        common = gcd(common, abs(n))
    if common > 1:
        ints = [n // common for n in ints]

    if ints[-1] == 0:
        return True

    lead = abs(ints[0])
    const = abs(ints[-1])
    int_coeffs = [Fraction(n, 1) for n in ints]

    for p in _int_divisors(const):
        for q in _int_divisors(lead):
            if q == 0 or gcd(p, q) != 1:
                continue
            for sign in (-1, 1):
                x = Fraction(sign * p, q)
                if _poly_eval_desc(int_coeffs, x) == 0:
                    return True
    return False


def _rule_irreducible_QQ_dummit_resolvent(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "IrreducibleQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"

    r_ref = _get_ref_id(args_any[0])
    if r_ref is None:
        return False, "E_TYPE: malformed ObjectRef"

    f_ref: str | None = None
    p_ref: str | None = None
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping):
            continue
        if p.get("pred") != "ResolventQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 3:
            return False, "E_PREMISE_BINDING: malformed ResolventQQ premise"
        r_candidate = _get_ref_id(p_args[0])
        f_candidate = _get_ref_id(p_args[1])
        p_candidate = _get_ref_id(p_args[2])
        if r_candidate == r_ref:
            f_ref = f_candidate
            p_ref = p_candidate
            break

    if f_ref is None:
        return False, "E_PREMISE_MISSING: missing ResolventQQ(R,f,p) for the claimed R"

    ok, err = _check_canonical_deg5_f20_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    n, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
        expected=5,
    )
    if n is None:
        return False, err

    found_irred_f = False
    for prem in premises:
        p = prem.get("claim", prem)
        if not isinstance(p, Mapping) or p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        if _get_ref_id(p_args[0]) == f_ref:
            found_irred_f = True
            break
    if not found_irred_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f)"

    r_poly = _decode_polyqq_to_fracs(r_ref, ctx)
    if r_poly is None:
        return False, "E_TYPE: cannot decode PolyQQ claim"

    try:
        theta = _find_rational_root_QQ_desc_resolvent_6_1plus5(
            _trim_leading_zeros_desc(r_poly)
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"E_TYPE: Dummit rational-root test setup failed: {exc}"

    if theta is not None:
        return False, "E_SIDE_CONDITION: Dummit resolvent has a rational root"
    return True, ""



def _rule_solvable_by_radicals_QQ_from_galois_group(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "SolvableByRadicals":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    if f_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    g_ref: str | None = None
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "GaloisGroup":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed GaloisGroup premise"
        p_f = _get_ref_id(p_args[0])
        p_g = _get_ref_id(p_args[1])
        if p_f is None or p_g is None:
            return False, "E_PREMISE_BINDING: malformed GaloisGroup premise (refs)"
        if p_f == f_ref:
            g_ref = p_g
            break
    if g_ref is None:
        return False, "E_PREMISE_MISSING: missing GaloisGroup(f,G) premise"

    pair = _decode_groupid_smallgroup(g_ref, ctx)
    if pair is None:
        return False, "E_TYPE: cannot decode GroupId"
    if pair in _RESOLVABLE_SMALLGROUPS:
        return True, ""
    if pair in _NONSOLVABLE_SMALLGROUPS:
        return False, "E_GROUP_NOT_RESOLVABLE: certified group is not resoluble"
    return False, "E_GROUP_UNSUPPORTED: unsupported SmallGroup identifier"


def _rule_nonsolvable_by_radicals_QQ_from_galois_group(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "NonSolvableByRadicals":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    if f_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    g_ref: str | None = None
    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "GaloisGroup":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 2:
            return False, "E_PREMISE_BINDING: malformed GaloisGroup premise"
        p_f = _get_ref_id(p_args[0])
        p_g = _get_ref_id(p_args[1])
        if p_f is None or p_g is None:
            return False, "E_PREMISE_BINDING: malformed GaloisGroup premise (refs)"
        if p_f == f_ref:
            g_ref = p_g
            break
    if g_ref is None:
        return False, "E_PREMISE_MISSING: missing GaloisGroup(f,G) premise"

    pair = _decode_groupid_smallgroup(g_ref, ctx)
    if pair is None:
        return False, "E_TYPE: cannot decode GroupId"
    if pair in _NONSOLVABLE_SMALLGROUPS:
        return True, ""
    if pair in _RESOLVABLE_SMALLGROUPS:
        return False, "E_GROUP_RESOLUBLE: certified group is resoluble"
    return False, "E_GROUP_UNSUPPORTED: unsupported SmallGroup identifier"


def _rule_irreducible_QQ_to_depressed_monic(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: Any,
) -> tuple[bool, str]:
    if claim.get("pred") != "IrreducibleQQ":
        return False, "E_TYPE: claim predicate must be IrreducibleQQ"
    args = claim.get("args")
    if not isinstance(args, list) or len(args) != 1:
        return False, "E_TYPE: IrreducibleQQ claim must have arity 1"

    g_claim = _get_ref_id(args[0])
    if g_claim is None:
        return False, "E_TYPE: malformed IrreducibleQQ claim"

    f_norm: str | None = None
    g_norm: str | None = None
    has_irr_f = False

    for prem in premises:
        p = prem.get("claim", prem)

        if p.get("pred") == "DepressedMonicEq":
            p_args = p.get("args")
            if not isinstance(p_args, list) or len(p_args) != 2:
                return False, "E_PREMISE_BINDING: malformed DepressedMonicEq premise"
            f_ref = _get_ref_id(p_args[0])
            g_ref = _get_ref_id(p_args[1])
            if f_ref is None or g_ref is None:
                return False, "E_PREMISE_BINDING: malformed DepressedMonicEq premise (refs)"
            f_norm = f_ref
            g_norm = g_ref
            continue

    if g_norm is None or f_norm is None:
        return False, "E_PREMISE_MISSING: missing DepressedMonicEq(f,g)"

    if g_claim != g_norm:
        return (False, "E_PREMISE_BINDING: claim must be "
                "IrreducibleQQ(g) for g from DepressedMonicEq(f,g)")

    for prem in premises:
        p = prem.get("claim", prem)
        if p.get("pred") != "IrreducibleQQ":
            continue
        p_args = p.get("args")
        if not isinstance(p_args, list) or len(p_args) != 1:
            return False, "E_PREMISE_BINDING: malformed IrreducibleQQ premise"
        p_f = _get_ref_id(p_args[0])
        if p_f == f_norm:
            has_irr_f = True
            break

    if not has_irr_f:
        return False, "E_PREMISE_MISSING: missing IrreducibleQQ(f) matching DepressedMonicEq(f,g)"

    return True, ""

def _rule_radical_roots_QQ_deg5_mcclintock_depressed_monic(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id
    _ = evidence

    if claim.get("pred") != "RadicalRoots":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 2:
        return False, "E_TYPE: arity"
    g_ref = _get_ref_id(args_any[0])
    roots_ref = _get_ref_id(args_any[1])
    if g_ref is None or roots_ref is None:
        return False, "E_TYPE: args must be ObjectRef"

    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=g_ref,
        ctx=ctx,
        expected=5,
    )
    if deg is None:
        return False, err

    ok_irred, err = _require_irreducible_premise(premises=premises, poly_ref=g_ref)
    if not ok_irred:
        return False, err

    dep, err = _require_depressed_monic_target_premise(premises=premises, target_ref=g_ref)
    if dep is None:
        return False, err

    res_prem, err = _require_resolvent_premise_for_poly(premises=premises, poly_ref=g_ref)
    if res_prem is None:
        return False, err
    r_ref, p_ref = res_prem

    ok, err = _check_canonical_deg5_f20_resolvent_family(ctx, p_ref)
    if not ok:
        return False, err

    factorization, err = _require_factorization_premise(premises=premises, poly_ref=r_ref)
    if factorization is None:
        return False, err
    factor_list_ref, unit_ref = factorization

    unit_val = _decode_ratqq_to_frac(unit_ref, ctx)
    if unit_val is None:
        return False, "E_TYPE: cannot decode RatQQ"
    if unit_val != 1:
        return False, "E_BAD_FACTORIZATION: expected unit = 1"

    list_obj = ctx.objects.get(factor_list_ref)
    if not isinstance(list_obj, Mapping) or list_obj.get("kind") != "PolyQQList":
        return False, "E_TYPE: cannot decode PolyQQList"
    items = list_obj.get("items")
    if not isinstance(items, list) or not items or not all(isinstance(x, str) and x for x in items):
        return False, "E_TYPE: invalid PolyQQList.items"

    theta: Fraction | None = None
    for ref in items:
        coeffs = _decode_polyqq_to_fracs(ref, ctx)
        if coeffs is None:
            return False, "E_TYPE: cannot decode PolyQQ"
        coeffs = _trim_leading_zeros_desc(coeffs)
        if len(coeffs) == 2:
            if coeffs[0] != 1:
                return False, "E_BAD_FACTORIZATION: linear factor must be monic"
            theta = -coeffs[1]
            break
    if theta is None:
        return False, "E_BAD_FACTORIZATION: expected a monic linear factor"

    poly = _decode_polyqq_to_fracs(g_ref, ctx)
    if poly is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    poly = _trim_leading_zeros_desc(poly)
    if len(poly) != 6 or poly[0] != 1 or poly[1] != 0:
        return False, "E_SIDE_CONDITION: polynomial is not a monic depressed quintic"

    try:
        expected_exprs = _deg5_mcclintock_build(coeffs_desc=poly, theta=theta)
    except Exception as e:  # noqa: BLE001
        return False, f"E_EXCEPTION: McClintock builder raised: {e}"

    expected = [_radical_expr_payload(dict(expr)) for expr in expected_exprs]

    actual = _decode_radical_expr_list_payloads(roots_ref, ctx)
    if actual is None:
        return False, "E_TYPE: cannot decode RadicalExprList"
    if actual != expected:
        return False, (
            "E_MISMATCH: claimed root list does not match canonical quintic McClintock scheme"
        )
    return True, ""

def _is_prime_int(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def _fpx_factor_to_desc_mod_p_strings(poly_asc: list[int], p: int) -> list[str]:
    asc = [coeff % p for coeff in poly_asc]
    while len(asc) > 1 and asc[-1] == 0:
        asc.pop()
    return [str(coeff % p) for coeff in reversed(asc)]


def _decode_mod_p_factorization_evidence(evidence: Any) -> tuple[int | None, int |
                                                                 None, list[list[str]] | None, str]:
    if not isinstance(evidence, Mapping):
        return None, None, None, "E_EVIDENCE: evidence must be an object"

    prime_s = evidence.get("prime")
    if not isinstance(prime_s, str) or not _INT_RE.fullmatch(prime_s):
        return None, None, None, "E_EVIDENCE: prime must be a canonical integer string"
    p = int(prime_s)
    if not _is_prime_int(p):
        return None, None, None, "E_EVIDENCE: prime is not prime"

    ell = evidence.get("ell")
    if not isinstance(ell, int) or isinstance(ell, bool) or ell < 0:
        return None, None, None, "E_EVIDENCE: ell must be a non-negative integer"

    mod_fac = evidence.get("mod_p_factorization")
    if not isinstance(mod_fac, Mapping):
        return None, None, None, "E_EVIDENCE: missing mod_p_factorization object"

    raw_factors = mod_fac.get("factors_desc")
    if not isinstance(raw_factors, list) or not raw_factors:
        return None, None, None, "E_EVIDENCE: factors_desc must be a non-empty list"

    factors: list[list[str]] = []
    for i, raw_factor in enumerate(raw_factors):
        if not isinstance(raw_factor, list) or not raw_factor:
            return None, None, None, f"E_EVIDENCE: factors_desc[{i}] must be a non-empty list"
        factor: list[str] = []
        for j, coeff in enumerate(raw_factor):
            if not isinstance(coeff, str) or not _INT_RE.fullmatch(coeff):
                return None, None, None, f"E_EVIDENCE: factors_desc[{i}][{j}] must "
            "be an integer string"
            c = int(coeff)
            if not (0 <= c < p):
                return None, None, None, f"E_EVIDENCE: factors_desc[{i}][{j}] not in [0,p)"
            factor.append(str(c))
        if factor[0] == "0":
            return None, None, None, f"E_EVIDENCE: factors_desc[{i}] has zero leading coefficient"
        factors.append(factor)

    return p, ell, factors, ""


def _rule_irreducible_QQ_zassenhaus_trace(
    *,
    claim: Mapping[str, Any],
    fact_id: str,
    evidence: Any,
    premises: list[Mapping[str, Any]],
    ctx: _V3Ctx,
) -> tuple[bool, str]:
    _ = fact_id

    if claim.get("pred") != "IrreducibleQQ":
        return False, "E_TYPE: claim.pred mismatch"
    args_any = claim.get("args")
    if not isinstance(args_any, list) or len(args_any) != 1:
        return False, "E_TYPE: arity"
    f_ref = _get_ref_id(args_any[0])
    if f_ref is None:
        return False, "E_TYPE: arg must be ObjectRef"

    deg, err = _require_degree_premise(
        premises=premises,
        poly_ref=f_ref,
        ctx=ctx,
    )
    if deg is None:
        return False, err
    if deg not in {2, 3, 4, 5}:
        return False, "E_SIDE_CONDITION: degree must be in {2,3,4,5}"

    f = _decode_polyqq_to_fracs(f_ref, ctx)
    if f is None:
        return False, "E_TYPE: cannot decode PolyQQ"
    f = _trim_leading_zeros_desc(f)
    if not f or f[0] == 0:
        return False, "E_TYPE: leading coefficient is zero"

    p, ell, claimed_factors, err = _decode_mod_p_factorization_evidence(evidence)
    if p is None or ell is None or claimed_factors is None:
        return False, err

    try:
        f_z = _trim_leading_zeros_desc_z(_primitive_integer_poly_from_QQ_desc(f))
        expected_p = _choose_zassenhaus_prime(f_z)
    except Exception as exc:  # noqa: BLE001
        return False, f"E_EXCEPTION: primitive model / prime choice failed: {exc}"

    if p != expected_p:
        return False, f"E_EVIDENCE: prime mismatch (expected {expected_p}, got {p})"

    try:
        _, _, factors_asc, _ = _modular_factorization_z(f_z, p)
    except Exception as exc:  # noqa: BLE001
        return False, f"E_EXCEPTION: modular factorization failed: {exc}"

    expected_factors = [_fpx_factor_to_desc_mod_p_strings(factor, p) for factor in factors_asc]
    if claimed_factors != expected_factors:
        return False, "E_EVIDENCE: modular factorization mismatch"

    if len(factors_asc) == 1:
        expected_ell = 0
    else:
        bound = _zassenhaus_factor_bound_z(f_z)
        expected_ell, _ = _hensel_precision_from_bound(p, bound)

    if ell != expected_ell:
        return False, f"E_EVIDENCE: ell mismatch (expected {expected_ell}, got {ell})"

    # Final normative irreducibility decision: replay the deterministic
    # degree-bounded Zassenhaus implementation used by the verifier.
    try:
        monic = [c / f[0] for c in f]
        factors = factorize_le5(monic)
    except Exception as exc:  # noqa: BLE001
        return False, f"E_EXCEPTION: factorization recomputation failed: {exc}"

    if len(factors) != 1 or _trim_leading_zeros_desc(factors[0]) != _trim_leading_zeros_desc(monic):
        return False, "E_NOT_IRREDUCIBLE: non-trivial factorization found"

    return True, ""

RULE_CHECKERS: dict[str, Any] = {
    "irreducible.QQ.deg5_recompute@1": _rule_irreducible_QQ_deg5_recompute,
    "factorization.QQ.monic@1": _rule_factorization_QQ_monic,
    "normalize.depressed_monic_QQ@1": _rule_normalize_depressed_monic_QQ,
    "irreducible.QQ.deg1_trivial@1": _rule_irreducible_QQ_deg1_trivial,
    "galois_group.QQ.deg1.trivial@1": _rule_galois_group_QQ_deg1_trivial,
    "degree.QQ@1": _rule_degree_QQ,
    "galois_group.QQ.deg2.C2@1": _rule_galois_group_QQ_deg2_C2,
    "disc.QQ.compute@1": _rule_disc_QQ_compute,
    "sqrt.QQ.check@1": _rule_sqrt_QQ_check,
    "is_square.QQ.lift@1": _rule_is_square_QQ_lift,
    "nonsquare.QQ.isqrt@1": _rule_nonsquare_QQ_isqrt,
    "nonsquare.QQ.isqrt@2": _rule_nonsquare_QQ_isqrt_v2,
    "disc.square.QQ.lift@1": _rule_disc_square_QQ_lift,
    "disc.nonsquare.QQ.lift@1": _rule_disc_nonsquare_QQ_lift,
    "galois_group.QQ.deg3.C3@1": _rule_galois_group_QQ_deg3_C3,
    "galois_group.QQ.deg3.S3@1": _rule_galois_group_QQ_deg3_S3,
    "resolvent.QQ.compute.deg4.cubic_x1x2_plus_x3x4@1": 
        _rule_resolvent_QQ_compute_deg4_cubic_x1x2_plus_x3x4,
    "resolvent.QQ.compute.deg4.cubic_x1plusx2_times_x3plusx4@1":
        _rule_resolvent_QQ_compute_deg4_cubic_x1plusx2_times_x3plusx4,
    "galois_group.QQ.deg4.S4@1": _rule_galois_group_QQ_deg4_S4,
    "galois_group.QQ.deg4.A4@1": _rule_galois_group_QQ_deg4_A4,
    "galois_group.QQ.deg4.V4@1": _rule_galois_group_QQ_deg4_V4,
    "galois_group.QQ.deg4.C4@1": _rule_galois_group_QQ_deg4_C4,
    "galois_group.QQ.deg4.D4.w1@1": _rule_galois_group_QQ_deg4_D4_w1,
    "galois_group.QQ.deg4.D4.w2@1": _rule_galois_group_QQ_deg4_D4_w2,
    "galois_group.QQ.deg4.S4@2": _rule_galois_group_QQ_deg4_S4_v2,
    "galois_group.QQ.deg4.A4@2": _rule_galois_group_QQ_deg4_A4_v2,
    "galois_group.QQ.deg4.V4@2": _rule_galois_group_QQ_deg4_V4_v2,
    "galois_group.QQ.deg4.V4@3": _rule_galois_group_QQ_deg4_V4_v3,
    "galois_group.QQ.deg4.C4@2": _rule_galois_group_QQ_deg4_C4_v2,
    "galois_group.QQ.deg4.D4.w1@2": _rule_galois_group_QQ_deg4_D4_w1_v2,
    "galois_group.QQ.deg4.D4.w2@2": _rule_galois_group_QQ_deg4_D4_w2_v2,
    "galois_group.QQ.reducible.all_linear.trivial@1": 
        _rule_galois_group_QQ_reducible_all_linear_trivial,
    "galois_group.QQ.reducible.single_nonlinear.inherit@1": 
        _rule_galois_group_QQ_reducible_single_nonlinear_inherit,
    "galois_group.QQ.reducible.double_quadratic.C2@1":
        _rule_galois_group_QQ_reducible_double_quadratic_C2,
    "galois_group.QQ.reducible.double_quadratic.V4@1":
        _rule_galois_group_QQ_reducible_double_quadratic_V4,
    "galois_group.QQ.reducible.quadratic_cubic.C6@1":
        _rule_galois_group_QQ_reducible_quadratic_cubic_C6,
    "galois_group.QQ.reducible.quadratic_cubic.S3@1":
        _rule_galois_group_QQ_reducible_quadratic_cubic_S3,
    "galois_group.QQ.reducible.quadratic_cubic.D6@1":
        _rule_galois_group_QQ_reducible_quadratic_cubic_D6,
    "galois_group.QQ.reducible.quadratic_cubic.S3@2":
        _rule_galois_group_QQ_reducible_quadratic_cubic_S3_v2,
    "galois_group.QQ.reducible.quadratic_cubic.D6@2":
        _rule_galois_group_QQ_reducible_quadratic_cubic_D6_v2,
    "resolvent.QQ.compute.deg5.sextic_dummit_F20@1":
        _rule_resolvent_QQ_compute_deg5_sextic_dummit_F20,
    "galois_group.QQ.deg5.S5@1": _rule_galois_group_QQ_deg5_S5,
    "galois_group.QQ.deg5.A5@1": _rule_galois_group_QQ_deg5_A5,
    "galois_group.QQ.deg5.F20@1": _rule_galois_group_QQ_deg5_F20,
    "galois_group.QQ.deg5.D5@1": _rule_galois_group_QQ_deg5_D5,
    "galois_group.QQ.deg5.C5@1": _rule_galois_group_QQ_deg5_C5,
    "galois_group.QQ.lift.depressed_monic@1": _rule_galois_group_QQ_lift_depressed_monic,
    "irreducible.QQ.dummit_resolvent@1": _rule_irreducible_QQ_dummit_resolvent,
    "solvable_by_radicals.QQ.from_galois_group@1":
        _rule_solvable_by_radicals_QQ_from_galois_group,
    "nonsolvable_by_radicals.QQ.from_galois_group@1": 
        _rule_nonsolvable_by_radicals_QQ_from_galois_group,
    "radical_roots.QQ.reducible.compose@1": _rule_radical_roots_QQ_reducible_compose,
    "radical_roots.QQ.deg1.trivial@1": _rule_radical_roots_QQ_deg1_trivial,
    "radical_roots.QQ.deg2.quadratic_formula@1": _rule_radical_roots_QQ_deg2_quadratic_formula,
    "radical_roots.QQ.deg3.cardano.depressed_monic@1": 
        _rule_radical_roots_QQ_deg3_cardano_depressed_monic,
    "radical_roots.QQ.deg3.cardano.depressed_monic@2":
        _rule_radical_roots_QQ_deg3_cardano_depressed_monic_v2,
    "radical_roots.QQ.deg4.ferrari.depressed_monic@1":
        _rule_radical_roots_QQ_deg4_ferrari_depressed_monic,
    "radical_roots.QQ.deg4.ferrari.depressed_monic@2":
        _rule_radical_roots_QQ_deg4_ferrari_depressed_monic_v2,
    "radical_roots.QQ.deg4.resolvent_symmetric.depressed_monic@1": 
        _rule_radical_roots_QQ_deg4_resolvent_symmetric_depressed_monic,
    "radical_roots.QQ.lift.depressed_monic@1": _rule_radical_roots_QQ_lift_depressed_monic,
    "radical_roots.QQ.reducible.compose@2": _rule_radical_roots_QQ_reducible_compose_v2,
    "irreducible.QQ.to.depressed_monic@1": _rule_irreducible_QQ_to_depressed_monic,
    "radical_roots.QQ.deg5.mcclintock.depressed_monic@1":
        _rule_radical_roots_QQ_deg5_mcclintock_depressed_monic,
    "irreducible.QQ.zassenhaus_trace@1": _rule_irreducible_QQ_zassenhaus_trace,
    
}

def verify_certificate(certificate: Mapping[str, Any]) -> VerifiedResult:
    """Verify an OpenGalois v3 certificate (fact+rule format), skeleton version."""
    checks: list[CheckResult] = []

    # (1) Schema conformance
    try:
        schema = _load_schema_v300()
        validator = Draft202012Validator(schema)
        errors = sorted(
            validator.iter_errors(certificate),
            key=lambda e: list(getattr(e, "absolute_path", [])),
        )
    except Exception as e:  # noqa: BLE001
        _add(checks, "schema.conformance", False, f"Schema validation failed: {e}")
        return VerifiedResult(False, tuple(checks))

    if errors:
        msg = "; ".join(_format_schema_error(e) for e in errors[:8])
        _add(checks, "schema.conformance", False, msg)
        return VerifiedResult(False, tuple(checks))
    _add(checks, "schema.conformance", True)

    # (2) meta + ruleset gating
    meta = certificate.get("meta")
    if not isinstance(meta, Mapping):
        _add(checks, "meta.present", False, "Missing or invalid 'meta' object")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "meta.present", True)

    schema_version = meta.get("schema_version")
    if schema_version != _SCHEMA_VERSION:
        _add(checks, "meta.schema_version", False, f"Expected schema_version={_SCHEMA_VERSION!r}")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "meta.schema_version", True)

    ruleset_id = meta.get("ruleset_id")
    if not isinstance(ruleset_id, str) or not ruleset_id:
        _add(checks, "meta.ruleset_id", False, "Missing or invalid meta.ruleset_id")
        return VerifiedResult(False, tuple(checks))

    try:
        ruleset = get_ruleset(ruleset_id)
    except Exception as e:  # noqa: BLE001
        _add(checks, "ruleset.known", False, str(e))
        return VerifiedResult(False, tuple(checks))
    _add(checks, "ruleset.known", True, ruleset_id)

    # (3) input well-formedness + hash
    inp = certificate.get("input")
    if not isinstance(inp, Mapping):
        _add(checks, "input.present", False, "Missing or invalid 'input' object")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "input.present", True)

    deg = inp.get("degree")
    if not isinstance(deg, int) or deg < 1:
        _add(checks, "input.degree", False, "input.degree must be an integer >= 1")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "input.degree", True, str(deg))

    coeffs_qq_any = inp.get("coeffs_qq")
    ok_poly, coeffs_qq = _validate_polyqq_block(checks, "input.coeffs_qq", coeffs_qq_any)
    if not ok_poly:
        return VerifiedResult(False, tuple(checks))
    if len(coeffs_qq) != deg + 1:
        _add(checks, "input.coeffs_qq.degree_len", False, 
             f"Expected {deg+1} coefficients for degree {deg}")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "input.coeffs_qq.degree_len", True)

    h = inp.get("hash")
    if not isinstance(h, str) or not _HASH_RE.match(h):
        _add(checks, "input.hash.format", False, 
             "input.hash must be a 64-char lowercase hex string")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "input.hash.format", True)

    try:
        scope = _build_scope_from_input(inp, coeffs_qq)
        expected_hash = compute_input_hash(scope)
    except Exception as e:  # noqa: BLE001
        _add(checks, "input.hash.recompute", False, f"Failed to recompute input hash: {e}")
        return VerifiedResult(False, tuple(checks))

    if expected_hash != h:
        _add(checks, "input.hash.match", False, f"Hash mismatch: expected {expected_hash}, got {h}")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "input.hash.match", True)

    # (4) objects basic shape
    objects_any = certificate.get("objects", {})
    if not isinstance(objects_any, Mapping):
        _add(checks, "objects.present", False, "objects must be an object/map when present")
        return VerifiedResult(False, tuple(checks))
    objects = cast(Mapping[str, Any], objects_any)
    _add(checks, "objects.present", True, f"{len(objects)} objects")

    if _INPUT_REF in objects:
        _add(checks, "objects.no_input_key", False, "objects must not contain a '$input' key")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "objects.no_input_key", True)

    for oid, obj in objects.items():
        if not (isinstance(obj, Mapping) and isinstance(obj.get("kind"), str) 
                and obj.get("kind")):
            _add(checks, "objects.kind_present", False, 
                 f"Object {oid!r} must be an object with non-empty 'kind'")
            return VerifiedResult(False, tuple(checks))
    _add(checks, "objects.kind_present", True)

    ctx = _V3Ctx(input_block=inp, input_coeffs_qq=coeffs_qq, objects=objects, checks=checks)

    # (5) typed object decoding (incl. composite kinds)
    validated: dict[tuple[str, str], bool] = {}

    def validate_ref_as_kind(ref: str, expected_kind: str, where: str) -> bool:
        if ref == _INPUT_REF:
            if expected_kind != "PolyQQ":
                _add(checks, f"{where}.ref_kind", False, 
                     f"$input used where {expected_kind} expected")
                return False
            return True

        key = (ref, expected_kind)
        if key in validated:
            return validated[key]

        obj = ctx.objects.get(ref)
        if obj is None:
            _add(checks, f"{where}.object_ref", False, f"Missing object id: {ref!r}")
            validated[key] = False
            return False
        actual_kind = cast(Mapping[str, Any], obj).get("kind", "")
        if actual_kind != expected_kind:
            _add(checks, f"{where}.kind", False, 
                 f"Expected kind {expected_kind!r} for {ref!r}, got {actual_kind!r}")
            validated[key] = False
            return False

        ok = True
        if expected_kind == "PolyQQ":
            ok, _ = _validate_polyqq_block(checks, f"objects[{ref}].coeffs_qq", 
                                           cast(Mapping[str, Any], obj).get("coeffs_qq"))
        elif expected_kind == "MPolyQQ":
            ok = _validate_mpolyqq_block(checks, f"objects[{ref}]", obj)
        elif expected_kind == "RatQQ":
            ok = _validate_ratqq_value(checks, f"objects[{ref}].value",
                                       cast(Mapping[str, Any], obj).get("value"))
        elif expected_kind == "IntZ":
            ok = _validate_intz_value(checks, f"objects[{ref}].value",
                                      cast(Mapping[str, Any], obj).get("value"))
        elif expected_kind == "PolyQQList":
            items = cast(Mapping[str, Any], obj).get("items")
            if not isinstance(items, list) or not all(isinstance(x, str)
                                                      and x for x in items):
                _add(checks, f"objects[{ref}].items.shape", False, 
                     "PolyQQList.items must be a list[str] of non-empty ids")
                ok = False
            else:
                for j, item_id in enumerate(cast(list[str], items)):
                    if item_id == _INPUT_REF:
                        _add(checks, f"objects[{ref}].items.ref", False, 
                             "PolyQQList.items must not reference $input")
                        ok = False
                        break
                    if not validate_ref_as_kind(item_id, "PolyQQ", f"objects[{ref}].items[{j}]"):
                        ok = False
                        break
        elif expected_kind == "GroupId":
            ok = _validate_groupid_block(
                checks,
                f"objects[{ref}]",
                obj,
            )
        elif expected_kind == "RadicalExpr":
            ok = _validate_radical_expr_block(
                checks,
                f"objects[{ref}]",
                obj,
                ctx=ctx,
            )
        elif expected_kind == "RadicalExprList":
            ok = _validate_radical_expr_list_block(
                checks,
                f"objects[{ref}]",
                obj,
                ctx=ctx,
            )
        else:
            _add(checks, f"{where}.kind_supported", False, 
                 f"Unsupported kind in verifier skeleton: {expected_kind!r}")
            ok = False

        validated[key] = ok
        return ok

    # Validate every object payload against its declared kind, even if unused by the proof.
    objects_ok = True
    for oid, obj_any in objects.items():
        obj_map = cast(Mapping[str, Any], obj_any)
        actual_kind = cast(str, obj_map.get("kind"))
        if not validate_ref_as_kind(oid, actual_kind, f"objects[{oid}]"):
            objects_ok = False
    _add(checks, "objects.typed_payloads", objects_ok)
    if not objects_ok:
        return VerifiedResult(False, tuple(checks))

    # (6) proof + streaming checks + rule dispatch strict
    proof = certificate.get("proof")
    if not isinstance(proof, Mapping):
        _add(checks, "proof.present", False, "Missing or invalid 'proof' object")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "proof.present", True)

    version = proof.get("version")
    if not isinstance(version, str) or not version:
        _add(checks, "proof.version", False, "proof.version must be a non-empty string")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "proof.version", True, version)

    facts_any = proof.get("facts", [])
    if not isinstance(facts_any, list):
        _add(checks, "proof.facts.shape", False, "proof.facts must be a list")
        return VerifiedResult(False, tuple(checks))
    facts = facts_any
    if not facts:
        _add(checks, "proof.facts.nonempty", False, "Proof must contain at least one fact node")
        return VerifiedResult(False, tuple(checks))
    _add(checks, "proof.facts.nonempty", True, str(len(facts)))

    proved: dict[str, Mapping[str, Any]] = {}
    seen: set[str] = set()

    for idx, node_any in enumerate(facts):
        where = f"proof.facts[{idx}]"
        if not isinstance(node_any, Mapping):
            _add(checks, f"{where}.shape", False, "FactNode must be an object")
            continue
        node = cast(Mapping[str, Any], node_any)

        fid = node.get("id")
        if not isinstance(fid, str) or not fid:
            _add(checks, f"{where}.id", False, "FactNode.id must be a non-empty string")
            continue
        if fid in seen:
            _add(checks, f"{where}.id_unique", False, f"Duplicate fact id: {fid!r}")
            continue
        seen.add(fid)

        claim_any = node.get("claim")
        if not isinstance(claim_any, Mapping):
            _add(checks, f"{where}.claim", False, "Missing/invalid claim object")
            continue
        claim = cast(Mapping[str, Any], claim_any)

        pred = claim.get("pred")
        if not isinstance(pred, str) or not pred:
            _add(checks, f"{where}.claim.pred", False, 
                 "claim.pred must be a non-empty string")
            continue

        spec = ruleset.predicates.get(pred)
        if spec is None:
            _add(checks, f"{where}.claim.pred_known", False, 
                 f"Unknown predicate for ruleset {ruleset_id!r}: {pred!r}")
            continue

        args_any = claim.get("args")
        if not isinstance(args_any, list):
            _add(checks, f"{where}.claim.args", False, "claim.args must be a list")
            continue
        args = args_any

        if len(args) != len(spec.arg_kinds):
            _add(checks, f"{where}.claim.arity", False, 
                 f"Expected {len(spec.arg_kinds)} args, got {len(args)}")
            continue

        premises_any = node.get("premises", [])
        if not isinstance(premises_any, list) or not all(isinstance(x, str)
                                                         and x for x in premises_any):
            _add(checks, f"{where}.premises.shape", False, "premises must be a list[str]")
            continue
        premises = cast(list[str], premises_any)
        ok_prem = True
        for p_id in premises:
            if p_id not in proved:
                _add(checks, f"{where}.premises.order", False, 
                     f"Premise {p_id!r} not verified earlier (no forward refs)")
                ok_prem = False
                break
        if not ok_prem:
            continue

        rule_id = node.get("rule")
        if not isinstance(rule_id, str) or not rule_id:
            _add(checks, f"{where}.rule", False, "rule must be a non-empty string")
            continue
        if rule_id not in ruleset.allowed_rules:
            _add(checks, f"{where}.rule.allowed", False, 
                 f"Rule not allowed by ruleset {ruleset_id!r}: {rule_id!r}")
            continue

        evidence = node.get("evidence", None)  # extracted for future checker plumbing

        ok_args = True
        for j, (arg_any, expected_kind) in enumerate(zip(args, spec.arg_kinds, strict=True)):
            ref = _get_ref_id(arg_any)
            if ref is None:
                _add(checks, f"{where}.claim.args[{j}].ref", False, 
                     "Each arg must be an ObjectRef {'ref': <id>}")
                ok_args = False
                break
            if not validate_ref_as_kind(ref, expected_kind, f"{where}.claim.args[{j}]"):
                ok_args = False
                break
        if not ok_args:
            continue
        checker = RULE_CHECKERS.get(rule_id)
        if checker is None:
            _add(checks, "v3.rule.dispatch.implemented", False, 
                 f"Missing checker for rule: {rule_id!r} (fact id {fid!r})")
            continue

        premise_claims = [proved[p_id] for p_id in premises]
        ok_rule, details = checker(
            claim=claim,
            fact_id=fid,
            evidence=evidence,
            premises=premise_claims,
            ctx=ctx,
        )
        _add(checks, f"v3.rule.{rule_id}", ok_rule, (details or f"fact id {fid!r}"))
        if ok_rule:
            proved[fid] = claim
        else:
            continue

    verified = all(c.ok for c in checks)
    return VerifiedResult(verified, tuple(checks))


