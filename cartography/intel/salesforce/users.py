import logging
from collections import defaultdict
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import query_salesforce
from cartography.intel.salesforce.util import strip_attributes
from cartography.models.salesforce.user import SalesforceUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    instance_url = common_job_parameters["INSTANCE_URL"]
    users = get(api_session, instance_url)
    assignments = get_permission_set_assignments(api_session, instance_url)
    users = transform(users, assignments)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, instance_url: str) -> list[dict[str, Any]]:
    return query_salesforce(
        api_session,
        instance_url,
        "SELECT Id, Username, Name, Email, IsActive, UserType, ProfileId FROM User",
    )


@timeit
def get_permission_set_assignments(
    api_session: requests.Session, instance_url: str
) -> list[dict[str, Any]]:
    # Only standalone (non-profile-owned) permission set assignments; these mirror the
    # SalesforcePermissionSet nodes loaded by the permission_sets module.
    return query_salesforce(
        api_session,
        instance_url,
        "SELECT AssigneeId, PermissionSetId FROM PermissionSetAssignment "
        "WHERE PermissionSet.IsOwnedByProfile = false",
    )


def transform(
    users: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Attach the list of permission set IDs assigned to each user so the data model can
    build (:SalesforceUser)-[:HAS_PERMISSION_SET]->(:SalesforcePermissionSet) edges.
    """
    permission_sets_by_user: dict[str, list[str]] = defaultdict(list)
    for assignment in assignments:
        permission_sets_by_user[assignment["AssigneeId"]].append(
            assignment["PermissionSetId"]
        )

    transformed = strip_attributes(users)
    for user in transformed:
        user["permission_set_ids"] = permission_sets_by_user.get(user["Id"], [])
    return transformed


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
