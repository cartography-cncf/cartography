import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.ontology.utils import get_source_nodes_from_graph
from cartography.intel.ontology.utils import link_ontology_nodes
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.ontology.device import DeviceSchema
from cartography.models.ontology.device import HOSTNAME_MATCHLINKS
from cartography.util import timeit

logger = logging.getLogger(__name__)

MATCHLINK_SUB_RESOURCE_LABEL = "Ontology"
MATCHLINK_SUB_RESOURCE_ID = "devices"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    source_of_truth: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data = get_source_nodes_from_graph(neo4j_session, source_of_truth, "devices")
    load_devices(
        neo4j_session,
        data,
        update_tag,
    )
    _run_hostname_matchlinks(neo4j_session, update_tag)
    link_ontology_nodes(neo4j_session, "devices", update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def load_devices(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DeviceSchema(),
        data,
        lastupdated=update_tag,
    )


def _should_run_hostname_matchlink(
    neo4j_session: neo4j.Session,
    target_label: str,
    hostname_field: str,
    has_serial_rel: bool,
    update_tag: int,
) -> bool:
    """Check if hostname matchlink should be run for a given module.

    Conditions checked:
    1. For modules with serial_number: at least one OBSERVED_AS exists (confirming module data)
    2. Hostnames on target nodes are unique (no duplicates)
    3. Hostnames on Device nodes are unique (no duplicates on source side)
    """
    if has_serial_rel:
        result = neo4j_session.run(
            f"MATCH (:Device)-[r:OBSERVED_AS]->(:{target_label}) "
            "WHERE r.lastupdated = $update_tag "
            "RETURN count(r) > 0 as has_links",
            update_tag=update_tag,
        ).single()
        if not result or not result["has_links"]:
            logger.debug(
                "No serial_number OBSERVED_AS links found for %s, skipping hostname matchlink.",
                target_label,
            )
            return False

    # Check hostname uniqueness on target nodes
    result = neo4j_session.run(
        f"MATCH (t:{target_label}) WHERE t.`{hostname_field}` IS NOT NULL "
        f"WITH count(DISTINCT t.`{hostname_field}`) as distinct_count, count(t) as total_count "
        "RETURN distinct_count = total_count as unique_hostnames",
    ).single()

    if not result or not result["unique_hostnames"]:
        logger.debug(
            "Duplicate hostnames found on %s nodes, skipping hostname matchlink.",
            target_label,
        )
        return False

    # Check hostname uniqueness on Device nodes (source side)
    result = neo4j_session.run(
        "MATCH (d:Device) WHERE d.lastupdated = $update_tag AND d.hostname IS NOT NULL "
        "WITH count(DISTINCT d.hostname) as distinct_count, count(d) as total_count "
        "RETURN distinct_count = total_count as unique_hostnames",
        update_tag=update_tag,
    ).single()

    if not result or not result["unique_hostnames"]:
        logger.debug(
            "Duplicate hostnames found on Device nodes, skipping hostname matchlink for %s.",
            target_label,
        )
        return False

    return True


def _get_device_hostnames(
    neo4j_session: neo4j.Session,
    update_tag: int,
) -> list[dict[str, str]]:
    """Get hostnames of all Device nodes from the current sync run."""
    results = neo4j_session.run(
        "MATCH (d:Device) "
        "WHERE d.lastupdated = $update_tag AND d.hostname IS NOT NULL "
        "RETURN d.hostname as hostname",
        update_tag=update_tag,
    )
    return [{"hostname": record["hostname"]} for record in results]


def _run_hostname_matchlinks(
    neo4j_session: neo4j.Session,
    update_tag: int,
) -> None:
    """Run hostname-based matchlinks for all configured modules.

    Hostname matching is a fallback strategy: it is only used when
    serial_number matching is not available or as a supplement when
    serial_number links already exist and hostnames are unique.
    """
    device_hostnames = _get_device_hostnames(neo4j_session, update_tag)

    for target_label, hostname_field, matchlink, has_serial_rel in HOSTNAME_MATCHLINKS:
        # Always run cleanup to remove stale hostname matchlinks
        _cleanup_hostname_matchlink(neo4j_session, matchlink, update_tag)

        if not device_hostnames:
            continue

        if not _should_run_hostname_matchlink(
            neo4j_session, target_label, hostname_field, has_serial_rel, update_tag,
        ):
            continue

        logger.info("Running hostname matchlink for %s.", target_label)
        load_matchlinks(
            neo4j_session,
            matchlink,
            device_hostnames,
            UPDATE_TAG=update_tag,
            _sub_resource_label=MATCHLINK_SUB_RESOURCE_LABEL,
            _sub_resource_id=MATCHLINK_SUB_RESOURCE_ID,
        )


def _cleanup_hostname_matchlink(
    neo4j_session: neo4j.Session,
    matchlink: CartographyRelSchema,
    update_tag: int,
) -> None:
    """Clean up stale hostname matchlink relationships."""
    cleanup_job = GraphJob.from_matchlink(
        matchlink,
        MATCHLINK_SUB_RESOURCE_LABEL,
        MATCHLINK_SUB_RESOURCE_ID,
        update_tag,
    )
    cleanup_job.run(neo4j_session)


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DeviceSchema(), common_job_parameters).run(
        neo4j_session,
    )
