from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from collections.abc import Mapping
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from typing import Any
from typing import IO
from typing import Literal
from typing import Protocol
from typing import TypeGuard
from urllib.parse import quote
from urllib.parse import urljoin
from urllib.parse import urlsplit

import requests
from requests.adapters import DEFAULT_POOLBLOCK
from requests.adapters import DEFAULT_POOLSIZE
from requests.adapters import DEFAULT_RETRIES
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest
from requests.utils import parse_dict_header
from urllib3 import Retry
from urllib3.connection import HTTPSConnection
from urllib3.connectionpool import HTTPSConnectionPool

from cartography.intel.container_image import ContainerImageReference
from cartography.intel.container_image import parse_container_image_reference

DOCKER_IMAGE_MANIFEST = "application/vnd.docker.distribution.manifest.v2+json"
DOCKER_MANIFEST_LIST = "application/vnd.docker.distribution.manifest.list.v2+json"
OCI_IMAGE_MANIFEST = "application/vnd.oci.image.manifest.v1+json"
OCI_IMAGE_INDEX = "application/vnd.oci.image.index.v1+json"

IMAGE_MANIFEST_MEDIA_TYPES = frozenset({DOCKER_IMAGE_MANIFEST, OCI_IMAGE_MANIFEST})
MANIFEST_LIST_MEDIA_TYPES = frozenset({DOCKER_MANIFEST_LIST, OCI_IMAGE_INDEX})
MANIFEST_MEDIA_TYPES = IMAGE_MANIFEST_MEDIA_TYPES | MANIFEST_LIST_MEDIA_TYPES
MANIFEST_ACCEPT = ", ".join(
    (DOCKER_IMAGE_MANIFEST, DOCKER_MANIFEST_LIST, OCI_IMAGE_MANIFEST, OCI_IMAGE_INDEX),
)

_CONFIG_MEDIA_TYPES = frozenset(
    {
        "application/vnd.docker.container.image.v1+json",
        "application/vnd.oci.image.config.v1+json",
    },
)
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_RETRY_STATUSES = (429, 500, 502, 503, 504)
_DOCKER_API_HOST = "registry-1.docker.io"
_PUBLIC_ECR_AUTHORITY = ("public.ecr.aws", 443)
_MAX_REDIRECTS = 5
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_MAX_CONFIG_BYTES = 16 * 1024 * 1024
_MAX_TOKEN_BYTES = 1024 * 1024
_MAX_INDEX_DESCRIPTORS = 1024
_MAX_MANIFEST_CHILDREN = 64
_MAX_METADATA_VALUE_LENGTH = 128
_MAX_BEARER_TOKEN_LENGTH = 64 * 1024
_MAX_RESOLUTION_SECONDS = 120.0
_WORKER_RESOLUTION_SECONDS = 115.0
_MAX_REQUEST_ATTEMPTS = 4
_RETRY_BACKOFF_SECONDS = 0.5
_DEFAULT_TOTAL_TIMEOUT_SECONDS = 300.0
_WORKER_SHUTDOWN_SECONDS = 1.0


class RegistryError(RuntimeError):
    """Base class for public registry resolution failures."""


class RegistrySecurityError(RegistryError):
    """A registry URL failed HTTPS or public-address validation."""


class RegistryAuthenticationError(RegistryError):
    """Anonymous access was denied or a bearer challenge was invalid."""


class RegistryNotFoundError(RegistryError):
    """The requested registry object does not exist."""


class RegistryRateLimitError(RegistryError):
    """The registry rate-limited the request after retries."""


class RegistryTransientError(RegistryError):
    """A transient network or registry failure exhausted retries."""


class RegistryResponseError(RegistryError):
    """The registry returned malformed or unverifiable content."""


class RegistryUnsupportedArtifactError(RegistryResponseError):
    """The referenced object is not a runnable image or image index."""


@dataclass(frozen=True, slots=True)
class ResolvedRegistryArtifact:
    digest: str
    media_type: str
    type: Literal["image", "manifest_list"]
    size: int
    os: str | None = None
    architecture: str | None = None
    variant: str | None = None
    config_digest: str | None = None
    created_at: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedRegistryReference:
    reference: ContainerImageReference
    top: ResolvedRegistryArtifact
    children: tuple[ResolvedRegistryArtifact, ...] = ()


class RegistryClient(Protocol):
    def resolve(
        self,
        reference: str | ContainerImageReference,
    ) -> ResolvedRegistryReference:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class _Platform:
    os: str
    architecture: str
    variant: str | None
    created_at: str | None


class _PinnedHTTPSConnection(HTTPSConnection):
    """Keep TLS hostname verification while connecting to a vetted IP."""

    def __init__(self, *args: Any, pinned_address: str, **kwargs: Any) -> None:
        self._pinned_address = pinned_address
        super().__init__(*args, **kwargs)

    def _new_conn(self) -> socket.socket:
        dns_host = self._dns_host
        self._dns_host = self._pinned_address
        try:
            return super()._new_conn()
        finally:
            self._dns_host = dns_host


class _PinnedHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _PinnedHTTPSConnection


class _PinnedHTTPSAdapter(HTTPAdapter):
    """Pin each pool to the public IP vetted immediately before connecting."""

    def __init__(
        self,
        pool_connections: int = DEFAULT_POOLSIZE,
        pool_maxsize: int = DEFAULT_POOLSIZE,
        max_retries: int | Retry = DEFAULT_RETRIES,
        pool_block: bool = DEFAULT_POOLBLOCK,
    ) -> None:
        super().__init__(pool_connections, pool_maxsize, max_retries, pool_block)
        self._pinned_pool_connections = max(1, pool_connections)
        self._pinned_pool_maxsize = pool_maxsize
        self._pinned_pool_block = pool_block
        self._pinned_pools: OrderedDict[
            tuple[str, int, str, str, str],
            _PinnedHTTPSConnectionPool,
        ] = OrderedDict()

    def get_connection_with_tls_context(
        self,
        request: PreparedRequest,
        verify: bool | str | None,
        proxies: Mapping[str, str] | None = None,
        cert: str | tuple[str, str] | None = None,
    ) -> HTTPSConnectionPool:
        if proxies and any(proxies.values()):
            raise RegistrySecurityError("registry requests may not use a proxy")
        if request.url is None:
            raise RegistrySecurityError("registry URL is missing")
        pool_verify = True if verify is None else verify
        host_params, pool_kwargs = self.build_connection_pool_key_attributes(
            request,
            pool_verify,
            cert,
        )
        host = host_params.get("host")
        port = host_params.get("port") or 443
        if host_params.get("scheme") != "https" or not isinstance(host, str):
            raise RegistrySecurityError("registry URL must use HTTPS")
        if not isinstance(port, int):
            raise RegistrySecurityError("registry URL has an invalid port")
        address = _resolve_public_https_url(request.url)
        key = (host, port, address, str(verify), str(cert))
        pool = self._pinned_pools.pop(key, None)
        if pool is None:
            pool = _PinnedHTTPSConnectionPool(
                host,
                port,
                maxsize=self._pinned_pool_maxsize,
                block=self._pinned_pool_block,
                pinned_address=address,
                **pool_kwargs,
            )
            if len(self._pinned_pools) >= self._pinned_pool_connections:
                _, evicted_pool = self._pinned_pools.popitem(last=False)
                evicted_pool.close()
        self._pinned_pools[key] = pool
        return pool

    def close(self) -> None:
        for pool in self._pinned_pools.values():
            pool.close()
        self._pinned_pools.clear()
        super().close()


class _AnonymousRegistryClient:
    """Resolve anonymous public Docker/OCI references without fetching layers."""

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: tuple[float, float] = (5.0, 30.0),
        resolution_timeout_seconds: float = _MAX_RESOLUTION_SECONDS,
    ) -> None:
        self._session = session or requests.Session()
        self._session.trust_env = False
        self._session.auth = None
        self._session.cert = None
        self._session.verify = True
        self._session.headers.clear()
        self._session.cookies.clear()
        self._session.params = {}
        self._session.proxies.clear()
        self._session.hooks = {"response": []}
        self._session.adapters.clear()
        self._timeout = timeout
        self._resolution_timeout_seconds = max(0.0, resolution_timeout_seconds)
        self._resolve_deadline: float | None = None
        # Retry here, outside urllib3, so retryable response bodies cannot be
        # drained indefinitely before the resolution deadline is checked.
        self._session.mount("https://", _PinnedHTTPSAdapter(max_retries=0))
        self._manifest_cache: dict[
            tuple[str, str, str],
            tuple[ResolvedRegistryArtifact, tuple[dict[str, Any], ...]],
        ] = {}
        self._config_cache: dict[
            tuple[str, str, str],
            tuple[_Platform, int, int],
        ] = {}

    def __enter__(self) -> _AnonymousRegistryClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._session.close()

    def resolve(
        self,
        reference: str | ContainerImageReference,
    ) -> ResolvedRegistryReference:
        self._resolve_deadline = time.monotonic() + self._resolution_timeout_seconds
        try:
            parsed = (
                parse_container_image_reference(reference)
                if isinstance(reference, str)
                else reference
            )
            api_host = (
                _DOCKER_API_HOST if parsed.registry == "docker.io" else parsed.registry
            )
            top, descriptors, token = self._fetch_manifest(
                api_host,
                parsed.repository,
                parsed.selector,
                None,
            )
            if top.type == "image":
                return ResolvedRegistryReference(parsed, top)

            children: list[ResolvedRegistryArtifact] = []
            for descriptor in descriptors:
                digest, size, media_type, platform = _parse_child_descriptor(descriptor)
                try:
                    child, nested, token = self._fetch_manifest(
                        api_host,
                        parsed.repository,
                        digest,
                        token,
                        expected_size=size,
                        expected_media_type=media_type,
                        descriptor_platform=platform,
                    )
                except RegistryUnsupportedArtifactError:
                    # OCI indexes may mix runnable images with attestation manifests
                    # whose non-runnable nature is only visible after fetching them.
                    continue
                if child.type != "image" or nested:
                    raise RegistryUnsupportedArtifactError(
                        "manifest list child is not a runnable image manifest",
                    )
                children.append(child)
            if not children:
                raise RegistryUnsupportedArtifactError(
                    "manifest list contains no runnable image manifests",
                )
            return ResolvedRegistryReference(parsed, top, tuple(children))
        finally:
            self._resolve_deadline = None

    def _fetch_manifest(
        self,
        host: str,
        repository: str,
        selector: str,
        token: str | None,
        *,
        expected_size: int | None = None,
        expected_media_type: str | None = None,
        descriptor_platform: dict[str, str] | None = None,
    ) -> tuple[
        ResolvedRegistryArtifact,
        tuple[dict[str, Any], ...],
        str | None,
    ]:
        if expected_size is not None and expected_size > _MAX_MANIFEST_BYTES:
            raise RegistryResponseError("manifest exceeds the response size limit")
        if selector.startswith("sha256:"):
            cached = self._manifest_cache.get((host, repository, selector))
            if cached is not None:
                _validate_cached_manifest(cached[0], expected_size, expected_media_type)
                return (
                    _with_descriptor_platform(cached[0], descriptor_platform),
                    cached[1],
                    token,
                )

        url = (
            f"https://{host}/v2/{quote(repository, safe='/')}/manifests/"
            f"{quote(selector, safe=':')}"
        )
        response, token = self._get_authenticated(
            url,
            repository,
            token,
            {"Accept": MANIFEST_ACCEPT},
        )
        try:
            raw = _read_body(
                response,
                "manifest",
                _MAX_MANIFEST_BYTES,
                self._resolve_deadline,
            )
            canonical_digest = _canonical_digest(response, raw, selector)
            if expected_size is not None and len(raw) != expected_size:
                raise RegistryResponseError(
                    "manifest descriptor size does not match content",
                )

            cached = self._manifest_cache.get((host, repository, canonical_digest))
            if cached is not None:
                _validate_cached_manifest(cached[0], expected_size, expected_media_type)
                return (
                    _with_descriptor_platform(cached[0], descriptor_platform),
                    cached[1],
                    token,
                )

            payload = _json_object(raw, "manifest")
            if payload.get("schemaVersion") != 2:
                raise RegistryResponseError("manifest schemaVersion must be 2")
            media_type = _manifest_media_type(response, payload)
            if expected_media_type is not None and media_type != expected_media_type:
                raise RegistryResponseError(
                    "manifest media type does not match descriptor"
                )
            if payload.get("artifactType") is not None:
                raise RegistryUnsupportedArtifactError(
                    "OCI artifact is not a runnable image",
                )

            if media_type in MANIFEST_LIST_MEDIA_TYPES:
                raw_descriptors = payload.get("manifests")
                if not isinstance(raw_descriptors, list):
                    raise RegistryResponseError("manifest list has no descriptor list")
                if len(raw_descriptors) > _MAX_INDEX_DESCRIPTORS:
                    raise RegistryResponseError(
                        "manifest list has too many descriptors"
                    )
                if any(
                    not isinstance(descriptor, dict) for descriptor in raw_descriptors
                ):
                    raise RegistryResponseError(
                        "manifest list contains a malformed descriptor",
                    )
                # OCI requires unknown descriptor media types to be tolerated. Do
                # not retain them in the shared immutable-manifest cache.
                descriptors = tuple(
                    descriptor
                    for descriptor in raw_descriptors
                    if not _is_attestation_descriptor(descriptor)
                    and isinstance(descriptor.get("mediaType"), str)
                    and descriptor["mediaType"] in IMAGE_MANIFEST_MEDIA_TYPES
                )
                if len(descriptors) > _MAX_MANIFEST_CHILDREN:
                    raise RegistryResponseError(
                        "manifest list has too many runnable children"
                    )
                artifact = ResolvedRegistryArtifact(
                    digest=canonical_digest,
                    media_type=media_type,
                    type="manifest_list",
                    size=len(raw),
                )
            else:
                artifact, token = self._parse_image_manifest(
                    host,
                    repository,
                    canonical_digest,
                    media_type,
                    raw,
                    payload,
                    token,
                )
                descriptors = ()
        finally:
            response.close()

        result = (artifact, descriptors)
        self._manifest_cache[(host, repository, canonical_digest)] = result
        return (
            _with_descriptor_platform(artifact, descriptor_platform),
            descriptors,
            token,
        )

    def _parse_image_manifest(
        self,
        host: str,
        repository: str,
        digest: str,
        media_type: str,
        raw: bytes,
        payload: dict[str, Any],
        token: str | None,
    ) -> tuple[ResolvedRegistryArtifact, str | None]:
        config = payload.get("config")
        layers = payload.get("layers")
        if not isinstance(config, dict) or not isinstance(layers, list):
            raise RegistryResponseError("image manifest is missing config or layers")
        config_media_type = config.get("mediaType")
        if (
            not isinstance(config_media_type, str)
            or config_media_type not in _CONFIG_MEDIA_TYPES
        ):
            raise RegistryUnsupportedArtifactError(
                "unsupported image config media type"
            )
        for layer in layers:
            if not isinstance(layer, dict):
                raise RegistryResponseError("image manifest has a malformed layer")
            layer_media_type = layer.get("mediaType")
            if not isinstance(layer_media_type, str) or not layer_media_type:
                raise RegistryResponseError("image manifest has a malformed layer")
            if "in-toto" in layer_media_type.lower():
                raise RegistryUnsupportedArtifactError(
                    "attestation is not a runnable image"
                )
            _required_digest(layer.get("digest"), "layer")
            _required_size(layer.get("size"), "layer")
        config_digest = _required_digest(config.get("digest"), "config")
        config_size = _required_size(config.get("size"), "config")
        platform, token = self._fetch_config(
            host,
            repository,
            config_digest,
            config_size,
            len(layers),
            token,
        )
        if platform.os == "unknown" or platform.architecture == "unknown":
            raise RegistryUnsupportedArtifactError(
                "unknown-platform artifact is not runnable"
            )
        return (
            ResolvedRegistryArtifact(
                digest=digest,
                media_type=media_type,
                type="image",
                size=len(raw),
                os=platform.os,
                architecture=platform.architecture,
                variant=platform.variant,
                config_digest=config_digest,
                created_at=platform.created_at,
            ),
            token,
        )

    def _fetch_config(
        self,
        host: str,
        repository: str,
        digest: str,
        expected_size: int,
        expected_layer_count: int,
        token: str | None,
    ) -> tuple[_Platform, str | None]:
        if expected_size > _MAX_CONFIG_BYTES:
            raise RegistryResponseError("config exceeds the response size limit")
        key = (host, repository, digest)
        cached = self._config_cache.get(key)
        if cached is not None:
            if cached[1] != expected_size:
                raise RegistryResponseError("config descriptor size changed")
            if cached[2] != expected_layer_count:
                raise RegistryResponseError(
                    "config rootfs does not match manifest layers"
                )
            return cached[0], token

        url = f"https://{host}/v2/{quote(repository, safe='/')}/blobs/{quote(digest, safe=':')}"
        response, token = self._get_authenticated(url, repository, token)
        try:
            raw = _read_body(
                response,
                "config",
                _MAX_CONFIG_BYTES,
                self._resolve_deadline,
            )
            _verify_digest(raw, digest, "config")
            if len(raw) != expected_size:
                raise RegistryResponseError(
                    "config descriptor size does not match content"
                )
            payload = _json_object(raw, "config")
        finally:
            response.close()
        os_name = payload.get("os")
        architecture = payload.get("architecture")
        variant = payload.get("variant")
        created_at = payload.get("created")
        rootfs = payload.get("rootfs")
        diff_ids = rootfs.get("diff_ids") if isinstance(rootfs, dict) else None
        if (
            not _is_metadata_string(os_name)
            or not _is_metadata_string(architecture)
            or (variant is not None and not _is_metadata_string(variant))
            or (created_at is not None and not _is_metadata_string(created_at))
            or not isinstance(rootfs, dict)
            or rootfs.get("type") != "layers"
            or not isinstance(diff_ids, list)
            or len(diff_ids) != expected_layer_count
        ):
            raise RegistryResponseError("image config is malformed")
        for diff_id in diff_ids:
            _required_digest(diff_id, "rootfs layer")
        platform = _Platform(os_name, architecture, variant, created_at)
        self._config_cache[key] = (platform, len(raw), len(diff_ids))
        return platform, token

    def _get_authenticated(
        self,
        url: str,
        repository: str,
        token: str | None,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[requests.Response, str | None]:
        headers = {"User-Agent": "cartography"}
        if extra_headers:
            headers.update(extra_headers)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self._get(url, headers=headers)
        if response.status_code != 401:
            _raise_for_status(response, url)
            return response, token

        challenge = response.headers.get("WWW-Authenticate", "")
        challenged_url = response.url or url
        response.close()
        if _authority(challenged_url) != _authority(url):
            raise RegistryAuthenticationError(
                "cross-host registry redirect requires authentication",
            )
        token = self._fetch_bearer_token(
            challenge,
            repository,
            allow_public_ecr_scope=_authority(url) == _PUBLIC_ECR_AUTHORITY,
        )
        headers["Authorization"] = f"Bearer {token}"
        response = self._get(url, headers=headers)
        _raise_for_status(response, url)
        return response, token

    def _fetch_bearer_token(
        self,
        challenge: str,
        repository: str,
        *,
        allow_public_ecr_scope: bool,
    ) -> str:
        scheme, separator, parameters = challenge.partition(" ")
        if not separator or scheme.lower() != "bearer":
            raise RegistryAuthenticationError(
                "registry did not offer Bearer authentication"
            )
        values = parse_dict_header(parameters)
        realm = values.get("realm")
        if not isinstance(realm, str) or not realm:
            raise RegistryAuthenticationError("registry Bearer challenge has no realm")

        requested_scope = f"repository:{repository}:pull"
        challenge_scope = values.get("scope")
        if challenge_scope is not None:
            if not isinstance(challenge_scope, str):
                raise RegistryAuthenticationError(
                    "registry Bearer challenge has invalid scope",
                )
            if allow_public_ecr_scope and challenge_scope == "aws":
                requested_scope = challenge_scope
            else:
                scope_parts = challenge_scope.split(":", 2)
                if (
                    len(scope_parts) != 3
                    or scope_parts[0] != "repository"
                    or scope_parts[1] != repository
                    or "pull" not in scope_parts[2].split(",")
                ):
                    raise RegistryAuthenticationError(
                        "registry Bearer challenge has invalid scope"
                    )
        query = {"scope": requested_scope, "client_id": "cartography"}
        service = values.get("service")
        if service:
            if not isinstance(service, str):
                raise RegistryAuthenticationError(
                    "registry Bearer challenge has invalid service",
                )
            query["service"] = service
        response = self._get(
            realm,
            headers={"User-Agent": "cartography"},
            params=query,
        )
        _raise_for_status(response, realm)
        try:
            payload = _json_object(
                _read_body(
                    response,
                    "token response",
                    _MAX_TOKEN_BYTES,
                    self._resolve_deadline,
                ),
                "token response",
            )
        finally:
            response.close()
        token = payload.get("token")
        access_token = payload.get("access_token")
        if token is not None and access_token is not None and token != access_token:
            raise RegistryAuthenticationError(
                "token response contains conflicting tokens"
            )
        result = token or access_token
        if (
            not isinstance(result, str)
            or not result
            or len(result) > _MAX_BEARER_TOKEN_LENGTH
        ):
            raise RegistryAuthenticationError(
                "token response contains an invalid token"
            )
        return result

    def _get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str] | None = None,
    ) -> requests.Response:
        current_url = url
        current_headers = headers.copy()
        current_params = params
        for _ in range(_MAX_REDIRECTS + 1):
            _assert_public_https_url(current_url)
            response = self._request_with_retries(
                current_url,
                headers=current_headers,
                params=current_params,
            )
            if response.status_code not in _REDIRECT_STATUSES:
                return response
            location = response.headers.get("Location")
            if not location:
                response.close()
                raise RegistryResponseError("registry redirect has no location")
            try:
                next_url = urljoin(response.url or current_url, location)
                crosses_host = _authority(next_url) != _authority(current_url)
            except ValueError as error:
                raise RegistrySecurityError("registry URL is malformed") from error
            finally:
                response.close()
            if crosses_host:
                current_headers.pop("Authorization", None)
            current_url = next_url
            current_params = None
        raise RegistryResponseError("registry returned too many redirects")

    def _request_with_retries(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str] | None,
    ) -> requests.Response:
        for attempt in range(_MAX_REQUEST_ATTEMPTS):
            try:
                self._session.cookies.clear()
                response = self._session.get(
                    url,
                    headers=headers.copy(),
                    params=params,
                    timeout=self._request_timeout(),
                    allow_redirects=False,
                    stream=True,
                )
            except requests.RequestException:
                if attempt == _MAX_REQUEST_ATTEMPTS - 1:
                    raise RegistryTransientError(
                        f"registry network request failed for {_safe_url(url)}",
                    ) from None
            else:
                self._session.cookies.clear()
                if (
                    response.status_code not in _RETRY_STATUSES
                    or attempt == _MAX_REQUEST_ATTEMPTS - 1
                ):
                    return response
                response.close()
            self._wait_before_retry(attempt)
        raise AssertionError("unreachable")

    def _wait_before_retry(self, attempt: int) -> None:
        delay = _RETRY_BACKOFF_SECONDS * 2**attempt
        remaining = _remaining_resolution_time(self._resolve_deadline)
        if remaining is not None and delay >= remaining:
            raise RegistryTransientError("registry resolution exceeded time limit")
        time.sleep(delay)

    def _request_timeout(self) -> tuple[float, float]:
        remaining = _remaining_resolution_time(self._resolve_deadline)
        if remaining is None:
            return self._timeout
        return min(self._timeout[0], remaining), min(self._timeout[1], remaining)


_WORKER_ERROR_TYPES = {
    error_type.__name__: error_type
    for error_type in (
        RegistrySecurityError,
        RegistryAuthenticationError,
        RegistryNotFoundError,
        RegistryRateLimitError,
        RegistryTransientError,
        RegistryResponseError,
        RegistryUnsupportedArtifactError,
    )
}


def _registry_worker_main() -> None:
    with _AnonymousRegistryClient(
        resolution_timeout_seconds=_WORKER_RESOLUTION_SECONDS,
    ) as client:
        for line in sys.stdin:
            command = json.loads(line)
            reference = command.get("reference")
            if not isinstance(reference, str):
                raise ValueError("registry worker received an invalid reference")
            try:
                resolved = client.resolve(reference)
            except RegistryError as error:
                response = {
                    "error": {
                        "type": type(error).__name__,
                        "message": str(error),
                    },
                }
            else:
                response = {"result": _resolved_reference_payload(resolved)}
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def _read_worker_response(stream: IO[str], output: list[str]) -> None:
    try:
        output.append(stream.readline())
    except (OSError, ValueError):
        output.append("")


class AnonymousRegistryClient:
    """Resolve public registry references behind a killable wall-clock boundary."""

    def __init__(
        self,
        resolution_timeout_seconds: float = _MAX_RESOLUTION_SECONDS,
        total_timeout_seconds: float | None = _DEFAULT_TOTAL_TIMEOUT_SECONDS,
        *,
        _worker_command: Sequence[str] | None = None,
    ) -> None:
        self._resolution_timeout_seconds = max(0.0, resolution_timeout_seconds)
        self._total_timeout_seconds = (
            max(0.0, total_timeout_seconds)
            if total_timeout_seconds is not None
            else None
        )
        self._overall_deadline: float | None = None
        self._worker_command = tuple(_worker_command) if _worker_command else None
        self._process: subprocess.Popen[str] | None = None

    def __enter__(self) -> AnonymousRegistryClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._stop_worker(graceful=True)

    def resolve(
        self,
        reference: str | ContainerImageReference,
    ) -> ResolvedRegistryReference:
        parsed = (
            parse_container_image_reference(reference)
            if isinstance(reference, str)
            else reference
        )
        deadline = self._resolution_deadline()
        if self._process is None:
            try:
                self._start_worker()
            except Exception:
                raise RegistryTransientError(
                    "registry resolver worker failed to start",
                ) from None
        process = self._process
        if process is None or process.stdin is None or process.stdout is None:
            raise RegistryTransientError("registry resolver worker failed to start")
        try:
            process.stdin.write(
                json.dumps({"reference": parsed.original}, separators=(",", ":"))
                + "\n",
            )
            process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            self._stop_worker(graceful=False)
            raise RegistryTransientError("registry resolver worker failed") from None

        output: list[str] = []
        receiver = threading.Thread(
            target=_read_worker_response,
            args=(process.stdout, output),
            daemon=True,
        )
        receiver.start()
        receiver.join(max(0.0, deadline - time.monotonic()))
        if receiver.is_alive():
            self._stop_worker(graceful=False)
            receiver.join(_WORKER_SHUTDOWN_SECONDS)
            raise RegistryTransientError(
                "registry resolution exceeded wall-clock time limit",
            )
        if not output or not output[0]:
            self._stop_worker(graceful=False)
            raise RegistryTransientError("registry resolver worker failed")
        try:
            result = _decode_worker_response(output[0])
        except (KeyError, TypeError, ValueError):
            self._stop_worker(graceful=False)
            raise RegistryTransientError(
                "registry resolver worker returned invalid data",
            ) from None
        if isinstance(result, RegistryError):
            raise result
        return result

    def _resolution_deadline(self) -> float:
        now = time.monotonic()
        if self._overall_deadline is None and self._total_timeout_seconds is not None:
            self._overall_deadline = now + self._total_timeout_seconds
        deadline = now + self._resolution_timeout_seconds
        if self._overall_deadline is not None:
            deadline = min(deadline, self._overall_deadline)
        if deadline <= now:
            raise RegistryTransientError(
                "registry resolution exceeded wall-clock time limit",
            )
        return deadline

    def _start_worker(self) -> None:
        command = self._worker_command or (
            sys.executable,
            "-m",
            "cartography.client.container_registry",
            "--worker",
        )
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            shell=False,
        )

    def _stop_worker(self, *, graceful: bool) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        try:
            if graceful and process.poll() is None and process.stdin is not None:
                with suppress(OSError, ValueError):
                    process.stdin.close()
                with suppress(subprocess.TimeoutExpired):
                    process.wait(_WORKER_SHUTDOWN_SECONDS)
            if process.poll() is None:
                with suppress(OSError):
                    process.terminate()
                with suppress(subprocess.TimeoutExpired):
                    process.wait(_WORKER_SHUTDOWN_SECONDS)
            if process.poll() is None:
                with suppress(OSError):
                    process.kill()
                with suppress(subprocess.TimeoutExpired):
                    process.wait(_WORKER_SHUTDOWN_SECONDS)
        finally:
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    with suppress(OSError, ValueError):
                        stream.close()


def _resolved_reference_payload(
    resolved: ResolvedRegistryReference,
) -> dict[str, Any]:
    return {
        "reference": asdict(resolved.reference),
        "top": asdict(resolved.top),
        "children": [asdict(child) for child in resolved.children],
    }


def _decode_worker_response(
    line: str,
) -> ResolvedRegistryReference | RegistryError:
    response = json.loads(line)
    if not isinstance(response, dict):
        raise ValueError("registry worker response is not an object")
    error = response.get("error")
    if error is not None:
        if not isinstance(error, dict):
            raise ValueError("registry worker error is malformed")
        raw_error_type = error.get("type")
        message = error.get("message")
        if not isinstance(raw_error_type, str) or not isinstance(message, str):
            raise ValueError("registry worker error is malformed")
        error_type = _WORKER_ERROR_TYPES.get(raw_error_type)
        if error_type is None:
            raise ValueError("registry worker error is malformed")
        return error_type(message)
    result = response.get("result")
    if not isinstance(result, dict):
        raise ValueError("registry worker result is malformed")
    reference = result.get("reference")
    top = result.get("top")
    children = result.get("children")
    if (
        not isinstance(reference, dict)
        or not isinstance(top, dict)
        or not isinstance(children, list)
        or any(not isinstance(child, dict) for child in children)
    ):
        raise ValueError("registry worker result is malformed")
    return ResolvedRegistryReference(
        ContainerImageReference(**reference),
        ResolvedRegistryArtifact(**top),
        tuple(ResolvedRegistryArtifact(**child) for child in children),
    )


def _manifest_media_type(
    response: requests.Response,
    payload: dict[str, Any],
) -> str:
    header = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    declared = payload.get("mediaType")
    if declared is not None and not isinstance(declared, str):
        raise RegistryResponseError("manifest mediaType is malformed")
    if declared:
        declared = declared.lower()
        if declared not in MANIFEST_MEDIA_TYPES:
            raise RegistryUnsupportedArtifactError(
                f"unsupported manifest media type: {declared}",
            )
        if header in MANIFEST_MEDIA_TYPES and header != declared:
            raise RegistryResponseError(
                "manifest Content-Type disagrees with mediaType"
            )
        return declared
    if header not in MANIFEST_MEDIA_TYPES:
        raise RegistryUnsupportedArtifactError(
            f"unsupported manifest media type: {header or 'missing'}",
        )
    return header


def _parse_child_descriptor(
    descriptor: dict[str, Any],
) -> tuple[str, int, str, dict[str, str] | None]:
    digest = _required_digest(descriptor.get("digest"), "manifest")
    size = _required_size(descriptor.get("size"), "manifest")
    media_type = descriptor.get("mediaType")
    if not isinstance(media_type, str) or media_type not in IMAGE_MANIFEST_MEDIA_TYPES:
        raise RegistryUnsupportedArtifactError("unsupported manifest-list child type")
    raw_platform = descriptor.get("platform")
    if raw_platform is None:
        return digest, size, media_type, None
    if not isinstance(raw_platform, dict):
        raise RegistryResponseError("manifest descriptor platform is malformed")
    platform: dict[str, str] = {}
    for field in ("os", "architecture", "variant"):
        value = raw_platform.get(field)
        if value is not None:
            if not _is_metadata_string(value):
                raise RegistryResponseError("manifest descriptor platform is malformed")
            platform[field] = value
    return digest, size, media_type, platform or None


def _is_attestation_descriptor(descriptor: dict[str, Any]) -> bool:
    annotations = descriptor.get("annotations")
    annotations = annotations if isinstance(annotations, dict) else {}
    platform = descriptor.get("platform")
    platform = platform if isinstance(platform, dict) else {}
    artifact_type = descriptor.get("artifactType")
    return (
        (
            artifact_type is not None
            and (
                not isinstance(artifact_type, str)
                or artifact_type not in _CONFIG_MEDIA_TYPES
            )
        )
        or annotations.get("vnd.docker.reference.type") == "attestation-manifest"
        or "vnd.docker.reference.digest" in annotations
        or (
            platform.get("os") == "unknown"
            and platform.get("architecture") == "unknown"
        )
    )


def _is_metadata_string(value: object) -> TypeGuard[str]:
    return (
        isinstance(value, str)
        and bool(value)
        and len(value) <= _MAX_METADATA_VALUE_LENGTH
    )


def _remaining_resolution_time(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RegistryTransientError("registry resolution exceeded time limit")
    return remaining


def _read_body(
    response: requests.Response,
    object_name: str,
    limit: int,
    deadline: float | None = None,
) -> bytes:
    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError:
            raise RegistryResponseError(
                f"{object_name} has an invalid Content-Length",
            ) from None
        if declared_length < 0 or declared_length > limit:
            raise RegistryResponseError(
                f"{object_name} exceeds the response size limit"
            )
    chunks: list[bytes] = []
    size = 0
    try:
        _remaining_resolution_time(deadline)
        for chunk in response.iter_content(chunk_size=64 * 1024):
            _remaining_resolution_time(deadline)
            if not chunk:
                continue
            size += len(chunk)
            if size > limit:
                raise RegistryResponseError(
                    f"{object_name} exceeds the response size limit",
                )
            chunks.append(chunk)
        _remaining_resolution_time(deadline)
    except requests.RequestException:
        raise RegistryTransientError(f"failed reading {object_name} response") from None
    return b"".join(chunks)


def _with_descriptor_platform(
    artifact: ResolvedRegistryArtifact,
    expected: dict[str, str] | None,
) -> ResolvedRegistryArtifact:
    if expected is None:
        return artifact
    if artifact.type != "image" or artifact.os is None or artifact.architecture is None:
        raise RegistryResponseError("manifest descriptor platform has no image config")
    for field in ("os", "architecture", "variant"):
        wanted = expected.get(field)
        got = getattr(artifact, field)
        if wanted is not None and got is not None and wanted != got:
            raise RegistryResponseError(
                "manifest descriptor platform disagrees with config"
            )
    return replace(
        artifact,
        os=expected.get("os", artifact.os),
        architecture=expected.get("architecture", artifact.architecture),
        variant=expected.get("variant", artifact.variant),
    )


def _canonical_digest(response: requests.Response, raw: bytes, selector: str) -> str:
    if selector.startswith("sha256:"):
        _verify_digest(raw, selector, "manifest")
    header_digest = response.headers.get("Docker-Content-Digest")
    if header_digest:
        header_digest = _required_digest(header_digest, "manifest")
        _verify_digest(raw, header_digest, "manifest")
    return header_digest or (
        selector if selector.startswith("sha256:") else _sha256_digest(raw)
    )


def _verify_digest(raw: bytes, expected: str, object_name: str) -> None:
    if _sha256_digest(raw) != _required_digest(expected, object_name):
        raise RegistryResponseError(f"{object_name} digest does not match content")


def _sha256_digest(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _required_digest(value: object, object_name: str) -> str:
    if not isinstance(value, str):
        raise RegistryResponseError(f"{object_name} descriptor has no digest")
    algorithm, separator, encoded = value.partition(":")
    if (
        not separator
        or algorithm.lower() != "sha256"
        or len(encoded) != 64
        or any(char not in "0123456789abcdefABCDEF" for char in encoded)
    ):
        raise RegistryResponseError(f"{object_name} descriptor has an invalid digest")
    return f"sha256:{encoded.lower()}"


def _required_size(value: object, object_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RegistryResponseError(f"{object_name} descriptor has an invalid size")
    return value


def _json_object(raw: bytes, object_name: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (ValueError, RecursionError):
        raise RegistryResponseError(f"{object_name} is not valid JSON") from None
    if not isinstance(value, dict):
        raise RegistryResponseError(f"{object_name} is not a JSON object")
    return value


def _validate_cached_manifest(
    artifact: ResolvedRegistryArtifact,
    expected_size: int | None,
    expected_media_type: str | None,
) -> None:
    if expected_size is not None and artifact.size != expected_size:
        raise RegistryResponseError("cached manifest size does not match descriptor")
    if expected_media_type is not None and artifact.media_type != expected_media_type:
        raise RegistryResponseError("cached manifest type does not match descriptor")


def _https_host_and_port(url: str) -> tuple[str, int]:
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port if parsed.port is not None else 443
    except ValueError as error:
        raise RegistrySecurityError("registry URL is malformed") from error
    if (
        parsed.scheme.lower() != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or port == 0
    ):
        raise RegistrySecurityError(
            "registry URL must be an HTTPS URL without credentials"
        )
    return hostname, port


def _assert_public_https_url(url: str) -> None:
    hostname, _ = _https_host_and_port(url)
    try:
        address = ipaddress.ip_address(hostname.split("%", 1)[0])
    except ValueError:
        return
    if not address.is_global:
        raise RegistrySecurityError("registry host resolved to a non-public address")


def _resolve_public_https_url(url: str) -> str:
    hostname, port = _https_host_and_port(url)
    try:
        addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except OSError:
        raise RegistrySecurityError(
            "registry host could not be safely resolved"
        ) from None
    if not addresses:
        raise RegistrySecurityError("registry host resolved to no addresses")
    public_addresses: list[str] = []
    for address in addresses:
        raw_address = address[4][0]
        if not isinstance(raw_address, str):
            raise RegistrySecurityError("registry host resolved to an invalid address")
        try:
            ip = ipaddress.ip_address(raw_address.split("%", 1)[0])
        except ValueError:
            raise RegistrySecurityError(
                "registry host resolved to an invalid address"
            ) from None
        if not ip.is_global:
            raise RegistrySecurityError(
                "registry host resolves to a non-public address"
            )
        public_addresses.append(ip.compressed)
    return public_addresses[0]


def _authority(url: str) -> tuple[str | None, int]:
    try:
        parsed = urlsplit(url)
        return parsed.hostname, parsed.port if parsed.port is not None else 443
    except ValueError as error:
        raise RegistrySecurityError("registry URL is malformed") from error


def _safe_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def _raise_for_status(response: requests.Response, url: str) -> None:
    status = response.status_code
    if 200 <= status < 300:
        return
    message = f"registry returned HTTP {status} for {_safe_url(url)}"
    response.close()
    if status in (401, 403):
        raise RegistryAuthenticationError(message)
    if status == 404:
        raise RegistryNotFoundError(message)
    if status == 429:
        raise RegistryRateLimitError(message)
    if 500 <= status < 600:
        raise RegistryTransientError(message)
    raise RegistryResponseError(message)


if __name__ == "__main__":
    if sys.argv[1:] != ["--worker"]:
        raise SystemExit(2)
    _registry_worker_main()
