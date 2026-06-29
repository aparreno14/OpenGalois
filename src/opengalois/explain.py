from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any, Literal, overload

from .codec.rationals import _frac_to_str, _parse_fraction

ExplainFormat = Literal["md", "tex", "json"]

_INPUT_REF = "$input"
_POLY_KIND = "poly_qq_desc"


def _tex_escape(s: str) -> str:
    return (
        s.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("$", "\\$")
    )


def _frac_to_tex(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    # keep sign in numerator
    return rf"\frac{{{f.numerator}}}{{{f.denominator}}}"


def _poly_to_str(coeffs_qq: list[str], var: str = "x") -> str:
    """Human-friendly polynomial string from descending QQ coeffs."""
    coeffs = [_parse_fraction(c) for c in coeffs_qq]
    n = len(coeffs) - 1

    def term(c: Fraction, k: int) -> tuple[str, str]:
        if c == 0:
            return "+", ""
        # power k corresponds to x^(n-k)
        p = n - k
        abs_c = abs(c)
        sign = "-" if c < 0 else "+"

        if p == 0:
            body = _frac_to_str(abs_c)
        else:
            if abs_c == 1:
                coeff_part = ""
            else:
                coeff_part = _frac_to_str(abs_c) + "*"
            if p == 1:
                body = f"{coeff_part}{var}"
            else:
                body = f"{coeff_part}{var}^{p}"
        return sign, body

    parts: list[str] = []
    for k, c in enumerate(coeffs):
        if c == 0:
            continue
        sgn, body = term(c, k)
        if not parts:
            # first term keeps sign only if negative
            parts.append(body if sgn == "+" else f"-{body}")
        else:
            parts.append(f" {sgn} {body}")
    return "".join(parts) if parts else "0"


def _poly_to_tex(coeffs_qq: list[str], var: str = "x") -> str:
    coeffs = [_parse_fraction(c) for c in coeffs_qq]
    n = len(coeffs) - 1

    def term(c: Fraction, k: int) -> tuple[str, str]:
        if c == 0:
            return "+", ""
        p = n - k
        abs_c = abs(c)
        sign = "-" if c < 0 else "+"

        if p == 0:
            body = _frac_to_tex(abs_c)
        else:
            if abs_c == 1:
                coeff_part = ""
            else:
                coeff_part = _frac_to_tex(abs_c)
            if p == 1:
                body = f"{coeff_part}{var}"
            else:
                body = f"{coeff_part}{var}^{{{p}}}"
        return sign, body

    parts: list[str] = []
    for k, c in enumerate(coeffs):
        if c == 0:
            continue
        sgn, body = term(c, k)
        if not parts:
            parts.append(body if sgn == "+" else f"-{body}")
        else:
            parts.append(f" {sgn} {body}")
    return "".join(parts) if parts else "0"


def _summarize_object(obj_id: str, obj: Mapping[str, Any], *,
                      fmt: ExplainFormat) -> str:
    kind = obj.get("kind")
    if fmt == "tex":
        prefix = rf"\texttt{{{_tex_escape(obj_id)}}}"
    else:
        prefix = f"`{obj_id}`"

    if kind == _POLY_KIND:
        coeffs_qq = obj.get("coeffs_qq")
        if isinstance(coeffs_qq, list) and \
           all(isinstance(s, str) for s in coeffs_qq):
            if fmt == "tex":
                poly = _poly_to_tex(coeffs_qq)
                return f"{prefix}: \\texttt{{poly\\_qq\\_desc}};$f(x) = {poly}$"
            poly = _poly_to_str(coeffs_qq)
            return f"{prefix}: poly_qq_desc; f(x) = {poly}"
        return f"{prefix}: poly_qq_desc"
    # generic
    if fmt == "tex":
        return rf"{prefix}: \texttt{{{_tex_escape(str(kind))}}}"
    return f"{prefix}: {kind}"


def _node_lines(
    node: Mapping[str, Any],
    *,
    objects: Mapping[str, Any],
    indent: int,
    fmt: ExplainFormat,
) -> list[str]:
    """Render proof nodes recursively (non-normative)."""
    sp = "  " * indent
    kind = node.get("kind", "<missing-kind>")
    statement = node.get("statement")
    inputs = node.get("inputs", [])
    outputs = node.get("outputs", [])
    witness = node.get("witness")
    children = node.get("children", [])

    def ref_list(xs: Any) -> list[str]:
        if not isinstance(xs, list):
            return []
        out: list[str] = []
        for x in xs:
            if isinstance(x, Mapping) and isinstance(x.get("ref"), str):
                out.append(x["ref"])
        return out

    in_refs = ref_list(inputs)
    out_refs = ref_list(outputs)

    lines: list[str] = []
    if fmt == "tex":
        lines.append(rf"{sp}\item \textbf{{{_tex_escape(str(kind))}}}")
        if isinstance(statement, str) and statement.strip():
            lines.append(rf"{sp}  \\emph{{{_tex_escape(statement.strip())}}}")
        if in_refs:
            lines.append(rf"{sp}  \\\\ Inputs: " + 
                         ", ".join(rf"\texttt{{{_tex_escape(r)}}}" for r in in_refs))
        if out_refs:
            lines.append(rf"{sp}  \\\\ Outputs: " + 
                         ", ".join(rf"\texttt{{{_tex_escape(r)}}}" for r in out_refs))
        if isinstance(witness, Mapping) and witness:
            # compact witness keys
            keys = ", ".join(_tex_escape(k) for k in sorted(witness.keys()))
            lines.append(rf"{sp}  \\\\ Witness keys: \texttt{{{keys}}}")
    else:
        lines.append(f"{sp}- **{kind}**")
        if isinstance(statement, str) and statement.strip():
            lines.append(f"{sp}  - _{statement.strip()}_")
        if in_refs:
            lines.append(f"{sp}  - inputs: {', '.join(f'`{r}`' for r in in_refs)}")
        if out_refs:
            lines.append(f"{sp}  - outputs: {', '.join(f'`{r}`' for r in out_refs)}")
        if isinstance(witness, Mapping) and witness:
            keys = ", ".join(sorted(witness.keys()))
            lines.append(f"{sp}  - witness keys: {keys}")

    # Recurse
    if isinstance(children, list) and children:
        if fmt == "tex":
            lines.append(rf"{sp}  \begin{{itemize}}")
        for ch in children:
            if isinstance(ch, Mapping):
                lines.extend(_node_lines(ch, objects=objects, indent=indent + 1, fmt=fmt))
        if fmt == "tex":
            lines.append(rf"{sp}  \end{{itemize}}")
    return lines


@overload
def render_explanation_from_certificate(
    certificate: Mapping[str, Any],
    fmt: Literal["json"],
) -> dict[str, Any]: ...


@overload
def render_explanation_from_certificate(
    certificate: Mapping[str, Any],
    fmt: Literal["md", "tex"] = "md",
) -> str: ...


def render_explanation_from_certificate(
    certificate: Mapping[str, Any],
    fmt: ExplainFormat = "md",
) -> str | dict[str, Any]:
    """Render markdown/TeX/JSON explanation content from a v2 proof-first certificate.

    Normative note:
    - This renderer is for UX/pedagogy and MUST NOT be used for verification.
    - Verifiers should ignore `summary` and rely on proof/objects + recomputation.
    """
    meta = certificate.get("meta", {})
    inp = certificate.get("input", {})
    proof = certificate.get("proof", {})
    objects = certificate.get("objects", {})
    summary = certificate.get("summary", {})

    # Build a structured JSON explanation payload (still non-normative)
    payload: dict[str, Any] = {
        "schema_version": meta.get("schema_version"),
        "backend": meta.get("backend"),
        "input": {
            "domain": inp.get("domain"),
            "variable": inp.get("variable"),
            "ordering": inp.get("ordering"),
            "degree": inp.get("degree"),
            "coeffs_qq": inp.get("coeffs_qq"),
            "hash": inp.get("hash"),
        },
        "summary": summary,
        "proof": {
            "version": proof.get("version"),
            "root_kind": (proof.get("root") or {}).get("kind") 
            if isinstance(proof.get("root"), Mapping) else None,
        },
        "note": "Explanation is non-normative: for correctness,"
        "verify the certificate with the independent verifier.",
    }

    if fmt == "json":
        return payload

    var = "x"
    coeffs_qq = inp.get("coeffs_qq")
    if isinstance(coeffs_qq, list) and all(isinstance(s, str) for s in coeffs_qq):
        poly_s = _poly_to_str(coeffs_qq, var=var)
        poly_t = _poly_to_tex(coeffs_qq, var=var)
    else:
        poly_s = "<invalid coeffs_qq>"
        poly_t = r"\textit{invalid coeffs\_qq}"

    # Proof rendering
    root = proof.get("root") if isinstance(proof, Mapping) else None
    obj_map = objects if isinstance(objects, Mapping) else {}
    if isinstance(root, Mapping):
        proof_lines_md = _node_lines(root, objects=obj_map, indent=0, fmt="md")
        proof_lines_tex = _node_lines(root, objects=obj_map, indent=0, fmt="tex")
    else:
        proof_lines_md = ["- <missing proof.root>"]
        proof_lines_tex = [r"\item \textit{missing proof.root}"]

    # Objects summary
    object_lines_md: list[str] = []
    object_lines_tex: list[str] = []
    if isinstance(obj_map, Mapping) and obj_map:
        for obj_id in sorted(obj_map.keys()):
            obj = obj_map[obj_id]
            if isinstance(obj, Mapping):
                object_lines_md.append("- " + _summarize_object(obj_id, obj, fmt="md"))
                object_lines_tex.append(r"\item " + _summarize_object(obj_id, obj, fmt="tex"))
    else:
        object_lines_md.append("- (none)")
        object_lines_tex.append(r"\item (none)")

    # Emit markdown
    if fmt == "md":
        lines = [
            "# OpenGalois Explanation (v2 proof-first)",
            "",
            "This explanation is **non-normative**. Correctness is established by"
            " the independent verifier replaying `proof`.",
            "",
            "## Metadata",
            f"- schema_version: {payload['schema_version']}",
            f"- backend: {payload['backend']}",
            "",
            "## Input",
            f"- f(x) = {poly_s}",
            f"- input.hash: `{payload['input']['hash']}`",
            "",
            "## Summary (UX-only)",
            f"- status: `{summary.get('status')}`",
            f"- galois_group: `{summary.get('galois_group')}`",
            f"- solvable_by_radicals: `{summary.get('solvable_by_radicals')}`",
            "",
            "## Proof",
            *proof_lines_md,
            "",
            "## Objects (DAG store)",
            *object_lines_md,
        ]
        return "\n".join(lines)

    # Emit TeX-ish output
    escaped_hash = _tex_escape(str(payload["input"]["hash"]))
    lines = [
        r"\section*{OpenGalois Explanation (v2 proof-first)}",
        r"\textbf{Non-normative.} Correctness is established by the "
        r"independent verifier replaying \texttt{proof}.",
        "",
        r"\subsection*{Metadata}",
        rf"Schema version: \texttt{{{_tex_escape(str(payload['schema_version']))}}}\\",
        rf"Backend: \texttt{{{_tex_escape(str(payload['backend']))}}}\\",
        "",
        r"\subsection*{Input}",
        rf"$f(x) = {poly_t}$\\",
        rf"Input hash: \texttt{{{escaped_hash}}}\\",
        "",
        r"\subsection*{Summary (UX-only)}",
        rf"Status: \texttt{{{_tex_escape(str(summary.get('status'))) }}}\\",
        rf"Galois group: \texttt{{{_tex_escape(str(summary.get('galois_group'))) }}}\\",
        rf"Solvable by radicals: "
        rf"\texttt{{{_tex_escape(str(summary.get('solvable_by_radicals'))) }}}\\",
        "",
        r"\subsection*{Proof}",
        r"\begin{itemize}",
        *proof_lines_tex,
        r"\end{itemize}",
        "",
        r"\subsection*{Objects (DAG store)}",
        r"\begin{itemize}",
        *object_lines_tex,
        r"\end{itemize}",
    ]
    return "\n".join(lines)
