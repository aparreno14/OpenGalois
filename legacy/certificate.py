from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from fractions import Fraction
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from .models import AnalysisOptions, GaloisGroup, Status
from .polyops.desc_qx import _shift_desc
from 

try:
    _GENERATOR_VERSION = version("opengalois")
except PackageNotFoundError:
    _GENERATOR_VERSION = "0.0.0"

SCHEMA_VERSION = "1.1.0"
_VARIABLE = "x"
_DOMAIN = "Q"
_ORDERING = "descending_degree"
_DEGREE = 5
_CANONICALIZATION = "jcs-rfc8785"
_HASH_ALG = "sha256"
_HASH_SCOPE = "input_v1"


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


def build_input_scope(coeffs_qq: list[str]) -> dict[str, Any]:
    """Build the stable input_v1 scope used for canonical hashing."""
    return {
        "coeffs_qq": coeffs_qq,
        "variable": _VARIABLE,
        "domain": _DOMAIN,
        "ordering": _ORDERING,
        "degree": _DEGREE,
    }


def compute_input_hash(scope_payload: Mapping[str, Any]) -> str:
    """Compute the SHA-256 hash of the canonicalized input scope payload."""
    return _sha256_hex_bytes(_canonical_json_bytes(scope_payload))

def add_normalization(cert: dict[str, Any], coeffs: list[Fraction]) -> None:
    """Add normalization fields to the certificate based on the provided coefficients."""
    a5 = coeffs[0]
    # monicize
    monic = [c / a5 for c in coeffs]   # leading becomes 1
    # depress: shift = a4/(5*a5) but here a5=1 so shift = monic[1]/5
    shift = monic[1] / 5
    dep = _shift_desc(monic, -shift)   # g(y)=f_monic(y-shift)

    cert["normalization"] = {
        "basis": "depressed_monic_QQ",
        "tschirnhaus_shift": _frac_to_str(shift),
        "monic_scale": _frac_to_str(a5),
        "poly_coeffs": [_frac_to_str(c) for c in dep],
    }

def build_certificate(coeffs: list[Fraction], options: AnalysisOptions) -> dict[str, Any]:
    """Build a minimal schema v1.1.0 certificate for the provided polynomial."""
    coeffs_qq = coeffs_to_qq_strings(coeffs)
    scope_payload = build_input_scope(coeffs_qq)
    input_hash = compute_input_hash(scope_payload)

    cert: dict[str, Any] = {
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "generator": "opengalois",
            "generator_version": _GENERATOR_VERSION,
            "backend": options.backend,
        },
        "input": {
            **scope_payload,
            "canonicalization": _CANONICALIZATION,
            "hash_alg": _HASH_ALG,
            "hash_scope": _HASH_SCOPE,
            "hash": input_hash,
        },
        "result": {
            "status": Status.unclassified.value,
            "solvable_by_radicals": None,
            "galois_group": GaloisGroup.UNKNOWN.value,
            "transitive_group_id": None,
        },
    }
    add_normalization(cert, coeffs)
    return cert
