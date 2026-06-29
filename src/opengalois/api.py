from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from .certificate import build_certificate
from .explain import ExplainFormat, render_explanation_from_certificate
from .models import (
    AnalysisOptions,
    GaloisGroup,
    Result,
    Status,
    VerifiedResult,
)
from .verify import verify_certificate


def _to_fraction(x: Any) -> Fraction:
    """Convert a supported coefficient to an exact Fraction.

    Supported inputs:
      - Fraction
      - int
      - str representing an integer, e.g. "3", "-7"
      - str representing a rational, e.g. "5/2", "-9/4"

    Raises:
        ValueError: If the string does not encode a valid exact rational,
            or if the denominator is zero.
        TypeError: If the input type is unsupported.
    """
    if isinstance(x, Fraction):
        return x

    if isinstance(x, int):
        return Fraction(x, 1)

    if isinstance(x, str):
        s = x.strip()
        if not s:
            raise ValueError("empty coefficient is not allowed")

        if "/" in s:
            parts = s.split("/")
            if len(parts) != 2:
                raise ValueError(f"invalid rational coefficient: {x!r}")

            p_s, q_s = parts[0].strip(), parts[1].strip()
            if not p_s or not q_s:
                raise ValueError(f"invalid rational coefficient: {x!r}")

            try:
                p = int(p_s)
                q = int(q_s)
            except ValueError as exc:
                raise ValueError(f"invalid rational coefficient: {x!r}") from exc

            if q == 0:
                raise ValueError(
                    f"invalid rational coefficient with zero denominator: {x!r}"
                )

            return Fraction(p, q)

        try:
            return Fraction(int(s), 1)
        except ValueError as exc:
            raise ValueError(f"invalid integer coefficient: {x!r}") from exc

    raise TypeError(
        f"unsupported coefficient type: {type(x).__name__}; "
        "expected int, str, or Fraction"
    )


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
) -> Result:
    """Analyze a polynomial f(x) ∈ Q[x] of degree 1..5 and return a certificate.

    Notes (v3.0.0):
    - The certificate is proof-first: `proof` + `objects` are normative.
    - `summary` is UX-only; the verifier must ignore it for correctness.
    """
    opts = AnalysisOptions(
        explain=explain
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
    certificate: Mapping[str, Any]
) -> VerifiedResult:
    """Verify an OpenGalois certificate and return per-check verification output."""
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
