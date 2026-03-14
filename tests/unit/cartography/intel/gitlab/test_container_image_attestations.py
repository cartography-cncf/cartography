from unittest.mock import Mock

import requests

from cartography.intel.gitlab.container_image_attestations import (
    AttestationDiscoverySummary,
)
from cartography.intel.gitlab.container_image_attestations import (
    get_container_image_attestations,
)
from cartography.intel.gitlab.container_image_attestations import (
    sync_container_image_attestations,
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
        "cartography.intel.gitlab.container_image_attestations.cleanup_container_image_attestations",
        cleanup_mock,
    )

    sync_container_image_attestations(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_url="https://gitlab.example.com/groups/core",
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
        "cartography.intel.gitlab.container_image_attestations.cleanup_container_image_attestations",
        cleanup_mock,
    )

    sync_container_image_attestations(
        neo4j_session=Mock(),
        gitlab_url="https://gitlab.example.com",
        token="pat",
        org_url="https://gitlab.example.com/groups/core",
        manifests=[],
        manifest_lists=[],
        update_tag=123,
        common_job_parameters={},
    )

    load_mock.assert_called_once()
    cleanup_mock.assert_called_once()
