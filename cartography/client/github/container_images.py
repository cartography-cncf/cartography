from typing import Any

import neo4j

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.util import timeit


@timeit
def get_ghcr_image_sources(
    neo4j_session: neo4j.Session,
    digests: list[str],
) -> dict[str, dict[str, Any]]:
    """
    Return the source fields each GHCR image holds, keyed by digest.

    :param neo4j_session: The neo4j session object.
    :param digests: The image digests to look up.
    :return: Mapping of digest to its source_uri, source_revision and source_file.
    """
    if not digests:
        return {}
    query = """
    MATCH (img:GitHubContainerImage)
    WHERE img.id IN $digests
    RETURN img.digest AS digest, img.source_uri AS source_uri,
           img.source_revision AS source_revision, img.source_file AS source_file
    """
    records = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        digests=digests,
    )
    return {record["digest"]: record for record in records}


@timeit
def get_ghcr_enriched_attestations(
    neo4j_session: neo4j.Session,
    org_url: str,
) -> list[dict[str, Any]]:
    """
    Return the stored attestations of every GHCR image that already holds the source
    of one of its attestations, in the shape GitHubContainerImageAttestationSchema loads.

    The image has to hold its attestation's source, not just any source: an OCI label
    sets source_uri first, and the higher-priority attestation must still be read.

    :param neo4j_session: The neo4j session object.
    :param org_url: The GitHub organization URL that scopes the attestations.
    :return: One dict per attestation node.
    """
    query = """
    MATCH (org:GitHubOrganization {id: $org_url})-[:RESOURCE]->(att:GitHubContainerImageAttestation)
    WHERE att.source_uri IS NOT NULL
    MATCH (org)-[:RESOURCE]->(img:GitHubContainerImage {digest: att.attests_digest})
    WHERE img.source_uri = att.source_uri
    WITH DISTINCT org, att.attests_digest AS digest
    MATCH (org)-[:RESOURCE]->(enriched:GitHubContainerImageAttestation {attests_digest: digest})
    RETURN enriched.id AS id, enriched.bundle_id AS bundle_id,
           enriched.predicate_type AS predicate_type,
           enriched.attests_digest AS attests_digest,
           enriched.source_uri AS source_uri,
           enriched.source_revision AS source_revision,
           enriched.source_file AS source_file
    """
    return neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        org_url=org_url,
    )
