import base64
from unittest.mock import patch

from cartography.intel.gitlab.supply_chain import (
    build_singleton_dockerfile_fallback_matchlinks,
)
from cartography.intel.gitlab.supply_chain import (
    GITLAB_SINGLETON_DOCKERFILE_FALLBACK_CONFIDENCE,
)
from cartography.intel.gitlab.supply_chain import get_file_content
from cartography.intel.supply_chain import ContainerImage

TEST_GITLAB_URL = "https://gitlab.example.com"


@patch("cartography.intel.gitlab.supply_chain.get_single")
def test_get_file_content_returns_none_for_non_utf8_content(mock_get_single):
    # A file named "Dockerfile" whose contents are actually binary (e.g. a PNG), matching
    # the crash reported in VMP-1868: base64-encoded PNG magic bytes are not valid UTF-8.
    png_magic_bytes = b"\x89PNG\r\n\x1a\n"
    mock_get_single.return_value = {
        "encoding": "base64",
        "content": base64.b64encode(png_magic_bytes).decode("ascii"),
    }

    content = get_file_content(TEST_GITLAB_URL, "tok", 1, "Dockerfile")

    assert content is None


@patch("cartography.intel.gitlab.supply_chain.get_single")
def test_get_file_content_decodes_valid_utf8_content(mock_get_single):
    mock_get_single.return_value = {
        "encoding": "base64",
        "content": base64.b64encode(b"FROM alpine:latest\n").decode("ascii"),
    }

    content = get_file_content(TEST_GITLAB_URL, "tok", 1, "Dockerfile")

    assert content == "FROM alpine:latest\n"


def test_build_singleton_dockerfile_fallback_matchlinks_uses_scoped_singleton():
    image = ContainerImage(
        digest="sha256:image1",
        uri="registry.gitlab.com/acme/service:latest",
        registry_id="registry.gitlab.com/acme/service",
        display_name="registry.gitlab.com/acme/service",
        tag="latest",
        layer_diff_ids=["sha256:layer1"],
        image_type="image",
        architecture="amd64",
        os="linux",
        layer_history=[],
        scope_keys={"gitlab_project_id": "100"},
    )

    dockerfiles = [
        {
            "path": "Dockerfile",
            "project_url": "https://gitlab.example.com/acme/service",
            "scope_keys": {"gitlab_project_id": "100"},
        },
        {
            "path": "Dockerfile",
            "project_url": "https://gitlab.example.com/acme/other",
            "scope_keys": {"gitlab_project_id": "200"},
        },
    ]

    fallback = build_singleton_dockerfile_fallback_matchlinks(
        [image],
        dockerfiles,
        set(),
    )

    assert fallback == [
        {
            "image_digest": "sha256:image1",
            "project_url": "https://gitlab.example.com/acme/service",
            "match_method": "dockerfile_singleton_fallback",
            "dockerfile_path": "Dockerfile",
            "confidence": GITLAB_SINGLETON_DOCKERFILE_FALLBACK_CONFIDENCE,
            "matched_commands": 0,
            "total_commands": 0,
            "command_similarity": 0.0,
        },
    ]


def test_build_singleton_dockerfile_fallback_matchlinks_skips_already_matched_and_ambiguous():
    image_already_matched = ContainerImage(
        digest="sha256:image1",
        uri="registry.gitlab.com/acme/service:latest",
        registry_id="registry.gitlab.com/acme/service",
        display_name="registry.gitlab.com/acme/service",
        tag="latest",
        layer_diff_ids=["sha256:layer1"],
        image_type="image",
        architecture="amd64",
        os="linux",
        layer_history=[],
        scope_keys={"gitlab_project_id": "100"},
    )
    image_ambiguous = ContainerImage(
        digest="sha256:image2",
        uri="registry.gitlab.com/acme/ambiguous:latest",
        registry_id="registry.gitlab.com/acme/ambiguous",
        display_name="registry.gitlab.com/acme/ambiguous",
        tag="latest",
        layer_diff_ids=["sha256:layer2"],
        image_type="image",
        architecture="amd64",
        os="linux",
        layer_history=[],
        scope_keys={"gitlab_project_id": "200"},
    )

    dockerfiles = [
        {
            "path": "Dockerfile",
            "project_url": "https://gitlab.example.com/acme/service",
            "scope_keys": {"gitlab_project_id": "100"},
        },
        {
            "path": "Dockerfile",
            "project_url": "https://gitlab.example.com/acme/ambiguous",
            "scope_keys": {"gitlab_project_id": "200"},
        },
        {
            "path": "docker/Dockerfile",
            "project_url": "https://gitlab.example.com/acme/ambiguous",
            "scope_keys": {"gitlab_project_id": "200"},
        },
    ]

    fallback = build_singleton_dockerfile_fallback_matchlinks(
        [image_already_matched, image_ambiguous],
        dockerfiles,
        {"sha256:image1"},
    )

    assert fallback == []
