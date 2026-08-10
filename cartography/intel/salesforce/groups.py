from collections import defaultdict
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import SalesforceClient
from cartography.models.salesforce.group import SalesforceGroupSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SalesforceClient,
    common_job_parameters: dict[str, Any],
) -> None:
    groups = get_groups(client)
    members = get_members(client)
    groups = transform(groups, members)
    load_groups(
        neo4j_session,
        groups,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_groups(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all(
        "SELECT Id, Name, DeveloperName, Type, RelatedId FROM Group"
    )


@timeit
def get_members(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all("SELECT Id, GroupId, UserOrGroupId FROM GroupMember")


def transform(
    groups: list[dict[str, Any]],
    members: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    group_ids = {group["Id"] for group in groups}
    users_by_group: dict[str, list[str]] = defaultdict(list)
    groups_by_group: dict[str, list[str]] = defaultdict(list)
    for member in members:
        member_id = member["UserOrGroupId"]
        # A group member is either another group or a user; groups we synced win.
        if member_id in group_ids:
            groups_by_group[member["GroupId"]].append(member_id)
        else:
            users_by_group[member["GroupId"]].append(member_id)
    for group in groups:
        group["_member_user_ids"] = users_by_group.get(group["Id"], [])
        group["_member_group_ids"] = groups_by_group.get(group["Id"], [])
    return groups


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SalesforceGroupSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SalesforceGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
