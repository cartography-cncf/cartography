from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

_AZURE_DOCKER_PREFIX = "DOCKER|"
_DEFAULT_REGISTRY = "docker.io"
_DOCKER_REGISTRY_ALIASES = frozenset(
    {"docker.io", "index.docker.io", "registry-1.docker.io"},
)
_NAME_COMPONENT = r"[a-z0-9]+(?:(?:[._]|__|[-]+)[a-z0-9]+)*"
_REPOSITORY_RE = re.compile(rf"{_NAME_COMPONENT}(?:/{_NAME_COMPONENT})*")
_TAG_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")
_SHA256_RE = re.compile(r"sha256:[A-Fa-f0-9]{64}")
_DNS_LABEL_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


@dataclass(frozen=True, slots=True)
class ContainerImageReference:
    """A normalized Docker/OCI image reference."""

    original: str
    registry: str
    repository: str
    tag: str | None
    digest: str | None
    normalized: str
    selector: str


def parse_container_image_reference(raw: str) -> ContainerImageReference:
    """Strictly parse a Docker-compatible image reference.

    Unqualified names use Docker Hub, the ``library`` namespace, and the
    ``latest`` tag. A digest remains the immutable selector when both a tag and
    digest are present, while both values are retained for graph provenance.
    """
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        raise ValueError("container image reference must be a non-empty string")
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in raw):
        raise ValueError("container image reference contains whitespace or controls")
    if "://" in raw or "?" in raw or "#" in raw or raw.count("@") > 1:
        raise ValueError("container image reference contains unsupported URL syntax")

    name_and_tag, separator, digest_candidate = raw.partition("@")
    digest: str | None
    if separator:
        if not _SHA256_RE.fullmatch(digest_candidate):
            raise ValueError("container image digest must be a sha256 digest")
        digest = digest_candidate.lower()
    else:
        digest = None

    last_slash = name_and_tag.rfind("/")
    last_colon = name_and_tag.rfind(":")
    if last_colon > last_slash:
        name = name_and_tag[:last_colon]
        tag = name_and_tag[last_colon + 1 :]
        if not _TAG_RE.fullmatch(tag):
            raise ValueError("invalid container image tag")
    else:
        name = name_and_tag
        tag = None

    if not name or len(name) > 255:
        raise ValueError("invalid container image repository")
    first, slash, remainder = name.partition("/")
    has_registry = "." in first or ":" in first or first.lower() == "localhost"
    if has_registry:
        if not slash or not remainder:
            raise ValueError("container image repository is missing")
        registry = _normalize_registry(first)
        repository = remainder
    else:
        registry = _DEFAULT_REGISTRY
        repository = name

    if not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError("invalid container image repository")
    if registry == _DEFAULT_REGISTRY and "/" not in repository:
        repository = f"library/{repository}"
    if tag is None and digest is None:
        tag = "latest"

    normalized = f"{registry}/{repository}"
    if tag is not None:
        normalized += f":{tag}"
    if digest is not None:
        normalized += f"@{digest}"
    return ContainerImageReference(
        original=raw,
        registry=registry,
        repository=repository,
        tag=tag,
        digest=digest,
        normalized=normalized,
        selector=digest or tag or "latest",
    )


def _normalize_registry(value: str) -> str:
    try:
        parsed = urlsplit(f"//{value}")
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("invalid container registry host") from error
    if port == 0:
        raise ValueError("invalid container registry port")
    if (
        not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("invalid container registry host")

    hostname = hostname.lower()
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if any(not _DNS_LABEL_RE.fullmatch(label) for label in hostname.split(".")):
            raise ValueError("invalid container registry host") from None
        normalized_host = hostname
    else:
        normalized_host = (
            f"[{address.compressed}]" if address.version == 6 else str(address)
        )

    if normalized_host in _DOCKER_REGISTRY_ALIASES and port is None:
        return _DEFAULT_REGISTRY
    return f"{normalized_host}:{port}" if port is not None else normalized_host


def parse_image_uri(raw: str | None) -> tuple[str | None, str | None]:
    """Return ``(image_uri, image_digest)`` extracted from a raw image reference.

    Handles the common forms produced by the different container/function
    providers:

    - ``registry/repo:tag`` — bare tag, no digest.
    - ``registry/repo@sha256:xxx`` — digest pinned, no tag.
    - ``registry/repo:tag@sha256:xxx`` — tag + digest (Lambda's Code.ImageUri
      shape when a tag is used alongside the resolved digest).
    - ``DOCKER|registry/repo:tag`` — Azure App Service's ``linuxFxVersion``
      encoding for container deployments; the prefix is stripped.

    Returns ``(None, None)`` for empty / whitespace-only input. ``image_digest``
    is ``None`` when the reference is not digest-pinned.
    """
    if raw is None:
        return None, None
    uri = raw.strip()
    if not uri:
        return None, None

    if uri.startswith(_AZURE_DOCKER_PREFIX):
        uri = uri[len(_AZURE_DOCKER_PREFIX) :].strip()
        if not uri:
            return None, None

    digest: str | None = None
    if "@" in uri:
        _, _, digest_candidate = uri.rpartition("@")
        digest = digest_candidate or None

    return uri, digest
