from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from .certificate import build_certificate
from .explain import ExplainFormat, render_explanation_from_certificate
from .models import (
    AnalysisOptions,
    BackendName,
    GaloisGroup,
    PrimePolicy,
    ProofLevel,
    Result,
    Status,
    VerifiedResult,
)
from .verify import verify_certificate


def _to_fraction(x: Any) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x, 1)
    if isinstance(x, str):
        s = x.strip()
        if "/" in s:
            p, q = s.split("/", 1)
            return Fraction(int(p.strip()), int(q.strip()))
        return Fraction(int(s), 1)
    raise TypeError(f"Unsupported coefficient type: {type(x)!r}")


def _parse_coeffs_le5(coeffs: Sequence[Any]) -> list[Fraction]:
    """Parse coefficients in descending degree order for degree 1..5 polynomials.

    Expected input format: [a_n, a_{n-1}, ..., a_0] with:
      - 2 <= len(coeffs) <= 6
      - leading coefficient a_n != 0
    """
    if not (2 <= len(coeffs) <= 6):
        raise ValueError(
            "Expected 2..6 coefficients [a_n,...,a_0] for a polynomial of degree 1..5."
        )
    out = [_to_fraction(c) for c in coeffs]
    if out[0] == 0:
        raise ValueError("Leading coefficient a_n must be non-zero.")
    return out


def analyze(
    polynomial: Sequence[Any],
    *,
    explain: bool = False,
    backend: BackendName = "sympy",
    proof_level: ProofLevel = "core",
    prime_policy: PrimePolicy = "deterministic",
    prime_budget: int = 50,
) -> Result:
    """Analyze a polynomial f(x) ∈ Q[x] of degree 1..5 and return a certificate.

    Notes (v2.0.0):
    - The certificate is proof-first: `proof` + `objects` are normative.
    - `summary` is UX-only; the verifier must ignore it for correctness.
    """
    if prime_budget <= 0:
        raise ValueError("prime_budget must be a positive integer")

    opts = AnalysisOptions(
        explain=explain,
        backend=backend,
        proof_level=proof_level,
        prime_policy=prime_policy,
        prime_budget=int(prime_budget),
    )

    coeffs = _parse_coeffs_le5(polynomial)
    cert = copy.deepcopy(build_certificate(coeffs, opts))

    explanation_text = None
    if opts.explain:
        # The explanation renderer is currently a lightweight skeleton; it should not
        # be used for verification logic.
        explanation_text = render_explanation_from_certificate(cert, fmt="md")

    summary = cert.get("summary", {})
    status_raw = summary.get("status", Status.unclassified.value)
    gg_raw = summary.get("galois_group", GaloisGroup.UNKNOWN.value)
    sbr_raw = summary.get("solvable_by_radicals", None)

    # Convert to enums defensively (certificate could be tampered or partial in dev)
    try:
        status = Status(str(status_raw))
    except Exception:
        status = Status.unclassified

    try:
        gg = GaloisGroup(str(gg_raw))
    except Exception:
        gg = GaloisGroup.UNKNOWN

    sbr: bool | None
    if isinstance(sbr_raw, bool) or sbr_raw is None:
        sbr = sbr_raw
    else:
        sbr = None

    return Result(
        status=status,
        solvable_by_radicals=sbr,
        galois_group=gg,
        certificate=cert,
        explanation=explanation_text,
    )


def verify(
    certificate: Mapping[str, Any], *, backend: BackendName = "sympy"
) -> VerifiedResult:
    """Verify an OpenGalois certificate and return per-check verification output."""
    _ = AnalysisOptions(backend=backend)  # validate backend literal
    return verify_certificate(certificate)


def render_explanation(
    obj: Result | dict[str, Any], *, format: ExplainFormat = "md"
) -> str | dict[str, Any]:
    """Render a human-friendly explanation for a result or raw certificate."""
    if isinstance(obj, Result):
        cert = obj.certificate
    else:
        cert = obj
    return render_explanation_from_certificate(cert, fmt=format)
