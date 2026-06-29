# src/opengalois/verify.py
from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from opengalois.algorithms.factorization import factorize_le5

from .certificate import compute_input_hash
from .codec.rationals import _frac_to_str, _is_canonical_rational_str, _parse_fraction
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
    resource_files = None  # type: ignore[assignment]


# ============================
# Schema + core invariants
# ============================

SUPPORTED_SCHEMA_VERSIONS = {"2.0.0"}
SUPPORTED_PROOF_VERSIONS = {"0.1"}
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

_SCHEMA_VERSION = "2.0.0"
_SCHEMA_RESOURCE = "schemas/certificate/2.0.0.json"

# Reserved pseudo-reference for the input polynomial.
_INPUT_REF = "$input"

# OpenGalois v2.0.0 "object store" kind used for rational polynomials in Q[x]
# represented as coeff lists in descending degree order.
_POLY_KIND = "poly_qq_desc"


def _build_scope_from_input(inp: Mapping[str, Any], coeffs_qq: list[str]) -> dict[str, Any]:
    """Build the stable 'input_v1' hash scope payload."""
    return {
        "domain": inp["domain"],
        "variable": inp["variable"],
        "ordering": inp["ordering"],
        "degree": inp["degree"],
        "coeffs_qq": coeffs_qq,
    }


@lru_cache
def _load_schema_v200() -> dict[str, Any]:
    # 1) Prefer packaged resource (installed usage)
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

    # 2) Fallback: repo checkout path (dev usage)
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # .../src/opengalois/verify.py -> parents[2] == repo root
    p2 = repo_root / "schemas" / "certificate" / f"{_SCHEMA_VERSION}.json"
    if p2.is_file():
        content = json.loads(p2.read_text(encoding="utf-8"))
        if not isinstance(content, dict):
            raise TypeError(f"The schema in {p2} must be a JSON object, got {type(content)}")
        return content

    raise FileNotFoundError(f"Could not locate schemas/certificate/{_SCHEMA_VERSION}.json")


def _format_schema_error(err: Any) -> str:
    path = getattr(err, "absolute_path", [])
    if path:
        loc = "$" + "".join(f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in path)
    else:
        loc = "$"
    msg = getattr(err, "message", str(err))
    return f"{loc}: {msg}"


# ============================
# Proof-first verification
# ============================

@dataclass(frozen=True)
class _Ctx:
    """Verifier context for v2.0.0 proof-first certificates."""
    inp_poly: list[Fraction]  # input polynomial coefficients, descending
    objects: dict[str, Any]   # object store
    checks: list[CheckResult] # accumulated checks


def _add(ctx: _Ctx, name: str, ok: bool, details: str = "") -> None:
    ctx.checks.append(CheckResult(name, ok, details))


def _get_ref_id(x: Any) -> str | None:
    """Extract {'ref': <id>} and return <id> if shape is correct."""
    if not isinstance(x, Mapping):
        return None
    ref = x.get("ref")
    if not isinstance(ref, str) or not ref:
        return None
    return ref


def _resolve_object(ctx: _Ctx, ref: str) -> Any | None:
    """Resolve a reference into the object store (excluding $input)."""
    if ref == _INPUT_REF:
        return None
    return ctx.objects.get(ref)


def _resolve_poly(ctx: _Ctx, ref: str) -> list[Fraction] | None:
    """Resolve a polynomial reference to a list[Fraction] (descending)."""
    if ref == _INPUT_REF:
        return ctx.inp_poly

    obj = _resolve_object(ctx, ref)
    if obj is None:
        return None
    if not isinstance(obj, Mapping):
        return None
    if obj.get("kind") != _POLY_KIND:
        return None

    coeffs_qq = obj.get("coeffs_qq")
    if not isinstance(coeffs_qq, list) or not all(isinstance(s, str) for s in coeffs_qq):
        return None
    if not all(_is_canonical_rational_str(s) for s in coeffs_qq):
        return None

    # Optional degree consistency (if present)
    deg = obj.get("degree")
    if deg is not None:
        if not isinstance(deg, int) or deg < 0 or deg + 1 != len(coeffs_qq):
            return None

    coeffs = [_parse_fraction(s) for s in coeffs_qq]
    return _trim_leading_zeros_desc(coeffs)


# ----------------------------
# Lemma registry
# ----------------------------

LemmaChecker = Callable[[_Ctx, Mapping[str, Any]], None]


def _lemma_root_analyze(ctx: _Ctx, node: Mapping[str, Any]) -> None:
    """Structural root/container lemma.

    Contract (OpenGalois convention):
    - inputs: one polynomial ref (usually $input)
    - outputs: absent or empty
    - witness: absent
    - children: any
    """
    inputs = node.get("inputs", [])
    outputs = node.get("outputs")
    witness = node.get("witness")

    if not isinstance(inputs, list) or len(inputs) != 1:
        _add(ctx, "lemma.root.inputs", False, "Expected inputs: [ {ref: '$input'} ]")
        return

    input_ref = _get_ref_id(inputs[0])
    if input_ref != _INPUT_REF:
        _add(ctx, "lemma.root.inputs", False, "Root input must be exactly {'ref': '$input'}")
        return
    if outputs is not None and (not isinstance(outputs, list) or len(outputs) != 0):
        _add(ctx, "lemma.root.outputs", False, "Root outputs must be absent or []")
        return
    if witness is not None:
        _add(ctx, "lemma.root.witness", False, "Root witness must be absent")
        return

    _add(ctx, "lemma.root", True)


def _lemma_normalize_depressed_monic(ctx: _Ctx, node: Mapping[str, Any]) -> None:
    """Verify normalization to depressed monic basis over Q.

    Node contract (OpenGalois convention):
    - inputs:  one polynomial ref (usually $input)
    - outputs: one polynomial ref (kind=poly_qq_desc) for the depressed-monic polynomial
    - witness:
        - tschirnhaus_shift: canonical rational string
        - monic_scale: canonical rational string (must equal leading coefficient of input)
    """
    inputs = node.get("inputs")
    outputs = node.get("outputs")
    witness = node.get("witness")

    if not isinstance(inputs, list) or len(inputs) != 1:
        _add(ctx, "lemma.normalize.inputs", False, "Expected inputs: [ {ref: ...} ]")
        return
    if not isinstance(outputs, list) or len(outputs) != 1:
        _add(ctx, "lemma.normalize.outputs", False, "Expected outputs: [ {ref: ...} ]")
        return
    if not isinstance(witness, Mapping):
        _add(ctx, "lemma.normalize.witness", False, "Missing/invalid witness object")
        return

    in_ref = _get_ref_id(inputs[0])
    out_ref = _get_ref_id(outputs[0])
    if in_ref is None or out_ref is None or out_ref == _INPUT_REF:
        _add(ctx, "lemma.normalize.refs", False, "Invalid input/output refs")
        return

    p = _resolve_poly(ctx, in_ref)
    g = _resolve_poly(ctx, out_ref)
    if p is None:
        _add(ctx, "lemma.normalize.input.resolve", False,
             f"Cannot resolve input polynomial ref {in_ref!r}")
        return
    if g is None:
        _add(ctx, "lemma.normalize.output.resolve", False,
             f"Cannot resolve output polynomial ref {out_ref!r} (kind={_POLY_KIND})")
        return

    shift_s = witness.get("tschirnhaus_shift")
    scale_s = witness.get("monic_scale")
    if not isinstance(shift_s, str) or not isinstance(scale_s, str):
        _add(ctx, "lemma.normalize.witness.shape", False, 
             "witness must contain tschirnhaus_shift and monic_scale as strings")
        return

    if not (_is_canonical_rational_str(shift_s) and _is_canonical_rational_str(scale_s)):
        _add(ctx, "lemma.normalize.witness.canonical", False, "Non-canonical rational in witness")
        return

    n = len(p) - 1
    if n <= 0:
        _add(ctx, "lemma.normalize.degree", False, "Input polynomial must have degree >= 1")
        return

    a_n = p[0]
    expected_scale = a_n
    monic = [c / a_n for c in p]
    expected_shift = monic[1] / n  # coefficient of x^{n-1} divided by n

    shift = _parse_fraction(shift_s)
    scale = _parse_fraction(scale_s)

    if scale != expected_scale:
        _add(ctx, "lemma.normalize.monic_scale", False,
             f"Expected monic_scale={_frac_to_str(expected_scale)}, got {scale_s}")
        return
    if shift != expected_shift:
        _add(ctx, "lemma.normalize.tschirnhaus_shift", False,
             f"Expected tschirnhaus_shift={_frac_to_str(expected_shift)}, got {shift_s}")
        return

    dep = _shift_desc(monic, -expected_shift)
    dep = _trim_leading_zeros_desc(dep)

    if dep != g:
        _add(ctx, "lemma.normalize.soundness", False,
             "Output polynomial does not match depressed-monic transform")
        return
    if not (g[0] == 1 and (len(g) < 2 or g[1] == 0)):
        _add(ctx, "lemma.normalize.invariants", False, 
             "Output is not monic and depressed (leading=1, x^{n-1} coeff=0)")
        return

    _add(ctx, "lemma.normalize", True)


def _lemma_factorization_QQ_monic(ctx: _Ctx, node: Mapping[str, Any]) -> None:
    """Verify explicit exact factorization in Q[x] with monic factors.

    Node contract (OpenGalois convention):
    - inputs: one polynomial ref (often $input)
    - witness:
        - unit: canonical rational string (nonzero)
        - factors: list of {ref: <poly>, multiplicity: <int>=1}
    """
    inputs = node.get("inputs")
    witness = node.get("witness")

    if not isinstance(inputs, list) or len(inputs) != 1:
        _add(ctx, "lemma.factorization.inputs", False, "Expected inputs: [ {ref: ...} ]")
        return
    if not isinstance(witness, Mapping):
        _add(ctx, "lemma.factorization.witness", False, "Missing/invalid witness object")
        return

    in_ref = _get_ref_id(inputs[0])
    if in_ref is None:
        _add(ctx, "lemma.factorization.refs", False, "Invalid input ref")
        return

    p = _resolve_poly(ctx, in_ref)
    if p is None:
        _add(ctx, "lemma.factorization.input.resolve", False, 
             f"Cannot resolve input polynomial ref {in_ref!r}")
        return

    unit_s = witness.get("unit")
    factors = witness.get("factors")

    if not isinstance(unit_s, str) or not isinstance(factors, list):
        _add(ctx, "lemma.factorization.witness.shape", False, 
             "witness must contain unit (str) and factors (list)")
        return
    if not _is_canonical_rational_str(unit_s):
        _add(ctx, "lemma.factorization.unit.canonical", False, 
             "unit is not a canonical rational string")
        return
    unit = _parse_fraction(unit_s)
    if unit == 0:
        _add(ctx, "lemma.factorization.unit.nonzero", False, "unit must be non-zero")
        return

    acc: list[Fraction] = [Fraction(1)]
    for i, fdesc in enumerate(factors):
        if not isinstance(fdesc, Mapping):
            _add(ctx, "lemma.factorization.factors.shape", False, f"factors[{i}] must be an object")
            return
        ref = fdesc.get("ref")
        mult = fdesc.get("multiplicity", 1)
        if not isinstance(ref, str) or not ref:
            _add(ctx, "lemma.factorization.factors.ref", False,
                 f"factors[{i}].ref must be a string")
            return
        if ref == _INPUT_REF:
            _add(ctx, "lemma.factorization.factors.ref", False, 
                 f"factors[{i}].ref cannot be $input")
            return
        if not isinstance(mult, int) or mult <= 0:
            _add(ctx, "lemma.factorization.factors.multiplicity", False, 
                 f"factors[{i}].multiplicity must be a positive int")
            return

        fac = _resolve_poly(ctx, ref)
        if fac is None:
            _add(ctx, "lemma.factorization.factor.resolve", False, 
                 f"Cannot resolve factor polynomial ref {ref!r}")
            return
        if not fac or len(fac) < 2:
            _add(ctx, "lemma.factorization.factor.degree", False, 
                 f"Factor {ref!r} must be non-constant")
            return
        if fac[0] != 1:
            _add(ctx, "lemma.factorization.factor.monic", False,
                 f"Factor {ref!r} must be monic (leading coeff 1)")
            return

        acc = _mul_desc(acc, _pow_desc(fac, mult))

    recon = _mul_scalar_desc(acc, unit)
    recon = _trim_leading_zeros_desc(recon)
    target = _trim_leading_zeros_desc(p)

    if recon != target:
        _add(ctx, "lemma.factorization.soundness", False, 
             "Reconstruction unit*Π f_i^{e_i} does not match input polynomial")
        return

    _add(ctx, "lemma.factorization", True)
    
def _lemma_irreducible_QQ(ctx: _Ctx, node: Mapping[str, Any]) -> None:
    """Verify `irreducible.QQ` using the declared procedure.

    Contract (v2.0.0):
    - inputs: one polynomial ref ($input or objects[ref] with kind=poly_qq_desc)
    - witness: {"method": "<supported method>"} and no other keys
    - obligation: replay the deterministic glass-box procedure;
      accept iff no non-trivial factorization exists.
    """
    inputs = node.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != 1:
        _add(ctx, "lemma.irreducible.inputs.shape", False, "inputs must be a 1-element list.")
        return
    
    outputs = node.get("outputs")
    if outputs is not None and outputs != []:
        _add(ctx, "lemma.irreducible.outputs.shape", False,
             "outputs MUST be absent or an empty list.")
        return

    ref = inputs[0].get("ref") if isinstance(inputs[0], Mapping) else None
    if not isinstance(ref, str) or not ref:
        _add(ctx, "lemma.irreducible.inputs.ref", False,
             "inputs[0].ref must be a non-empty string.")
        return

    witness = node.get("witness")
    if not isinstance(witness, Mapping):
        _add(ctx, "lemma.irreducible.witness.shape", False, "witness must be an object.")
        return

    # Enforce "witness only method" (per docs/lemmas/irreducible.QQ.md).
    if set(witness.keys()) != {"method"}:
        _add(
            ctx,
            "lemma.irreducible.witness.keys",
            False,
            "witness must contain exactly the key 'method' (no extra fields).",
        )
        return

    method = witness.get("method")
    if method not in ("glassbox_le5", "trivial_linear"):
        _add(ctx, "lemma.irreducible.witness.method", False, "Unsupported method.")
        return
    _add(ctx, "lemma.irreducible.witness.method", True)

    p = _resolve_poly(ctx, ref)
    if p is None:
        _add(ctx, "lemma.irreducible.input.resolve", False,
             f"Cannot resolve polynomial ref {ref!r}.")
        return
    
    p = _trim_leading_zeros_desc(p)
    deg = len(p) - 1
    
    if method == "trivial_linear":
        if deg != 1:
            _add(ctx, "lemma.irreducible.degree", False, "trivial_linear supports degree 1 only.")
            return
        _add(ctx, "lemma.irreducible.degree", True)
        
        _add(ctx, "lemma.irreducible.soundness", True, "")
        return
    
    if deg not in (2, 3, 4, 5):
        _add(ctx, "lemma.irreducible.degree", False, "glassbox_le5 supports degrees 2..5 only.")
        return
    _add(ctx, "lemma.irreducible.degree", True)
    
    unit = p[0]
    monic_p = [c / unit for c in p]

    try:
        facs = factorize_le5(monic_p)
    except Exception as e:  # noqa: BLE001
        _add(ctx, "lemma.irreducible.exception", False, f"factorize_le5 raised: {e}")
        return

    facs = [_trim_leading_zeros_desc(f) for f in facs if f]
    ok = (len(facs) == 1 and facs[0] == monic_p)

    _add(
        ctx,
        "lemma.irreducible.soundness",
        ok,
        (
            "glassbox_le5 found a non-trivial factorization; polynomial is not irreducible."
            if not ok
            else ""
        ),
    )




_LEMMA_CHECKERS: dict[str, LemmaChecker] = {
    "opengalois.analyze": _lemma_root_analyze,
    "normalize.depressed_monic_QQ": _lemma_normalize_depressed_monic,
    "factorization.QQ.monic": _lemma_factorization_QQ_monic,
    "irreducible.QQ": _lemma_irreducible_QQ,
}


# ----------------------------
# Proof traversal + reference integrity
# ----------------------------

def _iter_nodes_postorder(root: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []

    def rec(n: Any) -> None:
        if not isinstance(n, Mapping):
            return
        children = n.get("children", [])
        if isinstance(children, list):
            for ch in children:
                rec(ch)
        out.append(cast(Mapping[str, Any], n))

    rec(root)
    return out


def _check_refs_exist(ctx: _Ctx, node: Mapping[str, Any]) -> bool:
    """Return True iff all refs in node exist in objects (except $input)."""
    ok = True
    for field in ("inputs", "outputs"):
        xs = node.get(field, [])
        if xs is None:
            continue
        if not isinstance(xs, list):
            _add(ctx, f"proof_node.{field}.shape", False, f"{field} must be a list")
            return False
        for i, x in enumerate(xs):
            ref = _get_ref_id(x)
            if ref is None:
                _add(ctx, f"proof_node.{field}.ref", False, 
                     f"{field}[{i}] must be {{'ref': <string>}}")
                return False
            if ref == _INPUT_REF:
                if field == "outputs":
                    _add(ctx, "proof_node.outputs.no_input_ref", False, 
                         "outputs cannot reference $input")
                    return False
                continue
            if ref not in ctx.objects:
                ok = False
                _add(ctx, "objects.ref_integrity", False, 
                     f"Missing object id referenced by {field}[{i}]: {ref!r}")
            else:
                obj = ctx.objects.get(ref)
                if not (isinstance(obj, Mapping) and isinstance(obj.get("kind"), str) 
                        and obj.get("kind")):
                    ok = False
                    _add(ctx, "objects.kind_present", False, 
                         f"Object {ref!r} must be an object with non-empty 'kind'")
    return ok


def verify_certificate(certificate: Mapping[str, Any]) -> VerifiedResult:
    """Verify a v2.0.0 proof-first OpenGalois certificate.

    Policy:
    - Unknown lemma kinds => verification failure (strict).
    - `summary` is ignored for correctness (UX only).
    """
    checks: list[CheckResult] = []

    # --- (1) Schema conformance (Draft 2020-12) ---
    try:
        schema = _load_schema_v200()
        validator = Draft202012Validator(schema)
        errors = sorted(
            validator.iter_errors(certificate),
            key=lambda e: list(getattr(e, "absolute_path", [])),
        )
    except Exception as e:  # noqa: BLE001
        checks.append(CheckResult("schema.conformance", False, 
                                  f"Schema validation failed: {e}"))
        return VerifiedResult(False, tuple(checks))

    if errors:
        msg = "; ".join(_format_schema_error(e) for e in errors[:5])
        if len(errors) > 5:
            msg += f" (+{len(errors) - 5} more)"
        checks.append(CheckResult("schema.conformance", False, msg))
        # Continue best-effort.
    else:
        checks.append(CheckResult("schema.conformance", True))

    meta = certificate.get("meta")
    inp = certificate.get("input")
    proof = certificate.get("proof")
    objects = certificate.get("objects", {})

    if not isinstance(meta, Mapping):
        checks.append(CheckResult("meta.present", False, "Missing or invalid 'meta' object"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("meta.present", True))

    if not isinstance(inp, Mapping):
        checks.append(CheckResult("input.present", False, "Missing or invalid 'input' object"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("input.present", True))

    if not isinstance(proof, Mapping):
        checks.append(CheckResult("proof.present", False, "Missing or invalid 'proof' object"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("proof.present", True))

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
                f"Unsupported schema_version: {schema_version!r}." 
                f"Supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            )
        )

    # --- (2) Input sanity + canonical rationals + hashing ---
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

    deg = inp.get("degree")
    if not isinstance(deg, int) or not (1 <= deg <= 5):
        checks.append(CheckResult("input.degree", False, 
                                  "input.degree must be an integer in [1,5]"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("input.degree", True))

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

    if len(coeffs_qq) != deg + 1:
        checks.append(CheckResult("input.coeffs_qq.length", False, 
                                  f"Expected {deg+1} coefficients for degree {deg}"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("input.coeffs_qq.length", True))

    canonical_ok = all(_is_canonical_rational_str(s) for s in coeffs_qq)
    checks.append(CheckResult("input.coeffs_qq.canonical", canonical_ok, 
                              "Non-canonical rational in coeffs_qq"))
    if not canonical_ok:
        return VerifiedResult(False, tuple(checks))

    inp_poly = _trim_leading_zeros_desc([_parse_fraction(s) for s in coeffs_qq])
    if not inp_poly or inp_poly[0] == 0:
        checks.append(CheckResult("input.leading_coefficient", False, 
                                  "Leading coefficient must be non-zero"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("input.leading_coefficient", True))

    # Hash recomputation
    try:
        scope_payload = _build_scope_from_input(inp, coeffs_qq)
        expected_hash = compute_input_hash(scope_payload)
        checks.append(CheckResult("input.hash.match", expected_hash == actual_hash, 
                                  "input.hash mismatch"))
    except Exception as e:  # noqa: BLE001
        checks.append(CheckResult("input.hash.match", False, 
                                  f"Failed to recompute input hash: {e}"))

    # --- (3) Object store integrity ---
    if objects is None:
        objects = {}
    if not isinstance(objects, Mapping):
        checks.append(CheckResult("objects.present", False, 
                                  "objects must be an object/map when present"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("objects.present", True))

    objects_dict = cast(dict[str, Any], dict(objects))
    if _INPUT_REF in objects_dict:
        checks.append(CheckResult("objects.reserved_id", False, 
                                  "objects must not contain a '$input' key"))
        return VerifiedResult(False, tuple(checks))

    for k, v in objects_dict.items():
        if not isinstance(v, Mapping) or not isinstance(v.get("kind"), str) or not v.get("kind"):
            checks.append(CheckResult("objects.kind_present", False, 
                                      f"Object {k!r} must be an object with non-empty 'kind'"))
            return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("objects.kind_present", True))

    # --- (4) Proof traversal + lemma checks (post-order) ---
    version = proof.get("version")
    root = proof.get("root")

    if not isinstance(version, str) or not version:
        checks.append(CheckResult("proof.version", False, 
                                  "proof.version must be a non-empty string"))
        return VerifiedResult(False, tuple(checks))
    if version not in SUPPORTED_PROOF_VERSIONS:
        checks.append(CheckResult(
            "proof.version",
            False,
            f"Unsupported proof.version: {version!r}. " 
            f"Supported: {sorted(SUPPORTED_PROOF_VERSIONS)}",
        ))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("proof.version", True))

    if not isinstance(root, Mapping):
        checks.append(CheckResult("proof.root", False, "proof.root must be an object"))
        return VerifiedResult(False, tuple(checks))
    checks.append(CheckResult("proof.root", True))

    ctx = _Ctx(inp_poly=inp_poly, objects=objects_dict, checks=checks)
    nodes = _iter_nodes_postorder(cast(Mapping[str, Any], root))
    checks.append(CheckResult("proof.nodes.nonempty", bool(nodes), 
                              "Proof tree must contain at least one node"))
    if not nodes:
        return VerifiedResult(False, tuple(checks))

    for idx, node in enumerate(nodes):
        kind = node.get("kind")
        if not isinstance(kind, str) or not kind:
            _add(ctx, "proof_node.kind", False, f"Node #{idx} missing/invalid kind")
            continue

        _check_refs_exist(ctx, node)

        checker = _LEMMA_CHECKERS.get(kind)
        if checker is None:
            _add(ctx, "lemma.known", False, f"Unknown lemma kind: {kind!r}")
            continue

        try:
            checker(ctx, node)
        except Exception as e:  # noqa: BLE001
            _add(ctx, f"lemma.{kind}.exception", False, 
                 f"Exception while verifying lemma {kind!r}: {e}")

    verified = all(c.ok for c in checks)
    return VerifiedResult(verified, tuple(checks))
