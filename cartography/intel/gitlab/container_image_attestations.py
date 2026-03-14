"""
GitLab Container Image Attestations Intelligence Module

Syncs container image attestations (signatures, provenance) from GitLab into the graph.
Attestations are discovered via cosign's tag-based scheme:
- Signatures: sha256-{digest}.sig
- Attestations: sha256-{digest}.att
"""

import logging
from dataclasses import dataclass
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import fetch_registry_manifest
from cartography.models.gitlab.container_image_attestations import (
    GitLabContainerImageAttestationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Attestation tag suffixes used by cosign
ATTESTATION_SUFFIXES = [".sig", ".att"]

_REGISTRY_AUTH_FAILURE_STATUS_CODES = {401, 403}


@dataclass(frozen=True)
class AttestationDiscoverySummary:
    attempted: int = 0
    discovered: int = 0
    failed: int = 0


def _is_registry_auth_failure(exc: requests.exceptions.RequestException) -> bool:
    if not isinstance(exc, requests.exceptions.HTTPError):
        return False
    response = exc.response
    return (
        response is not None
        and response.status_code in _REGISTRY_AUTH_FAILURE_STATUS_CODES
    )


def _digest_to_attestation_tag(digest: str, suffix: str) -> str:
    """
    Convert an image digest to a cosign attestation tag.

    Cosign stores attestations at predictable tags derived from the image digest:
    sha256:abc123... -> sha256-abc123....sig (or .att)
    """
    return digest.replace(":", "-") + suffix


def get_container_image_attestations(
    gitlab_url: str,
    token: str,
    manifests: list[dict[str, Any]],
    manifest_lists: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], AttestationDiscoverySummary]:
    """
    Discover and fetch attestations for container images.

    Supports two attestation discovery methods:
    1. Cosign tag-based: probes for sha256-{digest}.sig and sha256-{digest}.att tags
    2. Buildx embedded: scans manifest lists for entries with attestation-manifest annotation
    """
    all_attestations: list[dict[str, Any]] = []
    seen_digests: set[str] = set()
    attempted = 0
    failed = 0

    # Cosign-style discovery: probe for .sig and .att tags
    for manifest in manifests:
        image_digest = manifest.get("_digest")
        registry_url = manifest.get("_registry_url")
        repository_name = manifest.get("_repository_name")

        if not all([image_digest, registry_url, repository_name]):
            continue

        # Type narrowing after the guard check
        image_digest = str(image_digest)
        registry_url = str(registry_url)
        repository_name = str(repository_name)

        for suffix in ATTESTATION_SUFFIXES:
            attestation_tag = _digest_to_attestation_tag(image_digest, suffix)
            attempted += 1

            try:
                response = fetch_registry_manifest(
                    gitlab_url,
                    registry_url,
                    repository_name,
                    attestation_tag,
                    token,
                )

                if response.status_code == 404:
                    # Attestation doesn't exist for this image
                    continue

                response.raise_for_status()

                attestation = response.json()
                attestation_digest = response.headers.get("Docker-Content-Digest")

                if not attestation_digest or attestation_digest in seen_digests:
                    continue
                seen_digests.add(attestation_digest)

                attestation["_digest"] = attestation_digest
                attestation["_registry_url"] = registry_url
                attestation["_repository_name"] = repository_name
                attestation["_attests_digest"] = image_digest
                attestation["_attestation_type"] = suffix.lstrip(".")

                all_attestations.append(attestation)

            except requests.exceptions.RequestException as e:
                if _is_registry_auth_failure(e):
                    logger.error(
                        "Registry auth failed while fetching attestation %s for %s: %s",
                        attestation_tag,
                        image_digest,
                        e,
                    )
                    raise
                failed += 1
                logger.warning(
                    "Skipping attestation %s for %s after registry request failure: %s",
                    attestation_tag,
                    image_digest,
                    e,
                )
                continue

    # Buildx-style discovery: scan manifest lists for attestation entries
    for manifest_list in manifest_lists:
        registry_url = manifest_list.get("_registry_url")
        repository_name = manifest_list.get("_repository_name")

        if not all([registry_url, repository_name]):
            continue

        # Type narrowing after the guard check
        registry_url = str(registry_url)
        repository_name = str(repository_name)

        for entry in manifest_list.get("manifests", []):
            annotations = entry.get("annotations", {})
            if (
                not annotations
                or annotations.get("vnd.docker.reference.type")
                != "attestation-manifest"
            ):
                continue

            attestation_digest = entry.get("digest")
            attests_digest = annotations.get("vnd.docker.reference.digest")

            if not attestation_digest or attestation_digest in seen_digests:
                continue
            seen_digests.add(attestation_digest)

            # Fetch the attestation manifest
            try:
                attempted += 1
                response = fetch_registry_manifest(
                    gitlab_url,
                    registry_url,
                    repository_name,
                    attestation_digest,
                    token,
                    accept_header="application/vnd.oci.image.manifest.v1+json",
                )
                response.raise_for_status()

                attestation = response.json()
                attestation["_digest"] = attestation_digest
                attestation["_registry_url"] = registry_url
                attestation["_repository_name"] = repository_name
                attestation["_attests_digest"] = attests_digest
                attestation["_attestation_type"] = "buildx"

                all_attestations.append(attestation)

            except requests.exceptions.RequestException as e:
                if _is_registry_auth_failure(e):
                    logger.error(
                        "Registry auth failed while fetching buildx attestation %s: %s",
                        attestation_digest,
                        e,
                    )
                    raise
                failed += 1
                logger.warning(
                    "Skipping buildx attestation %s after registry request failure: %s",
                    attestation_digest,
                    e,
                )
                continue

    summary = AttestationDiscoverySummary(
        attempted=attempted,
        discovered=len(all_attestations),
        failed=failed,
    )
    logger.info(
        "Discovered %d attestations across %d probe(s); skipped %d failed probe(s) while scanning %d manifest list(s)",
        summary.discovered,
        summary.attempted,
        summary.failed,
        len(manifest_lists),
    )
    return all_attestations, summary


def transform_container_image_attestations(
    raw_attestations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform raw attestation data into the format expected by the schema.
    """
    transformed = []

    for attestation in raw_attestations:
        transformed.append(
            {
                "digest": attestation.get("_digest"),
                "media_type": attestation.get("mediaType"),
                "attestation_type": attestation.get("_attestation_type"),
                "predicate_type": attestation.get("predicateType"),
                "attests_digest": attestation.get("_attests_digest"),
            }
        )

    logger.info(f"Transformed {len(transformed)} container image attestations")
    return transformed


@timeit
def load_container_image_attestations(
    neo4j_session: neo4j.Session,
    attestations: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab container image attestations into the graph.
    """
    logger.info(
        f"Loading {len(attestations)} container image attestations for {org_url}"
    )
    load(
        neo4j_session,
        GitLabContainerImageAttestationSchema(),
        attestations,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_container_image_attestations(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale GitLab container image attestations from the graph.
    """
    logger.info("Running GitLab container image attestations cleanup")
    GraphJob.from_node_schema(
        GitLabContainerImageAttestationSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_container_image_attestations(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    org_url: str,
    manifests: list[dict[str, Any]],
    manifest_lists: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync GitLab container image attestations for an organization.
    """
    logger.info(f"Syncing container image attestations for organization {org_url}")

    raw_attestations, summary = get_container_image_attestations(
        gitlab_url, token, manifests, manifest_lists
    )

    transformed = transform_container_image_attestations(raw_attestations)
    load_container_image_attestations(neo4j_session, transformed, org_url, update_tag)
    if summary.failed:
        logger.warning(
            "Skipping GitLab container image attestations cleanup for %s because %d of %d registry probe(s) failed. Existing attestation data was preserved.",
            org_url,
            summary.failed,
            summary.attempted,
        )
        return
    cleanup_container_image_attestations(neo4j_session, common_job_parameters)
