#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from opengalois import analyze, verify


def family_993(m: int) -> list[str]:
    """Family (9.93):

    y^5 + (m^5 - 3)y^4
      + (-m^9 - 2m^8 - 3m^7 - 5m^6 - 6m^5 - 2m^4 + m^3 - m^2 + 3)y^3
      + (m^10 + 2m^9 + 4m^8 + 6m^7 + 10m^6 + 9m^5 + 4m^4
         - 2m^3 + 2m^2 - 1)y^2
      - m^2(m^7 + 2m^6 + 3m^5 + 5m^4 + 5m^3 + 2m^2 - m + 1)y
      + m^5.
    """
    return [
        "1",
        str(m**5 - 3),
        str(
            -m**9
            - 2 * m**8
            - 3 * m**7
            - 5 * m**6
            - 6 * m**5
            - 2 * m**4
            + m**3
            - m**2
            + 3
        ),
        str(
            m**10
            + 2 * m**9
            + 4 * m**8
            + 6 * m**7
            + 10 * m**6
            + 9 * m**5
            + 4 * m**4
            - 2 * m**3
            + 2 * m**2
            - 1
        ),
        str(
            -m**2
            * (
                m**7
                + 2 * m**6
                + 3 * m**5
                + 5 * m**4
                + 5 * m**3
                + 2 * m**2
                - m
                + 1
            )
        ),
        str(m**5),
    ]


def family_994(n: int) -> list[str]:
    """Family (9.94):

    y^5 - n^2 y^4
      + 2(n^3 - 3n^2 + 5n - 5)y^3
      - (n^4 - 5n^3 + 11n^2 - 15n + 5)y^2
      + (-n^3 + 4n^2 - 10n + 10)y
      - 1.
    """
    return [
        "1",
        str(-n**2),
        str(2 * (n**3 - 3 * n**2 + 5 * n - 5)),
        str(-(n**4 - 5 * n**3 + 11 * n**2 - 15 * n + 5)),
        str(-n**3 + 4 * n**2 - 10 * n + 10),
        "-1",
    ]


def get_summary_group(cert: dict[str, Any]) -> str | None:
    summary = cert.get("summary")
    if isinstance(summary, dict):
        group = summary.get("galois_group")
        if isinstance(group, str):
            return group
    return None


def poly_str(coeffs: list[str]) -> str:
    return " ".join(coeffs)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate C5 examples from the two parametric quintic families."
    )
    parser.add_argument("--lo", type=int, default=-10)
    parser.add_argument("--hi", type=int, default=10)
    parser.add_argument("--max", type=int, default=10, help="Maximum C5 certificates to save.")
    parser.add_argument(
        "--family",
        choices=("993", "994", "both"),
        default="both",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("build/c5_families"),
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
    )

    args = parser.parse_args()

    if args.lo > args.hi:
        raise SystemExit("--lo must be <= --hi")

    outdir: Path = args.outdir
    certdir = outdir / "certs"
    certdir.mkdir(parents=True, exist_ok=True)

    manifest_path = outdir / "manifest.tsv"
    failures_path = outdir / "failures.tsv"

    saved = 0
    tested = 0
    failed = 0

    with manifest_path.open("w", encoding="utf-8", newline="") as mf, \
         failures_path.open("w", encoding="utf-8", newline="") as ff:

        manifest = csv.DictWriter(
            mf,
            fieldnames=[
                "family",
                "parameter",
                "group",
                "coeffs_desc",
                "certificate",
            ],
            delimiter="\t",
        )
        manifest.writeheader()

        failures = csv.DictWriter(
            ff,
            fieldnames=[
                "family",
                "parameter",
                "coeffs_desc",
                "stage",
                "error",
            ],
            delimiter="\t",
        )
        failures.writeheader()

        families: list[tuple[str, Any]] = []
        if args.family in ("993", "both"):
            families.append(("993", family_993))
        if args.family in ("994", "both"):
            families.append(("994", family_994))

        for family_name, family_fn in families:
            for t in range(args.lo, args.hi + 1):
                # En la familia (9.93) el discriminante tiene factor m^18.
                # m=0 es degenerado, así que se salta.
                if family_name == "993" and t == 0:
                    continue

                coeffs = family_fn(t)
                tested += 1

                try:
                    result = analyze(coeffs, explain=False)
                    cert = result.certificate
                except Exception as exc:
                    failed += 1
                    failures.writerow(
                        {
                            "family": family_name,
                            "parameter": t,
                            "coeffs_desc": poly_str(coeffs),
                            "stage": "analyze",
                            "error": repr(exc),
                        }
                    )
                    continue

                group = get_summary_group(cert)

                if group != "C5":
                    continue

                if not args.no_verify:
                    try:
                        vr = verify(cert)
                    except Exception as exc:
                        failed += 1
                        failures.writerow(
                            {
                                "family": family_name,
                                "parameter": t,
                                "coeffs_desc": poly_str(coeffs),
                                "stage": "verify_exception",
                                "error": repr(exc),
                            }
                        )
                        continue

                    if not getattr(vr, "verified", False):
                        failed += 1
                        failures.writerow(
                            {
                                "family": family_name,
                                "parameter": t,
                                "coeffs_desc": poly_str(coeffs),
                                "stage": "verify_rejected",
                                "error": "certificate rejected by verifier",
                            }
                        )
                        continue

                cert_name = f"C5_family_{family_name}_t{t}.json"
                cert_path = certdir / cert_name
                cert_path.write_text(
                    json.dumps(cert, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

                saved += 1
                manifest.writerow(
                    {
                        "family": family_name,
                        "parameter": t,
                        "group": group,
                        "coeffs_desc": poly_str(coeffs),
                        "certificate": str(cert_path),
                    }
                )

                print(
                    f"[{saved}] C5 from family {family_name}, parameter {t}: "
                    f"{coeffs} -> {cert_path}",
                    flush=True,
                )

                if args.max and saved >= args.max:
                    print()
                    print(f"Saved:   {saved}")
                    print(f"Tested:  {tested}")
                    print(f"Failed:  {failed}")
                    print(f"Manifest: {manifest_path}")
                    print(f"Failures: {failures_path}")
                    return 0

    print()
    print(f"Saved:   {saved}")
    print(f"Tested:  {tested}")
    print(f"Failed:  {failed}")
    print(f"Manifest: {manifest_path}")
    print(f"Failures: {failures_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())