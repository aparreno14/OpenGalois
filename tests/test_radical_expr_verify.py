from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

from opengalois.rulesets import get_ruleset
from opengalois.verify import verify_certificate

ROOT = Path(__file__).resolve().parents[1]


def _load_json(relpath: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ROOT / relpath).read_text(encoding="utf-8")))


def _check_details_contain(result, needle: str) -> None:
    joined = "\n".join(f"{c.name}: {c.details}" for c in result.checks if not c.ok)
    assert needle in joined, joined


def _base_cert() -> dict[str, Any]:
    return copy.deepcopy(
        _load_json("fixtures/v3/le5-core@1/ok/solvable_by_radicals.QQ.from_galois_group@1_001.json")
    )


def test_ruleset_catalog_exposes_radical_roots_signature() -> None:
    rs = get_ruleset("le5-core@1")
    spec = rs.predicates["RadicalRoots"]
    assert spec.arg_kinds == ("PolyQQ", "RadicalExprList")


def test_verify_accepts_valid_unused_radical_objects() -> None:
    cert = _base_cert()
    cert["objects"]["rexpr.literal"] = {
        "kind": "RadicalExpr",
        "expr": {"kind": "qq", "value_qq": "1/2"},
    }
    cert["objects"]["rexpr.ref"] = {
        "kind": "RadicalExpr",
        "expr": {"kind": "qq", "ref": "rat.dummit.unit.1"},
    }
    cert["objects"]["rexpr.composite"] = {
        "kind": "RadicalExpr",
        "expr": {
            "kind": "add",
            "left": {"kind": "root", "n": 2, "arg": {"kind": "qq", "value_qq": "5"}},
            "right": {"kind": "mul", "left": {"kind": "zeta", "n": 5, "k": 1}, "right": {"kind": "qq", "value_qq": "3"}},
        },
    }
    cert["objects"]["rlist.ok"] = {
        "kind": "RadicalExprList",
        "items": ["rexpr.literal", "rexpr.ref", "rexpr.composite"],
    }

    result = verify_certificate(cert)
    assert result.verified


def test_verify_rejects_invalid_radical_expr_payload() -> None:
    cert = _base_cert()
    cert["objects"]["rexpr.bad"] = {
        "kind": "RadicalExpr",
        "expr": {"kind": "qq", "value_qq": "1/2", "ref": "rat.dummit.unit.1"},
    }

    result = verify_certificate(cert)
    assert not result.verified
    _check_details_contain(result, "qq node must contain exactly one of 'value_qq' or 'ref'")


def test_verify_rejects_radical_expr_ref_to_non_ratqq() -> None:
    cert = _base_cert()
    cert["objects"]["rexpr.bad"] = {
        "kind": "RadicalExpr",
        "expr": {"kind": "qq", "ref": "group.F20"},
    }

    result = verify_certificate(cert)
    assert not result.verified
    _check_details_contain(result, "qq.ref must point to a RatQQ object")


def test_verify_rejects_invalid_radical_expr_list_payload() -> None:
    cert = _base_cert()
    cert["objects"]["rexpr.ok"] = {
        "kind": "RadicalExpr",
        "expr": {"kind": "qq", "value_qq": "1"},
    }
    cert["objects"]["rlist.bad"] = {
        "kind": "RadicalExprList",
        "items": ["group.F20"],
    }

    result = verify_certificate(cert)
    assert not result.verified
    _check_details_contain(result, "Expected RadicalExpr item, got 'GroupId'")
