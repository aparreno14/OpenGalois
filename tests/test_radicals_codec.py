"""Unit tests for ``opengalois.radicals.codec``."""

from __future__ import annotations

from opengalois.radicals import (
    add,
    build_expr_object_bundle,
    decode_expr_list_payloads,
    expr_from_object_payload,
    expr_to_object_payload,
    qq,
    root,
)


def test_expr_object_roundtrip() -> None:
    """A single expression object should round-trip through the codec."""
    expr = add(qq("-1/2"), root(2, qq("-3/4")))
    payload = expr_to_object_payload(expr)
    assert expr_from_object_payload(payload) == expr



def test_expr_list_bundle_and_decode() -> None:
    """Generated list objects should decode back to the input expressions."""
    exprs = [
        add(qq(1), qq(2)),
        root(3, qq("5/7")),
    ]
    objects, list_id = build_expr_object_bundle(
        exprs,
        expr_id_prefix="rexpr.cardano",
        list_id="rlist.cardano",
    )
    decoded = decode_expr_list_payloads(objects[list_id], objects)
    assert decoded == exprs



def test_rat_ref_validation_hook() -> None:
    """The optional RatQQ resolver should validate ``qq.ref`` nodes."""
    payload = {
        "kind": "RadicalExpr",
        "expr": {"kind": "root", "n": 2, "arg": {"kind": "qq", "ref": "rat:delta"}},
    }
    expr = expr_from_object_payload(payload, rat_ref_resolver=lambda ref: ref == "rat:delta")
    assert expr["arg"] == {"kind": "qq", "ref": "rat:delta"}
