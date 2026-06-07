from unittest.mock import Mock

import requests

from cartography.intel.gitlab.container_image_attestations import (
    _extract_image_provenance,
)
from cartography.intel.gitlab.container_image_attestations import (
    _extract_predicate_from_attestation,
)
from cartography.intel.gitlab.container_image_attestations import (
    AttestationDiscoverySummary,
)
from cartography.intel.gitlab.container_image_attestations import (
    get_container_image_attestations,
)
from cartography.intel.gitlab.container_image_attestations import (
    sync_container_image_attestations,
)
from cartography.intel.gitlab.container_image_attestations import (
    transform_image_provenance_records,
)


def _make_manifest_response(attestation_digest: str):
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.headers = {"Docker-Content-Digest": attestation_digest}
    response.json.return_value = {
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "predicateType": "https://example.com/provenance",
    }
    response.raise_for_status.return_value = None
    return response


def _make_http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    return requests.exceptions.HTTPError(
        f"{status_code} error",
        response=response,
    )


def test_get_container_image_attestations_continues_after_request_failure(monkeypatch):
    manifests = [
        {
            "_digest": "sha256:abc123",
            "_registry_url": "https://registry.example.com",
            "_repository_name": "group/project",
        }
    ]
    attempts = 0

    def _fetch_registry_manifest(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise requests.exceptions.HTTPError("502 bad gateway")
        return _make_manifest_response("sha256:attestation123")

    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.fetch_registry_manifest",
        _fetch_registry_manifest,
    )

    attestations, summary = get_container_image_attestations(
        "https://gitlab.example.com",
        "pat",
        manifests,
        [],
    )

    assert len(attestations) == 1
    assert attestations[0]["_digest"] == "sha256:attestation123"
    assert summary == AttestationDiscoverySummary(
        attempted=2,
        discovered=1,
        failed=1,
    )


def test_get_container_image_attestations_raises_on_registry_auth_failure(
    monkeypatch,
):
    manifests = [
        {
            "_digest": "sha256:abc123",
            "_registry_url": "https://registry.example.com",
            "_repository_name": "group/project",
        }
    ]

    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.fetch_registry_manifest",
        lambda *args, **kwargs: (_ for _ in ()).throw(_make_http_error(403)),
    )

    try:
        get_container_image_attestations(
            "https://gitlab.example.com",
            "pat",
            manifests,
            [],
        )
    except requests.exceptions.HTTPError as exc:
        assert exc.response is not None
        assert exc.response.status_code == 403
    else:
        raise AssertionError("expected registry auth failure to be raised")


def test_sync_container_image_attestations_skips_cleanup_after_partial_failure(
    monkeypatch,
):
    load_mock = Mock()
    cleanup_mock = Mock()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.get_container_image_attestations",
        lambda *args, **kwargs: (
            [],
            AttestationDiscoverySummary(attempted=4, discovered=0, failed=1),
        ),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.load_container_image_attestations",
        load_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.load_image_provenance",
        Mock(),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.cleanup_container_image_attestations",
        cleanup_mock,
    )

    sync_container_image_attestations(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_id=123,
        manifests=[],
        manifest_lists=[],
        update_tag=123,
        common_job_parameters={},
    )

    load_mock.assert_called_once()
    cleanup_mock.assert_not_called()


def test_sync_container_image_attestations_runs_cleanup_when_complete(monkeypatch):
    load_mock = Mock()
    cleanup_mock = Mock()
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.get_container_image_attestations",
        lambda *args, **kwargs: (
            [],
            AttestationDiscoverySummary(attempted=2, discovered=0, failed=0),
        ),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.load_container_image_attestations",
        load_mock,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.load_image_provenance",
        Mock(),
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.cleanup_container_image_attestations",
        cleanup_mock,
    )

    sync_container_image_attestations(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_id=123,
        manifests=[],
        manifest_lists=[],
        update_tag=123,
        common_job_parameters={},
    )

    load_mock.assert_called_once()
    cleanup_mock.assert_called_once()


def test_extract_predicate_from_attestation_unwraps_dsse_payload(monkeypatch):
    predicate_blob = {
        "payload": "eyJwcmVkaWNhdGUiOiB7IkJ1aWxkRGVmaW5pdGlvbiI6IG51bGx9fQ==",
    }
    attestation = {
        "_digest": "sha256:attestation123",
        "_registry_url": "https://registry.example.com",
        "_repository_name": "group/project",
        "layers": [{"digest": "sha256:layer"}],
    }

    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.fetch_registry_blob",
        lambda *args, **kwargs: predicate_blob,
    )

    predicate = _extract_predicate_from_attestation(
        attestation,
        "https://gitlab.example.com",
        "pat",
    )

    assert predicate == {"BuildDefinition": None}


def test_extract_predicate_from_attestation_accepts_raw_in_toto_statement(monkeypatch):
    attestation = {
        "_digest": "sha256:attestation123",
        "_registry_url": "https://registry.example.com",
        "_repository_name": "group/project",
        "layers": [{"digest": "sha256:layer"}],
    }
    raw_statement = {
        "_type": "https://in-toto.io/Statement/v0.1",
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "externalParameters": {
                    "source": "https://gitlab.example.com/myorg/project.git",
                },
            },
        },
    }

    monkeypatch.setattr(
        "cartography.intel.gitlab.container_image_attestations.fetch_registry_blob",
        lambda *args, **kwargs: raw_statement,
    )

    predicate = _extract_predicate_from_attestation(
        attestation,
        "https://gitlab.example.com",
        "pat",
    )

    assert predicate == raw_statement["predicate"]


def test_extract_image_provenance_supports_buildkit_shape():
    attestation = {"_attests_digest": "sha256:image123"}
    predicate = {
        "materials": [
            {
                "uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
                "digest": {
                    "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                },
            },
        ],
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

    result = _extract_image_provenance(attestation, predicate)

    assert result == {
        "source_uri": "https://gitlab.example.com/myorg/awesome-project",
        "source_revision": "deadbeefcafebabe",
        "source_file": "docker/Dockerfile",
        "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
        "parent_image_digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "attests_digest": "sha256:image123",
    }


def test_extract_image_provenance_supports_gitlab_slsa_v1_shape():
    attestation = {"_attests_digest": "sha256:image123"}
    predicate = {
        "buildDefinition": {
            "externalParameters": {
                "source": "https://gitlab.example.com/myorg/awesome-project.git",
                "entryPoint": "docker/Dockerfile",
            },
            "resolvedDependencies": [
                {
                    "uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
                    "digest": {
                        "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                    },
                },
                {
                    "uri": "https://gitlab.example.com/myorg/awesome-project",
                    "digest": {
                        "gitCommit": "a288201509dd9a85da4141e07522bad412938dbe",
                    },
                },
            ],
        },
        "runDetails": {
            "metadata": {
                "invocationId": 412,
            },
        },
    }

    result = _extract_image_provenance(attestation, predicate)

    assert result == {
        "source_uri": "https://gitlab.example.com/myorg/awesome-project",
        "source_revision": "a288201509dd9a85da4141e07522bad412938dbe",
        "source_file": "docker/Dockerfile",
        "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
        "parent_image_digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "attests_digest": "sha256:image123",
    }


def test_transform_image_provenance_records_keeps_gitlab_slsa_fields():
    records = transform_image_provenance_records(
        [
            {
                "attests_digest": "sha256:image123",
                "source_uri": "https://gitlab.example.com/myorg/awesome-project",
                "source_revision": "a288201509dd9a85da4141e07522bad412938dbe",
                "source_file": "docker/Dockerfile",
                "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
                "parent_image_digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            },
        ],
    )

    assert records == [
        {
            "digest": "sha256:image123",
            "source_uri": "https://gitlab.example.com/myorg/awesome-project",
            "source_revision": "a288201509dd9a85da4141e07522bad412938dbe",
            "source_file": "docker/Dockerfile",
            "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
            "parent_image_digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "from_attestation": True,
            "confidence": 1.0,
        },
    ]


def test_transform_image_provenance_records_keeps_parent_only_records():
    records = transform_image_provenance_records(
        [
            {
                "attests_digest": "sha256:image123",
                "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
                "parent_image_digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            },
        ],
    )

    assert records == [
        {
            "digest": "sha256:image123",
            "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
            "parent_image_digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "from_attestation": True,
            "confidence": 1.0,
        },
    ]


def test_transform_image_provenance_records_merges_parent_only_without_overwriting_source():
    records = transform_image_provenance_records(
        [
            {
                "attests_digest": "sha256:image123",
                "source_uri": "https://gitlab.example.com/myorg/awesome-project",
                "source_revision": "a288201509dd9a85da4141e07522bad412938dbe",
                "source_file": "docker/Dockerfile",
            },
            {
                "attests_digest": "sha256:image123",
                "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
                "parent_image_digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            },
        ],
    )

    assert records == [
        {
            "digest": "sha256:image123",
            "source_uri": "https://gitlab.example.com/myorg/awesome-project",
            "source_revision": "a288201509dd9a85da4141e07522bad412938dbe",
            "source_file": "docker/Dockerfile",
            "parent_image_uri": "pkg:docker/registry.gitlab.com/base-images/python@3.12",
            "parent_image_digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "from_attestation": True,
            "confidence": 1.0,
        },
    ]
