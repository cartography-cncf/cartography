import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.gsuite.group import GSuiteGroupSchema
from cartography.models.gsuite.group import GSuiteGroupToGroupMemberRel
from cartography.models.gsuite.group import GSuiteGroupToGroupOwnerRel
from cartography.models.gsuite.tenant import GSuiteTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_groups(
    admin: Resource, customer_id: str = "my_customer"
) -> list[dict[str, Any]]:
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons

    googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)

    :param admin: google's apiclient discovery resource object.  From googleapiclient.discovery.build
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: list of Google groups in domain
    """
    request = admin.groups().list(
        customer=customer_id,
        maxResults=20,
        orderBy="email",
    )
    response_objects = []
    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.extend(resp.get("groups", []))
            request = admin.groups().list_next(request, resp)
        except HttpError as e:
            if (
                e.resp.status == 403
                and "Request had insufficient authentication scopes" in str(e)
            ):
                logger.error(
                    "Missing required GSuite scopes. If using the gcloud CLI, "
                    "run: gcloud auth application-default login --scopes="
                    '"https://www.googleapis.com/auth/admin.directory.user.readonly,'
                    "https://www.googleapis.com/auth/admin.directory.group.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.group.member.readonly,"
                    'https://www.googleapis.com/auth/cloud-platform"'
                )
            raise
    return response_objects


@timeit
def get_members_for_groups(
    admin: Resource, groups_email: list[str]
) -> dict[str, list[dict[str, Any]]]:
    """Get all members for given groups emails

    Args:
        admin (Resource): google's apiclient discovery resource object.  From googleapiclient.discovery.build
        See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
        groups_email (list[str]): List of group email addresses to get members for


    :return: list of dictionaries representing Users or Groups grouped by group email
    """
    results: dict[str, list[dict]] = {}
    for group_email in groups_email:
        request = admin.members().list(
            groupKey=group_email,
            maxResults=500,
        )
        members: list[dict] = []
        while request is not None:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            members = members + resp.get("members", [])
            request = admin.members().list_next(request, resp)
        results[group_email] = members

    return results


@timeit
def transform_groups(
    groups: list[dict], group_memberships: dict[str, list[dict[str, Any]]]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Strips list of API response objects to return list of group objects only and lists of subgroup relationships

    :param groups: Raw groups from Google API
    :param group_memberships: Group memberships data
    :return: tuple of (groups, group_member_relationships, group_owner_relationships)
    """
    transformed_groups: list[dict] = []
    group_member_relationships: list[dict] = []
    group_owner_relationships: list[dict] = []

    for group in groups:
        group_id = group["id"]
        group_email = group["email"]
        group["member_ids"] = []
        group["owner_ids"] = []

        for member in group_memberships.get(group_email, []):
            if member["type"] == "GROUP":
                # Create group-to-group relationships
                relationship_data = {
                    "parent_group_id": group_id,
                    "subgroup_id": member.get("id"),
                    "role": member.get("role"),
                }

                if member.get("role") == "OWNER":
                    group_owner_relationships.append(relationship_data)
                else:
                    group_member_relationships.append(relationship_data)
                continue

            # Handle user memberships
            if member.get("role") == "OWNER":
                group["owner_ids"].append(member.get("id"))
            group["member_ids"].append(member.get("id"))

        transformed_groups.append(group)

    return transformed_groups, group_member_relationships, group_owner_relationships


@timeit
def load_gsuite_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict],
    customer_id: str,
    gsuite_update_tag: int,
) -> None:
    """
    Load GSuite groups using the modern data model
    """
    logger.info("Ingesting %d gsuite groups", len(groups))

    # Load tenant first if it doesn't exist
    tenant_data = [{"id": customer_id}]
    load(
        neo4j_session,
        GSuiteTenantSchema(),
        tenant_data,
        lastupdated=gsuite_update_tag,
    )

    # Load groups with relationship to tenant
    load(
        neo4j_session,
        GSuiteGroupSchema(),
        groups,
        lastupdated=gsuite_update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def load_gsuite_group_to_group_relationships(
    neo4j_session: neo4j.Session,
    group_member_relationships: list[dict],
    group_owner_relationships: list[dict],
    customer_id: str,
    gsuite_update_tag: int,
) -> None:
    """
    Load GSuite group-to-group relationships using MatchLinks
    """
    logger.info(
        "Ingesting %d group member relationships", len(group_member_relationships)
    )
    logger.info(
        "Ingesting %d group owner relationships", len(group_owner_relationships)
    )

    # Load group member relationships (Group -> Group MEMBER)
    if group_member_relationships:
        load_matchlinks(
            neo4j_session,
            GSuiteGroupToGroupMemberRel(),
            group_member_relationships,
            lastupdated=gsuite_update_tag,
            _sub_resource_label="GSuiteTenant",
            _sub_resource_id=customer_id,
        )

    # Load group owner relationships (Group -> Group OWNER)
    if group_owner_relationships:
        load_matchlinks(
            neo4j_session,
            GSuiteGroupToGroupOwnerRel(),
            group_owner_relationships,
            lastupdated=gsuite_update_tag,
            _sub_resource_label="GSuiteTenant",
            _sub_resource_id=customer_id,
        )


@timeit
def cleanup_gsuite_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    customer_id: str,
    gsuite_update_tag: int,
) -> None:
    """
    Clean up GSuite groups and group-to-group relationships using the modern data model
    """
    logger.debug("Running GSuite groups cleanup job")

    # Cleanup group nodes
    GraphJob.from_node_schema(GSuiteGroupSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Cleanup group-to-group member relationships
    GraphJob.from_matchlink(
        GSuiteGroupToGroupMemberRel(),
        "GSuiteTenant",
        customer_id,
        gsuite_update_tag,
    ).run(neo4j_session)

    # Cleanup group-to-group owner relationships
    GraphJob.from_matchlink(
        GSuiteGroupToGroupOwnerRel(),
        "GSuiteTenant",
        customer_id,
        gsuite_update_tag,
    ).run(neo4j_session)


@timeit
def sync_gsuite_groups(
    neo4j_session: neo4j.Session,
    admin: Resource,
    gsuite_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    GET GSuite group objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gsuite_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GSuite Groups")

    customer_id = common_job_parameters.get(
        "CUSTOMER_ID", "my_customer"
    )  # Default to "my_customer" for backward compatibility

    # 1. GET - Fetch data from API
    resp_objs = get_all_groups(admin, customer_id)
    group_members = get_members_for_groups(admin, [resp["email"] for resp in resp_objs])

    # 2. TRANSFORM - Shape data for ingestion
    groups, group_member_relationships, group_owner_relationships = transform_groups(
        resp_objs, group_members
    )

    # 3. LOAD - Ingest to Neo4j using data model
    load_gsuite_groups(neo4j_session, groups, customer_id, gsuite_update_tag)

    # Load group-to-group relationships after groups are loaded
    load_gsuite_group_to_group_relationships(
        neo4j_session,
        group_member_relationships,
        group_owner_relationships,
        customer_id,
        gsuite_update_tag,
    )

    # 4. CLEANUP - Remove stale data
    cleanup_params = {**common_job_parameters, "CUSTOMER_ID": customer_id}
    cleanup_gsuite_groups(neo4j_session, cleanup_params, customer_id, gsuite_update_tag)
