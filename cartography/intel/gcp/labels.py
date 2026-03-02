import logging
from string import Template
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import execute_write_with_retry
from cartography.stats import get_stats_client
from cartography.util import batch
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

DEFAULT_CLEANUP_BATCH_SIZE = 1000


# Mapping of GCP resource types to their Cartography node labels, unique ID properties,
# and the field path where labels are found in the API response.
# label: the node label used in Cartography for this resource type
# property: the field of this node that uniquely identifies this resource type
# labels_field: the key path to extract labels from the raw API response dict
LABEL_RESOURCE_TYPE_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "gcp_instance": {
        "label": "GCPInstance",
        "property": "id",
        "labels_field": "labels",
        "id_field": "partial_uri",
    },
    "gcp_bucket": {
        "label": "GCPBucket",
        "property": "id",
        "labels_field": "labels",
    },
    "gke_cluster": {
        "label": "GKECluster",
        "property": "id",
        "labels_field": "resourceLabels",
    },
    "gcp_bigtable_instance": {
        "label": "GCPBigtableInstance",
        "property": "id",
        "labels_field": "labels",
    },
    "gcp_cloud_sql_instance": {
        "label": "GCPCloudSQLInstance",
        "property": "id",
        "labels_field": "settings.userLabels",
    },
    "gcp_dns_zone": {
        "label": "GCPDNSZone",
        "property": "id",
        "labels_field": "labels",
    },
    "gcp_secret_manager_secret": {
        "label": "GCPSecretManagerSecret",
        "property": "id",
        "labels_field": "labels",
    },
    "gcp_cloud_run_service": {
        "label": "GCPCloudRunService",
        "property": "id",
        "labels_field": "labels",
    },
    "gcp_cloud_run_job": {
        "label": "GCPCloudRunJob",
        "property": "id",
        "labels_field": "labels",
    },
}

# Mapping of resource labels to their path to GCPProject for cleanup
_RESOURCE_CLEANUP_PATHS: Dict[str, str] = {
    "GCPInstance": "(:GCPInstance)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GCPBucket": "(:GCPBucket)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GKECluster": "(:GKECluster)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GCPBigtableInstance": "(:GCPBigtableInstance)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GCPCloudSQLInstance": "(:GCPCloudSQLInstance)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GCPDNSZone": "(:GCPDNSZone)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GCPSecretManagerSecret": "(:GCPSecretManagerSecret)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GCPCloudRunService": "(:GCPCloudRunService)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
    "GCPCloudRunJob": "(:GCPCloudRunJob)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})",
}


def _resolve_labels_field(resource: Dict, labels_field: str) -> Dict[str, str]:
    """
    Extract the labels dict from a resource, supporting dot-separated nested field paths.
    For example, 'settings.userLabels' will resolve resource['settings']['userLabels'].

    :param resource: A single raw GCP API resource dict.
    :param labels_field: Dot-separated path to the labels field.
    :return: A dict of label key-value pairs, or empty dict if not found.
    """
    obj: Any = resource
    for part in labels_field.split("."):
        if not isinstance(obj, dict):
            return {}
        obj = obj.get(part)
        if obj is None:
            return {}
    if not isinstance(obj, dict):
        return {}
    return obj


@timeit
def get_labels(
    resource_list: List[Dict],
    resource_type: str,
) -> List[Dict]:
    """
    Extract labels from a list of already-fetched GCP resource dicts.

    GCP labels are embedded in each resource's own API response. This function extracts them into a
    normalized format suitable for loading as GCPLabel nodes.

    :param resource_list: List of raw resource dicts from a GCP API response.
    :param resource_type: Key into LABEL_RESOURCE_TYPE_MAPPINGS identifying the resource type.
    :return: List of label dicts with keys: id, key, value, resource_id.
    """
    mapping = LABEL_RESOURCE_TYPE_MAPPINGS.get(resource_type)
    if not mapping:
        logger.warning("Unknown GCP resource type for labels: %s", resource_type)
        return []

    labels_field = mapping["labels_field"]
    # id_field is the key in the resource dict to use as the resource ID.
    # Falls back to "property" which is also used for the Cypher match.
    id_field = mapping.get("id_field", mapping["property"])
    labels: List[Dict] = []

    for resource in resource_list:
        resource_id = resource.get(id_field)
        if not resource_id:
            continue

        resource_labels = _resolve_labels_field(resource, labels_field)
        for key, value in resource_labels.items():
            labels.append(
                {
                    "id": f"{resource_id}:{key}:{value}",
                    "key": key,
                    "value": value,
                    "resource_id": resource_id,
                }
            )

    logger.debug(
        "Extracted %d labels from %d %s resources",
        len(labels),
        len(resource_list),
        resource_type,
    )
    return labels


@timeit
def sync_labels(
    neo4j_session: neo4j.Session,
    resource_list: List[Dict],
    resource_type: str,
    project_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    End-to-end sync of GCPLabel nodes for a single resource type.

    Call this from each resource module's sync() after loading the resources themselves.

    :param neo4j_session: The Neo4j session.
    :param resource_list: List of raw resource dicts from the GCP API response.
    :param resource_type: Key into LABEL_RESOURCE_TYPE_MAPPINGS (e.g. "gcp_bucket").
    :param project_id: The GCP project ID.
    :param update_tag: Timestamp for marking data freshness.
    :param common_job_parameters: Dict with UPDATE_TAG and PROJECT_ID for cleanup.
    """
    label_data = get_labels(resource_list, resource_type)
    transform_labels(label_data, resource_type)
    load_labels(neo4j_session, label_data, resource_type, project_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def transform_labels(label_data: List[Dict], resource_type: str) -> List[Dict]:
    """
    Add the resource_type field to each label dict for use in conditional node labeling.

    For GCP, get_labels() already produces normalized dicts with id, key, value, and
    resource_id. This transform step enriches each label with the Cartography node label
    of the source resource (e.g. "GCPBucket") so that backward-compatible extra labels
    like GCPBucketLabel can be applied during ingestion.

    :param label_data: List of label dicts from get_labels().
    :param resource_type: Key into LABEL_RESOURCE_TYPE_MAPPINGS.
    :return: The same list, mutated in place with resource_type added.
    """
    mapping = LABEL_RESOURCE_TYPE_MAPPINGS.get(resource_type)
    if not mapping:
        return label_data

    node_label = mapping["label"]
    for label in label_data:
        label["resource_type"] = node_label

    return label_data


def _load_labels_tx(
    tx: neo4j.Transaction,
    label_data: List[Dict],
    resource_type: str,
    project_id: str,
    update_tag: int,
) -> None:
    """
    Transaction function that creates GCPLabel nodes and LABELED relationships
    using a template-based Cypher query.

    The template substitutes the resource's node label and ID property so that the same
    query pattern works across all GCP resource types.
    """
    INGEST_LABEL_TEMPLATE = Template(
        """
        UNWIND $LabelData as label
            MATCH
            (:GCPProject{id: $ProjectId})-[:RESOURCE]->(resource:$resource_label{$property: label.resource_id})
            MERGE
            (gcp_label:GCPLabel:Label{id: label.id})
            ON CREATE SET gcp_label.firstseen = timestamp()

            SET gcp_label.lastupdated = $UpdateTag,
            gcp_label.key = label.key,
            gcp_label.value = label.value,
            gcp_label.resource_type = label.resource_type

            MERGE (resource)-[r:LABELED]->(gcp_label)
            SET r.lastupdated = $UpdateTag,
            r.firstseen = timestamp()
    """
    )

    if not label_data:
        return

    query = INGEST_LABEL_TEMPLATE.safe_substitute(
        resource_label=LABEL_RESOURCE_TYPE_MAPPINGS[resource_type]["label"],
        property=LABEL_RESOURCE_TYPE_MAPPINGS[resource_type]["property"],
    )
    tx.run(
        query,
        LabelData=label_data,
        ProjectId=project_id,
        UpdateTag=update_tag,
    ).consume()


@timeit
def load_labels(
    neo4j_session: neo4j.Session,
    label_data: List[Dict],
    resource_type: str,
    project_id: str,
    update_tag: int,
) -> None:
    """
    Load GCPLabel nodes and LABELED relationships into Neo4j.

    :param neo4j_session: The Neo4j session.
    :param label_data: List of label dicts from transform_labels().
    :param resource_type: Key into LABEL_RESOURCE_TYPE_MAPPINGS.
    :param project_id: The GCP project ID (used to match resources via GCPProject).
    :param update_tag: Timestamp for marking data freshness.
    """
    if not label_data:
        return
    for label_batch in batch(label_data, size=100):
        neo4j_session.execute_write(
            _load_labels_tx,
            label_data=label_batch,
            resource_type=resource_type,
            project_id=project_id,
            update_tag=update_tag,
        )


def _run_cleanup_until_empty(
    neo4j_session: neo4j.Session,
    query: str,
    batch_size: int = DEFAULT_CLEANUP_BATCH_SIZE,
    **kwargs: Any,
) -> int:
    """Run a cleanup query in batches until no more items are deleted.

    Returns the total number of items deleted.
    """

    def _cleanup_batch_tx(tx: neo4j.Transaction, query: str, **params: Any) -> int:
        result = tx.run(query, **params)
        summary = result.consume()
        stat_handler.incr("nodes_deleted", summary.counters.nodes_deleted)
        stat_handler.incr(
            "relationships_deleted",
            summary.counters.relationships_deleted,
        )
        return summary.counters.nodes_deleted + summary.counters.relationships_deleted

    total_deleted = 0
    while True:
        deleted = execute_write_with_retry(
            neo4j_session,
            _cleanup_batch_tx,
            query,
            LIMIT_SIZE=batch_size,
            **kwargs,
        )
        total_deleted += deleted
        if deleted == 0:
            break
    return total_deleted


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Clean up stale GCPLabel nodes and LABELED relationships.

    Iterates over each supported resource type and removes labels and relationships
    that were not updated in the current sync run. Also removes orphaned label nodes
    that have no remaining relationships.
    """
    cleanup_batch_size = common_job_parameters.get(
        "gcp_label_cleanup_batch",
        DEFAULT_CLEANUP_BATCH_SIZE,
    )
    for _label, path in _RESOURCE_CLEANUP_PATHS.items():
        # Delete stale label nodes
        _run_cleanup_until_empty(
            neo4j_session,
            f"""
            MATCH (n:GCPLabel)<-[:LABELED]-{path}
            WHERE n.lastupdated <> $UPDATE_TAG
            WITH n LIMIT $LIMIT_SIZE
            DETACH DELETE n
            """,
            batch_size=cleanup_batch_size,
            GCP_PROJECT_ID=common_job_parameters["PROJECT_ID"],
            UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        )
        # Delete stale LABELED relationships
        _run_cleanup_until_empty(
            neo4j_session,
            f"""
            MATCH (:GCPLabel)<-[r:LABELED]-{path}
            WHERE r.lastupdated <> $UPDATE_TAG
            WITH r LIMIT $LIMIT_SIZE
            DELETE r
            """,
            batch_size=cleanup_batch_size,
            GCP_PROJECT_ID=common_job_parameters["PROJECT_ID"],
            UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        )

    # Clean up orphaned labels (labels with no relationships)
    _run_cleanup_until_empty(
        neo4j_session,
        """
        MATCH (n:GCPLabel)
        WHERE NOT (n)--() AND n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n
        """,
        batch_size=cleanup_batch_size,
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
    )
