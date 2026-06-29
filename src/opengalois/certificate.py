from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from fractions import Fraction
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from .codec.rationals import _frac_to_str
from .models import AnalysisOptions
from .polyops.desc_qx import _trim_leading_zeros_desc

try:
    _GENERATOR_VERSION = version("opengalois")
except PackageNotFoundError:
    _GENERATOR_VERSION = "0.0.0"


# =========================
# Certificate v3.0.0 core
# =========================

SCHEMA_VERSION = "3.0.0"
_VARIABLE = "x"
_DOMAIN = "Q"
_ORDERING = "descending_degree"
_CANONICALIZATION = "jcs-rfc8785"
_HASH_ALG = "sha256"
_HASH_SCOPE = "input_v1"

# Object-store conventions (OpenGalois lemma library; core schema stays agnostic)
_POLY_KIND = "poly_qq_desc"
_INPUT_REF = "$input"


def _jcs_encode(obj: Any) -> str:
    """RFC8785-like canonical encoder restricted to this project's payload types.

    Supported types: dict[str, ...], list, str, int, bool, None.
    Floats are intentionally rejected to avoid non-canonical number rendering.
    """
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, list):
        return "[" + ",".join(_jcs_encode(v) for v in obj) + "]"
    if isinstance(obj, Mapping):
        if not all(isinstance(k, str) for k in obj):
            raise TypeError("JCS objects require string keys")
        parts = []
        for key in sorted(obj):
            parts.append(f"{_jcs_encode(key)}:{_jcs_encode(obj[key])}")
        return "{" + ",".join(parts) + "}"
    raise TypeError(f"Unsupported type for canonicalization: {type(obj)!r}")


def _canonical_json_bytes(obj: Any) -> bytes:
    return _jcs_encode(obj).encode("utf-8")


def _sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def coeffs_to_qq_strings(coeffs: Iterable[Fraction]) -> list[str]:
    """Convert rational coefficients to canonical QQ string literals."""
    return [_frac_to_str(c) for c in coeffs]


def build_input_scope(degree: int, coeffs_qq: list[str]) -> dict[str, Any]:
    """Build the stable input_v1 scope used for canonical hashing."""
    return {
        "domain": _DOMAIN,
        "variable": _VARIABLE,
        "ordering": _ORDERING,
        "degree": degree,
        "coeffs_qq": coeffs_qq,
    }


def compute_input_hash(scope_payload: Mapping[str, Any]) -> str:
    """Compute the SHA-256 hash of the canonicalized input scope payload."""
    return _sha256_hex_bytes(_canonical_json_bytes(scope_payload))


def _build_input_block(coeffs: list[Fraction]) -> dict[str, Any]:
    """Build the v2.0.0 'input' block (including input_v1 hash)."""
    coeffs = _trim_leading_zeros_desc(list(coeffs))
    degree = len(coeffs) - 1
    coeffs_qq = coeffs_to_qq_strings(coeffs)

    scope_payload = build_input_scope(degree=degree, coeffs_qq=coeffs_qq)
    input_hash = compute_input_hash(scope_payload)

    return {
        **scope_payload,
        "canonicalization": _CANONICALIZATION,
        "hash_alg": _HASH_ALG,
        "hash_scope": _HASH_SCOPE,
        "hash": input_hash,
    }


def build_certificate(coeffs: list[Fraction], options: AnalysisOptions) -> dict[str, Any]:
    """Build a minimal schema v3.0.0 fact+rule certificate for the provided polynomial."""
    input_block = _build_input_block(coeffs)

    from .engine.engine import run_engine
    engine_result = run_engine(coeffs=coeffs, options=options)

    # v3: proof is a flat list of fact nodes
    cert: dict[str, Any] = {
        "$schema": f"https://opengalois.org/schemas/certificate/{SCHEMA_VERSION}.json",
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "generator": "opengalois",
            "generator_version": _GENERATOR_VERSION,
            "ruleset_id": getattr(engine_result, "ruleset_id", "le5-core@1"),
        },
        "input": input_block,
        "objects": engine_result.objects,
        "proof": {
            "version": "1.0",
            "facts": engine_result.facts,
        },
        # UX-only
        "summary": engine_result.summary,
    }
    return cert
