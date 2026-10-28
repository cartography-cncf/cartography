from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import org_scoped_id
from cartography.intel.salesforce.util import SalesforceClient
from cartography.models.salesforce.userrole import SalesforceUserRoleSchema
from cartography.util import timeit

_FIELDS = "Id, Name, DeveloperName, ParentRoleId, RollupDescription, PortalType"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SalesforceClient,
    common_job_parameters: dict[str, Any],
) -> None:
    roles = get(client)
    roles = transform(roles, common_job_parameters["ORG_ID"])
    load_user_roles(
        neo4j_session,
        roles,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all(f"SELECT {_FIELDS} FROM UserRole")


def transform(roles: list[dict[str, Any]], org_id: str) -> list[dict[str, Any]]:
    for role in roles:
        role["id"] = org_scoped_id(org_id, role["Id"])
        parent_role_id = role.get("ParentRoleId")
        role["_parent_role_id"] = (
            org_scoped_id(org_id, parent_role_id) if parent_role_id else None
        )
    return roles


@timeit
def load_user_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SalesforceUserRoleSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SalesforceUserRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
