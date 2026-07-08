from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import parse_sf_datetime
from cartography.intel.salesforce.util import SalesforceClient
from cartography.models.salesforce.organization import SalesforceOrganizationSchema
from cartography.util import timeit

_FIELDS = (
    "Id, Name, OrganizationType, InstanceName, IsSandbox, PrimaryContact, "
    "Country, LanguageLocaleKey, NamespacePrefix, TrialExpirationDate, CreatedDate"
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SalesforceClient,
    common_job_parameters: dict[str, Any],
) -> dict[str, Any]:
    org = get(client)
    org = transform(org)
    load_organization(neo4j_session, org, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return org


@timeit
def get(client: SalesforceClient) -> dict[str, Any]:
    records = client.query_all(f"SELECT {_FIELDS} FROM Organization")
    return records[0]


def transform(org: dict[str, Any]) -> dict[str, Any]:
    org["CreatedDate"] = parse_sf_datetime(org.get("CreatedDate"))
    org["TrialExpirationDate"] = parse_sf_datetime(org.get("TrialExpirationDate"))
    return org


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    org: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SalesforceOrganizationSchema(),
        [org],
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        SalesforceOrganizationSchema(), common_job_parameters
    ).run(neo4j_session)
