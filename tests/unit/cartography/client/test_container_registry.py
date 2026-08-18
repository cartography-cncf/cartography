from __future__ import annotations

import hashlib
import json
import socket
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from requests.adapters import HTTPAdapter

from cartography.client.container_registry import AnonymousRegistryClient
from cartography.client.container_registry import DOCKER_IMAGE_MANIFEST
from cartography.client.container_registry import DOCKER_MANIFEST_LIST
from cartography.client.container_registry import MANIFEST_MEDIA_TYPES
from cartography.client.container_registry import OCI_IMAGE_INDEX
from cartography.client.container_registry import OCI_IMAGE_MANIFEST
from cartography.client.container_registry import RegistryAuthenticationError
from cartography.client.container_registry import RegistryNotFoundError
from cartography.client.container_registry import RegistryRateLimitError
from cartography.client.container_registry import RegistryResponseError
from cartography.client.container_registry import RegistrySecurityError
from cartography.client.container_registry import RegistryTransientError
from cartography.client.container_registry import RegistryUnsupportedArtifactError

_PUBLIC_IP = "93.184.216.34"
_REGISTRY = "registry.example.com"
_REPOSITORY = "team/service"


@pytest.fixture(autouse=True)  # type: ignore[misc]
def public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    def getaddrinfo(
        host: str,
        port: int,
        **_kwargs: object,
    ) -> list[tuple[int, int, int, str, tuple[str, int]]]:
        address = "127.0.0.1" if host == "127.0.0.1" else _PUBLIC_IP
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)


def _digest(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def _response(
    status: int,
    body: bytes = b"",
    *,
    headers: dict[str, str] | None = None,
    url: str = f"https://{_REGISTRY}/v2/",
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = body
    setattr(response, "_content_consumed", True)
    response.headers.update(headers or {})
    response.url = url
    return response


def _image_payload(
    media_type: str,
    *,
    os_name: str = "linux",
    architecture: str = "amd64",
    variant: str | None = None,
    created_at: str | None = None,
) -> tuple[bytes, bytes]:
    layer_digest = f"sha256:{'f' * 64}"
    config_data: dict[str, Any] = {
        "os": os_name,
        "architecture": architecture,
        "rootfs": {"type": "layers", "diff_ids": [layer_digest]},
    }
    if variant is not None:
        config_data["variant"] = variant
    if created_at is not None:
        config_data["created"] = created_at
    config = _json_bytes(config_data)
    config_media_type = (
        "application/vnd.docker.container.image.v1+json"
        if media_type == DOCKER_IMAGE_MANIFEST
        else "application/vnd.oci.image.config.v1+json"
    )
    manifest = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": media_type,
            "config": {
                "mediaType": config_media_type,
                "digest": _digest(config),
                "size": len(config),
            },
            "layers": [
                {
                    "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                    "digest": layer_digest,
                    "size": 123,
                },
            ],
        },
    )
    return manifest, config


def _manifest_response(raw: bytes, media_type: str) -> requests.Response:
    return _response(
        200,
        raw,
        headers={
            "Content-Type": media_type,
            "Docker-Content-Digest": _digest(raw),
        },
    )


def _mock_session(
    responses: Iterator[requests.Response] | list[requests.Response],
) -> MagicMock:
    session = MagicMock(spec=requests.Session)
    session.headers = requests.structures.CaseInsensitiveDict()
    session.cookies = requests.cookies.RequestsCookieJar()
    session.params = {}
    session.proxies = {}
    session.hooks = {"response": []}
    session.adapters = {}
    session.get.side_effect = iter(responses)
    return session


@pytest.mark.parametrize(  # type: ignore[misc]
    "media_type",
    [DOCKER_IMAGE_MANIFEST, OCI_IMAGE_MANIFEST],
)
def test_resolve_single_platform_manifest_fetches_config_not_layers(
    media_type: str,
) -> None:
    # Arrange
    created_at = "2024-01-02T03:04:05Z"
    manifest, config = _image_payload(
        media_type,
        variant="v8",
        created_at=created_at,
    )
    session = _mock_session(
        [_manifest_response(manifest, media_type), _response(200, config)],
    )
    client = AnonymousRegistryClient(session)

    # Act
    resolved = client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")

    # Assert
    assert resolved.top.type == "image"
    assert resolved.top.media_type == media_type
    assert resolved.top.digest == _digest(manifest)
    assert resolved.top.os == "linux"
    assert resolved.top.architecture == "amd64"
    assert resolved.top.variant == "v8"
    assert resolved.top.config_digest == _digest(config)
    assert resolved.top.created_at == created_at
    assert resolved.children == ()
    assert session.get.call_count == 2
    assert "/manifests/stable" in session.get.call_args_list[0].args[0]
    assert f"/blobs/{_digest(config)}" in session.get.call_args_list[1].args[0]
    accepted = set(
        session.get.call_args_list[0].kwargs["headers"]["Accept"].split(", "),
    )
    assert accepted == MANIFEST_MEDIA_TYPES


@pytest.mark.parametrize(  # type: ignore[misc]
    ("index_type", "image_type"),
    [
        (DOCKER_MANIFEST_LIST, DOCKER_IMAGE_MANIFEST),
        (OCI_IMAGE_INDEX, OCI_IMAGE_MANIFEST),
    ],
)
def test_resolve_manifest_list_keeps_runnable_children_and_skips_attestation(
    index_type: str,
    image_type: str,
) -> None:
    # Arrange
    child, config = _image_payload(
        image_type,
        architecture="arm64",
        variant="v8",
    )
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": index_type,
            "manifests": [
                {
                    "mediaType": image_type,
                    "digest": _digest(child),
                    "size": len(child),
                    "platform": {
                        "os": "linux",
                        "architecture": "arm64",
                        "variant": "v8",
                    },
                },
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": f"sha256:{'e' * 64}",
                    "size": 456,
                    "platform": {"os": "unknown", "architecture": "unknown"},
                    "annotations": {
                        "vnd.docker.reference.type": "attestation-manifest",
                    },
                },
                {
                    "mediaType": "application/vnd.example.sbom.v1+json",
                    "digest": f"sha256:{'d' * 64}",
                    "size": 789,
                    "artifactType": "application/vnd.example.sbom.v1+json",
                },
            ],
        },
    )
    session = _mock_session(
        [
            _manifest_response(index, index_type),
            _manifest_response(child, image_type),
            _response(200, config),
        ],
    )
    client = AnonymousRegistryClient(session)

    # Act
    resolved = client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")

    # Assert
    assert resolved.top.type == "manifest_list"
    assert resolved.top.media_type == index_type
    assert len(resolved.children) == 1
    assert resolved.children[0].type == "image"
    assert resolved.children[0].architecture == "arm64"
    assert resolved.children[0].variant == "v8"
    assert session.get.call_count == 3


def test_anonymous_bearer_challenge_uses_minimal_pull_scope_and_hides_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    secret = "synthetic-secret-token"
    manifest, config = _image_payload(OCI_IMAGE_MANIFEST)
    challenge = (
        'Bearer realm="https://auth.example.com/token",'
        f'service="{_REGISTRY}",scope="repository:{_REPOSITORY}:pull,push"'
    )
    session = _mock_session(
        [
            _response(401, headers={"WWW-Authenticate": challenge}),
            _response(200, _json_bytes({"token": secret})),
            _manifest_response(manifest, OCI_IMAGE_MANIFEST),
            _response(200, config),
        ],
    )
    client = AnonymousRegistryClient(session)

    # Act
    client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")

    # Assert
    token_call = session.get.call_args_list[1]
    assert token_call.args[0] == "https://auth.example.com/token"
    assert token_call.kwargs["params"] == {
        "scope": f"repository:{_REPOSITORY}:pull",
        "client_id": "cartography",
        "service": _REGISTRY,
    }
    assert "Authorization" not in token_call.kwargs["headers"]
    assert session.get.call_args_list[2].kwargs["headers"]["Authorization"] == (
        f"Bearer {secret}"
    )
    assert secret not in caplog.text


@pytest.mark.parametrize(  # type: ignore[misc]
    ("status", "error"),
    [
        (401, RegistryAuthenticationError),
        (403, RegistryAuthenticationError),
        (404, RegistryNotFoundError),
        (429, RegistryRateLimitError),
        (503, RegistryTransientError),
    ],
)
def test_registry_http_failures_are_classified(
    status: int,
    error: type[Exception],
) -> None:
    # Arrange
    session = _mock_session([_response(status)])
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(error):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_client_configures_get_retries_and_closes_its_session() -> None:
    # Arrange
    client = AnonymousRegistryClient()

    # Act
    adapter = client._session.get_adapter("https://registry.example.com")
    assert isinstance(adapter, HTTPAdapter)
    retry = adapter.max_retries
    client.close()

    # Assert
    assert retry.total == 3
    assert retry.allowed_methods == frozenset({"GET"})
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
    assert retry.respect_retry_after_header is False


def test_client_removes_supplied_session_credentials_and_hooks() -> None:
    # Arrange
    session = requests.Session()
    session.auth = ("synthetic-user", "synthetic-password")
    session.cert = "synthetic-certificate.pem"
    session.verify = False
    session.headers["Authorization"] = "Bearer synthetic-token"
    session.cookies.set("session", "synthetic-cookie")
    session.params = {"secret": "synthetic-parameter"}
    session.proxies["https"] = "https://proxy.example.com"
    session.hooks["response"] = [lambda response: response]
    unsafe_adapter = HTTPAdapter()
    session.mount(f"https://{_REGISTRY}/", unsafe_adapter)

    # Act
    client = AnonymousRegistryClient(session)

    # Assert
    assert session.auth is None
    assert session.cert is None
    assert session.verify is True
    assert not session.headers
    assert not session.cookies
    assert not session.params
    assert not session.proxies
    assert session.hooks == {"response": []}
    assert session.get_adapter(f"https://{_REGISTRY}/v2/") is not unsafe_adapter
    client.close()


def test_context_manager_closes_session() -> None:
    # Arrange
    session = _mock_session([])

    # Act
    with AnonymousRegistryClient(session):
        pass

    # Assert
    session.close.assert_called_once_with()


def test_private_registry_address_is_blocked_before_request() -> None:
    # Arrange
    session = _mock_session([])
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistrySecurityError, match="non-public"):
        client.resolve("127.0.0.1/team/service:stable")
    session.get.assert_not_called()


def test_non_https_bearer_realm_is_blocked() -> None:
    # Arrange
    challenge = (
        'Bearer realm="http://auth.example.com/token",'
        f'scope="repository:{_REPOSITORY}:pull"'
    )
    session = _mock_session(
        [_response(401, headers={"WWW-Authenticate": challenge})],
    )
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistrySecurityError, match="HTTPS"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_redirect_does_not_forward_authorization_to_another_host() -> None:
    # Arrange
    session = _mock_session(
        [
            _response(
                307,
                headers={"Location": "https://cdn.example.com/config"},
                url=f"https://{_REGISTRY}/config",
            ),
            _response(200, b"content", url="https://cdn.example.com/config"),
        ],
    )
    client = AnonymousRegistryClient(session)

    # Act
    client._get(
        f"https://{_REGISTRY}/config",
        headers={"Authorization": "Bearer synthetic-token"},
    )

    # Assert
    assert "Authorization" in session.get.call_args_list[0].kwargs["headers"]
    assert "Authorization" not in session.get.call_args_list[1].kwargs["headers"]


def test_cross_host_auth_challenge_cannot_send_its_token_to_registry() -> None:
    # Arrange
    challenge = (
        'Bearer realm="https://auth.cdn.example.com/token",'
        f'scope="repository:{_REPOSITORY}:pull"'
    )
    session = _mock_session(
        [
            _response(
                307,
                headers={"Location": "https://cdn.example.com/config"},
                url=f"https://{_REGISTRY}/config",
            ),
            _response(
                401,
                headers={"WWW-Authenticate": challenge},
                url="https://cdn.example.com/config",
            ),
        ],
    )
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistryAuthenticationError, match="cross-host"):
        client._get_authenticated(
            f"https://{_REGISTRY}/config",
            _REPOSITORY,
            "registry-token",
        )
    assert session.get.call_count == 2
    assert "Authorization" not in session.get.call_args_list[1].kwargs["headers"]


def test_redirect_to_private_address_is_blocked() -> None:
    # Arrange
    session = _mock_session(
        [
            _response(
                307,
                headers={"Location": "https://127.0.0.1/config"},
                url=f"https://{_REGISTRY}/config",
            ),
        ],
    )
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistrySecurityError, match="non-public"):
        client._get(f"https://{_REGISTRY}/config", headers={})
    assert session.get.call_count == 1


def test_malformed_redirect_is_classified_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    response = _response(
        307,
        headers={"Location": "https://cdn.example.com:not-a-port/config"},
    )
    close = MagicMock()
    monkeypatch.setattr(response, "close", close)
    session = _mock_session(
        [response],
    )
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistrySecurityError, match="malformed"):
        client._get(f"https://{_REGISTRY}/config", headers={})
    assert session.get.call_count == 1
    close.assert_called_once_with()


def test_dns_rebinding_to_private_address_is_blocked_by_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    lookups = 0

    def rebinding_getaddrinfo(
        _host: str,
        port: int,
        **_kwargs: object,
    ) -> list[tuple[int, int, int, str, tuple[str, int]]]:
        nonlocal lookups
        lookups += 1
        address = _PUBLIC_IP if lookups == 1 else "127.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    monkeypatch.setattr(socket, "getaddrinfo", rebinding_getaddrinfo)
    client = AnonymousRegistryClient()

    # Act and assert
    with pytest.raises(RegistrySecurityError, match="non-public"):
        client._get(f"https://{_REGISTRY}/v2/", headers={})
    client.close()


def test_successful_resolve_closes_manifest_and_config_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    manifest, config = _image_payload(OCI_IMAGE_MANIFEST)
    manifest_response = _manifest_response(manifest, OCI_IMAGE_MANIFEST)
    config_response = _response(200, config)
    manifest_close = MagicMock()
    config_close = MagicMock()
    monkeypatch.setattr(manifest_response, "close", manifest_close)
    monkeypatch.setattr(config_response, "close", config_close)
    client = AnonymousRegistryClient(
        _mock_session([manifest_response, config_response]),
    )

    # Act
    client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")

    # Assert
    manifest_close.assert_called_once_with()
    config_close.assert_called_once_with()


def test_manifest_digest_mismatch_is_rejected() -> None:
    # Arrange
    manifest, _ = _image_payload(OCI_IMAGE_MANIFEST)
    response = _response(
        200,
        manifest,
        headers={
            "Content-Type": OCI_IMAGE_MANIFEST,
            "Docker-Content-Digest": f"sha256:{'0' * 64}",
        },
    )
    client = AnonymousRegistryClient(_mock_session([response]))

    # Act and assert
    with pytest.raises(RegistryResponseError, match="digest"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_oversized_manifest_is_rejected_before_reading_body() -> None:
    # Arrange
    response = _response(
        200,
        b"{}",
        headers={
            "Content-Type": OCI_IMAGE_MANIFEST,
            "Content-Length": str(20 * 1024 * 1024),
        },
    )
    client = AnonymousRegistryClient(_mock_session([response]))

    # Act and assert
    with pytest.raises(RegistryResponseError, match="size limit"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_child_descriptor_size_mismatch_aborts_resolution() -> None:
    # Arrange
    child, _ = _image_payload(OCI_IMAGE_MANIFEST)
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": [
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": _digest(child),
                    "size": len(child) + 1,
                    "platform": {"os": "linux", "architecture": "amd64"},
                },
            ],
        },
    )
    client = AnonymousRegistryClient(
        _mock_session(
            [
                _manifest_response(index, OCI_IMAGE_INDEX),
                _manifest_response(child, OCI_IMAGE_MANIFEST),
            ],
        ),
    )

    # Act and assert
    with pytest.raises(RegistryResponseError, match="size"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_immutable_manifest_and_config_are_cached() -> None:
    # Arrange
    manifest, config = _image_payload(OCI_IMAGE_MANIFEST)
    session = _mock_session(
        [_manifest_response(manifest, OCI_IMAGE_MANIFEST), _response(200, config)],
    )
    client = AnonymousRegistryClient(session)
    reference = f"{_REGISTRY}/{_REPOSITORY}@{_digest(manifest)}"

    # Act
    first = client.resolve(reference)
    second = client.resolve(reference)

    # Assert
    assert first == second
    assert session.get.call_count == 2


def test_cached_manifest_applies_descriptor_only_platform_variant() -> None:
    # Arrange
    manifest, config = _image_payload(OCI_IMAGE_MANIFEST)
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": [
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": _digest(manifest),
                    "size": len(manifest),
                    "platform": {
                        "os": "linux",
                        "architecture": "amd64",
                        "variant": "v3",
                    },
                },
            ],
        },
    )
    session = _mock_session(
        [
            _manifest_response(manifest, OCI_IMAGE_MANIFEST),
            _response(200, config),
            _manifest_response(index, OCI_IMAGE_INDEX),
        ],
    )
    client = AnonymousRegistryClient(session)
    client.resolve(f"{_REGISTRY}/{_REPOSITORY}@{_digest(manifest)}")

    # Act
    resolved = client.resolve(f"{_REGISTRY}/{_REPOSITORY}:multi")

    # Assert
    assert resolved.children[0].variant == "v3"
    assert session.get.call_count == 3


def test_cached_manifest_rejects_conflicting_descriptor_platforms() -> None:
    # Arrange
    manifest, config = _image_payload(OCI_IMAGE_MANIFEST)
    descriptors = [
        {
            "mediaType": OCI_IMAGE_MANIFEST,
            "digest": _digest(manifest),
            "size": len(manifest),
            "platform": {
                "os": "linux",
                "architecture": "amd64",
                "variant": variant,
            },
        }
        for variant in ("v3", "v4")
    ]
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": descriptors,
        },
    )
    session = _mock_session(
        [
            _manifest_response(index, OCI_IMAGE_INDEX),
            _manifest_response(manifest, OCI_IMAGE_MANIFEST),
            _response(200, config),
        ],
    )
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistryResponseError, match="conflicting platform"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:multi")
    assert session.get.call_count == 3


def test_oversized_config_metadata_is_rejected() -> None:
    # Arrange
    manifest, config = _image_payload(
        OCI_IMAGE_MANIFEST,
        created_at="x" * 129,
    )
    client = AnonymousRegistryClient(
        _mock_session(
            [
                _manifest_response(manifest, OCI_IMAGE_MANIFEST),
                _response(200, config),
            ],
        ),
    )

    # Act and assert
    with pytest.raises(RegistryResponseError, match="config is malformed"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_oversized_descriptor_platform_is_rejected_before_child_fetch() -> None:
    # Arrange
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": [
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": f"sha256:{'d' * 64}",
                    "size": 123,
                    "platform": {
                        "os": "x" * 129,
                        "architecture": "amd64",
                    },
                },
            ],
        },
    )
    session = _mock_session([_manifest_response(index, OCI_IMAGE_INDEX)])
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistryResponseError, match="platform is malformed"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:multi")
    assert session.get.call_count == 1


def test_oversized_bearer_token_is_rejected() -> None:
    # Arrange
    challenge = f'Bearer realm="https://auth.example.com/token",service="{_REGISTRY}"'
    client = AnonymousRegistryClient(
        _mock_session(
            [
                _response(401, headers={"WWW-Authenticate": challenge}),
                _response(
                    200,
                    _json_bytes({"token": "x" * (64 * 1024 + 1)}),
                    url="https://auth.example.com/token",
                ),
            ],
        ),
    )

    # Act and assert
    with pytest.raises(RegistryAuthenticationError, match="invalid token"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_runnable_manifest_with_subject_is_not_misclassified_as_artifact() -> None:
    # Arrange
    original_manifest, config = _image_payload(OCI_IMAGE_MANIFEST)
    payload = json.loads(original_manifest)
    payload["subject"] = {
        "mediaType": OCI_IMAGE_MANIFEST,
        "digest": f"sha256:{'d' * 64}",
        "size": 123,
    }
    manifest = _json_bytes(payload)
    client = AnonymousRegistryClient(
        _mock_session(
            [_manifest_response(manifest, OCI_IMAGE_MANIFEST), _response(200, config)],
        ),
    )

    # Act
    resolved = client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")

    # Assert
    assert resolved.top.type == "image"


def test_empty_config_attestation_child_is_excluded() -> None:
    # Arrange
    child, config = _image_payload(OCI_IMAGE_MANIFEST)
    empty_config = b"{}"
    attestation = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_MANIFEST,
            "config": {
                "mediaType": "application/vnd.oci.empty.v1+json",
                "digest": _digest(empty_config),
                "size": len(empty_config),
            },
            "layers": [
                {
                    "mediaType": "application/vnd.in-toto+json",
                    "digest": f"sha256:{'c' * 64}",
                    "size": 50,
                },
            ],
        },
    )
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": [
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": _digest(child),
                    "size": len(child),
                    "platform": {"os": "linux", "architecture": "amd64"},
                },
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": _digest(attestation),
                    "size": len(attestation),
                },
            ],
        },
    )
    session = _mock_session(
        [
            _manifest_response(index, OCI_IMAGE_INDEX),
            _manifest_response(child, OCI_IMAGE_MANIFEST),
            _response(200, config),
            _manifest_response(attestation, OCI_IMAGE_MANIFEST),
        ],
    )
    client = AnonymousRegistryClient(session)

    # Act
    resolved = client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")

    # Assert
    assert len(resolved.children) == 1
    assert resolved.children[0].digest == _digest(child)
    assert session.get.call_count == 4


def test_index_with_only_non_runnable_artifacts_is_rejected() -> None:
    # Arrange
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": [
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": f"sha256:{'b' * 64}",
                    "size": 100,
                    "artifactType": "application/vnd.example.sbom.v1+json",
                },
            ],
        },
    )
    client = AnonymousRegistryClient(
        _mock_session([_manifest_response(index, OCI_IMAGE_INDEX)]),
    )

    # Act and assert
    with pytest.raises(RegistryUnsupportedArtifactError, match="no runnable"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_partial_child_failure_raises_without_returning_partial_resolution() -> None:
    # Arrange
    first_child, first_config = _image_payload(OCI_IMAGE_MANIFEST)
    second_child, _ = _image_payload(
        OCI_IMAGE_MANIFEST,
        architecture="arm64",
    )
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": [
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": _digest(first_child),
                    "size": len(first_child),
                    "platform": {"os": "linux", "architecture": "amd64"},
                },
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": _digest(second_child),
                    "size": len(second_child),
                    "platform": {"os": "linux", "architecture": "arm64"},
                },
            ],
        },
    )
    client = AnonymousRegistryClient(
        _mock_session(
            [
                _manifest_response(index, OCI_IMAGE_INDEX),
                _manifest_response(first_child, OCI_IMAGE_MANIFEST),
                _response(200, first_config),
                _response(503),
            ],
        ),
    )

    # Act and assert
    with pytest.raises(RegistryTransientError):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


@pytest.mark.parametrize(  # type: ignore[misc]
    "payload",
    [
        {
            "schemaVersion": 2,
            "mediaType": "application/vnd.example.artifact.v1+json",
        },
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_MANIFEST,
            "artifactType": "application/vnd.in-toto+json",
        },
    ],
)
def test_unsupported_or_artifact_manifests_are_rejected(
    payload: dict[str, Any],
) -> None:
    # Arrange
    raw = _json_bytes(payload)
    media_type = str(payload["mediaType"])
    client = AnonymousRegistryClient(
        _mock_session([_manifest_response(raw, media_type)]),
    )

    # Act and assert
    with pytest.raises(RegistryUnsupportedArtifactError):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_malformed_manifest_is_rejected() -> None:
    # Arrange
    client = AnonymousRegistryClient(
        _mock_session(
            [
                _response(
                    200,
                    b"not-json",
                    headers={"Content-Type": OCI_IMAGE_MANIFEST},
                ),
            ],
        ),
    )

    # Act and assert
    with pytest.raises(RegistryResponseError, match="JSON"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_deeply_nested_manifest_is_classified_as_malformed() -> None:
    # Arrange
    raw = b'{"nested":' + (b"[" * 10_000) + b"0" + (b"]" * 10_000) + b"}"
    client = AnonymousRegistryClient(
        _mock_session(
            [
                _response(
                    200,
                    raw,
                    headers={"Content-Type": OCI_IMAGE_MANIFEST},
                ),
            ],
        ),
    )

    # Act and assert
    with pytest.raises(RegistryResponseError, match="JSON"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_manifest_without_schema_version_two_is_rejected() -> None:
    # Arrange
    raw = _json_bytes({"mediaType": OCI_IMAGE_INDEX, "manifests": []})
    client = AnonymousRegistryClient(
        _mock_session([_manifest_response(raw, OCI_IMAGE_INDEX)]),
    )

    # Act and assert
    with pytest.raises(RegistryResponseError, match="schemaVersion"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


@pytest.mark.parametrize(  # type: ignore[misc]
    "layer",
    [
        "not-a-descriptor",
        {"mediaType": "application/vnd.oci.image.layer.v1.tar+gzip", "size": 1},
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "digest": f"sha256:{'f' * 64}",
            "size": -1,
        },
    ],
)
def test_malformed_layer_descriptor_is_rejected(layer: object) -> None:
    # Arrange
    manifest, _ = _image_payload(OCI_IMAGE_MANIFEST)
    payload = json.loads(manifest)
    payload["layers"] = [layer]
    malformed_manifest = _json_bytes(payload)
    session = _mock_session(
        [_manifest_response(malformed_manifest, OCI_IMAGE_MANIFEST)],
    )
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistryResponseError, match="layer"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")
    assert session.get.call_count == 1


@pytest.mark.parametrize(  # type: ignore[misc]
    "rootfs",
    [
        None,
        {"type": "not-layers", "diff_ids": [f"sha256:{'f' * 64}"]},
        {"type": "layers", "diff_ids": []},
        {"type": "layers", "diff_ids": ["not-a-digest"]},
    ],
)
def test_malformed_config_rootfs_is_rejected(rootfs: object) -> None:
    # Arrange
    manifest, config = _image_payload(OCI_IMAGE_MANIFEST)
    config_payload = json.loads(config)
    if rootfs is None:
        config_payload.pop("rootfs")
    else:
        config_payload["rootfs"] = rootfs
    malformed_config = _json_bytes(config_payload)
    manifest_payload = json.loads(manifest)
    manifest_payload["config"]["digest"] = _digest(malformed_config)
    manifest_payload["config"]["size"] = len(malformed_config)
    malformed_manifest = _json_bytes(manifest_payload)
    client = AnonymousRegistryClient(
        _mock_session(
            [
                _manifest_response(malformed_manifest, OCI_IMAGE_MANIFEST),
                _response(200, malformed_config),
            ],
        ),
    )

    # Act and assert
    with pytest.raises(RegistryResponseError, match="config|rootfs"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")


def test_manifest_list_child_limit_is_enforced_before_child_fetches() -> None:
    # Arrange
    index = _json_bytes(
        {
            "schemaVersion": 2,
            "mediaType": OCI_IMAGE_INDEX,
            "manifests": [
                {
                    "mediaType": OCI_IMAGE_MANIFEST,
                    "digest": f"sha256:{position:064x}",
                    "size": 100,
                    "platform": {"os": "linux", "architecture": "amd64"},
                }
                for position in range(65)
            ],
        },
    )
    session = _mock_session([_manifest_response(index, OCI_IMAGE_INDEX)])
    client = AnonymousRegistryClient(session)

    # Act and assert
    with pytest.raises(RegistryResponseError, match="too many"):
        client.resolve(f"{_REGISTRY}/{_REPOSITORY}:stable")
    assert session.get.call_count == 1
