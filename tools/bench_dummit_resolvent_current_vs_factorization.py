#!/usr/bin/env python
# ruff: noqa
# ruff: format: off
"""Benchmark Dummit-resolvent rational-root detection methods.

This is an experimental local tool.  It compares exactly two strategies on the
same Dummit sextic resolvents:

1. ``current``: the method currently used by the degree-5 engine, namely
   ``_find_rational_root_QQ_desc_resolvent_6_1plus5``.
2. ``factorization``: an experimental degree-6 extension of the current
   Zassenhaus/Hensel reducibility pipeline, used only inside this benchmark.
   It factors the sextic over QQ and detects whether a linear factor exists.

The tool does not change OpenGalois runtime code.  It is intended to answer the
engineering question: should Dummit's sextic resolvent continue to use the
current specialized rational-root search, or is the reducibility pipeline faster
on real and hard cases?
"""

from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
import random
import statistics
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from opengalois.algorithms import factorization as fac
from opengalois.algorithms.factorization_fpx import (
    _ddf_logic_fpx,
    _factor_sort_key,
    eqdegr_fact_fpx,
)
from opengalois.engine.procedures.irreducible.deg5 import (
    _find_rational_root_QQ_desc_resolvent_6_1plus5,
)
from opengalois.nodes.resolvent import _compute_deg5_sextic_dummit_F20
from opengalois.polyops.asc_fpx import FpPoly, FpPolynomialRing
from opengalois.polyops.desc_qx import _degree_desc, _trim_leading_zeros_desc
from opengalois.polyops.desc_zx import ZPoly


@dataclass(frozen=True)
class BenchCase:
    family: str
    index: int
    quintic_desc: tuple[Fraction, ...]
    resolvent_desc: tuple[Fraction, ...]


@dataclass(frozen=True)
class MethodResult:
    ok: bool
    has_root: bool | None
    root: str | None
    seconds: float
    error: str | None = None
    num_factors: int | None = None
    degrees: str | None = None


# =============================================================================
# Experimental degree-6 reuse of the reducibility pipeline
# =============================================================================


def _factor_fpx_any_degree(
    ring: FpPolynomialRing,
    f: FpPoly,
) -> list[tuple[FpPoly, int]]:
    """Factor a square-free polynomial over F_p[x], without the <=5 guard.

    This intentionally reuses the same DDF/EDF implementation as the production
    finite-field factorizer, but removes the public degree check for benchmark
    purposes.  Multiplicities are one because the caller chooses a good prime.
    """
    f = ring.from_coeffs(f)
    if not f:
        raise ValueError("cannot factor the zero polynomial over F_p[x]")
    if ring.degree(f) <= 0:
        return []

    f = ring.monic(f)
    factors: list[tuple[FpPoly, int]] = []
    for product_factor, degree in _ddf_logic_fpx(ring, f):
        for factor in eqdegr_fact_fpx(ring, degree, product_factor):
            factors.append((ring.monic(factor), 1))

    return sorted(
        factors,
        key=lambda item: (_factor_sort_key(ring, item[0]), item[1]),
    )


def _modular_factorization_z_any_degree(
    f_desc: ZPoly,
    p: int,
) -> tuple[FpPolynomialRing, FpPoly, list[FpPoly], list[ZPoly]]:
    """Factor primitive square-free ``f_desc`` over F_p[x] without degree limit."""
    if f_desc[0] % p == 0:
        raise ValueError("p divides lc(f)")

    ring = FpPolynomialRing(p)
    f_mod = ring.from_desc_ints(f_desc)

    factors_asc: list[FpPoly] = []
    for factor, multiplicity in _factor_fpx_any_degree(ring, f_mod):
        if ring.degree(factor) <= 0:
            continue
        if multiplicity != 1:
            raise ValueError("p is not good: f mod p is not square-free")
        factors_asc.append(ring.monic(factor))

    factors_asc.sort(key=lambda h: (ring.degree(h), tuple(h)))
    if not fac._verify_modular_factorization(ring, f_mod, factors_asc, f_desc[0]):
        raise RuntimeError("invalid modular factorization")

    factors_desc = [fac._fpx_to_desc_z_centered(factor, p) for factor in factors_asc]
    return ring, f_mod, factors_asc, factors_desc


def _factor_squarefree_primitive_z_any_degree(f: ZPoly, *, max_degree: int = 6) -> list[ZPoly]:
    """Experimental Zassenhaus factorization for square-free primitive Z[x].

    This is a direct degree-6 generalization of the production degree-bounded
    recombination code.  It exists only for this benchmark.
    """
    degree = fac._degree_desc_z(f)
    if degree <= 0:
        return []
    if degree == 1:
        return [f]
    if degree > max_degree:
        raise ValueError(f"benchmark factorizer supports degree <= {max_degree}")

    p = fac._choose_zassenhaus_prime(f)
    _, _, _, local_factors = _modular_factorization_z_any_degree(f, p)

    if len(local_factors) == 1:
        return [f]

    bound = fac._zassenhaus_factor_bound_z(f)
    ell, target_modulus = fac._hensel_precision_from_bound(p, bound)
    f_asc = fac._desc_z_to_asc(f)
    leading_coeff = f[0]
    max_candidate_degree = degree // 2

    for subset in fac._candidate_subsets(local_factors, max_candidate_degree):
        selected = [local_factors[i] for i in subset]
        complement = [local_factors[i] for i in range(len(local_factors)) if i not in subset]

        u0_desc = fac._scalar_mul_desc_z(fac._prod_desc_z(selected), leading_coeff)
        v0_desc = fac._prod_desc_z(complement)
        lifted_u, lifted_v, modulus = fac._hensel_lift_pair_asc(
            f_asc,
            fac._desc_z_to_asc(u0_desc),
            fac._desc_z_to_asc(v0_desc),
            p,
            ell,
        )
        if modulus != target_modulus:
            raise RuntimeError("unexpected Hensel modulus")

        for lifted in (lifted_u, lifted_v):
            candidate = fac._primitive_part_desc_z(
                fac._asc_z_to_desc(fac._center_asc_z(lifted, modulus))
            )
            candidate_degree = fac._degree_desc_z(candidate)
            if candidate_degree <= 0 or candidate_degree >= degree:
                continue
            if fac._divides_desc_z(f, candidate):
                quotient = fac._primitive_part_desc_z(fac._div_exact_desc_z(f, candidate))
                return (
                    _factor_squarefree_primitive_z_any_degree(candidate, max_degree=max_degree)
                    + _factor_squarefree_primitive_z_any_degree(quotient, max_degree=max_degree)
                )

    return [f]


def factorize_q_degree6_for_benchmark(coeffs_q: list[Fraction]) -> list[list[Fraction]]:
    """Factor a monic degree <= 6 polynomial over QQ using the reducibility pipeline."""
    coeffs_q = _trim_leading_zeros_desc([Fraction(c) for c in coeffs_q])
    degree = _degree_desc(coeffs_q)
    if degree <= 0:
        raise ValueError("Input must be a non-constant polynomial.")
    if degree > 6:
        raise ValueError("Benchmark factorizer supports degree <= 6 only.")
    if coeffs_q[0] != Fraction(1, 1):
        raise ValueError(f"Input polynomial must be monic. Leading coefficient is {coeffs_q[0]}.")

    factors_with_mult: list[tuple[ZPoly, int]] = []
    for squarefree_part, multiplicity in fac._squarefree_decomposition_z(coeffs_q):
        for factor in _factor_squarefree_primitive_z_any_degree(squarefree_part, max_degree=6):
            factors_with_mult.append((factor, multiplicity))

    out: list[list[Fraction]] = []
    for factor, multiplicity in factors_with_mult:
        monic_factor = fac._z_factor_to_monic_q(factor)
        out.extend([monic_factor] * multiplicity)

    out.sort(key=lambda g: (len(g), tuple((c.numerator, c.denominator) for c in g)))
    return out


# =============================================================================
# Methods under comparison
# =============================================================================


def _current_method(resolvent_desc: list[Fraction]) -> tuple[bool, Fraction | None, int | None, str | None]:
    root = _find_rational_root_QQ_desc_resolvent_6_1plus5(resolvent_desc)
    return root is not None, root, None, None


def _factorization_method(resolvent_desc: list[Fraction]) -> tuple[bool, Fraction | None, int | None, str | None]:
    factors = factorize_q_degree6_for_benchmark(resolvent_desc)
    degrees = [_degree_desc(f) for f in factors]
    root: Fraction | None = None
    for factor in factors:
        if _degree_desc(factor) == 1:
            # Monic linear factor x - theta.
            root = -factor[1]
            break
    return root is not None, root, len(factors), "+".join(str(d) for d in degrees)


def _time_call(
    fn: Callable[[list[Fraction]], tuple[bool, Fraction | None, int | None, str | None]],
    resolvent_desc: list[Fraction],
) -> MethodResult:
    start = time.perf_counter()
    try:
        has_root, root, num_factors, degrees = fn(resolvent_desc)
    except Exception as exc:  # noqa: BLE001 - benchmark should record failures.
        return MethodResult(
            ok=False,
            has_root=None,
            root=None,
            seconds=time.perf_counter() - start,
            error=f"{type(exc).__name__}: {exc}",
        )
    return MethodResult(
        ok=True,
        has_root=has_root,
        root=str(root) if root is not None else None,
        seconds=time.perf_counter() - start,
        num_factors=num_factors,
        degrees=degrees,
    )


def _method_worker(method_name: str, resolvent_desc: list[Fraction], queue: mp.Queue[Any]) -> None:
    fn = _current_method if method_name == "current" else _factorization_method
    queue.put(_time_call(fn, resolvent_desc))


def _time_call_with_optional_timeout(
    method_name: str,
    resolvent_desc: list[Fraction],
    timeout: float,
) -> MethodResult:
    """Run method, using a subprocess only when a positive timeout is requested."""
    if timeout <= 0:
        fn = _current_method if method_name == "current" else _factorization_method
        return _time_call(fn, resolvent_desc)

    ctx = mp.get_context("spawn")
    queue: mp.Queue[Any] = ctx.Queue()
    proc = ctx.Process(target=_method_worker, args=(method_name, resolvent_desc, queue))
    start = time.perf_counter()
    proc.start()
    proc.join(timeout)
    elapsed = time.perf_counter() - start
    if proc.is_alive():
        proc.terminate()
        proc.join()
        return MethodResult(
            ok=False,
            has_root=None,
            root=None,
            seconds=elapsed,
            error=f"timeout after {timeout:.3f}s",
        )
    if queue.empty():
        return MethodResult(
            ok=False,
            has_root=None,
            root=None,
            seconds=elapsed,
            error="worker exited without result",
        )
    result = queue.get()
    if isinstance(result, MethodResult):
        # Keep the subprocess wall time.  It includes spawn overhead, so timeout
        # mode is for avoiding hangs, not for fine microbenchmarking.
        return MethodResult(
            ok=result.ok,
            has_root=result.has_root,
            root=result.root,
            seconds=elapsed,
            error=result.error,
            num_factors=result.num_factors,
            degrees=result.degrees,
        )
    return MethodResult(False, None, None, elapsed, error=f"unexpected worker result: {result!r}")


# =============================================================================
# Case generation
# =============================================================================


def _rand_signed_int(rng: random.Random, bits: int) -> int:
    if bits <= 0:
        return 0
    value = rng.getrandbits(bits)
    # Force the requested order of magnitude most of the time.
    if bits > 1:
        value |= 1 << (bits - 1)
    return -value if rng.randrange(2) else value


def _is_irreducible_quintic(coeffs: list[Fraction]) -> bool:
    try:
        return len(fac.factorize_le5(coeffs)) == 1
    except Exception:
        return False


def _make_case(family: str, index: int, p: int, q: int, r: int, s: int) -> BenchCase | None:
    quintic = [Fraction(1), Fraction(0), Fraction(p), Fraction(q), Fraction(r), Fraction(s)]
    if _degree_desc(quintic) != 5:
        return None
    resolvent = _compute_deg5_sextic_dummit_F20(quintic)
    if _degree_desc(resolvent) != 6:
        return None
    return BenchCase(family, index, tuple(quintic), tuple(resolvent))


def iter_small_box_cases(bound: int, max_cases: int, filter_irreducible: bool) -> Iterable[BenchCase]:
    index = 0
    produced = 0
    for p in range(-bound, bound + 1):
        for q in range(-bound, bound + 1):
            for r in range(-bound, bound + 1):
                for s in range(-bound, bound + 1):
                    case = _make_case("small_box", index, p, q, r, s)
                    index += 1
                    if case is None:
                        continue
                    if filter_irreducible and not _is_irreducible_quintic(list(case.quintic_desc)):
                        continue
                    yield case
                    produced += 1
                    if max_cases > 0 and produced >= max_cases:
                        return


def iter_random_bit_cases(
    bits: int,
    count: int,
    seed: int,
    filter_irreducible: bool,
    max_attempt_multiplier: int = 100,
) -> Iterable[BenchCase]:
    rng = random.Random(seed + 1009 * bits)
    produced = 0
    attempts = 0
    max_attempts = max(count * max_attempt_multiplier, count)
    while produced < count and attempts < max_attempts:
        attempts += 1
        p = _rand_signed_int(rng, bits)
        q = _rand_signed_int(rng, bits)
        r = _rand_signed_int(rng, bits)
        s = _rand_signed_int(rng, bits)
        case = _make_case(f"random_{bits}bit", attempts, p, q, r, s)
        if case is None:
            continue
        if filter_irreducible and not _is_irreducible_quintic(list(case.quintic_desc)):
            continue
        produced += 1
        yield case


# =============================================================================
# Reporting
# =============================================================================


def _primitive_integer_metrics(coeffs: list[Fraction]) -> tuple[int, int]:
    ints = fac._primitive_integer_poly_from_QQ_desc(coeffs)
    return abs(ints[0]).bit_length(), abs(ints[-1]).bit_length()


def _row_for_case(case: BenchCase, timeout: float) -> dict[str, Any]:
    resolvent = list(case.resolvent_desc)
    lc_bits, const_bits = _primitive_integer_metrics(resolvent)

    current = _time_call_with_optional_timeout("current", resolvent, timeout)
    factorization = _time_call_with_optional_timeout("factorization", resolvent, timeout)

    agree = current.ok and factorization.ok and current.has_root == factorization.has_root
    if current.ok and factorization.ok:
        if current.seconds < factorization.seconds:
            winner = "current"
        elif factorization.seconds < current.seconds:
            winner = "factorization"
        else:
            winner = "tie"
    else:
        winner = "error"

    return {
        "family": case.family,
        "index": case.index,
        "quintic_desc": " ".join(str(c) for c in case.quintic_desc),
        "resolvent_lc_bits": lc_bits,
        "resolvent_const_bits": const_bits,
        "current_ok": current.ok,
        "current_has_root": current.has_root,
        "current_root": current.root,
        "current_time_s": f"{current.seconds:.9f}",
        "current_error": current.error or "",
        "factorization_ok": factorization.ok,
        "factorization_has_root": factorization.has_root,
        "factorization_root": factorization.root,
        "factorization_time_s": f"{factorization.seconds:.9f}",
        "factorization_num_factors": factorization.num_factors if factorization.num_factors is not None else "",
        "factorization_degrees": factorization.degrees or "",
        "factorization_error": factorization.error or "",
        "agree": agree,
        "winner": winner,
        "speedup_factorization_vs_current": (
            f"{current.seconds / factorization.seconds:.6f}"
            if current.ok and factorization.ok and factorization.seconds > 0
            else ""
        ),
    }


def _summarize(rows: list[dict[str, Any]]) -> None:
    print("\nSummary by family")
    print("family,cases,agree,current_median_s,factor_median_s,current_p95_s,factor_p95_s,current_wins,factor_wins,errors")

    families = sorted({str(row["family"]) for row in rows})
    for family in families:
        group = [row for row in rows if row["family"] == family]
        cur = [float(row["current_time_s"]) for row in group if row["current_ok"]]
        fac_times = [float(row["factorization_time_s"]) for row in group if row["factorization_ok"]]
        current_wins = sum(1 for row in group if row["winner"] == "current")
        factor_wins = sum(1 for row in group if row["winner"] == "factorization")
        errors = sum(1 for row in group if row["winner"] == "error")
        agree = sum(1 for row in group if row["agree"])

        def median(xs: list[float]) -> str:
            return f"{statistics.median(xs):.6f}" if xs else "NA"

        def p95(xs: list[float]) -> str:
            if not xs:
                return "NA"
            if len(xs) == 1:
                return f"{xs[0]:.6f}"
            return f"{statistics.quantiles(xs, n=20)[18]:.6f}"

        print(
            f"{family},{len(group)},{agree},"
            f"{median(cur)},{median(fac_times)},"
            f"{p95(cur)},{p95(fac_times)},"
            f"{current_wins},{factor_wins},{errors}"
        )

    slow = sorted(
        rows,
        key=lambda row: float(row["current_time_s"]) if row["current_ok"] else -1,
        reverse=True,
    )[:10]
    if slow:
        print("\nTop current-method slow cases")
        print("family,index,current_time_s,factorization_time_s,winner,lc_bits,const_bits,quintic_desc")
        for row in slow:
            print(
                f"{row['family']},{row['index']},{row['current_time_s']},"
                f"{row['factorization_time_s']},{row['winner']},"
                f"{row['resolvent_lc_bits']},{row['resolvent_const_bits']},"
                f"{row['quintic_desc']}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark current Dummit rational-root method vs degree-6 reducibility-pipeline factorization."
    )
    parser.add_argument("--small-bound", type=int, default=2, help="Box bound for depressed quintics x^5+p*x^3+q*x^2+r*x+s.")
    parser.add_argument("--max-small-cases", type=int, default=200, help="Maximum accepted small-box cases; 0 means no cap.")
    parser.add_argument("--random-cases", type=int, default=50, help="Accepted random irreducible cases per bit size.")
    parser.add_argument("--bits", default="32,64,128", help="Comma-separated coefficient bit sizes for random cases.")
    parser.add_argument("--seed", type=int, default=20260624, help="Deterministic RNG seed.")
    parser.add_argument("--timeout", type=float, default=0.0, help="Optional per-method timeout in seconds. 0 disables subprocess timeouts.")
    parser.add_argument("--no-filter-irreducible", action="store_true", help="Do not filter generated quintics by irreducibility.")
    parser.add_argument("--out", type=Path, default=Path("dummit_resolvent_current_vs_factorization.csv"), help="CSV output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    filter_irreducible = not args.no_filter_irreducible
    bit_sizes = [int(part) for part in args.bits.split(",") if part.strip()]

    cases: list[BenchCase] = []
    cases.extend(iter_small_box_cases(args.small_bound, args.max_small_cases, filter_irreducible))
    for bits in bit_sizes:
        cases.extend(iter_random_bit_cases(bits, args.random_cases, args.seed, filter_irreducible))

    if not cases:
        raise SystemExit("No benchmark cases were generated. Try --no-filter-irreducible or larger bounds.")

    fieldnames = [
        "family",
        "index",
        "quintic_desc",
        "resolvent_lc_bits",
        "resolvent_const_bits",
        "current_ok",
        "current_has_root",
        "current_root",
        "current_time_s",
        "current_error",
        "factorization_ok",
        "factorization_has_root",
        "factorization_root",
        "factorization_time_s",
        "factorization_num_factors",
        "factorization_degrees",
        "factorization_error",
        "agree",
        "winner",
        "speedup_factorization_vs_current",
    ]

    rows: list[dict[str, Any]] = []
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for n, case in enumerate(cases, start=1):
            row = _row_for_case(case, args.timeout)
            rows.append(row)
            writer.writerow(row)
            print(
                f"[{n}/{len(cases)}] {row['family']}#{row['index']} "
                f"current={row['current_time_s']}s factorization={row['factorization_time_s']}s "
                f"winner={row['winner']} agree={row['agree']}"
            )

    print(f"\nWrote CSV: {args.out}")
    _summarize(rows)

    disagreements = [row for row in rows if not row["agree"]]
    if disagreements:
        print(f"\nWARNING: {len(disagreements)} disagreement/error rows. Inspect the CSV before drawing conclusions.")


if __name__ == "__main__":
    main()
