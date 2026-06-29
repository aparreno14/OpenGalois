from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, overload

ExplainFormat = Literal["md", "tex", "json"]

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
    """Render markdown/TeX/JSON explanation content from a certificate payload."""
    meta = certificate.get("meta", {})
    inp = certificate.get("input", {})
    res = certificate.get("result", {})

    payload: dict[str, Any] = {
        "schema_version": meta.get("schema_version"),
        "backend": meta.get("backend"),
        "input": {
            "domain": inp.get("domain"),
            "variable": inp.get("variable"),
            "ordering": inp.get("ordering"),
            "coeffs_qq": inp.get("coeffs_qq"),
            "hash": inp.get("hash"),
        },
        "result": res,
        "trace": {
            "decision_path": [],
            "reject_log": [],
            "note": "Explanation is provisional (skeleton).",
        },
    }

    if fmt == "json":
        return payload

    lines = [
        "# OpenGalois Explanation (provisional)",
        "",
        f"- schema_version: {payload['schema_version']}",
        f"- backend: {payload['backend']}",
        f"- input.hash: {payload['input']['hash']}",
        f"- result.status: {payload['result'].get('status')}",
        f"- result.galois_group: {payload['result'].get('galois_group')}",
        "",
        "Note: mathematical decision nodes are not implemented yet; this is a contract skeleton.",
    ]

    if fmt == "tex":
        escaped = [_tex_escape(line) for line in lines]
        # Minimal TeX-ish output (placeholder)
        body = "\n".join(escaped)
        return "\\section*{OpenGalois Explanation (provisional)}\n" + body + "\n"

    return "\n".join(lines)
