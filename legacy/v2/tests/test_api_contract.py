from opengalois import analyze, verify


def test_analyze_contract_minimal_certificate():
    """Analyze returns a minimal v2.0.0 proof-first certificate and it verifies."""
    r = analyze([1, 0, 0, 0, -1, -1], explain=False)
    cert = r.certificate

    assert "meta" in cert
    assert "input" in cert
    assert "proof" in cert

    assert cert["meta"]["schema_version"] == "2.0.0"
    assert cert["input"]["domain"] == "Q"
    assert cert["input"]["variable"] == "x"
    assert cert["input"]["ordering"] == "descending_degree"
    assert cert["input"]["degree"] == 5
    assert cert["input"]["canonicalization"] == "jcs-rfc8785"
    assert cert["input"]["hash_alg"] == "sha256"
    assert cert["input"]["hash_scope"] == "input_v1"
    assert len(cert["input"]["coeffs_qq"]) == 6
    assert isinstance(cert["input"]["hash"], str) and cert["input"]["hash"]

    assert cert["proof"]["version"] == "0.1"
    assert cert["proof"]["root"]["kind"] == "opengalois.analyze"

    v = verify(cert)
    assert v.verified is True


def test_verify_rejects_root_input_ref_not_input():
    """Verifier rejects proofs whose root is not anchored to $input."""
    cert = analyze([1, 0, 0, 0, -1, -1], explain=False).certificate
    cert["proof"]["root"]["inputs"] = [{"ref": "poly:other"}]

    v = verify(cert)

    assert v.verified is False
    assert any(
        c.name == "lemma.root.inputs" and c.ok is False
        for c in v.checks
    )


def test_verify_rejects_unsupported_proof_version():
    """Verifier rejects unknown/future proof format versions."""
    cert = analyze([1, 0, 0, 0, -1, -1], explain=False).certificate
    cert["proof"]["version"] = "999.0"

    v = verify(cert)

    assert v.verified is False
    assert any(c.name == "proof.version" and c.ok is False for c in v.checks)
