from cartography.intel.container_arch import normalize_architecture


def test_normalize_architecture_aliases() -> None:
    assert normalize_architecture("x86_64") == "amd64"
    assert normalize_architecture("X86_64") == "amd64"
    assert normalize_architecture("x64") == "amd64"
    assert normalize_architecture("aarch64") == "arm64"
    assert normalize_architecture("arm64/v8") == "arm64"
    assert normalize_architecture("armv7l") == "arm"
    assert normalize_architecture("arm/v7") == "arm"
    assert normalize_architecture("i386") == "386"
    assert normalize_architecture("invalid") == "unknown"
    assert normalize_architecture(None) == "unknown"
