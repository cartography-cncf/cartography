from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import parse_sf_datetime
from cartography.intel.salesforce.util import SalesforceClient
from cartography.models.salesforce.profile import SalesforceProfileSchema
from cartography.util import timeit

_FIELDS = (
    "Id, Name, UserType, Description, PermissionsModifyAllData, "
    "PermissionsViewAllData, PermissionsApiEnabled, PermissionsManageUsers, "
    "CreatedDate"
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SalesforceClient,
    common_job_parameters: dict[str, Any],
) -> None:
    profiles = get(client)
    profiles = transform(profiles)
    load_profiles(
        neo4j_session,
        profiles,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all(f"SELECT {_FIELDS} FROM Profile")


def transform(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for profile in profiles:
        profile["CreatedDate"] = parse_sf_datetime(profile.get("CreatedDate"))
    return profiles


@timeit
def load_profiles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SalesforceProfileSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SalesforceProfileSchema(), common_job_parameters).run(
        neo4j_session
    )
