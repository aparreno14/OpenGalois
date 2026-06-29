def test_import_and_version():
    """Test import and version."""
    import opengalois

    assert hasattr(opengalois, "__version__")
    assert isinstance(opengalois.__version__, str)
    assert opengalois.__version__
