from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import parse_sf_datetime
from cartography.intel.salesforce.util import SalesforceClient
from cartography.models.salesforce.user import SalesforceUserSchema
from cartography.util import timeit

_FIELDS = (
    "Id, Username, Name, FirstName, LastName, Email, Alias, IsActive, UserType, "
    "ProfileId, UserRoleId, ManagerId, Department, Title, FederationIdentifier, "
    "CreatedDate, LastLoginDate, LastPasswordChangeDate"
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SalesforceClient,
    common_job_parameters: dict[str, Any],
) -> None:
    users = get(client)
    users = transform(users)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all(f"SELECT {_FIELDS} FROM User")


def transform(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for user in users:
        user["CreatedDate"] = parse_sf_datetime(user.get("CreatedDate"))
        user["LastLoginDate"] = parse_sf_datetime(user.get("LastLoginDate"))
        user["LastPasswordChangeDate"] = parse_sf_datetime(
            user.get("LastPasswordChangeDate")
        )
    return users


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SalesforceUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SalesforceUserSchema(), common_job_parameters).run(
        neo4j_session
    )
