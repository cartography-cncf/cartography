import logging
import re
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentra import api
from cartography.intel.sentra.data_stores import AWS_RESOURCE_ID_FIELDS
from cartography.models.sentra.alert import SentraAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Cleanup removes alerts that Sentra resolved or ignored, so a sync fetches only the
# statuses that still need attention.
ACTIVE_ALERT_STATUSES = ["pending", "opened", "in_progress"]

# Maps each AWS ID field of a data store to the alert field that lists the AWS
# resources of that type that the alert affects, for example `aws_s3_bucket_name`
# to `affected_aws_s3_bucket_names`.
_AFFECTED_AWS_RESOURCE_FIELDS = {
    field: f"affected_{field}s" for field in AWS_RESOURCE_ID_FIELDS
}

# Statuses from the violated objects endpoint that concern a single alert.
_ALERT_SPECIFIC_ERROR_STATUSES = (404, 422)

_AWS_ROLE_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)*:iam::\d{12}:role/.+$")


@timeit
def get(session: requests.Session, api_url: str) -> Iterator[list[dict[str, Any]]]:
    yield from api.iter_search_pages(
        session,
        api_url,
        api.ALERTS_SEARCH_PATH,
        filters={"status": {"op": "EQ", "values": ACTIVE_ALERT_STATUSES}},
    )


def get_violated_objects(
    session: requests.Session,
    api_url: str,
    alert_id: str,
) -> Iterator[dict[str, Any]]:
    """
    Yield the data store and data classes of each object that violates an alert's policy.

    The fetch is all or nothing: every page is read before the first object is
    yielded, so an alert never loads with links from only some pages. Objects with
    the same store and data classes collapse into one, which keeps memory small
    when an alert has many violating objects.

    A 404 or 422 concerns only this alert, for example an alert that Sentra resolved
    during the sync, so the alert loads without violated-object links. Other errors
    mean that the sync can't read Sentra, so they propagate.
    """
    distinct: set[tuple[str, frozenset[str]]] = set()
    try:
        for violated_object in api.iter_violated_objects(session, api_url, alert_id):
            distinct.add(
                (
                    violated_object["store_id"],
                    frozenset(
                        data_class["id"]
                        for data_class in violated_object.get("data_classes") or []
                    ),
                ),
            )
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status not in _ALERT_SPECIFIC_ERROR_STATUSES:
            raise
        logger.warning(
            "Sentra returned HTTP %s for the violated objects of alert %s; "
            "loading the alert without them.",
            status,
            alert_id,
        )
        return
    for store_id, data_class_ids in distinct:
        yield {
            "store_id": store_id,
            "data_classes": [{"id": data_class_id} for data_class_id in data_class_ids],
        }


def transform(
    raw_alerts: list[dict[str, Any]],
    violated_objects: Mapping[str, Iterable[dict[str, Any]]] | None = None,
    aws_ids_by_store: Mapping[str, Mapping[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """
    Shape alerts for ingestion.

    `violated_objects` maps an alert ID to the objects that violate the alert's
    policy. The stores and data classes of those objects become `AFFECTS` and
    `INVOLVES` links.

    `aws_ids_by_store` maps a data store ID to the IDs of the AWS resource that the
    store represents. An alert links with `AFFECTS` to the AWS resource of every
    data store that it affects, in addition to the data store itself.
    """
    violated_objects = violated_objects or {}
    aws_ids_by_store = aws_ids_by_store or {}
    result: list[dict[str, Any]] = []
    for alert in raw_alerts:
        entity_type = alert["entity_type"]
        entity = alert.get("entity") or {}
        cloud_unique_id = entity.get("cloud_unique_id")

        affected_data_store_ids: set[str] = set()
        if entity_type == "STORE":
            affected_data_store_ids.add(alert["entity_id"])
        violated_data_class_ids: set[str] = set()
        for violated_object in violated_objects.get(alert["id"], ()):
            affected_data_store_ids.add(violated_object["store_id"])
            violated_data_class_ids.update(
                data_class["id"]
                for data_class in violated_object.get("data_classes") or []
            )

        affected_aws_resources: dict[str, set[str]] = {
            field: set() for field in _AFFECTED_AWS_RESOURCE_FIELDS.values()
        }
        for store_id in affected_data_store_ids:
            for id_field, aws_id in aws_ids_by_store.get(store_id, {}).items():
                affected_aws_resources[_AFFECTED_AWS_RESOURCE_FIELDS[id_field]].add(
                    aws_id,
                )

        result.append(
            {
                "id": alert["id"],
                "name": alert["name"],
                "description": alert.get("description"),
                "recommendation": alert.get("recommendation"),
                "severity": alert["severity"],
                "status": alert["status"],
                "status_reason": alert.get("status_reason"),
                "alert_type": alert["type"],
                "risk_type": alert.get("risk_type"),
                "policy_id": alert["policy_id"],
                "policy_type": alert.get("Policy__type"),
                "frameworks": alert.get("frameworks") or [],
                "tags": alert.get("tags") or [],
                "entity_type": entity_type,
                "entity_id": alert["entity_id"],
                "entity_name": entity.get("name"),
                "entity_cloud_unique_id": cloud_unique_id,
                "connector_id": alert["connector_id"],
                "connector_account_id": alert.get("Connector__account_id"),
                "connector_account_type": alert.get("Connector__account_type"),
                "sensitivity_level": alert.get("sensitivity_level"),
                "data_class_ids": [
                    data_class["id"] for data_class in alert.get("data_classes") or []
                ],
                "occurrences": alert.get("occurrences"),
                "total_violated_assets_count": alert.get(
                    "total_violated_assets_count",
                ),
                "created_at": alert.get("created_at"),
                "opened_at": alert.get("opened_at"),
                "last_modified": alert.get("last_modified"),
                "affected_data_store_ids": sorted(affected_data_store_ids),
                "violated_data_class_ids": sorted(violated_data_class_ids),
                **{
                    field: sorted(aws_ids)
                    for field, aws_ids in affected_aws_resources.items()
                },
                "affected_aws_role_arn": (
                    cloud_unique_id
                    if entity_type == "IAM_ROLE"
                    and cloud_unique_id
                    and _AWS_ROLE_ARN_RE.match(cloud_unique_id)
                    else None
                ),
            },
        )
    return result


@timeit
def load_alerts(
    neo4j_session: neo4j.Session,
    data: Iterable[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentraAlertSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentraAlertSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    aws_ids_by_store: Mapping[str, Mapping[str, str]],
) -> None:
    logger.info("Syncing Sentra alerts for organization %s", tenant_id)
    alerts = (
        alert
        for page in get(session, api_url)
        for alert in transform(
            page,
            # Only store alerts have violated objects. Each generator fetches its
            # alert's objects when the transform reaches that alert.
            {
                raw["id"]: get_violated_objects(session, api_url, raw["id"])
                for raw in page
                if raw["entity_type"] == "STORE"
            },
            aws_ids_by_store,
        )
    )
    load_alerts(neo4j_session, alerts, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
