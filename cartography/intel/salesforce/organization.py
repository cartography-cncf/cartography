import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.salesforce.util import query_salesforce
from cartography.models.salesforce.organization import SalesforceOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> str:
    """
    Sync the Salesforce Organization (tenant) and return its 18-character Org ID so
    downstream syncs can scope their resources to it.
    """
    org = get(api_session, common_job_parameters["INSTANCE_URL"])
    load_organization(neo4j_session, org, common_job_parameters["UPDATE_TAG"])
    return org["Id"]


@timeit
def get(api_session: requests.Session, instance_url: str) -> dict[str, Any]:
    records = query_salesforce(
        api_session,
        instance_url,
        "SELECT Id, Name, InstanceName, OrganizationType, IsSandbox FROM Organization",
    )
    if not records:
        raise ValueError("Salesforce returned no Organization record.")
    return records[0]


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
