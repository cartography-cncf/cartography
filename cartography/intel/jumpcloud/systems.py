import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jumpcloud.tenant import load_tenant
from cartography.intel.jumpcloud.util import paginated_get
from cartography.models.jumpcloud.system import JumpCloudSystemSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_BASE_URL = "https://console.jumpcloud.com/api/v2/assets/devices"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    org_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting JumpCloud systems sync")
    systems = get(session)
    transformed = transform(systems)
    load_systems(neo4j_session, transformed, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed JumpCloud systems sync")


@timeit
def get(session: requests.Session) -> list[dict[str, Any]]:
    return list(paginated_get(session, _BASE_URL))


def _get_field(system: dict[str, Any], *keys: str) -> Any:
    """Safely navigate nested field dicts, returning None if any key is missing."""
    value: Any = system.get("fields", {})
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _str_value(value: Any) -> str | None:
    """Extract a string from a field value that may be a plain string or a select dict."""
    if isinstance(value, dict):
        return value.get("name")
    return value


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for system in api_result:
        primary_users = _get_field(system, "Primary User", "value") or []
        primary_user = primary_users[0] if primary_users else {}
        result.append(
            {
                "id": system.get("id"),
                "jcSystemId": system.get("jcSystemId"),
                "primary_user": primary_user.get("name"),
                "primary_user_id": primary_user.get("id"),
                "model": _str_value(_get_field(system, "Model", "value")),
                "os_family": _str_value(_get_field(system, "OS Family", "value")),
                "os_version": _str_value(_get_field(system, "OS Version", "value")),
                "os": _str_value(_get_field(system, "Operating System (OS)", "value")),
                "status": _str_value(_get_field(system, "Status", "value")),
                "serial_number": _str_value(
                    _get_field(system, "Serial Number", "value")
                ),
            },
        )
    return result


@timeit
def load_systems(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load_tenant(neo4j_session, org_id, update_tag)
    load(
        neo4j_session,
        JumpCloudSystemSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(JumpCloudSystemSchema(), common_job_parameters).run(
        neo4j_session,
    )
