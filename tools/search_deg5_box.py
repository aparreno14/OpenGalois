#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from opengalois import analyze, verify

ALL_GROUPS = ("S5", "A5", "F20", "D5", "C5")


def coeffs_for(p: int, q: int, r: int, s: int) -> list[str]:
    # x^5 + p x^3 + q x^2 + r x + s
    return ["1", "0", str(p), str(q), str(r), str(s)]


def filename_for(group: str, p: int, q: int, r: int, s: int) -> str:
    def fmt(n: int) -> str:
        return f"m{-n}" if n < 0 else str(n)

    return f"{group}_p{fmt(p)}_q{fmt(q)}_r{fmt(r)}_s{fmt(s)}.json"


def poly_str(p: int, q: int, r: int, s: int) -> str:
    return f"x^5 + ({p})x^3 + ({q})x^2 + ({r})x + ({s})"


def get_summary_group(cert: dict[str, Any]) -> str | None:
    summary = cert.get("summary")
    if isinstance(summary, dict):
        g = summary.get("galois_group")
        if isinstance(g, str):
            return g
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search depressed monic quintics x^5+p x^3+q x^2+r x+s in a box."
    )
    parser.add_argument(
        "--lo",
        type=int,
        default=-5,
        help="Lower bound for p,q,r,s. Default: -5.",
    )
    parser.add_argument(
        "--hi",
        type=int,
        default=5,
        help="Upper bound for p,q,r,s. Default: 5.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("build/deg5_box"),
        help="Output directory.",
    )
    parser.add_argument(
        "--target-groups",
        nargs="+",
        choices=ALL_GROUPS,
        default=list(ALL_GROUPS),
        help=(
            "Groups to save. Default: S5 A5 F20 D5 C5. "
            "Example: --target-groups C5"
        ),
    )
    parser.add_argument(
        "--max-per-group",
        type=int,
        default=0,
        help="Stop saving after this many certificates per target group. 0 means no limit.",
    )
    parser.add_argument(
        "--stop-when-full",
        action="store_true",
        help="Stop the whole search once every target group reaches --max-per-group.",
    )
    parser.add_argument(
        "--exclude-box",
        nargs=2,
        type=int,
        metavar=("LO", "HI"),
        default=None,
        help=(
            "Skip polynomials with p,q,r,s all inside [LO,HI]. "
            "Useful when extending a previous box search."
        ),
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Do not run the independent verifier on generated certificates.",
    )

    args = parser.parse_args()

    if args.lo > args.hi:
        raise SystemExit("--lo must be <= --hi")

    target_groups = tuple(dict.fromkeys(args.target_groups))

    exclude_box: tuple[int, int] | None = None
    if args.exclude_box is not None:
        excl_lo, excl_hi = args.exclude_box
        if excl_lo > excl_hi:
            raise SystemExit("--exclude-box LO must be <= HI")
        exclude_box = (excl_lo, excl_hi)

    outdir: Path = args.outdir
    certdir = outdir / "certs"
    certdir.mkdir(parents=True, exist_ok=True)

    manifest_path = outdir / "manifest.tsv"
    failures_path = outdir / "failures.tsv"
    counts_path = outdir / "counts.json"

    counts: dict[str, int] = {g: 0 for g in target_groups}
    seen_total = 0
    excluded_total = 0
    analyzed_total = 0
    saved_total = 0
    failed_total = 0

    with manifest_path.open("w", encoding="utf-8", newline="") as mf, \
         failures_path.open("w", encoding="utf-8", newline="") as ff:

        manifest = csv.DictWriter(
            mf,
            fieldnames=[
                "group",
                "p",
                "q",
                "r",
                "s",
                "polynomial",
                "certificate",
            ],
            delimiter="\t",
        )
        manifest.writeheader()

        failures = csv.DictWriter(
            ff,
            fieldnames=[
                "p",
                "q",
                "r",
                "s",
                "polynomial",
                "stage",
                "error",
            ],
            delimiter="\t",
        )
        failures.writeheader()

        values = range(args.lo, args.hi + 1)

        for p in values:
            for q in values:
                for r in values:
                    for s in values:
                        if exclude_box is not None:
                            excl_lo, excl_hi = exclude_box
                            if (
                                excl_lo <= p <= excl_hi
                                and excl_lo <= q <= excl_hi
                                and excl_lo <= r <= excl_hi
                                and excl_lo <= s <= excl_hi
                            ):
                                excluded_total += 1
                                continue

                        seen_total += 1
                        coeffs = coeffs_for(p, q, r, s)
                        fstr = poly_str(p, q, r, s)

                        try:
                            result = analyze(coeffs, explain=False)
                            cert = result.certificate
                            analyzed_total += 1
                        except Exception as exc:
                            failed_total += 1
                            failures.writerow(
                                {
                                    "p": p,
                                    "q": q,
                                    "r": r,
                                    "s": s,
                                    "polynomial": fstr,
                                    "stage": "analyze",
                                    "error": repr(exc),
                                }
                            )
                            continue

                        group = get_summary_group(cert)
                        if group not in target_groups:
                            continue

                        if args.max_per_group and counts[group] >= args.max_per_group:
                            continue

                        if not args.no_verify:
                            try:
                                vr = verify(cert)
                            except Exception as exc:
                                failed_total += 1
                                failures.writerow(
                                    {
                                        "p": p,
                                        "q": q,
                                        "r": r,
                                        "s": s,
                                        "polynomial": fstr,
                                        "stage": "verify_exception",
                                        "error": repr(exc),
                                    }
                                )
                                continue

                            if not getattr(vr, "verified", False):
                                failed_total += 1
                                failures.writerow(
                                    {
                                        "p": p,
                                        "q": q,
                                        "r": r,
                                        "s": s,
                                        "polynomial": fstr,
                                        "stage": "verify_rejected",
                                        "error": "certificate rejected by verifier",
                                    }
                                )
                                continue

                        group_dir = certdir / group
                        group_dir.mkdir(parents=True, exist_ok=True)

                        cert_name = filename_for(group, p, q, r, s)
                        cert_path = group_dir / cert_name

                        cert_path.write_text(
                            json.dumps(cert, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8",
                        )

                        counts[group] += 1
                        saved_total += 1

                        manifest.writerow(
                            {
                                "group": group,
                                "p": p,
                                "q": q,
                                "r": r,
                                "s": s,
                                "polynomial": fstr,
                                "certificate": str(cert_path),
                            }
                        )

                        print(
                            f"[{saved_total}] {group}: "
                            f"p={p}, q={q}, r={r}, s={s} -> {cert_path}",
                            flush=True,
                        )

                        if (
                            args.stop_when_full
                            and args.max_per_group
                            and all(counts[g] >= args.max_per_group for g in target_groups)
                        ):
                            break
                    else:
                        continue
                    break
                else:
                    continue
                break
            else:
                continue
            break

    summary = {
        "box": [args.lo, args.hi],
        "exclude_box": list(exclude_box) if exclude_box is not None else None,
        "target_groups": list(target_groups),
        "seen_total": seen_total,
        "excluded_total": excluded_total,
        "analyzed_total": analyzed_total,
        "saved_total": saved_total,
        "failed_total": failed_total,
        "counts": counts,
    }

    counts_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print()
    print("Resumen:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print()
    print(f"Certificados: {certdir}")
    print(f"Manifest:     {manifest_path}")
    print(f"Fallos:       {failures_path}")
    print(f"Counts:       {counts_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())