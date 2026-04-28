import base64
import json

from cartography.intel.supply_chain import ContainerImage
from cartography.intel.supply_chain import decode_attestation_blob_to_predicate
from cartography.intel.supply_chain import extract_container_parent_image
from cartography.intel.supply_chain import extract_image_source_provenance
from cartography.intel.supply_chain import get_slsa_dependency_list
from cartography.intel.supply_chain import match_images_to_dockerfiles
from cartography.intel.supply_chain import unwrap_attestation_predicate


def test_decode_attestation_blob_dsse_envelope():
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicate": {
            "buildDefinition": {
                "externalParameters": {"source": "https://github.com/foo/bar"},
            },
        },
    }
    blob = {"payload": base64.b64encode(json.dumps(statement).encode()).decode()}

    predicate = decode_attestation_blob_to_predicate(blob)

    assert predicate == statement["predicate"]


def test_decode_attestation_blob_raw_in_toto():
    blob = {"predicate": {"buildDefinition": {"externalParameters": {"a": "b"}}}}

    assert decode_attestation_blob_to_predicate(blob) == blob["predicate"]


def test_decode_attestation_blob_invalid_payload_returns_none():
    blob = {"payload": "not-valid-base64!!"}

    assert decode_attestation_blob_to_predicate(blob) is None


def test_decode_attestation_blob_empty_returns_none():
    assert decode_attestation_blob_to_predicate({}) is None


def test_unwrap_attestation_predicate_supports_dsse_data():
    predicate = {
        "Data": '{"predicate": {"buildDefinition": {"externalParameters": {"entryPoint": "Dockerfile"}}}}'
    }

    assert unwrap_attestation_predicate(predicate) == {
        "buildDefinition": {
            "externalParameters": {
                "entryPoint": "Dockerfile",
            },
        },
    }


def test_get_slsa_dependency_list_supports_v02_and_v1():
    v02 = {"materials": [{"uri": "oci://example/base"}]}
    v1 = {"buildDefinition": {"resolvedDependencies": [{"uri": "oci://example/base"}]}}

    assert get_slsa_dependency_list(v02) == [{"uri": "oci://example/base"}]
    assert get_slsa_dependency_list(v1) == [{"uri": "oci://example/base"}]


def test_extract_image_source_provenance_supports_buildkit_shape():
    predicate = {
        "metadata": {
            "https://mobyproject.org/buildkit@v1#metadata": {
                "vcs": {
                    "source": "https://gitlab.example.com/myorg/awesome-project.git",
                    "revision": "deadbeefcafebabe",
                    "localdir:dockerfile": "docker",
                },
            },
        },
        "buildDefinition": {
            "externalParameters": {
                "configSource": {
                    "path": "Dockerfile",
                },
            },
        },
    }

    assert extract_image_source_provenance(predicate) == {
        "source_uri": "https://gitlab.example.com/myorg/awesome-project",
        "source_revision": "deadbeefcafebabe",
        "source_file": "docker/Dockerfile",
    }


def test_extract_image_source_provenance_supports_gitlab_slsa_v1_shape():
    predicate = {
        "buildDefinition": {
            "externalParameters": {
                "source": "https://gitlab.example.com/myorg/awesome-project.git",
                "entryPoint": "docker/Dockerfile",
            },
            "resolvedDependencies": [
                {
                    "uri": "https://gitlab.example.com/myorg/awesome-project",
                    "digest": {
                        "gitCommit": "a288201509dd9a85da4141e07522bad412938dbe",
                    },
                },
            ],
        },
    }

    assert extract_image_source_provenance(predicate) == {
        "source_uri": "https://gitlab.example.com/myorg/awesome-project",
        "source_revision": "a288201509dd9a85da4141e07522bad412938dbe",
        "source_file": "docker/Dockerfile",
    }


def test_extract_container_parent_image_supports_slsa_v1_dependencies():
    predicate = {
        "buildDefinition": {
            "resolvedDependencies": [
                {
                    "uri": "pkg:docker/docker/dockerfile@1.9",
                    "digest": {"sha256": "ignored"},
                },
                {
                    "uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
                    "digest": {
                        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    },
                },
            ],
        },
    }

    assert extract_container_parent_image(predicate) == {
        "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
        "parent_image_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }


def test_match_images_to_dockerfiles_scopes_by_scope_keys():
    image = ContainerImage(
        digest="sha256:test",
        uri="registry.gitlab.com/acme/service:latest",
        registry_id="registry.gitlab.com/acme/service",
        display_name="registry.gitlab.com/acme/service",
        tag="latest",
        layer_diff_ids=["sha256:layer1"],
        image_type="image",
        architecture="amd64",
        os="linux",
        layer_history=[
            {
                "created_by": "RUN apk add curl",
                "empty_layer": False,
            },
        ],
        scope_keys={"gitlab_project_id": "100"},
    )

    dockerfiles = [
        {
            "path": "Dockerfile",
            "content": "FROM alpine\nRUN apk add curl\n",
            "scope_keys": {"gitlab_project_id": "100"},
            "source_repo_id": "https://gitlab.example.com/acme/service",
        },
        {
            "path": "Dockerfile",
            "content": "FROM alpine\nRUN apk add curl\n",
            "scope_keys": {"gitlab_project_id": "200"},
            "source_repo_id": "https://gitlab.example.com/acme/other-service",
        },
    ]

    matches = match_images_to_dockerfiles([image], dockerfiles, min_confidence=0.5)

    assert len(matches) == 1
    assert matches[0].source_repo_id == "https://gitlab.example.com/acme/service"


def test_match_images_to_dockerfiles_matches_copy_destination_patterns():
    image = ContainerImage(
        digest="sha256:test-copy",
        uri="registry.gitlab.com/acme/service:latest",
        registry_id="registry.gitlab.com/acme/service",
        display_name="registry.gitlab.com/acme/service",
        tag="latest",
        layer_diff_ids=["sha256:layer1"],
        image_type="image",
        architecture="amd64",
        os="linux",
        layer_history=[
            {
                "created_by": "/bin/sh -c #(nop) COPY file:abcd1234 in /usr/local/bin/",
                "empty_layer": False,
            },
        ],
    )

    dockerfiles = [
        {
            "path": "Dockerfile",
            "content": "FROM alpine\nCOPY ./bin/service /usr/local/bin/\n",
            "source_repo_id": "https://gitlab.example.com/acme/service",
        },
    ]

    matches = match_images_to_dockerfiles([image], dockerfiles, min_confidence=0.5)

    assert len(matches) == 1
    assert matches[0].source_repo_id == "https://gitlab.example.com/acme/service"
