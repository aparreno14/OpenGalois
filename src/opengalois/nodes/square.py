# src/opengalois/nodes/square.py
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from opengalois.codec.rationals import _frac_to_str
from opengalois.engine.context import _next_fact_id

if TYPE_CHECKING:
    from opengalois.engine.context import EngineContext


def _nonsquare_fraction_evidence(q: Fraction) -> dict[str, Any]:
    """Build compact verifier-checked evidence for NonSquareQQ(q)."""
    a = q.numerator
    b = q.denominator

    if a < 0:
        return {"obstruction": {"kind": "negative"}}

    ra = math.isqrt(a)
    if ra * ra != a:
        return {
            "obstruction": {
                "kind": "integer_isqrt_interval",
                "side": "numerator",
                "lower_root": str(ra),
                "lower_square": str(ra * ra),
                "upper_root": str(ra + 1),
                "upper_square": str((ra + 1) * (ra + 1)),
            }
        }

    rb = math.isqrt(b)
    if rb * rb != b:
        return {
            "obstruction": {
                "kind": "integer_isqrt_interval",
                "side": "denominator",
                "lower_root": str(rb),
                "lower_square": str(rb * rb),
                "upper_root": str(rb + 1),
                "upper_square": str((rb + 1) * (rb + 1)),
            }
        }

    raise ValueError("q is a square in QQ; no NonSquareQQ evidence exists")


def _is_square_int(n: int) -> bool:
    if n < 0:
        return False
    r = math.isqrt(n)
    return r * r == n


def _sqrt_fraction_if_square(q: Fraction) -> Fraction | None:
    """Return canonical sqrt(q) >= 0 if q is a square in QQ; else None."""
    if q < 0:
        return None
    a = q.numerator
    b = q.denominator  # Fraction normalizes b > 0 and gcd(a,b)=1
    if not _is_square_int(a) or not _is_square_int(b):
        return None
    return Fraction(math.isqrt(a), math.isqrt(b))


def _resolve_ratqq(ctx: EngineContext, rat_ref: str) -> Fraction:
    """Resolve a RatQQ object reference to a Fraction."""
    if rat_ref == "$input":
        raise ValueError("SquareNode expects a RatQQ object ref, not $input.")

    obj = ctx.objects.objects.get(rat_ref)
    if not isinstance(obj, dict):
        raise KeyError(f"Unknown object ref: {rat_ref!r}")
    if obj.get("kind") != "RatQQ":
        raise ValueError(f"Object {rat_ref!r} is not a RatQQ.")
    value = obj.get("value")
    if not isinstance(value, str):
        raise ValueError(f"RatQQ object {rat_ref!r} is missing canonical string value.")

    return Fraction(value)


@dataclass(frozen=True)
class SquareNode:
    """Classify a RatQQ object as square or non-square in QQ.

    Emits:
      - if square:
          SqrtQQ(q, k)
          IsSquareQQ(q)
      - if non-square:
          NonSquareQQ(q)

    This node is intentionally generic and does not emit lifted predicates such as
    DiscSquareQQ/DiscNonSquareQQ. Those belong to higher-level polynomial logic.
    """

    sqrt_pred: str = "SqrtQQ"
    sqrt_rule: str = "sqrt.QQ.check@1"

    is_square_pred: str = "IsSquareQQ"
    is_square_rule: str = "is_square.QQ.lift@1"

    non_square_pred: str = "NonSquareQQ"
    non_square_rule: str = "nonsquare.QQ.isqrt@2"

    def run(
        self,
        ctx: EngineContext,
        *,
        rat_ref: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Run square/non-square classification for a RatQQ object.

        Returns:
            (facts, out) where out has shape:
              {
                "rat_ref": ...,
                "value": "...",
                "decision": "square" | "nonsquare",
                "sqrt_ref": "... | None",
                "sqrt_value": "... | None",
                "facts": {
                    "sqrt": "...",        # only if square
                    "square": "...",      # only if square
                    "non_square": "...",  # only if nonsquare
                },
              }
        """
        out_map = ctx.cache.setdefault("_square_out_by_rat", {})
        if not isinstance(out_map, dict):
            raise TypeError("ctx.cache['_square_out_by_rat'] must be a dict")

        cached = out_map.get(rat_ref)
        if isinstance(cached, dict):
            return [], dict(cached)

        q = _resolve_ratqq(ctx, rat_ref)
        facts: list[dict[str, Any]] = []

        out: dict[str, Any]
        k = _sqrt_fraction_if_square(q)
        if k is not None:
            k_ref = f"{rat_ref}.sqrt"
            ctx.objects.put_rat(k_ref, k)

            fid_sqrt = _next_fact_id(ctx)
            facts.append(
                {
                    "id": fid_sqrt,
                    "claim": {"pred": self.sqrt_pred, "args": [{"ref": rat_ref}, {"ref": k_ref}]},
                    "rule": self.sqrt_rule,
                    "premises": [],
                    "statement": "Explicit square root witness in QQ.",
                }
            )

            fid_is = _next_fact_id(ctx)
            facts.append(
                {
                    "id": fid_is,
                    "claim": {"pred": self.is_square_pred, "args": [{"ref": rat_ref}]},
                    "rule": self.is_square_rule,
                    "premises": [fid_sqrt],
                    "statement": "Rational value is a square in QQ.",
                }
            )

            out = {
                "rat_ref": rat_ref,
                "value": _frac_to_str(q),
                "decision": "square",
                "sqrt_ref": k_ref,
                "sqrt_value": _frac_to_str(k),
                "facts": {
                    "sqrt": fid_sqrt,
                    "square": fid_is,
                },
            }
        else:
            evidence = _nonsquare_fraction_evidence(q)
            fid_ns = _next_fact_id(ctx)
            facts.append(
                {
                    "id": fid_ns,
                    "claim": {"pred": self.non_square_pred, "args": [{"ref": rat_ref}]},
                    "rule": self.non_square_rule,
                    "premises": [],
                    "evidence": evidence,
                    "statement": "Rational value is not a square in QQ.",
                }
            )

            out = {
                "rat_ref": rat_ref,
                "value": _frac_to_str(q),
                "decision": "nonsquare",
                "sqrt_ref": None,
                "sqrt_value": None,
                "facts": {
                    "non_square": fid_ns,
                },
            }

        out_map[rat_ref] = dict(out)
        return facts, out