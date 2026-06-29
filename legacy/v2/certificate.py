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
# Certificate v2.0.0 core
# =========================

SCHEMA_VERSION = "2.0.0"
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
    """Build a minimal schema v2.0.0 proof-first certificate for the provided polynomial.

    Parity goal with the previous repo state:
    - deterministic input_v1 hash
    - degree-5: provide a normalization lemma with a checkable witness
    - other degrees: no normalization obligation (proof can be minimal)
    """
    input_block = _build_input_block(coeffs)

    from .engine.engine import run_engine
    engine_result = run_engine(coeffs=coeffs, options=options)

    # Root "analyze" node acts as a container/derivation root. It is intentionally lightweight.
    proof_root: dict[str, Any] = {
        "kind": "opengalois.analyze",
        "inputs": [{"ref": _INPUT_REF}],
        "children": engine_result.children,
        "statement": "OpenGalois analysis derivation root.",
    }

    cert: dict[str, Any] = {
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "generator": "opengalois",
            "generator_version": _GENERATOR_VERSION,
            "backend": options.backend,
        },
        "input": input_block,
        "objects": engine_result.objects,
        "proof": {
            "version": "0.1",
            "root": proof_root,
        },
        # Non-normative UX summary: verifiers must ignore it.
        "summary": engine_result.summary,
    }
    return cert
