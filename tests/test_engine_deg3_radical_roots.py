from __future__ import annotations

from typing import Any

from opengalois import analyze, verify

Certificate = dict[str, Any]
Fact = dict[str, Any]


def _proof_facts(cert: Certificate) -> list[Fact]:
    proof = cert.get("proof", {})
    assert isinstance(proof, dict)
    facts = proof.get("facts", [])
    assert isinstance(facts, list)
    return [fact for fact in facts if isinstance(fact, dict)]


def _get_ref(arg: Any) -> str | None:
    if isinstance(arg, dict):
        ref = arg.get("ref")
        if isinstance(ref, str):
            return ref
    return None


def _claim_ref0(fact: Fact) -> str | None:
    claim = fact.get("claim", {})
    if not isinstance(claim, dict):
        return None
    args = claim.get("args", [])
    if not isinstance(args, list) or not args:
        return None
    return _get_ref(args[0])


def _claim_ref1(fact: Fact) -> str | None:
    claim = fact.get("claim", {})
    if not isinstance(claim, dict):
        return None
    args = claim.get("args", [])
    if not isinstance(args, list) or len(args) < 2:
        return None
    return _get_ref(args[1])


def _facts_by_pred(cert: Certificate, pred: str) -> list[Fact]:
    out: list[Fact] = []
    for fact in _proof_facts(cert):
        claim = fact.get("claim", {})
        if isinstance(claim, dict) and claim.get("pred") == pred:
            out.append(fact)
    return out


def _normalization_facts(cert: Certificate) -> list[Fact]:
    return [
        fact
        for fact in _facts_by_pred(cert, "DepressedMonicEq")
        if fact.get("rule") == "normalize.depressed_monic_QQ@1"
    ]


def _radical_facts_for(cert: Certificate, poly_ref: str) -> list[Fact]:
    return [
        fact
        for fact in _facts_by_pred(cert, "RadicalRoots")
        if _claim_ref0(fact) == poly_ref
    ]


def test_irreducible_deg3_radicals_reuse_identity_normalization() -> None:
    """A monic depressed cubic should use Cardano directly, without lift."""
    result = analyze([1, 0, -3, 1], explain=False)
    cert: Certificate = result.certificate

    verified = verify(cert)
    assert verified.verified

    normalizations = _normalization_facts(cert)
    assert any(
        _claim_ref0(fact) == "$input" and _claim_ref1(fact) == "$input"
        for fact in normalizations
    )

    input_radicals = _radical_facts_for(cert, "$input")
    assert any(
        fact.get("rule") == "radical_roots.QQ.deg3.cardano.depressed_monic@2"
        for fact in input_radicals
    )
    assert not any(
        fact.get("rule") == "radical_roots.QQ.lift.depressed_monic@1"
        for fact in input_radicals
    )

    objects = cert.get("objects", {})
    assert isinstance(objects, dict)
    assert not any(str(ref).startswith("poly.depressed_monic.") for ref in objects)

    input_irred_facts = [
        fact
        for fact in _facts_by_pred(cert, "IrreducibleQQ")
        if _claim_ref0(fact) == "$input"
    ]
    assert len(input_irred_facts) == 1


def test_irreducible_deg3_radicals_transport_irreducibility_when_normalizing() -> None:
    """A non-depressed cubic should normalize, transport irreducibility, and lift roots."""
    result = analyze([1, 1, 0, 1], explain=False)
    cert: Certificate = result.certificate

    verified = verify(cert)
    assert verified.verified

    normalization = next(
        fact
        for fact in _normalization_facts(cert)
        if _claim_ref0(fact) == "$input" and _claim_ref1(fact) != "$input"
    )
    g_ref = _claim_ref1(normalization)
    assert g_ref is not None

    irred_g = [
        fact
        for fact in _facts_by_pred(cert, "IrreducibleQQ")
        if _claim_ref0(fact) == g_ref
    ]
    assert any(fact.get("rule") == "irreducible.QQ.to.depressed_monic@1" for fact in irred_g)
    assert not any(fact.get("rule") == "irreducible.QQ.deg5_recompute@1" for fact in irred_g)

    g_radicals = _radical_facts_for(cert, g_ref)
    assert any(
        fact.get("rule") == "radical_roots.QQ.deg3.cardano.depressed_monic@2"
        for fact in g_radicals
    )

    input_radicals = _radical_facts_for(cert, "$input")
    assert any(
        fact.get("rule") == "radical_roots.QQ.lift.depressed_monic@1"
        for fact in input_radicals
    )
