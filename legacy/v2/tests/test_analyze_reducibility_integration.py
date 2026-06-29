from __future__ import annotations

from typing import Any

from opengalois import analyze, verify


def _collect_kinds(cert: dict[str, Any]) -> set[str]:
    """Collect all proof node kinds in the derivation tree."""
    root = cert["proof"]["root"]
    out: set[str] = set()

    def rec(n: dict[str, Any]) -> None:
        k = n.get("kind")
        if isinstance(k, str):
            out.add(k)
        for ch in n.get("children", []) or []:
            if isinstance(ch, dict):
                rec(ch)

    rec(root)
    return out


def test_analyze_emits_irreducible_lemma_for_irreducible_input():
    """analyze() should emit irreducible.QQ for a known irreducible quintic."""
    cert = analyze([1, 0, 0, 0, -1, -1], explain=False).certificate
    kinds = _collect_kinds(cert)
    assert "irreducible.QQ" in kinds, "Expected analyze() to emit irreducible.QQ in proof."
    assert verify(cert).verified is True


def test_analyze_emits_factorization_lemma_for_reducible_input():
    """analyze() should emit factorization.QQ.monic for a known reducible polynomial."""
    cert = analyze([1, 0, -1], explain=False).certificate  # x^2 - 1
    kinds = _collect_kinds(cert)
    assert "factorization.QQ.monic" in kinds, "Expected analyze() to emit factorization.QQ.monic in proof."
    assert verify(cert).verified is True


def test_analyze_emits_factorization_lemma_for_repeated_factor_input():
    """analyze() should emit factorization.QQ.monic for a polynomial with a repeated factor."""
    # (x - 1)^2 = x^2 - 2x + 1
    cert = analyze([1, -2, 1], explain=False).certificate
    kinds = _collect_kinds(cert)
    assert "factorization.QQ.monic" in kinds, (
        "Expected analyze() to emit factorization.QQ.monic in proof for polynomial with repeated factor."
    )
    assert verify(cert).verified is True
    
def test_analyze_trivial_linear_degree_1():
    """Ensure that a degree 1 polynomial emits the 'irreducible.QQ' lemma.

    It verifies that the lemma uses the 'trivial_linear' method and that
    the verifier accepts it natively without executing the glassbox.
    """
    coeffs_deg1 = [1, -1]  # Represents 1*x + (-1)
    
    # 1. Generate the certificate
    cert = analyze(coeffs_deg1, explain=False).certificate
    
    # 2. Audit the internal structure of the generated JSON by traversing the proof tree
    irreducible_nodes: list[dict[str, Any]] = []
    
    def _find_irreducible(node: dict[str, Any]) -> None:
        if node.get("kind") == "irreducible.QQ":
            irreducible_nodes.append(node)
        for ch in node.get("children", []) or []:
            if isinstance(ch, dict):
                _find_irreducible(ch)
                
    _find_irreducible(cert["proof"]["root"])
    
    assert len(irreducible_nodes) == 1, "Must emit exactly one irreducible.QQ lemma."
    
    witness = irreducible_nodes[0].get("witness", {})
    assert witness.get("method") == "trivial_linear", "Failed to assign trivial_linear method for degree 1."
    
    # 3. Validate cryptographically/logically with the strict verifier
    assert verify(cert).verified is True
