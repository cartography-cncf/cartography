import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import query_salesforce
from cartography.intel.salesforce.util import strip_attributes
from cartography.models.salesforce.profile import SalesforceProfileSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    profiles = get(api_session, common_job_parameters["INSTANCE_URL"])
    profiles = strip_attributes(profiles)
    load_profiles(
        neo4j_session,
        profiles,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, instance_url: str) -> list[dict[str, Any]]:
    return query_salesforce(
        api_session,
        instance_url,
        "SELECT Id, Name, UserType FROM Profile",
    )


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
