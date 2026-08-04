import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.miradore.tenant import load_tenant
from cartography.intel.miradore.util import get_paginated_miradore_items
from cartography.intel.miradore.util import parse_datetime
from cartography.intel.miradore.util import required_int_id
from cartography.intel.miradore.util import scoped_id
from cartography.models.miradore.user import MiradoreUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ITEM = "User"
_RETIRED_STATUS = "Retired"
_SELECT = ",".join(
    (
        "ID",
        "Email",
        "Name",
        "Firstname",
        "Lastname",
        "Middle",
        "PhoneNumber",
        "Status",
        "Source",
        "Created",
        "Modified",
    )
)


@timeit
def get(
    api_session: requests.Session,
    base_uri: str,
    site_name: str,
    api_key: str,
) -> list[dict[str, Any]]:
    return get_paginated_miradore_items(
        api_session,
        base_uri,
        site_name,
        api_key,
        _ITEM,
        _SELECT,
    )


def transform(api_result: list[dict[str, Any]], site_name: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for user in api_result:
        status = user.get("Status")
        miradore_id = required_int_id(user, "User")
        result.append(
            {
                "id": scoped_id(site_name, miradore_id),
                "miradore_id": miradore_id,
                "email": user.get("Email"),
                "name": user.get("Name"),
                "firstname": user.get("Firstname"),
                "lastname": user.get("Lastname"),
                "middle": user.get("Middle"),
                "phone_number": user.get("PhoneNumber"),
                "status": status,
                # Miradore reports New, Active, Retired or System. Retired is the only
                # status that means the account is no longer usable, so derive the
                # boolean here and let the ontology invert it into `active`.
                "retired": status == _RETIRED_STATUS if status is not None else None,
                "source": user.get("Source"),
                "created": parse_datetime(user.get("Created")),
                "modified": parse_datetime(user.get("Modified")),
            }
        )
    return result


def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load_tenant(neo4j_session, tenant_id, update_tag)
    if not data:
        return
    load(
        neo4j_session,
        MiradoreUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(MiradoreUserSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    site_name: str,
    api_key: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, base_uri, site_name, api_key)
    users = transform(raw_data, site_name)
    load_users(neo4j_session, users, site_name, update_tag)
    cleanup(neo4j_session, common_job_parameters)
