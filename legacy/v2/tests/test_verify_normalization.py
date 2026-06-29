from __future__ import annotations

import copy
from collections.abc import Iterator
from fractions import Fraction
from typing import Any

from opengalois import analyze, verify
from opengalois.certificate import compute_input_hash


def _recompute_input_hash(cert: dict[str, Any]) -> None:
    """Recompute input.hash for input_v1 scope (used to isolate non-hash checks)."""
    inp = cert["input"]
    scope = {
        "domain": inp["domain"],
        "variable": inp["variable"],
        "ordering": inp["ordering"],
        "degree": inp["degree"],
        "coeffs_qq": inp["coeffs_qq"],
    }
    inp["hash"] = compute_input_hash(scope)


def _iter_proof_nodes(node: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Depth-first traversal of proof nodes.

    Args:
        node: A proof node dict.

    Yields:
        All proof nodes in the subtree rooted at `node`, including `node`.
    """
    yield node
    children = node.get("children", [])
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                yield from _iter_proof_nodes(child)


def _get_norm_node(cert: dict[str, Any]) -> dict[str, Any]:
    """Return the unique normalization node in the certificate proof.

    This avoids relying on positional assumptions such as children[0].

    Args:
        cert: Certificate dict.

    Returns:
        The proof node with kind == "normalize.depressed_monic_QQ".

    Raises:
        AssertionError: If missing or if multiple normalization nodes exist.
    """
    root = cert["proof"]["root"]
    assert isinstance(root, dict)

    matches = [n for n in _iter_proof_nodes(root) if n.get("kind") == "normalize.depressed_monic_QQ"]
    assert matches, "Missing normalize.depressed_monic_QQ node in proof."
    assert len(matches) == 1, f"Expected exactly 1 normalization node, found {len(matches)}."
    return matches[0]


def test_verify_rejects_noncanonical_input_rational_even_if_hash_matches():
    """Canonicalization guard: reject non-canonical '2/4' even if attacker recomputes hash."""
    cert = analyze([Fraction(1, 2), 0, 0, 0, -1, -1], explain=False).certificate
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    assert tampered["input"]["coeffs_qq"][0] == "1/2"
    tampered["input"]["coeffs_qq"][0] = "2/4"

    _recompute_input_hash(tampered)

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "input.coeffs_qq.canonical" and c.ok is False for c in v.checks)


def test_verify_rejects_noncanonical_normalization_rational_strings():
    """Canonicalization applies to lemma witnesses too."""
    cert = analyze([1, 5, 0, 0, 0, 0], explain=False).certificate
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    node = _get_norm_node(tampered)
    node["witness"]["tschirnhaus_shift"] = "2/2"  # non-canonical

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name == "lemma.normalize.witness.canonical" and c.ok is False for c in v.checks)


def test_verify_detects_normalization_output_object_mismatch():
    """Soundness: output polynomial object must match the computed depressed-monic transform."""
    cert = analyze([1, 5, 0, 0, 0, 0], explain=False).certificate
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    node = _get_norm_node(tampered)
    out_ref = node["outputs"][0]["ref"]
    poly = tampered["objects"][out_ref]["coeffs_qq"]
    assert isinstance(poly, list) and poly
    poly[-1] = "1" if poly[-1] != "1" else "2"

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name in {"lemma.normalize.soundness", "lemma.normalize.invariants"} and c.ok is False for c in v.checks)


def test_verify_rejects_nonmonic_normalization_output():
    """Defense in depth: output must be monic and depressed."""
    cert = analyze([1, 5, 0, 0, 0, 0], explain=False).certificate
    v_ok = verify(cert)
    assert v_ok.verified is True

    tampered = copy.deepcopy(cert)
    node = _get_norm_node(tampered)
    out_ref = node["outputs"][0]["ref"]
    tampered["objects"][out_ref]["coeffs_qq"][0] = "2"  # break monic

    v = verify(tampered)
    assert v.verified is False
    assert any(c.name in {"lemma.normalize.soundness", "lemma.normalize.invariants", "schema.conformance"} and c.ok is False for c in v.checks)


def test_analyze_canonicalizes_equivalent_inputs():
    """Analyze canonicalizes mathematically equivalent inputs to the same canonical coeffs + hash."""
    cert = analyze([Fraction(1, 2), 0, 0, 0, -1, -1], explain=False).certificate
    cert2 = analyze([Fraction(2, 4), 0, 0, 0, -1, -1], explain=False).certificate

    assert cert["input"]["coeffs_qq"] == cert2["input"]["coeffs_qq"] == ["1/2", "0", "0", "0", "-1", "-1"]
    assert cert["input"]["hash"] == cert2["input"]["hash"]
