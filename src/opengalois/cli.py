"""Command-line interface for OpenGalois.

This module provides the public ``opengalois`` command.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import textwrap
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import __version__, analyze, verify
from .codec.rationals import _poly_to_str
from .explain import ExplainError, explain_certificate, explain_certificate_to_pdf
from .radicals import decode_expr_list_payloads
from .radicals.cli_format import CliRadicalLines, format_cli_radical_lines
from .radicals.render import RenderStyle

_COEFF_TOKEN_RE = re.compile(r"^[+-]?\d+(?:/\d+)?$")

def _looks_like_coeff_token(token: str) -> bool:
    """Return whether a token looks like an exact coefficient literal.

    Args:
        token: CLI token.

    Returns:
        ``True`` when the token looks like an integer or rational literal.
    """
    return bool(_COEFF_TOKEN_RE.fullmatch(token.strip()))


def _build_parser() -> argparse.ArgumentParser:
    """Construct the top-level OpenGalois CLI parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="opengalois",
        description=(
            "OpenGalois: glass-box Galois analysis for polynomials over Q "
            "of degree 1..5."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze",
        usage=(
            "opengalois analyze [--ascending] [--json | --verbose] "
            "[--output PATH] COEFF [COEFF ...]"
        ),
        help="Analyze a polynomial over Q of degree 1..5 and emit a certificate.",
        description=(
            "Analyze a polynomial over Q of degree 1..5. Coefficients are "
            "interpreted in descending degree order by default."
        ),
        epilog=(
            "COEFF values must be exact integers or rationals such as "
            "3, -7, 5/2, -9/4."
        ),
    )
    analyze_parser.add_argument(
        "--ascending",
        action="store_true",
        help="Interpret coefficients as [a0,...,an] instead of [an,...,a0].",
    )
    analyze_out = analyze_parser.add_mutually_exclusive_group()
    analyze_out.add_argument(
        "--json",
        action="store_true",
        help="Print the generated certificate JSON to stdout.",
    )
    analyze_out.add_argument(
        "--verbose",
        action="store_true",
        help="Print an expanded human-readable summary.",
    )
    analyze_parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write the generated certificate JSON to PATH.",
    )

    verify_parser = subparsers.add_parser(
        "verify",
        usage="opengalois verify [--json | --verbose] CERTIFICATE",
        help="Verify an OpenGalois certificate JSON file.",
        description=(
            "Verify an OpenGalois certificate from a JSON file using the "
            "independent verifier."
        ),
    )
    verify_out = verify_parser.add_mutually_exclusive_group()
    verify_out.add_argument(
        "--json",
        action="store_true",
        help="Print verification result as JSON to stdout.",
    )
    verify_out.add_argument(
        "--verbose",
        action="store_true",
        help="Print all verification checks.",
    )
    verify_parser.add_argument(
        "certificate",
        metavar="CERTIFICATE",
        help="Path to a certificate JSON file.",
    )

    explain_parser = subparsers.add_parser(
        "explain",
        usage=(
            "opengalois explain [--format {markdown,latex,pdf}] [--target FACT_ID] "
            "[--out PATH] [--no-verify] CERTIFICATE"
        ),
        help="Generate a human-readable explanation from a certificate.",
        description=(
            "Generate a non-normative explanation derived from a verified "
            "OpenGalois certificate. By default the certificate is verified before "
            "the explanation is rendered."
        ),
    )
    explain_parser.add_argument(
        "certificate",
        metavar="CERTIFICATE",
        help="Path to a certificate JSON file.",
    )
    explain_parser.add_argument(
        "--format",
        choices=("md", "markdown", "tex", "latex", "pdf"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    explain_parser.add_argument(
        "--target",
        metavar="FACT_ID",
        help="Explain a specific fact id instead of the inferred final targets.",
    )
    explain_parser.add_argument(
        "--out",
        metavar="PATH",
        help="Write the explanation to PATH instead of stdout.",
    )
    explain_parser.add_argument(
        "--no-verify",
        action="store_true",
        help=(
            "Do not run the verifier before rendering. Intended only for structural "
            "debugging of partially built certificates."
        ),
    )

    return parser


def _normalize_cli_coeffs(raw_coeffs: Sequence[str], *, ascending: bool) -> list[str]:
    """Normalize CLI coefficients into descending order for the public API.

    Args:
        raw_coeffs: Raw CLI coefficient tokens.
        ascending: Whether the user supplied coefficients in ascending order.

    Returns:
        Coefficients in descending-degree order.

    Raises:
        ValueError: If the coefficient list is invalid.
    """
    coeffs = [c.strip() for c in raw_coeffs]

    if len(coeffs) < 2 or len(coeffs) > 6:
        raise ValueError("expected 2..6 coefficients for a polynomial of degree 1..5")
    if any(c == "" for c in coeffs):
        raise ValueError("empty coefficient is not allowed")
    if ascending:
        coeffs.reverse()
    return coeffs


def _write_json(path: str, payload: dict[str, Any]) -> None:
    """Write a JSON payload to disk in a stable human-readable form.

    Args:
        path: Output path.
        payload: JSON object to write.
    """
    out_path = Path(path)
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_text(path: str, payload: str) -> None:
    """Write UTF-8 text, appending a trailing newline if absent."""
    out_path = Path(path)
    if not payload.endswith("\n"):
        payload += "\n"
    out_path.write_text(payload, encoding="utf-8")


def _emit_explanation(payload: str, *, out_path: str | None) -> None:
    """Emit an explanation payload either to stdout or to a file."""
    if out_path is not None:
        _write_text(out_path, payload)
        return

    sys.stdout.write(payload)
    if not payload.endswith("\n"):
        sys.stdout.write("\n")


def _load_json_object(path: str) -> dict[str, Any]:
    """Load a JSON object from disk.

    Args:
        path: Input path.

    Returns:
        Parsed JSON object.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the payload is not a valid JSON object.
    """
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"could not read certificate file: {path}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in certificate file: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("certificate JSON top-level value must be an object")

    return payload


def _verify_result_to_json(result: Any) -> dict[str, Any]:
    """Convert a ``VerifiedResult`` into a JSON-serializable dictionary.

    Args:
        result: Verifier result object.

    Returns:
        JSON-serializable dictionary.
    """
    checks_out: list[dict[str, Any]] = []
    for c in result.checks:
        checks_out.append(
            {
                "name": c.name,
                "ok": c.ok,
                "details": c.details,
            }
        )
    return {
        "verified": result.verified,
        "checks": checks_out,
    }


def _print_analyze_summary(
    certificate: dict[str, Any],
    *,
    verbose: bool,
    output_path: str | None,
) -> None:
    """Print a human-readable analyze summary from a certificate.

    Args:
        certificate: Generated certificate.
        verbose: Whether to print extended metadata.
        output_path: Optional JSON output path.
    """
    meta = certificate.get("meta", {})
    inp = certificate.get("input", {})
    proof = certificate.get("proof", {})
    summary = certificate.get("summary", {})

    coeffs_qq = inp.get("coeffs_qq")
    poly_s = "<invalid coeffs_qq>"
    if isinstance(coeffs_qq, list) and all(isinstance(x, str) for x in coeffs_qq):
        poly_s = _poly_to_str(coeffs_qq)

    rows = [
        ("Polynomial:", poly_s),
        ("Degree:", str(inp.get("degree"))),
        ("Status:", str(summary.get("status"))),
        ("Galois group:", str(summary.get("galois_group"))),
        ("Solvable by radicals:", str(summary.get("solvable_by_radicals"))),
    ]
    _print_aligned_rows(rows)

    radical_lines = _extract_input_radical_roots(certificate, style="unicode")
    if radical_lines is not None:
        print("Radical roots:")
        for name, expr_s in radical_lines.aliases:
            _print_wrapped_equation(name, expr_s, separator=":=")
        if radical_lines.aliases:
            print()
        for index, root_s in enumerate(radical_lines.roots, start=1):
            _print_wrapped_equation(f"r{index}", root_s)

    if verbose:
        facts = proof.get("facts")
        goals = proof.get("goals")
        fact_count = len(facts) if isinstance(facts, list) else None
        goal_count = len(goals) if isinstance(goals, list) else None

        verbose_rows = [
            ("Schema version:", str(meta.get("schema_version"))),
            ("Ruleset:", str(meta.get("ruleset_id"))),
            ("Input ordering:", str(inp.get("ordering"))),
            ("Input hash:", str(inp.get("hash"))),
            ("Proof facts:", str(fact_count)),
            ("Goals:", str(goal_count)),
        ]
        _print_aligned_rows(verbose_rows)

    if output_path is not None:
        print(f"Certificate written to: {output_path}")


def _extract_input_radical_roots(
    certificate: Mapping[str, object],
    *,
    style: RenderStyle = "unicode",
) -> CliRadicalLines | None:
    """Extract and render certified radical roots for ``$input``.

    Args:
        certificate: Certificate mapping.
        style: Rendering style.

    Returns:
        Rendered alias and root lines, ``None`` when no
        ``RadicalRoots($input, ...)`` fact is present, or an error block when the
        payload is malformed.
    """
    proof_obj = certificate.get("proof")
    objects_obj = certificate.get("objects")
    if not isinstance(proof_obj, Mapping) or not isinstance(objects_obj, Mapping):
        return None

    facts_obj = proof_obj.get("facts")
    if not isinstance(facts_obj, list):
        return None

    objects: dict[str, Mapping[str, object]] = {}
    for key, value in objects_obj.items():
        if isinstance(key, str) and isinstance(value, Mapping):
            objects[key] = value

    list_ref: str | None = None
    matched_fact: Mapping[str, object] | None = None
    for fact_obj in reversed(facts_obj):
        if not isinstance(fact_obj, Mapping):
            continue
        claim_obj = fact_obj.get("claim")
        if not isinstance(claim_obj, Mapping):
            continue
        if claim_obj.get("pred") != "RadicalRoots":
            continue
        args_obj = claim_obj.get("args")
        if not isinstance(args_obj, list) or len(args_obj) != 2:
            continue
        input_ref = _extract_ref_arg(args_obj[0])
        roots_ref = _extract_ref_arg(args_obj[1])
        if input_ref == "$input" and roots_ref is not None:
            list_ref = roots_ref
            matched_fact = fact_obj
            break

    if list_ref is None or matched_fact is None:
        return None

    list_payload = objects.get(list_ref)
    if list_payload is None:
        return CliRadicalLines(aliases=[], roots=["<invalid RadicalRoots payload>"])

    try:
        exprs = decode_expr_list_payloads(list_payload, objects)
    except (KeyError, TypeError, ValueError):
        return CliRadicalLines(aliases=[], roots=["<invalid RadicalRoots payload>"])

    return format_cli_radical_lines(certificate, matched_fact, exprs, style=style)


def _extract_ref_arg(arg: object) -> str | None:
    """Extract a ``{"ref": ...}`` argument from a claim.

    Args:
        arg: Raw claim argument.

    Returns:
        Referenced object id, or ``None`` when the shape is invalid.
    """
    if not isinstance(arg, Mapping):
        return None
    ref = arg.get("ref")
    if not isinstance(ref, str) or not ref:
        return None
    return ref


def _print_verify_summary(result: Any, *, path: str, verbose: bool) -> None:
    """Print a human-readable verification summary.

    Args:
        result: Verifier result.
        path: Certificate path.
        verbose: Whether to print all checks.
    """
    print(f"Certificate: {path}")
    print(f"Verification: {'VERIFIED' if result.verified else 'REJECTED'}")

    failed = [c for c in result.checks if not c.ok]

    if result.verified:
        print(f"Checks: {len(result.checks)} passed")
        if verbose:
            for c in result.checks:
                details = f" — {c.details}" if c.details else ""
                print(f"[OK] {c.name}{details}")
        return

    print(f"Failed checks: {len(failed)} / {len(result.checks)}")

    if verbose:
        for c in result.checks:
            prefix = "OK" if c.ok else "FAIL"
            details = f" — {c.details}" if c.details else ""
            print(f"[{prefix}] {c.name}{details}")
    else:
        for c in failed[:3]:
            details = f" — {c.details}" if c.details else ""
            print(f"[FAIL] {c.name}{details}")


def _print_aligned_rows(rows: Sequence[tuple[str, object]]) -> None:
    """Print left-aligned label/value rows."""
    if not rows:
        return
    label_width = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"{label:<{label_width}}  {value}")


def _print_wrapped_value(
    prefix: str,
    value: str,
    *,
    width: int | None = None,
) -> None:
    """Print a wrapped value with hanging indentation."""
    indent = " " * len(prefix)
    effective_width = (
        width
        if width is not None
        else max(
            shutil.get_terminal_size(fallback=(100, 24)).columns,
            len(prefix) + 20,
        )
    )
    wrapped = textwrap.fill(
        value,
        width=effective_width,
        initial_indent=prefix,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    print(wrapped)


def _print_wrapped_equation(
    name: str,
    expr_s: str,
    *,
    separator: str = "=",
) -> None:
    """Print a wrapped displayed expression with hanging indentation."""
    _print_wrapped_value(f"  {name} {separator} ", expr_s)


def _cmd_analyze(args: argparse.Namespace) -> int:
    """Run the ``analyze`` subcommand.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Process exit code.
    """
    try:
        coeffs = _normalize_cli_coeffs(args.coeffs, ascending=bool(args.ascending))
        result = analyze(coeffs, explain=False)
        certificate = result.certificate

        if args.output:
            _write_json(args.output, certificate)

        if args.json:
            json.dump(certificate, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
        else:
            _print_analyze_summary(
                certificate,
                verbose=bool(args.verbose),
                output_path=args.output,
            )
        return 0

    except ZeroDivisionError:
        print(
            "error: invalid rational coefficient with zero denominator",
            file=sys.stderr,
        )
        return 1
    except (TypeError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_verify(args: argparse.Namespace) -> int:
    """Run the ``verify`` subcommand.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Process exit code.
    """
    try:
        certificate = _load_json_object(args.certificate)
        result = verify(certificate)

        if args.json:
            json.dump(
                _verify_result_to_json(result),
                sys.stdout,
                indent=2,
                ensure_ascii=False,
            )
            sys.stdout.write("\n")
        else:
            _print_verify_summary(
                result,
                path=args.certificate,
                verbose=bool(args.verbose),
            )

        return 0 if result.verified else 1

    except (TypeError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_explain(args: argparse.Namespace) -> int:
    """Run the ``explain`` subcommand.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Process exit code.
    """
    try:
        certificate = _load_json_object(args.certificate)
        if args.format == "pdf":
            if args.out is None:
                raise ValueError("PDF output requires --out PATH")
            pdf_path = explain_certificate_to_pdf(
                certificate,
                args.out,
                target=args.target,
                verify_first=not bool(args.no_verify),
            )
            print(f"PDF written to: {pdf_path}")
            return 0

        rendered = explain_certificate(
            certificate,
            target=args.target,
            format=args.format,
            verify_first=not bool(args.no_verify),
        )
        _emit_explanation(rendered, out_path=args.out)
        return 0

    except (ExplainError, TypeError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the OpenGalois command-line interface.

    Args:
        argv: Optional argument vector.

    Returns:
        Process exit code.
    """
    parser = _build_parser()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]

    args, extras = parser.parse_known_args(raw_argv)

    if args.command == "analyze":
        bad_option_like = [
            tok
            for tok in extras
            if tok.startswith("-") and not _looks_like_coeff_token(tok)
        ]
        if bad_option_like:
            parser.error(f"unrecognized arguments: {' '.join(bad_option_like)}")

        args.coeffs = extras
        return _cmd_analyze(args)

    if args.command == "verify":
        if extras:
            parser.error(f"unrecognized arguments: {' '.join(extras)}")
        return _cmd_verify(args)

    if args.command == "explain":
        if extras:
            parser.error(f"unrecognized arguments: {' '.join(extras)}")
        return _cmd_explain(args)

    raise AssertionError(f"Unhandled command: {args.command!r}")
