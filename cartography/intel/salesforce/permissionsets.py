from collections import defaultdict
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import parse_sf_datetime
from cartography.intel.salesforce.util import SalesforceClient
from cartography.models.salesforce.permissionset import SalesforcePermissionSetSchema
from cartography.util import timeit

# Exclude profile-owned permission sets: those mirror a Profile and are already
# represented by the SalesforceProfile node.
_PS_FIELDS = (
    "Id, Name, Label, Description, Type, IsOwnedByProfile, ProfileId, "
    "PermissionsModifyAllData, PermissionsViewAllData, PermissionsApiEnabled, "
    "NamespacePrefix, CreatedDate"
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SalesforceClient,
    common_job_parameters: dict[str, Any],
) -> None:
    permission_sets = get_permission_sets(client)
    assignments = get_assignments(client)
    permission_sets = transform(permission_sets, assignments)
    load_permission_sets(
        neo4j_session,
        permission_sets,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_permission_sets(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all(
        f"SELECT {_PS_FIELDS} FROM PermissionSet WHERE IsOwnedByProfile = false"
    )


@timeit
def get_assignments(client: SalesforceClient) -> list[dict[str, Any]]:
    # Only pull assignments for standalone permission sets, matching the node
    # filter above (profile-owned permission sets are represented by profiles).
    return client.query_all(
        "SELECT Id, AssigneeId, PermissionSetId FROM PermissionSetAssignment "
        "WHERE PermissionSet.IsOwnedByProfile = false"
    )


def transform(
    permission_sets: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assignees_by_set: dict[str, list[str]] = defaultdict(list)
    for assignment in assignments:
        assignees_by_set[assignment["PermissionSetId"]].append(assignment["AssigneeId"])
    for permission_set in permission_sets:
        permission_set["CreatedDate"] = parse_sf_datetime(
            permission_set.get("CreatedDate")
        )
        permission_set["_assignee_ids"] = assignees_by_set.get(permission_set["Id"], [])
    return permission_sets


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
