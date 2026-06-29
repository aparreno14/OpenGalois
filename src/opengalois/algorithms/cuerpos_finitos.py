"""Compatibility exports for prime-field polynomial arithmetic.

The arithmetic itself lives in :mod:`opengalois.polyops.asc_fpx`. This module is
kept only so older experimental imports continue to resolve while the codebase
is migrated to the ``polyops`` namespace.
"""

from __future__ import annotations

from opengalois.polyops.asc_fpx import FpPoly, FpPolynomialRing, PrimeField

# Backward-compatible names used by the prototype code.
cuerpo_fp = PrimeField
anillo_fp_x = FpPolynomialRing

__all__ = [
    "FpPoly",
    "FpPolynomialRing",
    "PrimeField",
    "anillo_fp_x",
    "cuerpo_fp",
]
