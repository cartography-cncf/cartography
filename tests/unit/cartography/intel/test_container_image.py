from cartography.intel.container_image import parse_image_uri


def test_parse_image_uri_empty_and_none() -> None:
    assert parse_image_uri(None) == (None, None)
    assert parse_image_uri("") == (None, None)
    assert parse_image_uri("   ") == (None, None)


def test_parse_image_uri_bare_tag() -> None:
    assert parse_image_uri("nginx:latest") == ("nginx:latest", None)
    assert parse_image_uri("registry.example.com/ns/app:v1.2.3") == (
        "registry.example.com/ns/app:v1.2.3",
        None,
    )


def test_parse_image_uri_digest_only() -> None:
    assert parse_image_uri("registry.example.com/app@sha256:abc") == (
        "registry.example.com/app@sha256:abc",
        "sha256:abc",
    )


def test_parse_image_uri_tag_and_digest() -> None:
    raw = "123.dkr.ecr.us-east-1.amazonaws.com/repo:prod@sha256:deadbeef"
    assert parse_image_uri(raw) == (raw, "sha256:deadbeef")


def test_parse_image_uri_azure_docker_prefix() -> None:
    assert parse_image_uri("DOCKER|myregistry.azurecr.io/app:latest") == (
        "myregistry.azurecr.io/app:latest",
        None,
    )
    assert parse_image_uri("DOCKER|myregistry.azurecr.io/app@sha256:abc") == (
        "myregistry.azurecr.io/app@sha256:abc",
        "sha256:abc",
    )


def test_parse_image_uri_azure_docker_prefix_only() -> None:
    assert parse_image_uri("DOCKER|") == (None, None)
    assert parse_image_uri("DOCKER|   ") == (None, None)


def test_parse_image_uri_trailing_at_no_digest() -> None:
    # Malformed input: trailing '@' without digest returns None digest, not empty string.
    assert parse_image_uri("registry.example.com/app@") == (
        "registry.example.com/app@",
        None,
    )
