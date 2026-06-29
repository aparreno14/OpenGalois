from opengalois import analyze, verify


def test_analyze_contract_minimal_certificate():
    """Test analyze contract minimal certificate."""
    r = analyze([1, 0, 0, 0, -1, -1], explain=False)
    cert = r.certificate

    assert "meta" in cert
    assert "input" in cert
    assert "result" in cert

    assert cert["meta"]["schema_version"] == "1.1.0"
    assert cert["input"]["domain"] == "Q"
    assert cert["input"]["variable"] == "x"
    assert cert["input"]["ordering"] == "descending_degree"
    assert cert["input"]["degree"] == 5
    assert cert["input"]["canonicalization"] == "jcs-rfc8785"
    assert cert["input"]["hash_alg"] == "sha256"
    assert cert["input"]["hash_scope"] == "input_v1"
    assert len(cert["input"]["coeffs_qq"]) == 6
    assert isinstance(cert["input"]["hash"], str) and cert["input"]["hash"]
    assert cert["result"]["transitive_group_id"] is None

    v = verify(cert)
    assert v.verified is True
