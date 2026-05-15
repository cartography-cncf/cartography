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
from cartography.intel.gitlab.util import fetch_registry_blob
from cartography.intel.gitlab.util import fetch_registry_manifest
from cartography.intel.supply_chain import decode_attestation_blob_to_predicate
from cartography.intel.supply_chain import extract_container_parent_image
from cartography.intel.supply_chain import extract_image_source_provenance
from cartography.models.gitlab.container_image_attestations import (
    GitLabContainerImageAttestationSchema,
)
from cartography.models.gitlab.container_images import (
    GitLabContainerImageProvenanceSchema,
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


def _extract_predicate_from_attestation(
    attestation: dict[str, Any],
    gitlab_url: str,
    token: str,
) -> dict[str, Any] | None:
    """
    Decode an attestation blob and return the embedded predicate when present.

    Supports both:
    - DSSE/cosign envelopes where the blob contains a base64 `payload`
    - raw in-toto statements where the blob is already JSON with `predicate`
    """
    registry_url = attestation.get("_registry_url")
    repository_name = attestation.get("_repository_name")
    layers = attestation.get("layers", [])
    if not registry_url or not repository_name or not layers:
        return None

    layer_digest = layers[0].get("digest")
    if not layer_digest:
        return None

    try:
        blob = fetch_registry_blob(
            gitlab_url,
            str(registry_url),
            str(repository_name),
            str(layer_digest),
            token,
        )
    except requests.exceptions.RequestException:
        logger.warning(
            "Failed to fetch attestation blob for %s",
            attestation.get("_digest"),
            exc_info=True,
        )
        return None

    return decode_attestation_blob_to_predicate(blob)


def _extract_image_provenance(
    attestation: dict[str, Any],
    predicate: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract the subset of SLSA provenance fields used by supply-chain matching.
    """
    result = extract_image_source_provenance(predicate)
    result.update(extract_container_parent_image(predicate))
    attests_digest = attestation.get("_attests_digest")
    if attests_digest is not None:
        result["attests_digest"] = str(attests_digest)
    return result


def transform_container_image_attestations(
    raw_attestations: list[dict[str, Any]],
    gitlab_url: str,
    token: str,
) -> list[dict[str, Any]]:
    """
    Transform raw attestation data into the format expected by the schema.
    """
    transformed = []

    for attestation in raw_attestations:
        record = {
            "digest": attestation.get("_digest"),
            "media_type": attestation.get("mediaType"),
            "attestation_type": attestation.get("_attestation_type"),
            "predicate_type": attestation.get("predicateType"),
            "attests_digest": attestation.get("_attests_digest"),
        }
        if attestation.get("_attestation_type") in {"att", "buildx"}:
            predicate = _extract_predicate_from_attestation(
                attestation,
                gitlab_url,
                token,
            )
            if predicate:
                record.update(_extract_image_provenance(attestation, predicate))
        transformed.append(record)

    logger.info(f"Transformed {len(transformed)} container image attestations")
    return transformed


def transform_image_provenance_records(
    transformed_attestations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build provenance-only records to merge onto GitLabContainerImage nodes by digest.
    """
    provenance_by_digest: dict[str, dict[str, Any]] = {}

    for attestation in transformed_attestations:
        attests_digest = attestation.get("attests_digest")
        source_uri = attestation.get("source_uri")
        parent_image_digest = attestation.get("parent_image_digest")
        if not attests_digest or (not source_uri and not parent_image_digest):
            continue
        digest = str(attests_digest)
        existing = provenance_by_digest.get(digest, {"digest": attests_digest})
        candidate = {
            "source_uri": source_uri,
            "source_revision": attestation.get("source_revision"),
            "source_file": attestation.get("source_file"),
            "parent_image_uri": attestation.get("parent_image_uri"),
            "parent_image_digest": attestation.get("parent_image_digest"),
            "from_attestation": True,
            "confidence": 1.0,
        }
        existing.update({k: v for k, v in candidate.items() if v is not None})
        provenance_by_digest[digest] = existing

    records = list(provenance_by_digest.values())
    logger.info("Transformed %d image provenance record(s)", len(records))
    return records


@timeit
def load_container_image_attestations(
    neo4j_session: neo4j.Session,
    attestations: list[dict[str, Any]],
    org_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab container image attestations into the graph.
    """
    logger.info(
        f"Loading {len(attestations)} container image attestations for {org_id}"
    )
    load(
        neo4j_session,
        GitLabContainerImageAttestationSchema(),
        attestations,
        lastupdated=update_tag,
        org_id=org_id,
        gitlab_url=gitlab_url,
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
def load_image_provenance(
    neo4j_session: neo4j.Session,
    provenance_records: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load provenance fields directly onto GitLabContainerImage nodes.
    """
    if not provenance_records:
        return

    load(
        neo4j_session,
        GitLabContainerImageProvenanceSchema(),
        provenance_records,
        lastupdated=update_tag,
    )


@timeit
def sync_container_image_attestations(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    org_id: int,
    manifests: list[dict[str, Any]],
    manifest_lists: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync GitLab container image attestations for an organization.
    """
    logger.info(f"Syncing container image attestations for organization {org_id}")

    raw_attestations, summary = get_container_image_attestations(
        gitlab_url, token, manifests, manifest_lists
    )

    transformed = transform_container_image_attestations(
        raw_attestations,
        gitlab_url,
        token,
    )
    provenance_records = transform_image_provenance_records(transformed)
    load_container_image_attestations(
        neo4j_session,
        transformed,
        org_id,
        gitlab_url,
        update_tag,
    )
    load_image_provenance(
        neo4j_session,
        provenance_records,
        update_tag,
    )
    if summary.failed:
        logger.warning(
            "Skipping GitLab container image attestations cleanup for %s because %d of %d registry probe(s) failed. Existing attestation data was preserved.",
            org_id,
            summary.failed,
            summary.attempted,
        )
        return
    cleanup_container_image_attestations(neo4j_session, common_job_parameters)
