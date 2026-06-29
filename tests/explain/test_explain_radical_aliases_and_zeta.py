from __future__ import annotations

from typing import Any

from opengalois.explain import explain_certificate


def _ref(name: str) -> dict[str, str]:
    return {"ref": name}


def _mul(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "mul", "left": left, "right": right}


def _pow(base: dict[str, Any], exp: int) -> dict[str, Any]:
    return {"kind": "pow_int", "base": base, "exp": exp}


def _certificate() -> dict[str, Any]:
    sqrt_a = {
        "kind": "root",
        "n": 2,
        "arg": {"kind": "qq", "value_qq": "1/5"},
    }
    sqrt_b = {
        "kind": "root",
        "n": 2,
        "arg": {
            "kind": "add",
            "left": {"kind": "qq", "value_qq": "4/5"},
            "right": _mul({"kind": "qq", "value_qq": "4/5"}, sqrt_a),
        },
    }
    u = {
        "kind": "root",
        "n": 5,
        "arg": {
            "kind": "add",
            "left": {"kind": "qq", "value_qq": "-1"},
            "right": sqrt_b,
        },
    }
    zeta = {"kind": "zeta", "n": 5, "k": 1}
    roots = [
        u,
        _mul(zeta, u),
        _mul({"kind": "zeta", "n": 5, "k": 2}, _pow(u, 2)),
        _mul({"kind": "zeta", "n": 5, "k": 3}, _pow(u, 3)),
        _mul({"kind": "zeta", "n": 5, "k": 4}, _pow(u, 4)),
    ]
    objects: dict[str, Any] = {
        "roots": {"kind": "RadicalExprList", "items": []},
    }
    for i, expr in enumerate(roots, start=1):
        ref = f"r.{i}"
        objects[ref] = {"kind": "RadicalExpr", "expr": expr}
        objects["roots"]["items"].append(ref)

    return {
        "meta": {"ruleset_id": "le5-core@1"},
        "input": {"coeffs_qq": ["1", "0", "0", "0", "-5", "12"]},
        "objects": objects,
        "proof": {
            "facts": [
                {
                    "id": "F1",
                    "claim": {"pred": "RadicalRoots", "args": [_ref("$input"), _ref("roots")]},
                    "rule": "radical_roots.QQ.deg5.mcclintock.depressed_monic@1",
                }
            ],
            "goals": ["F1"],
        },
    }


def test_zeta_explanation_and_degree_five_aliases_are_rendered() -> None:
    rendered = explain_certificate(_certificate(), format="latex", strict=False)

    assert "denotes a primitive" in rendered
    assert r"\zeta_{5}" in rendered
    assert "To keep the expressions readable, set" in rendered
    assert "a &:= " in rendered
    assert "b &:= " in rendered
    assert "u &:= " in rendered
    assert r"r_{2} &:= \zeta_{5}u" in rendered
    long_root = (
        r"\sqrt[5]{-1 + \sqrt{\frac{4}{5} "
        r"+ \frac{4}{5}\sqrt{\frac{1}{5}}}}"
    )
    after_aliases = rendered.split("With this notation", maxsplit=1)[-1]
    assert long_root not in after_aliases
