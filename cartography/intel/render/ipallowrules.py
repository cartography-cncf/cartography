import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.render.ipallowrule import RenderIPAllowRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Maps a raw resource list's role to the row key that carries its id in the output rows,
# and to the CartographyNodeSchema label recorded on `resourceType` for readability.
_RESOURCE_KIND_TO_ROW_KEY = {
    "environment": "environment_id",
    "service": "service_id",
    "postgres": "postgres_id",
    "keyvalue": "key_value_id",
}
_RESOURCE_KIND_TO_LABEL = {
    "environment": "RenderEnvironment",
    "service": "RenderService",
    "postgres": "RenderPostgres",
    "keyvalue": "RenderKeyValue",
}


def extract_rows(
    raw_items: list[dict[str, Any]],
    resource_kind: str,
    owner_id: str,
) -> list[dict[str, Any]]:
    """
    Flatten each raw resource's inline `ipAllowList` into standalone rule rows.

    :param raw_items: The un-transformed API objects for one resource type (environments,
        services, postgres, or key-value instances), each carrying its own id and an
        `ipAllowList` of `{cidrBlock, description}` entries.
    :param resource_kind: One of "environment", "service", "postgres", "keyvalue" -
        selects which id field the output rows are keyed on for the GOVERNS relationship.
    """
    row_key = _RESOURCE_KIND_TO_ROW_KEY[resource_kind]
    resource_type = _RESOURCE_KIND_TO_LABEL[resource_kind]
    rows = []
    for item in raw_items:
        resource_id = item.get("id")
        if not resource_id:
            continue
        for rule in item.get("ipAllowList") or []:
            cidr_block = rule.get("cidrBlock")
            if not cidr_block:
                continue
            rows.append(
                {
                    "id": f"{resource_id}/{cidr_block}",
                    "cidrBlock": cidr_block,
                    "description": rule.get("description"),
                    "ownerId": owner_id,
                    "resourceId": resource_id,
                    "resourceType": resource_type,
                    row_key: resource_id,
                }
            )
    return rows


@timeit
def load_ip_allow_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderIPAllowRuleSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderIPAllowRuleSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    owner_id: str,
    environments: list[dict[str, Any]],
    services: list[dict[str, Any]],
    postgres_instances: list[dict[str, Any]],
    key_value_instances: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Build RenderIPAllowRule nodes from the `ipAllowList` already embedded on each of the
    resource types passed in. This makes no network calls of its own - every raw resource
    list here was already fetched by that resource type's own sync().
    """
    rows: list[dict[str, Any]] = []
    rows.extend(extract_rows(environments, "environment", owner_id))
    rows.extend(extract_rows(services, "service", owner_id))
    rows.extend(extract_rows(postgres_instances, "postgres", owner_id))
    rows.extend(extract_rows(key_value_instances, "keyvalue", owner_id))
    load_ip_allow_rules(neo4j_session, rows, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
