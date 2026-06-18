import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import query_salesforce
from cartography.intel.salesforce.util import strip_attributes
from cartography.models.salesforce.permission_set import SalesforcePermissionSetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    permission_sets = get(api_session, common_job_parameters["INSTANCE_URL"])
    permission_sets = strip_attributes(permission_sets)
    load_permission_sets(
        neo4j_session,
        permission_sets,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, instance_url: str) -> list[dict[str, Any]]:
    # Profile-owned permission sets are Salesforce's internal representation of a
    # profile's permissions; they are excluded here so that base permissions are
    # modeled via HAS_PROFILE and only standalone (additive) permission sets become
    # SalesforcePermissionSet nodes.
    return query_salesforce(
        api_session,
        instance_url,
        "SELECT Id, Name, Label, Type, IsOwnedByProfile FROM PermissionSet "
        "WHERE IsOwnedByProfile = false",
    )


@timeit
def load_permission_sets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SalesforcePermissionSetSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        SalesforcePermissionSetSchema(), common_job_parameters
    ).run(neo4j_session)
