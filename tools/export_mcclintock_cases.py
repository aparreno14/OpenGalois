#!/usr/bin/env python3
"""Export certificates and LaTeX explanations for McClintock examples.

This version does NOT call the `opengalois` executable and does NOT require
`python -m opengalois.cli`. It imports the local source tree directly:

    <repo>/src/opengalois

Run it from the root of the repository:

    python export_mcclintock_cases_api.py

or explicitly:

    python export_mcclintock_cases_api.py --repo .

Outputs:

    build/mcclintock_cases/
      manifest.json
      inputs.tex
      01_case_01/
        certificate.json
        verify.json
        explain.tex
        summary.txt
      ...
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Case:
    case_id: str
    slug: str
    coeffs: tuple[str, ...]
    note: str = ""
    depressed_reference: tuple[str, ...] | None = None


# Coefficients in descending degree order.
CASES: tuple[Case, ...] = (
    Case("01", "case_01", ("1", "0", "0", "-3", "2", "1")),
    Case(
        "02",
        "case_02_original",
        ("1", "-3", "3", "-3", "3", "3"),
        note="The user noted that its depressed form is 1 0 5 0 5 -2.",
        depressed_reference=("1", "0", "5", "0", "5", "-2"),
    ),
    Case("03", "case_03", ("1", "0", "5", "0", "5", "-5")),
    Case("04", "case_04", ("1", "0", "-20", "0", "180", "64")),
    Case("05", "case_05", ("1", "0", "-10", "-30", "-35", "-18")),
    Case("06", "case_06", ("1", "0", "10", "10", "10", "3")),
    Case("07", "case_07_binomial", ("1", "0", "0", "0", "0", "-2")),
    Case("08", "case_08_sc0_nontrivial", ("1", "0", "0", "10", "10", "-2")),
)


def install_local_src(repo: Path) -> None:
    src = repo / "src"
    pkg = src / "opengalois"
    if not pkg.is_dir():
        raise RuntimeError(
            f"Cannot find local package at {pkg}. "
            "Run from the OpenGalois repository root or pass --repo PATH."
        )
    sys.path.insert(0, str(src))


def verify_to_json(result: Any) -> dict[str, Any]:
    return {
        "verified": bool(getattr(result, "verified", False)),
        "checks": [
            {
                "name": getattr(c, "name", ""),
                "ok": bool(getattr(c, "ok", False)),
                "details": getattr(c, "details", ""),
            }
            for c in getattr(result, "checks", [])
        ],
    }


def write_inputs_tex(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    lines.append(r"\begin{longtable}{@{}p{0.10\textwidth}p{0.42\textwidth}p{0.38\textwidth}@{}}")
    lines.append(r"\toprule")
    lines.append(r"Caso & Coeficientes & Ficheros \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    for row in rows:
        case_label = str(row["case_id"]).replace("_", r"\_")
        coeffs = str(row["coeffs"])
        cert = str(row["certificate"]).replace("\\", "/").replace("_", r"\_")
        tex = str(row["explain_tex"]).replace("\\", "/").replace("_", r"\_")
        lines.append(
            rf"{case_label} & \(\texttt{{{coeffs}}}\) & "
            rf"\texttt{{{cert}}}, \texttt{{{tex}}} \\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    (out_dir / "inputs.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summary_text(cert: dict[str, Any], case: Case) -> str:
    summary = cert.get("summary", {})
    inp = cert.get("input", {})
    lines = [
        f"case_id: {case.case_id}",
        f"slug: {case.slug}",
        f"coeffs: {' '.join(case.coeffs)}",
        f"note: {case.note}",
        "",
        f"degree: {inp.get('degree')}",
        f"status: {summary.get('status')}",
        f"galois_group: {summary.get('galois_group')}",
        f"solvable_by_radicals: {summary.get('solvable_by_radicals')}",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".", help="OpenGalois repository root.")
    parser.add_argument("--out", default="build/mcclintock_cases")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument(
        "--also-depressed-reference",
        action="store_true",
        help="Also run the depressed reference 1 0 5 0 5 -2 as an extra case.",
    )
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    install_local_src(repo)

    try:
        from opengalois import analyze, verify
        from opengalois.explain import explain_certificate, explain_certificate_to_pdf
    except Exception as exc:
        raise RuntimeError(
            "Could not import local OpenGalois from src/. "
            "Make sure dependencies are installed in this Python environment."
        ) from exc

    cases: list[Case] = list(CASES)
    if args.also_depressed_reference:
        for c in CASES:
            if c.depressed_reference is not None:
                cases.insert(
                    2,
                    Case(
                        f"{c.case_id}b",
                        f"{c.slug}_depressed_reference",
                        c.depressed_reference,
                        note=f"Depressed-form reference for {c.case_id}.",
                    ),
                )
                break

    manifest: list[dict[str, Any]] = []

    for case in cases:
        case_dir = out_dir / f"{case.case_id}_{case.slug}"
        case_dir.mkdir(parents=True, exist_ok=True)

        cert_path = case_dir / "certificate.json"
        verify_path = case_dir / "verify.json"
        explain_tex_path = case_dir / "explain.tex"
        explain_pdf_path = case_dir / "explain.pdf"
        summary_path = case_dir / "summary.txt"
        error_path = case_dir / "error.txt"

        row: dict[str, Any] = {
            "case_id": case.case_id,
            "slug": case.slug,
            "coeffs": " ".join(case.coeffs),
            "directory": str(case_dir.relative_to(out_dir)),
            "certificate": str(cert_path.relative_to(out_dir)),
            "verify_json": str(verify_path.relative_to(out_dir)),
            "explain_tex": str(explain_tex_path.relative_to(out_dir)),
            "summary_txt": str(summary_path.relative_to(out_dir)),
            "success": False,
        }

        print(f"[{case.case_id}] analyze {' '.join(case.coeffs)}")
        try:
            result = analyze(list(case.coeffs), explain=False)
            cert = result.certificate

            cert_path.write_text(
                json.dumps(cert, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            verified = verify(cert)
            verify_payload = verify_to_json(verified)
            verify_path.write_text(
                json.dumps(verify_payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            tex = explain_certificate(
                cert,
                format="latex",
                verify_first=True,
            )
            explain_tex_path.write_text(tex if tex.endswith("\n") else tex + "\n", encoding="utf-8")

            if args.pdf:
                explain_certificate_to_pdf(
                    cert,
                    str(explain_pdf_path),
                    verify_first=True,
                )
                row["explain_pdf"] = str(explain_pdf_path.relative_to(out_dir))

            summary_path.write_text(summary_text(cert, case), encoding="utf-8")
            row["summary"] = cert.get("summary", {})
            row["verified"] = verify_payload.get("verified")
            row["success"] = True

            print(f"[{case.case_id}] ok")

        except Exception as exc:
            tb = traceback.format_exc()
            error_path.write_text(tb, encoding="utf-8", errors="replace")
            row["success"] = False
            row["error"] = str(exc)
            row["error_file"] = str(error_path.relative_to(out_dir))
            print(f"[{case.case_id}] ERROR: {exc}", file=sys.stderr)
            print(tb, file=sys.stderr)
            if not args.keep_going:
                manifest.append(row)
                break

        manifest.append(row)

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_inputs_tex(out_dir, manifest)

    ok = sum(1 for row in manifest if row.get("success"))
    print(f"Done: {ok}/{len(manifest)} successful")
    print(f"Output directory: {out_dir}")
    return 0 if ok == len(manifest) else 1


if __name__ == "__main__":
    raise SystemExit(main())
