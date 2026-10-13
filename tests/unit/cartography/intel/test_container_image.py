import pytest

from cartography.intel.container_image import parse_image_uri


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(None, (None, None), id="none"),
        pytest.param("", (None, None), id="empty"),
        pytest.param("   ", (None, None), id="whitespace"),
        pytest.param("nginx:latest", ("nginx:latest", None), id="bare_tag"),
        pytest.param(
            "registry.example.com/ns/app:v1.2.3",
            ("registry.example.com/ns/app:v1.2.3", None),
            id="registry_tag",
        ),
        pytest.param(
            "registry.example.com/app@sha256:abc",
            ("registry.example.com/app@sha256:abc", "sha256:abc"),
            id="digest_only",
        ),
        pytest.param(
            "123.dkr.ecr.us-east-1.amazonaws.com/repo:prod@sha256:deadbeef",
            (
                "123.dkr.ecr.us-east-1.amazonaws.com/repo:prod@sha256:deadbeef",
                "sha256:deadbeef",
            ),
            id="tag_and_digest",
        ),
        pytest.param(
            "DOCKER|myregistry.azurecr.io/app:latest",
            ("myregistry.azurecr.io/app:latest", None),
            id="azure_tag",
        ),
        pytest.param(
            "DOCKER|myregistry.azurecr.io/app@sha256:abc",
            ("myregistry.azurecr.io/app@sha256:abc", "sha256:abc"),
            id="azure_digest",
        ),
        pytest.param("DOCKER|", (None, None), id="azure_prefix_only"),
        pytest.param("DOCKER|   ", (None, None), id="azure_prefix_whitespace"),
        # Malformed input: trailing '@' without digest returns None digest, not empty string.
        pytest.param(
            "registry.example.com/app@",
            ("registry.example.com/app@", None),
            id="trailing_at",
        ),
    ],
)
def test_parse_image_uri(raw, expected):
    assert parse_image_uri(raw) == expected
