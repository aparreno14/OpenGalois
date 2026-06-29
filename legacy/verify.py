from __future__ import annotations

import json
import re
from collections.abc import Mapping
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from .certificate import compute_input_hash
from .models import CheckResult, VerifiedResult
from .polyops.desc_qx import (
    _mul_desc,
    _mul_scalar_desc,
    _pow_desc,
    _shift_desc,
    _trim_leading_zeros_desc,
)

try:
    from importlib.resources import files as resource_files
except Exception:  # pragma: no cover
    resource_files = None # type: ignore[assignment]

from jsonschema import Draft202012Validator

SUPPORTED_SCHEMA_VERSIONS = {"1.1.0"}
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_STATUSES_UNKNOWN = {"unclassified", "reducible", "error"}
_SCHEMA_VERSION = "1.1.0"
_SCHEMA_RESOURCE = "schemas/certificate/1.1.0.json"


def _build_scope_from_input(inp: Mapping[str, Any], coeffs_qq: list[str]) -> dict[str, Any]:
    return {
        "domain": inp["domain"],
        "variable": inp["variable"],
        "ordering": inp["ordering"],
        "degree": inp["degree"],
        "coeffs_qq": coeffs_qq,
    }


@lru_cache
def _load_schema_v110() -> dict[str, Any]:
    # 1) Prefer packaged resource (recommended for installed usage)
    if resource_files is not None:
        try:
            p = resource_files("opengalois").joinpath(_SCHEMA_RESOURCE)
            if p.is_file():
                content = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(content, dict):
                    raise TypeError(f"The scheme in {p} must be a JSON object, got {type(content)}")
                return content
        except (FileNotFoundError, ModuleNotFoundError):
            pass

    # 2) Fallback: repo checkout path (works in dev)
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # .../src/opengalois/verify.py -> parents[2] == repo root
    p2 = repo_root / "schemas" / "certificate" / f"{_SCHEMA_VERSION}.json"
    if p2.is_file():
        content = json.loads(p2.read_text(encoding="utf-8"))
        if not isinstance(content, dict):
            raise TypeError(f"The scheme in {p2} must be a JSON object, got {type(content)}")
        return content

    raise FileNotFoundError("Could not locate schemas/certificate/1.1.0.json")


def _format_schema_error(err: Any) -> str:
    # jsonschema ValidationError has absolute_path and message
    path = getattr(err, "absolute_path", [])
    if path:
        loc = "$" + "".join(f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in path)
    else:
        loc = "$"
    msg = getattr(err, "message", str(err))
    return f"{loc}: {msg}"


def verify_certificate(certificate: Mapping[str, Any]) -> VerifiedResult:
    """Validate certificate consistency and witness soundness checks."""
    checks: list[CheckResult] = []

    # --- Schema-first: Draft 2020-12 JSON Schema v1.1.0 ---
    try:
        schema = _load_schema_v110()
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(certificate), key=lambda e:
            list(getattr(e, "absolute_path", [])))
    except Exception as e:  # noqa: BLE001
        checks.append(CheckResult("schema.conformance", False, f"Schema validation failed: {e}"))
        return VerifiedResult(False, tuple(checks))

    if errors:
        msg = "; ".join(_format_schema_error(e) for e in errors[:5])
        if len(errors) > 5:
            msg += f" (+{len(errors) - 5} more)"
        checks.append(CheckResult("schema.conformance", False, msg))
    else:
        checks.append(CheckResult("schema.conformance", True))

    meta = certificate.get("meta")
    inp = certificate.get("input")
    result = certificate.get("result")

    if not isinstance(meta, Mapping):
        checks.append(CheckResult("meta.present", False, "Missing or invalid 'meta' object"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("meta.present", True))

    if not isinstance(inp, Mapping):
        checks.append(CheckResult("input.present", False, "Missing or invalid 'input' object"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("input.present", True))

    if not isinstance(result, Mapping):
        checks.append(CheckResult("result.present", False, "Missing or invalid 'result' object"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("result.present", True))

    schema_version = meta.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        checks.append(CheckResult("meta.schema_version", False, "Missing/invalid schema_version"))
    elif schema_version in SUPPORTED_SCHEMA_VERSIONS:
        checks.append(CheckResult("meta.schema_version", True))
    else:
        checks.append(
            CheckResult(
            "meta.schema_version",
            False,
            (
                f"Unsupported schema_version: {schema_version!r}. "
                f"Supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
            ),
            )
        )

    status = result.get("status")
    gg = result.get("galois_group")
    sbr = result.get("solvable_by_radicals")
    if not isinstance(status, str) or not isinstance(gg, str) or not (isinstance(sbr, bool) 
                                                                      or sbr is None):
        checks.append(CheckResult("result.shape", False, "Invalid result fields/types"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("result.shape", True))

    checks.append(CheckResult("input.domain", inp.get("domain") == "Q", "input.domain must be 'Q'"))
    checks.append(CheckResult("input.variable", inp.get("variable") == "x",
                              "input.variable must be 'x'"))
    checks.append(
        CheckResult(
            "input.ordering",
            inp.get("ordering") == "descending_degree",
            "input.ordering must be 'descending_degree'",
        )
    )
    checks.append(CheckResult("input.degree", inp.get("degree") == 5, "input.degree must be 5"))
    checks.append(
        CheckResult(
            "input.canonicalization",
            inp.get("canonicalization") == "jcs-rfc8785",
            "input.canonicalization must be 'jcs-rfc8785'",
        )
    )
    checks.append(CheckResult("input.hash_alg", inp.get("hash_alg") == "sha256",
                              "input.hash_alg must be 'sha256'"))
    checks.append(CheckResult("input.hash_scope", inp.get("hash_scope") == "input_v1",
                              "input.hash_scope must be 'input_v1'"))

    actual_hash = inp.get("hash")
    if not isinstance(actual_hash, str):
        checks.append(CheckResult("input.hash.present", False, "Missing/invalid input.hash"))
        checks.append(CheckResult("input.hash.format", False,
                                  "input.hash must be 64 lowercase hex chars"))
    else:
        checks.append(CheckResult("input.hash.present", True))
        checks.append(
            CheckResult(
                "input.hash.format",
                bool(_HASH_RE.fullmatch(actual_hash)),
                "input.hash must be 64 lowercase hex chars",
            )
        )

    coeffs_qq = inp.get("coeffs_qq")
    if not isinstance(coeffs_qq, list) or not all(isinstance(x, str) for x in coeffs_qq):
        checks.append(CheckResult("input.coeffs_qq", False, "coeffs_qq must be a list[str]"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("input.coeffs_qq", True))

    try:
        coeffs = [_parse_fraction(x) for x in coeffs_qq]
    except Exception as e:  # noqa: BLE001
        checks.append(CheckResult("input.coeffs_qq.parse", False,
                                  f"Failed to parse coeffs_qq: {e}"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("input.coeffs_qq.parse", True))

    if len(coeffs) != 6:
        checks.append(CheckResult("input.coeff_count", False,
                                  "Expected 6 coefficients for degree-5 polynomial"))
        checks.append(CheckResult("input.leading_coeff", False,
                                  "Leading coefficient not checked: invalid degree"))
    else:
        checks.append(CheckResult("input.coeff_count", True))
        checks.append(CheckResult("input.leading_coeff", coeffs[0] != 0,
                                  "Leading coefficient must be non-zero"))
        
    # --- Canonical encoding check (strong): rationals must be reduced and sign-normalized ---
    # This enforces the "SHOULD" in the schema description and is required for determinism:
    # equivalent rationals like "2/4" must be rejected (not canonical).
    noncanon = [s for s in coeffs_qq if not _is_canonical_rational_str(s)]
    details_noncanon = ""
    if noncanon:
        details_noncanon = (
            f"Non-canonical rational encodings in input.coeffs_qq: {noncanon[:3]}"
            + (f" (+{len(noncanon)-3} more)" if len(noncanon) > 3 else "")
        )
    checks.append(CheckResult("input.coeffs_qq.canonical", not noncanon, details_noncanon))


    # --- Witness check: normalization (depressed_monic_QQ) ---
    norm = certificate.get("normalization")
    if not isinstance(norm, Mapping):
        checks.append(CheckResult("normalization.witness", True, "N/A (no normalization)"))
        checks.append(CheckResult("normalization.canonical", True, "N/A (no normalization)"))
    else:
        basis = norm.get("basis")
        shift_any = norm.get("tschirnhaus_shift")
        scale_any = norm.get("monic_scale")
        poly_any = norm.get("poly_coeffs")

        # basic shape
        shape_ok = (
            basis == "depressed_monic_QQ"
            and isinstance(shift_any, str)
            and isinstance(scale_any, str)
            and isinstance(poly_any, list)
            and len(poly_any) == 6
            and all(isinstance(x, str) for x in poly_any)
        )
        if not shape_ok:
            checks.append(
                CheckResult(
                    "normalization.witness",
                    False,
                    "Invalid normalization shape/fields (basis/tschirnhaus_shift/monic_scale/"
                    "poly_coeffs)",
                )
            )
            checks.append(CheckResult("normalization.canonical", False,
                                      "Skipped (invalid normalization)"))
        else:
            shift_s = cast(str, shift_any)
            scale_s = cast(str, scale_any)
            poly_s = cast(list[str], poly_any)
            # strong canonicality on normalization rationals too
            bad_norm: list[tuple[str, object]] = []
            if not _is_canonical_rational_str(shift_s):
                bad_norm.append(("tschirnhaus_shift", shift_s))
            if not _is_canonical_rational_str(scale_s):
                bad_norm.append(("monic_scale", scale_s))
            bad_poly = [s for s in poly_s if not _is_canonical_rational_str(s)]
            if bad_poly:
                bad_norm.append(("poly_coeffs", bad_poly[:3] + 
                                 (["..."] if len(bad_poly) > 3 else [])))

            checks.append(
                CheckResult(
                    "normalization.canonical",
                    len(bad_norm) == 0,
                    f"Non-canonical rational encodings in normalization: {bad_norm}" 
                    if bad_norm else "",
                )
            )

            # parse normalization fields
            try:
                shift = _parse_fraction(shift_s)
                scale = _parse_fraction(scale_s)
                poly = [_parse_fraction(x) for x in poly_s]
            except Exception as e:  # noqa: BLE001
                checks.append(CheckResult("normalization.witness", False, 
                                          f"Parse failed: {e}"))
            else:
                # reconstruct g(x) = 1/scale * f(x - shift)
                # coeffs is f in descending order already
                try:
                    f_desc = _trim_leading_zeros_desc(coeffs)
                    g_desc = _shift_desc(f_desc, -shift)          # f(x - shift)
                    g_desc = _mul_scalar_desc(g_desc, 1/scale)      # 1/scale * ...
                    g_desc = _trim_leading_zeros_desc(g_desc)
                except Exception as e:  # noqa: BLE001
                    checks.append(CheckResult("normalization.witness", False, 
                                              f"Reconstruction failed: {e}"))
                else:
                    # Must be degree-5 with [1,0,*,*,*,*]
                    ok_len = (len(g_desc) == 6 and len(poly) == 6)
                    ok_head = ok_len and (g_desc[0] == 1 and g_desc[1] == 0)
                    ok_equal = ok_len and (g_desc == poly)
                    msg_parts = []
                    if not ok_len:
                        msg_parts.append("Expected 6 coefficients after normalization")
                    if ok_len and not ok_head:
                        msg_parts.append("Expected depressed monic head [1,0,...]")
                    if ok_len and not ok_equal:
                        msg_parts.append("Recomputed normalized polynomial does not "
                                         "match normalization.poly_coeffs")

                    checks.append(
                        CheckResult(
                            "normalization.witness",
                            ok_len and ok_head and ok_equal,
                            "; ".join(msg_parts) if msg_parts else "",
                        )
                    )

    # --- Witness check: factorization_QQ explicit factors (when present) ---
    checks_obj = certificate.get("checks")
    fact = checks_obj.get("factorization_QQ") if isinstance(checks_obj, Mapping) else None

    # If status is reducible, factorization_QQ MUST be present (schema enforces, but verifier too).
    if status == "reducible" and not isinstance(fact, Mapping):
        checks.append(
            CheckResult(
                "checks.factorization_QQ.present_for_reducible",
                False,
                "Missing checks.factorization_QQ for status='reducible'",
            )
        )
        checks.append(
            CheckResult(
                "checks.factorization_QQ.product",
                False,
                "Skipped: missing checks.factorization_QQ",
            )
        )
    elif not isinstance(fact, Mapping):
        checks.append(
            CheckResult(
                "checks.factorization_QQ.product",
                True,
                "N/A (no checks.factorization_QQ)",
            )
        )
    else:
        is_irred = fact.get("is_irreducible")

        # If this is a reducible factorization witness, unit + factors are mandatory.
        if is_irred is False:
            unit_s = fact.get("unit")
            factors = fact.get("factors")
            try:
                if not isinstance(unit_s, str):
                    raise ValueError("missing/invalid factorization_QQ.unit (expected string)")
                if not _is_canonical_rational_str(unit_s):
                    raise ValueError("factorization_QQ.unit must be canonical rational string")
                unit = _parse_fraction(unit_s)
                if unit == 0:
                    raise ValueError("factorization_QQ.unit must be non-zero")

                if not isinstance(factors, list):
                    raise ValueError("missing/invalid factorization_QQ.factors (expected list)")

                prod: list[Fraction] = [Fraction(1)]
                for fobj in factors:
                    if not isinstance(fobj, Mapping):
                        raise ValueError("factor entry must be an object")
                    cqq = fobj.get("coeffs_qq")
                    if not (isinstance(cqq, list) and all(isinstance(x, str) for x in cqq)):
                        raise ValueError("factor coeffs_qq must be list[str]")

                    # Determinism: enforce canonical rationals in factor coeffs too.
                    noncanon = [s for s in cqq if not _is_canonical_rational_str(s)]
                    if noncanon:
                        raise ValueError(
                            "non-canonical rational encodings in factor coeffs_qq: "
                            + repr(noncanon[:3])
                            + (f" (+{len(noncanon)-3} more)" if len(noncanon) > 3 else "")
                        )

                    poly = [_parse_fraction(x) for x in cqq]
                    poly = _trim_leading_zeros_desc(poly)
                    if not poly:
                        raise ValueError("factor polynomial must be non-zero")
                    if len(poly) < 2:
                        raise ValueError("factor polynomial must be non-constant")
                    # Normative: factors are monic; global scalar goes to unit.
                    if poly[0] != 1:
                        raise ValueError("factor polynomial must be monic (leading coeff = 1)")

                    mult = fobj.get("multiplicity")
                    if not isinstance(mult, int) or mult < 1:
                        raise ValueError("factor multiplicity must be integer >= 1")

                    prod = _mul_desc(prod, _pow_desc(poly, mult))

                # Exact check vs input polynomial in Q[x]:
                # unit * Π(f_i^m_i) == input
                prod = _mul_scalar_desc(prod, unit)
                prod = _trim_leading_zeros_desc(prod)
                target = _trim_leading_zeros_desc(coeffs)
                ok = (prod == target)
            except Exception as e:  # noqa: BLE001
                checks.append(
                    CheckResult(
                        "checks.factorization_QQ.product",
                        False,
                        f"Invalid factorization: {e}",
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        "checks.factorization_QQ.product",
                        ok,
                        "unit * Π(f_i^multiplicity) must equal input polynomial in Q[x]",
                    )
                )

        elif is_irred is True:
            # Irreducible witness: no reducible product obligation.
            # (Schema should already ensure unit/factors absent.)
            if status == "reducible":
                checks.append(
                    CheckResult(
                        "checks.factorization_QQ.is_irreducible_for_reducible_status",
                        False,
                        "factorization_QQ.is_irreducible must be false when status='reducible'",
                    )
                )
                checks.append(
                    CheckResult(
                        "checks.factorization_QQ.product",
                        False,
                        "Skipped: inconsistent is_irreducible for reducible status",
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        "checks.factorization_QQ.product",
                        True,
                        "N/A (is_irreducible=true)",
                    )
                )
        else:
            checks.append(
                CheckResult(
                    "checks.factorization_QQ.product",
                    False,
                    "Invalid factorization_QQ.is_irreducible (expected boolean)",
                )
            )

    if status in _REQUIRED_STATUSES_UNKNOWN:
        checks.append(
            CheckResult(
                "result.galois_group.unknown_status",
                gg == "UNKNOWN",
                "galois_group must be 'UNKNOWN' for unclassified/reducible/error",
            )
        )
        checks.append(
            CheckResult(
                "result.transitive_group_id.unknown_status",
                "transitive_group_id" in result and result.get("transitive_group_id") is None,
                "transitive_group_id must be present and null for unclassified/reducible/error",
            )
        )

    can_build_scope = (
        isinstance(inp.get("degree"), int)
        and isinstance(coeffs_qq, list)
        and all(isinstance(x, str) for x in coeffs_qq)
    )
    if not can_build_scope:
        checks.append(CheckResult("input.hash.match", False,
                                  "Skipped: cannot build input_v1 hash scope from invalid fields"))
    else:
        try:
            expected_hash = compute_input_hash(_build_scope_from_input(inp, coeffs_qq))
            checks.append(
                CheckResult(
                    "input.hash.match",
                    actual_hash == expected_hash,
                    "input.hash mismatch (certificate may be tampered)",
                )
            )
        except Exception as e:  # noqa: BLE001
            checks.append(CheckResult("input.hash.match", False, f"Tamper-check failed: {e}"))

    # --- Witness check: discriminant square witness ---
    inv = certificate.get("invariants")
    disc = inv.get("discriminant") if isinstance(inv, Mapping) else None

    if not isinstance(disc, Mapping):
        checks.append(CheckResult("invariants.discriminant.witness",
                                  True, "N/A (no invariants.discriminant)"))
    else:
        is_sq = disc.get("is_square")
        val = disc.get("value")
        sqrtw = disc.get("sqrt_witness")

        if is_sq is True:
            if isinstance(val, str) and isinstance(sqrtw, str):
                try:
                    v = _parse_fraction(val)
                    s = _parse_fraction(sqrtw)
                    ok = (s * s == v)
                except Exception:  # noqa: BLE001
                    ok = False
            else:
                ok = False
            checks.append(CheckResult("invariants.discriminant.witness", ok, 
                                      "sqrt_witness^2 must equal discriminant.value"))
        elif is_sq is False:
            # witness must be absent when is_square=false 
            # (schema already enforces, but verifier should too)
            ok = sqrtw is None
            checks.append(CheckResult("invariants.discriminant.witness", ok, 
                                      "sqrt_witness must be absent when is_square=false"))
        else:
            checks.append(CheckResult("invariants.discriminant.witness", False, 
                                      "Invalid invariants.discriminant.is_square"))
    # --- Witness check: Dummit quadratics discriminant witness ---
    dq = certificate.get("dummit_quadratics")
    if not isinstance(dq, Mapping):
        checks.append(CheckResult("dummit_quadratics.witness", True, "N/A (no dummit_quadratics)"))
    else:
        ok_all = True
        details = []
        for name in ("quad1", "quad2"):
            quad = dq.get(name)
            if not isinstance(quad, Mapping):
                continue
            reducible = quad.get("is_reducible_QQ")
            coeffs3 = quad.get("coeffs_qq")
            sqrtw = quad.get("sqrt_discriminant_witness")

            if reducible is True:
                if not (isinstance(coeffs3, list) and len(coeffs3) == 3 and 
                        all(isinstance(x, str) for x in coeffs3)):
                    ok_all = False
                    details.append(f"{name}: invalid coeffs_qq")
                    continue
                if not isinstance(sqrtw, str):
                    ok_all = False
                    details.append(f"{name}: missing sqrt_discriminant_witness")
                    continue
                try:
                    a, b, c = (_parse_fraction(x) for x in coeffs3)
                    disc_q = b*b - 4*a*c
                    s = _parse_fraction(sqrtw)
                    if s*s != disc_q:
                        ok_all = False
                        details.append(f"{name}: witness does not square to discriminant")
                except Exception: # noqa: BLE001
                    ok_all = False
                    details.append(f"{name}: parse/arithmetic failed")
            elif reducible is False:
                # witness must be absent
                if sqrtw is not None:
                    ok_all = False
                    details.append(f"{name}: witness must be absent when is_reducible_QQ=false")
            else:
                ok_all = False
                details.append(f"{name}: invalid is_reducible_QQ")
        checks.append(CheckResult("dummit_quadratics.witness", ok_all, "; ".join(details) if details
                                  else ""))

    verified = all(c.ok for c in checks)
    return VerifiedResult(verified, tuple(checks))
