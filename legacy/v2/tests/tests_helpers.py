from __future__ import annotations

import json
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from opengalois.certificate import compute_input_hash
from opengalois.codec.rationals import _frac_to_str


def make_input(coeffs: list[Fraction]) -> dict[str, Any]:
    """Build a v2.0.0 input block with a valid input.hash.

    Args:
        coeffs: Polynomial coefficients in descending degree order.

    Returns:
        The `input` object for a certificate (including input.hash).
    """
    coeffs_qq = [_frac_to_str(c) for c in coeffs]
    deg = len(coeffs_qq) - 1
    scope = {
        "domain": "Q",
        "variable": "x",
        "ordering": "descending_degree",
        "degree": deg,
        "coeffs_qq": coeffs_qq,
    }
    h = compute_input_hash(scope)
    return {
        "domain": "Q",
        "variable": "x",
        "ordering": "descending_degree",
        "degree": deg,
        "coeffs_qq": coeffs_qq,
        "canonicalization": "jcs-rfc8785",
        "hash_alg": "sha256",
        "hash_scope": "input_v1",
        "hash": h,
    }


def poly_obj(coeffs: list[Fraction]) -> dict[str, Any]:
    """Build a poly_qq_desc object payload.

    Args:
        coeffs: Polynomial coefficients in descending degree order.

    Returns:
        Object payload with kind=poly_qq_desc and canonical coeffs_qq.
    """
    coeffs_qq = [_frac_to_str(c) for c in coeffs]
    return {
        "kind": "poly_qq_desc",
        "degree": len(coeffs_qq) - 1,
        "coeffs_qq": coeffs_qq,
    }


def lemma_irreducible(ref: str, *, method: str = "glassbox_le5") -> dict[str, Any]:
    """Build an irreducible.QQ lemma node.

    Args:
        ref: Polynomial ref ('$input' or an objects id).
        method: Method identifier.

    Returns:
        A proof node dict for `irreducible.QQ`.
    """
    return {
        "kind": "irreducible.QQ",
        "inputs": [{"ref": ref}],
        "witness": {"method": method},
        "statement": "Irreducible over Q by the declared glass-box method.",
    }


def lemma_factorization(
    ref: str,
    *,
    unit: Fraction,
    factors: list[tuple[str, int]],
    outputs: list[str] | None = None,
) -> dict[str, Any]:
    """Build a factorization.QQ.monic lemma node.

    Args:
        ref: Input polynomial ref.
        unit: Unit scalar in Q (non-zero).
        factors: List of (poly_ref, multiplicity).
        outputs: Optional list of created object refs to place in node.outputs.

    Returns:
        A proof node dict for `factorization.QQ.monic`.
    """
    node: dict[str, Any] = {
        "kind": "factorization.QQ.monic",
        "inputs": [{"ref": ref}],
        "witness": {
            "unit": _frac_to_str(unit),
            "factors": [{"ref": r, "multiplicity": int(e)} for (r, e) in factors],
        },
        "statement": "Factorization in Q[x] with monic factors.",
    }
    if outputs is not None:
        node["outputs"] = [{"ref": r} for r in outputs]
    return node


def make_cert(
    *,
    coeffs: list[Fraction],
    children: list[dict[str, Any]],
    objects: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a schema-shaped v2.0.0 certificate skeleton.

    Args:
        coeffs: Input polynomial coefficients.
        children: Root children proof nodes.
        objects: Optional object store.

    Returns:
        Certificate dict.
    """
    inp = make_input(coeffs)
    cert: dict[str, Any] = {
        "meta": {"schema_version": "2.0.0", "generator": "opengalois", "backend": "sympy"},
        "input": inp,
        "proof": {
            "version": "0.1",
            "root": {"kind": "opengalois.analyze", "inputs": [{"ref": "$input"}], "children": children},
        },
        "summary": {
            "status": "unclassified",
            "solvable_by_radicals": None,
            "galois_group": "UNKNOWN",
            "transitive_group_id": None,
        },
    }
    if objects is not None:
        cert["objects"] = objects
    return cert


def load_schema_validator() -> Draft202012Validator:
    """Load the v2.0.0 certificate schema validator by searching upwards.

    Returns:
        Draft202012Validator for schemas/certificate/2.0.0.json.

    Raises:
        FileNotFoundError: If the schema cannot be located.
    """
    here = Path(__file__).resolve()
    start = here.parent

    for p in (start, *start.parents):
        schema_path = p / "schemas" / "certificate" / "2.0.0.json"
        if schema_path.is_file():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            return Draft202012Validator(schema)

    raise FileNotFoundError("Could not locate schemas/certificate/2.0.0.json by walking upwards.")


def schema_errors(validator: Draft202012Validator, cert: Mapping[str, Any]) -> list[str]:
    """Return up to 5 formatted schema errors for a certificate.

    Args:
        validator: Draft202012Validator instance.
        cert: Certificate mapping.

    Returns:
        List of formatted schema error messages.
    """
    errors = sorted(validator.iter_errors(cert), key=lambda e: list(getattr(e, "path", [])))
    out: list[str] = []
    for e in errors[:5]:
        path = "$" + "".join(f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in getattr(e, "path", []))
        out.append(f"{path}: {e.message}")
    return out


def assert_schema_valid(validator: Draft202012Validator, cert: Mapping[str, Any]) -> None:
    """Assert that a certificate validates against schema v2.0.0.

    Args:
        validator: Draft202012Validator instance.
        cert: Certificate mapping.

    Raises:
        AssertionError: If schema validation fails.
    """
    errs = schema_errors(validator, cert)
    assert not errs, "Schema validation failed:\n" + "\n".join(errs)
