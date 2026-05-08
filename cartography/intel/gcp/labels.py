import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.models.gcp.labels.label import GCPBigtableInstanceGCPLabelSchema
from cartography.models.gcp.labels.label import GCPBucketGCPLabelSchema
from cartography.models.gcp.labels.label import GCPCloudRunJobGCPLabelSchema
from cartography.models.gcp.labels.label import GCPCloudRunServiceGCPLabelSchema
from cartography.models.gcp.labels.label import GCPCloudSQLInstanceGCPLabelSchema
from cartography.models.gcp.labels.label import GCPDNSZoneGCPLabelSchema
from cartography.models.gcp.labels.label import GCPInstanceGCPLabelSchema
from cartography.models.gcp.labels.label import GCPSecretManagerSecretGCPLabelSchema
from cartography.models.gcp.labels.label import GKEClusterGCPLabelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# Mapping of GCP resource types to their extraction config and declarative schema.
# labels_field: the key path to extract labels from the raw API response dict
# id_field: the dict key used to get the resource's unique identifier
# schema: the CartographyNodeSchema used for load() and cleanup
LABEL_RESOURCE_TYPE_MAPPINGS: dict[str, dict[str, Any]] = {
    "gcp_instance": {
        "labels_field": "labels",
        "id_field": "partial_uri",
        "schema": GCPInstanceGCPLabelSchema(),
    },
    "gcp_bucket": {
        "labels_field": "labels",
        "id_field": "id",
        "schema": GCPBucketGCPLabelSchema(),
    },
    "gke_cluster": {
        "labels_field": "resourceLabels",
        "id_field": "id",
        "schema": GKEClusterGCPLabelSchema(),
    },
    "cloud_sql_instance": {
        "labels_field": "userLabels",
        "id_field": "selfLink",
        "schema": GCPCloudSQLInstanceGCPLabelSchema(),
    },
    "bigtable_instance": {
        "labels_field": "labels",
        "id_field": "name",
        "schema": GCPBigtableInstanceGCPLabelSchema(),
    },
    "dns_zone": {
        "labels_field": "labels",
        "id_field": "id",
        "schema": GCPDNSZoneGCPLabelSchema(),
    },
    "secret_manager_secret": {
        "labels_field": "raw_labels",
        "id_field": "id",
        "schema": GCPSecretManagerSecretGCPLabelSchema(),
    },
    "cloud_run_service": {
        "labels_field": "labels",
        "id_field": "id",
        "schema": GCPCloudRunServiceGCPLabelSchema(),
    },
    "cloud_run_job": {
        "labels_field": "labels",
        "id_field": "id",
        "schema": GCPCloudRunJobGCPLabelSchema(),
    },
}


def _resolve_labels_field(resource: dict, labels_field: str) -> dict[str, str]:
    """
    Extract the labels dict from a resource, supporting dot-separated nested field paths.
    For example, 'foo.bar' will resolve resource['foo']['bar'].

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
    resource_list: list[dict],
    resource_type: str,
) -> list[dict]:
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
    id_field = mapping["id_field"]
    labels: list[dict] = []

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
def transform_labels(label_data: list[dict], resource_type: str) -> list[dict]:
    """
    Add the resource_type field to each label dict.

    Enriches each label with the Cartography node label of the source resource
    (e.g. "GCPBucket") so that the resource_type property is set on GCPLabel nodes
    during ingestion, enabling queries filtered by resource type.

    :param label_data: List of label dicts from get_labels().
    :param resource_type: Key into LABEL_RESOURCE_TYPE_MAPPINGS.
    :return: The same list, mutated in place with resource_type added.
    """
    mapping = LABEL_RESOURCE_TYPE_MAPPINGS.get(resource_type)
    if not mapping:
        return label_data

    # Use the LABELED relationship's target_node_label (e.g. "GCPBucket") as resource_type
    schema = mapping["schema"]
    node_label = schema.other_relationships.rels[0].target_node_label
    for label in label_data:
        label["resource_type"] = node_label

    return label_data


@timeit
def load_labels(
    neo4j_session: neo4j.Session,
    label_data: list[dict],
    resource_type: str,
    project_id: str,
    update_tag: int,
    batch_size: int = 10000,
) -> None:
    """
    Load GCPLabel nodes and LABELED relationships into Neo4j.

    :param neo4j_session: The Neo4j session.
    :param label_data: List of label dicts from transform_labels().
    :param resource_type: Key into LABEL_RESOURCE_TYPE_MAPPINGS.
    :param project_id: The GCP project ID (used to match resources via GCPProject).
    :param update_tag: Timestamp for marking data freshness.
    """
    mapping = LABEL_RESOURCE_TYPE_MAPPINGS.get(resource_type)
    if not mapping or not label_data:
        return
    load(
        neo4j_session,
        mapping["schema"],
        label_data,
        batch_size=batch_size,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, resource_type: str, common_job_parameters: dict
) -> None:
    """
    Clean up stale GCPLabel nodes and LABELED relationships for a single resource type.

    GCPLabel nodes are shared across resource schemas under the same base node label.
    Scope deletion by `resource_type` so one partial sync cannot delete labels that
    belong to other resource classes.
    """
    mapping = LABEL_RESOURCE_TYPE_MAPPINGS.get(resource_type)
    if not mapping:
        return
    schema = mapping["schema"]
    resource_node_label = schema.other_relationships.rels[0].target_node_label
    run_write_query(
        neo4j_session,
        """
        MATCH (:GCPProject {id: $PROJECT_ID})-[:RESOURCE]->(l:GCPLabel)
        WHERE l.resource_type = $RESOURCE_NODE_LABEL
          AND l.lastupdated <> $UPDATE_TAG
        DETACH DELETE l
        """,
        PROJECT_ID=common_job_parameters["PROJECT_ID"],
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        RESOURCE_NODE_LABEL=resource_node_label,
    )


@timeit
def sync_labels(
    neo4j_session: neo4j.Session,
    resource_list: list[dict],
    resource_type: str,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    batch_size: int = 10000,
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
    :param batch_size: Optional batch size override for GCPLabel ingestion.
    """
    label_data = get_labels(resource_list, resource_type)
    transform_labels(label_data, resource_type)
    if label_data:
        logger.info(
            "Syncing %d %s labels for project %s with batch_size=%d.",
            len(label_data),
            resource_type,
            project_id,
            batch_size,
        )
    else:
        logger.debug(
            "No %s labels found for project %s.",
            resource_type,
            project_id,
        )
    load_labels(
        neo4j_session,
        label_data,
        resource_type,
        project_id,
        update_tag,
        batch_size=batch_size,
    )
    cleanup(neo4j_session, resource_type, common_job_parameters)
