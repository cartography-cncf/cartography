import pytest

from cartography.intel.container_image import ContainerImageReference
from cartography.intel.container_image import parse_container_image_reference
from cartography.intel.container_image import parse_image_uri

_DIGEST = f"sha256:{'a' * 64}"


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


@pytest.mark.parametrize(  # type: ignore[misc]
    ("raw", "expected"),
    [
        (
            "postgres:16",
            ContainerImageReference(
                original="postgres:16",
                registry="docker.io",
                repository="library/postgres",
                tag="16",
                digest=None,
                normalized="docker.io/library/postgres:16",
                selector="16",
            ),
        ),
        (
            "docker.io/library/postgres:16",
            ContainerImageReference(
                original="docker.io/library/postgres:16",
                registry="docker.io",
                repository="library/postgres",
                tag="16",
                digest=None,
                normalized="docker.io/library/postgres:16",
                selector="16",
            ),
        ),
        (
            "index.docker.io/postgres:16",
            ContainerImageReference(
                original="index.docker.io/postgres:16",
                registry="docker.io",
                repository="library/postgres",
                tag="16",
                digest=None,
                normalized="docker.io/library/postgres:16",
                selector="16",
            ),
        ),
        (
            "registry.example.com/team/service:v1",
            ContainerImageReference(
                original="registry.example.com/team/service:v1",
                registry="registry.example.com",
                repository="team/service",
                tag="v1",
                digest=None,
                normalized="registry.example.com/team/service:v1",
                selector="v1",
            ),
        ),
        (
            "team/service",
            ContainerImageReference(
                original="team/service",
                registry="docker.io",
                repository="team/service",
                tag="latest",
                digest=None,
                normalized="docker.io/team/service:latest",
                selector="latest",
            ),
        ),
        (
            f"repository@{_DIGEST}",
            ContainerImageReference(
                original=f"repository@{_DIGEST}",
                registry="docker.io",
                repository="library/repository",
                tag=None,
                digest=_DIGEST,
                normalized=f"docker.io/library/repository@{_DIGEST}",
                selector=_DIGEST,
            ),
        ),
        (
            f"repository:stable@{_DIGEST}",
            ContainerImageReference(
                original=f"repository:stable@{_DIGEST}",
                registry="docker.io",
                repository="library/repository",
                tag="stable",
                digest=_DIGEST,
                normalized=f"docker.io/library/repository:stable@{_DIGEST}",
                selector=_DIGEST,
            ),
        ),
    ],
)
def test_parse_container_image_reference(
    raw: str,
    expected: ContainerImageReference,
) -> None:
    # Act and assert
    assert parse_container_image_reference(raw) == expected


@pytest.mark.parametrize(  # type: ignore[misc]
    "raw",
    [
        "",
        " postgres:16",
        "postgres :16",
        "https://docker.io/library/postgres:16",
        "docker.io/Postgres:16",
        "registry.example.com",
        "registry.example.com:0/team/service:stable",
        "postgres:",
        "postgres@sha256:abc",
        "postgres@@sha256:" + "a" * 64,
        "postgres:16?platform=linux/amd64",
    ],
)
def test_parse_container_image_reference_rejects_malformed_input(raw: str) -> None:
    # Act and assert
    with pytest.raises(ValueError):
        parse_container_image_reference(raw)
