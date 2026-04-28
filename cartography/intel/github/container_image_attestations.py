"""
GitHub Container Image Attestations Intelligence Module.

Pulls SLSA attestations for image digests via the GitHub Attestations API
and uses the parsed payload to enrich each image with ``source_uri``,
``source_revision`` and ``source_file``. The supply-chain matcher then
relies on those properties to draw ``PACKAGED_FROM`` edges back to the
``GitHubRepository`` that built the image.

Cross-run de-duplication: digests that already have ``source_uri`` set in
the graph are skipped — a previous sync already enriched them.
"""

import base64
import binascii
import json
import logging
from typing import Any
from typing import cast
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.intel.github.util import call_github_rest_api
from cartography.intel.github.util import rest_api_base_url
from cartography.models.github.container_image_attestations import (
    GitHubContainerImageAttestationSchema,
)
from cartography.models.github.container_images import (
    GitHubContainerImageProvenanceSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _digests_from_manifests(raw_manifests: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    digests: list[str] = []
    for manifest in raw_manifests:
        digest = manifest.get("_digest")
        if digest and digest not in seen:
            seen.add(digest)
            digests.append(digest)
    return digests


def _digests_already_enriched(
    neo4j_session: neo4j.Session,
    org_url: str,
) -> set[str]:
    query = """
    MATCH (org:GitHubOrganization {id: $org_url})
    MATCH (img:GitHubContainerImage)-[:RESOURCE]->(org)
    WHERE img.source_uri IS NOT NULL
    RETURN img.digest
    """
    values = neo4j_session.execute_read(
        read_list_of_values_tx,
        query,
        org_url=org_url,
    )
    return {v for v in cast(list[str], values) if v}


def _decode_dsse_payload(envelope: dict[str, Any]) -> dict[str, Any] | None:
    """Decode the in-toto statement carried in a DSSE envelope, if possible."""
    payload_b64 = envelope.get("payload")
    if not isinstance(payload_b64, str):
        return None
    try:
        decoded = base64.b64decode(payload_b64).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        logger.debug("Failed to base64-decode DSSE payload: %s", exc)
        return None
    try:
        result = json.loads(decoded)
    except json.JSONDecodeError as exc:
        logger.debug("Failed to JSON-decode DSSE payload: %s", exc)
        return None
    return result if isinstance(result, dict) else None


def _extract_provenance(statement: dict[str, Any]) -> dict[str, str | None]:
    """
    Pull source URI / revision / file out of a SLSA in-toto statement.

    Supports SLSA Provenance v1 (predicate.buildDefinition.externalParameters)
    and the older v0.2 layout (predicate.invocation.configSource). Falls back
    to ``None`` for fields we can't resolve.
    """
    predicate = statement.get("predicate") or {}
    source_uri: str | None = None
    source_revision: str | None = None
    source_file: str | None = None

    build_def = predicate.get("buildDefinition") or {}

    # Resolved dependencies carry the actual commit SHA — preferred over the ref.
    resolved_deps = build_def.get("resolvedDependencies") or []
    if isinstance(resolved_deps, list) and resolved_deps:
        first = resolved_deps[0]
        if isinstance(first, dict):
            source_uri = first.get("uri") or source_uri
            digest = first.get("digest") or {}
            if isinstance(digest, dict):
                source_revision = (
                    digest.get("gitCommit") or digest.get("sha1") or source_revision
                )

    external = build_def.get("externalParameters") or {}
    if isinstance(external, dict):
        workflow = external.get("workflow") or {}
        if isinstance(workflow, dict):
            # The workflow.repository is the cleaner human-friendly URL.
            source_uri = workflow.get("repository") or source_uri
            source_revision = source_revision or workflow.get("ref")
            source_file = workflow.get("path") or source_file

    invocation = predicate.get("invocation") or {}
    if isinstance(invocation, dict):
        config_source = invocation.get("configSource") or {}
        if isinstance(config_source, dict):
            source_uri = source_uri or config_source.get("uri")
            digest = config_source.get("digest") or {}
            if isinstance(digest, dict) and not source_revision:
                source_revision = digest.get("sha1") or digest.get("gitCommit")
            source_file = source_file or config_source.get("entryPoint")

    return {
        "source_uri": source_uri,
        "source_revision": source_revision,
        "source_file": source_file,
    }


def _attestations_endpoint(organization: str, digest: str) -> str:
    return (
        f"/orgs/{quote(organization)}/attestations/{quote(digest, safe='')}"
        f"?per_page=100"
    )


@timeit
def get_attestations_for_digest(
    token: Any,
    api_url: str,
    organization: str,
    digest: str,
) -> list[dict[str, Any]]:
    base_url = rest_api_base_url(api_url)
    endpoint = _attestations_endpoint(organization, digest)
    try:
        response = call_github_rest_api(endpoint, token, base_url)
    except requests.exceptions.HTTPError as err:
        if err.response is not None and err.response.status_code == 404:
            return []
        raise
    return response.get("attestations") or []


def transform_attestations(
    organization: str,
    attestations_by_digest: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Build (attestation_rows, image_provenance_rows). Each attestation produces
    a ``GitHubContainerImageAttestation`` node; the most informative one per
    digest also populates the provenance enrichment row used by
    ``GitHubContainerImageProvenanceSchema``.
    """
    attestation_rows: list[dict[str, Any]] = []
    provenance_by_digest: dict[str, dict[str, Any]] = {}

    for digest, attestations in attestations_by_digest.items():
        for idx, attestation in enumerate(attestations):
            bundle = attestation.get("bundle") or {}
            envelope = bundle.get("dsseEnvelope") or {}
            statement = _decode_dsse_payload(envelope) or {}
            predicate_type = statement.get("predicateType") or attestation.get(
                "predicate_type",
            )
            provenance = _extract_provenance(statement)

            row_id = f"{organization}:{digest}:{predicate_type or 'unknown'}:{idx}"
            attestation_rows.append(
                {
                    "id": row_id,
                    "bundle_id": attestation.get("id"),
                    "predicate_type": predicate_type,
                    "attests_digest": digest,
                    "source_uri": provenance["source_uri"],
                    "source_revision": provenance["source_revision"],
                    "source_file": provenance["source_file"],
                },
            )

            existing = provenance_by_digest.get(digest)
            # Prefer the first attestation that yields a usable source_uri.
            if existing is None or (
                not existing.get("source_uri") and provenance["source_uri"]
            ):
                provenance_by_digest[digest] = {
                    "digest": digest,
                    "source_uri": provenance["source_uri"],
                    "source_revision": provenance["source_revision"],
                    "source_file": provenance["source_file"],
                    "parent_image_uri": None,
                    "parent_image_digest": None,
                }

    return attestation_rows, list(provenance_by_digest.values())


@timeit
def load_attestations(
    neo4j_session: neo4j.Session,
    rows: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubContainerImageAttestationSchema(),
        rows,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_image_provenance(
    neo4j_session: neo4j.Session,
    rows: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    if not rows:
        return
    load(
        neo4j_session,
        GitHubContainerImageProvenanceSchema(),
        rows,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_attestations(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        GitHubContainerImageAttestationSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_container_image_attestations(
    neo4j_session: neo4j.Session,
    token: Any,
    api_url: str,
    organization: str,
    raw_manifests: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    org_url = f"https://github.com/{organization}"
    digests = _digests_from_manifests(raw_manifests)
    skip = _digests_already_enriched(neo4j_session, org_url)

    attestations_by_digest: dict[str, list[dict[str, Any]]] = {}
    for digest in digests:
        if digest in skip:
            continue
        attestations = get_attestations_for_digest(
            token,
            api_url,
            organization,
            digest,
        )
        if attestations:
            attestations_by_digest[digest] = attestations

    attestation_rows, provenance_rows = transform_attestations(
        organization,
        attestations_by_digest,
    )
    if attestation_rows:
        logger.info(
            "Loading %d GHCR attestation nodes for %s",
            len(attestation_rows),
            organization,
        )
        load_attestations(neo4j_session, attestation_rows, org_url, update_tag)
    if provenance_rows:
        load_image_provenance(neo4j_session, provenance_rows, org_url, update_tag)

    cleanup_params = dict(common_job_parameters)
    cleanup_params["org_url"] = org_url
    cleanup_attestations(neo4j_session, cleanup_params)
