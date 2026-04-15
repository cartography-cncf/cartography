from cartography.intel.supply_chain import extract_container_parent_image
from cartography.intel.supply_chain import extract_image_source_provenance
from cartography.intel.supply_chain import get_slsa_dependency_list
from cartography.intel.supply_chain import unwrap_attestation_predicate


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
