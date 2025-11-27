import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.googleworkspace.group import GoogleWorkspaceGroupSchema
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceGroupToGroupInheritedMemberRel,
)
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceGroupToGroupInheritedOwnerRel,
)
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceGroupToGroupMemberRel,
)
from cartography.models.googleworkspace.group import GoogleWorkspaceGroupToGroupOwnerRel
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceUserToGroupInheritedMemberRel,
)
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceUserToGroupInheritedOwnerRel,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_groups(cloudidentity: Resource, customer_id: str) -> list[dict[str, Any]]:
    """
    Return list of Google Groups in your organization using Cloud Identity API.
    Returns empty list if we are unable to enumerate the groups for any reasons.

    :param cloudidentity: Google Cloud Identity resource object from googleapiclient.discovery.build
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param customer_id: The customer ID for the organization
    :return: list of Google groups in domain (transformed to match expected schema)
    """
    request = cloudidentity.groups().list(
        parent=f"customers/{customer_id}",
        pageSize=100,
        view="FULL",
    )
    response_objects = []
    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.extend(resp.get("groups", []))
            request = cloudidentity.groups().list_next(request, resp)
        except HttpError as e:
            if (
                e.resp.status == 403
                and "Request had insufficient authentication scopes" in str(e)
            ):
                logger.error(
                    "Missing required Google Workspace scopes. If using the gcloud CLI, "
                    "run: gcloud auth application-default login --scopes="
                    "https://www.googleapis.com/auth/admin.directory.customer.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.user.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.user.security,"
                    "https://www.googleapis.com/auth/cloud-identity.devices.readonly,"
                    "https://www.googleapis.com/auth/cloud-identity.groups.readonly,"
                    "https://www.googleapis.com/auth/cloud-platform"
                )
            raise
    return response_objects


@timeit
def get_members_for_groups(
    cloudidentity: Resource, group_names: list[str]
) -> dict[str, list[dict[str, Any]]]:
    """Get all members for given groups

    Args:
        cloudidentity (Resource): google's apiclient discovery resource object.  From googleapiclient.discovery.build
        See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
        groups_email (list[str]): List of group email addresses to get members for


    :return: list of dictionaries representing Users or Groups grouped by group email
    """
    results: dict[str, list[dict]] = {}
    for group_name in group_names:
        request = (
            cloudidentity.groups()
            .memberships()
            .list(
                parent=group_name,
                pageSize=100,
                view="FULL",
            )
        )
        members: list[dict] = []
        while request is not None:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            members = members + resp.get("memberships", [])
            request = cloudidentity.groups().memberships().list_next(request, resp)
        results[group_name] = members
    return results


@timeit
def get_user_inherited_member_relationships(
    neo4j_session: neo4j.Session,
    customer_id: str,
) -> list[dict[str, Any]]:
    """
    Query Neo4j to find User -> INHERITED_MEMBER_OF -> Group relationships.

    Finds users who are indirectly members of groups through the group hierarchy:
    User -[:MEMBER_OF]-> SubGroup -[:MEMBER_OF*1..]-> ParentGroup

    Returns list of relationship data for load_matchlinks():
    [
        {"user_id": "user-1", "group_id": "group-parent"},
        ...
    ]
    """
    query = """
        MATCH (t:GoogleWorkspaceTenant {id: $CUSTOMER_ID})-[:RESOURCE]->(u:GoogleWorkspaceUser),
              (u)-[:MEMBER_OF]->(g1:GoogleWorkspaceGroup)-[:MEMBER_OF*1..]->(g2:GoogleWorkspaceGroup)
        RETURN DISTINCT u.id AS user_id, g2.id AS group_id
    """
    result = neo4j_session.run(query, CUSTOMER_ID=customer_id)
    relationships = [dict(record) for record in result]
    logger.debug(
        "Found %d User INHERITED_MEMBER_OF Group relationships",
        len(relationships),
    )
    return relationships


@timeit
def get_user_inherited_owner_relationships(
    neo4j_session: neo4j.Session,
    customer_id: str,
) -> list[dict[str, Any]]:
    """
    Query Neo4j to find User -> INHERITED_OWNER_OF -> Group relationships.

    Finds users who are indirectly owners of groups through the group hierarchy:
    User -[:OWNER_OF]-> SubGroup -[:MEMBER_OF*1..]-> ParentGroup

    Returns list of relationship data for load_matchlinks():
    [
        {"user_id": "user-1", "group_id": "group-parent"},
        ...
    ]
    """
    query = """
        MATCH (t:GoogleWorkspaceTenant {id: $CUSTOMER_ID})-[:RESOURCE]->(u:GoogleWorkspaceUser),
              (u)-[:OWNER_OF]->(g1:GoogleWorkspaceGroup)-[:MEMBER_OF*1..]->(g2:GoogleWorkspaceGroup)
        RETURN DISTINCT u.id AS user_id, g2.id AS group_id
    """
    result = neo4j_session.run(query, CUSTOMER_ID=customer_id)
    relationships = [dict(record) for record in result]
    logger.debug(
        "Found %d User INHERITED_OWNER_OF Group relationships",
        len(relationships),
    )
    return relationships


@timeit
def get_group_inherited_member_relationships(
    neo4j_session: neo4j.Session,
    customer_id: str,
) -> list[dict[str, Any]]:
    """
    Query Neo4j to find Group -> INHERITED_MEMBER_OF -> Group relationships.

    Finds groups that are indirectly members of other groups through hierarchy:
    SubGroup1 -[:MEMBER_OF]-> SubGroup2 -[:MEMBER_OF*1..]-> ParentGroup

    Returns list of relationship data for load_matchlinks():
    [
        {"source_group_id": "group-sub1", "target_group_id": "group-parent"},
        ...
    ]
    """
    query = """
        MATCH (t:GoogleWorkspaceTenant {id: $CUSTOMER_ID})-[:RESOURCE]->(g1:GoogleWorkspaceGroup),
              (g1)-[:MEMBER_OF]->(g2:GoogleWorkspaceGroup)-[:MEMBER_OF*1..]->(g3:GoogleWorkspaceGroup)
        RETURN DISTINCT g1.id AS source_group_id, g3.id AS target_group_id
    """
    result = neo4j_session.run(query, CUSTOMER_ID=customer_id)
    relationships = [dict(record) for record in result]
    logger.debug(
        "Found %d Group INHERITED_MEMBER_OF Group relationships",
        len(relationships),
    )
    return relationships


@timeit
def get_group_inherited_owner_relationships(
    neo4j_session: neo4j.Session,
    customer_id: str,
) -> list[dict[str, Any]]:
    """
    Query Neo4j to find Group -> INHERITED_OWNER_OF -> Group relationships.

    Finds groups that are indirectly owners of other groups through hierarchy:
    SubGroup1 -[:OWNER_OF]-> SubGroup2 -[:MEMBER_OF*1..]-> ParentGroup

    Returns list of relationship data for load_matchlinks():
    [
        {"source_group_id": "group-sub1", "target_group_id": "group-parent"},
        ...
    ]
    """
    query = """
        MATCH (t:GoogleWorkspaceTenant {id: $CUSTOMER_ID})-[:RESOURCE]->(g1:GoogleWorkspaceGroup),
              (g1)-[:OWNER_OF]->(g2:GoogleWorkspaceGroup)-[:MEMBER_OF*1..]->(g3:GoogleWorkspaceGroup)
        RETURN DISTINCT g1.id AS source_group_id, g3.id AS target_group_id
    """
    result = neo4j_session.run(query, CUSTOMER_ID=customer_id)
    relationships = [dict(record) for record in result]
    logger.debug(
        "Found %d Group INHERITED_OWNER_OF Group relationships",
        len(relationships),
    )
    return relationships


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
        transformed_group = group.copy()
        # GroupKey.id can contains email address or not (for imported groups)
        if (
            "groupKey" in group
            and "id" in group["groupKey"]
            and "@" in group["groupKey"]["id"]
        ):
            transformed_group["email"] = group["groupKey"]["id"]
        # Serialize labels
        formated_labels: list[str] = []
        for key, value in group.get("labels", {}).items():
            if value:
                formated_labels.append(f"{key}:{value}")
            else:
                formated_labels.append(key)
        transformed_group["labels"] = formated_labels

        transformed_group["member_ids"] = []
        transformed_group["owner_ids"] = []

        for member in group_memberships.get(group["name"], []):
            is_owner: bool = False
            member_key_id = member.get("preferredMemberKey", {}).get("id")
            if member_key_id is None:
                continue

            for role_obj in member.get("roles", []):
                if role_obj.get("name") == "OWNER":
                    is_owner = True
                    break

            if member["type"] == "GROUP":
                # Create group-to-group relationships
                relationship_data = {
                    "parent_group_id": group["name"],
                    "subgroup_email": member_key_id,
                }

                if is_owner:
                    group_owner_relationships.append(relationship_data)
                else:
                    group_member_relationships.append(relationship_data)
                continue

            # Handle user memberships
            if is_owner:
                transformed_group["owner_ids"].append(member_key_id)
            transformed_group["member_ids"].append(member_key_id)

        transformed_groups.append(transformed_group)

    return transformed_groups, group_member_relationships, group_owner_relationships


@timeit
def load_googleworkspace_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict],
    customer_id: str,
    googleworkspace_update_tag: int,
) -> None:
    """
    Load Google Workspace groups using the modern data model
    """
    logger.info(
        "Ingesting %d Google Workspace groups for customer %s", len(groups), customer_id
    )

    # Load groups with relationship to tenant
    load(
        neo4j_session,
        GoogleWorkspaceGroupSchema(),
        groups,
        lastupdated=googleworkspace_update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def load_googleworkspace_group_to_group_relationships(
    neo4j_session: neo4j.Session,
    group_member_relationships: list[dict],
    group_owner_relationships: list[dict],
    customer_id: str,
    googleworkspace_update_tag: int,
) -> None:
    """
    Load Google Workspace group-to-group relationships using MatchLinks
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
            GoogleWorkspaceGroupToGroupMemberRel(),
            group_member_relationships,
            lastupdated=googleworkspace_update_tag,
            _sub_resource_label="GoogleWorkspaceTenant",
            _sub_resource_id=customer_id,
        )

    # Load group owner relationships (Group -> Group OWNER)
    if group_owner_relationships:
        load_matchlinks(
            neo4j_session,
            GoogleWorkspaceGroupToGroupOwnerRel(),
            group_owner_relationships,
            lastupdated=googleworkspace_update_tag,
            _sub_resource_label="GoogleWorkspaceTenant",
            _sub_resource_id=customer_id,
        )


@timeit
def load_googleworkspace_inherited_relationships(
    neo4j_session: neo4j.Session,
    user_member_rels: list[dict],
    user_owner_rels: list[dict],
    group_member_rels: list[dict],
    group_owner_rels: list[dict],
    customer_id: str,
    googleworkspace_update_tag: int,
) -> None:
    """
    Load inherited Google Workspace group relationships.

    These relationships represent indirect memberships and ownerships
    through the group hierarchy, computed via graph traversal.
    """
    logger.info("Computing inherited group relationships for customer %s", customer_id)

    if user_member_rels:
        load_matchlinks(
            neo4j_session,
            GoogleWorkspaceUserToGroupInheritedMemberRel(),
            user_member_rels,
            lastupdated=googleworkspace_update_tag,
            _sub_resource_label="GoogleWorkspaceTenant",
            _sub_resource_id=customer_id,
        )

    if user_owner_rels:
        load_matchlinks(
            neo4j_session,
            GoogleWorkspaceUserToGroupInheritedOwnerRel(),
            user_owner_rels,
            lastupdated=googleworkspace_update_tag,
            _sub_resource_label="GoogleWorkspaceTenant",
            _sub_resource_id=customer_id,
        )

    if group_member_rels:
        load_matchlinks(
            neo4j_session,
            GoogleWorkspaceGroupToGroupInheritedMemberRel(),
            group_member_rels,
            lastupdated=googleworkspace_update_tag,
            _sub_resource_label="GoogleWorkspaceTenant",
            _sub_resource_id=customer_id,
        )

    if group_owner_rels:
        load_matchlinks(
            neo4j_session,
            GoogleWorkspaceGroupToGroupInheritedOwnerRel(),
            group_owner_rels,
            lastupdated=googleworkspace_update_tag,
            _sub_resource_label="GoogleWorkspaceTenant",
            _sub_resource_id=customer_id,
        )

    logger.info("Finished computing inherited group relationships")


@timeit
def cleanup_googleworkspace_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    customer_id: str,
    googleworkspace_update_tag: int,
) -> None:
    """
    Clean up Google Workspace groups and group-to-group relationships using the modern data model
    """
    logger.debug("Running Google Workspace groups cleanup job")

    # Cleanup group nodes
    GraphJob.from_node_schema(GoogleWorkspaceGroupSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Cleanup group-to-group member relationships
    GraphJob.from_matchlink(
        GoogleWorkspaceGroupToGroupMemberRel(),
        "GoogleWorkspaceTenant",
        customer_id,
        googleworkspace_update_tag,
    ).run(neo4j_session)

    # Cleanup group-to-group owner relationships
    GraphJob.from_matchlink(
        GoogleWorkspaceGroupToGroupOwnerRel(),
        "GoogleWorkspaceTenant",
        customer_id,
        googleworkspace_update_tag,
    ).run(neo4j_session)

    # Cleanup inherited relationships
    logger.debug("Cleaning up inherited group relationships")

    # Cleanup User -> Group inherited relationships
    GraphJob.from_matchlink(
        GoogleWorkspaceUserToGroupInheritedMemberRel(),
        "GoogleWorkspaceTenant",
        customer_id,
        googleworkspace_update_tag,
    ).run(neo4j_session)

    GraphJob.from_matchlink(
        GoogleWorkspaceUserToGroupInheritedOwnerRel(),
        "GoogleWorkspaceTenant",
        customer_id,
        googleworkspace_update_tag,
    ).run(neo4j_session)

    # Cleanup Group -> Group inherited relationships
    GraphJob.from_matchlink(
        GoogleWorkspaceGroupToGroupInheritedMemberRel(),
        "GoogleWorkspaceTenant",
        customer_id,
        googleworkspace_update_tag,
    ).run(neo4j_session)

    GraphJob.from_matchlink(
        GoogleWorkspaceGroupToGroupInheritedOwnerRel(),
        "GoogleWorkspaceTenant",
        customer_id,
        googleworkspace_update_tag,
    ).run(neo4j_session)


@timeit
def sync_googleworkspace_groups(
    neo4j_session: neo4j.Session,
    cloudidentity: Resource,
    googleworkspace_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    GET Google Workspace group objects using the Cloud Identity API,
    load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param cloudidentity: Google Cloud Identity resource object created by `googleapiclient.discovery.build()`.
    Used for fetching groups and memberships via Cloud Identity API.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param googleworkspace_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing Google Workspace Groups")
    customer_id = common_job_parameters["CUSTOMER_ID"]

    # 1. GET - Fetch data from API
    resp_objs = get_all_groups(cloudidentity, customer_id)
    group_members = get_members_for_groups(
        cloudidentity, [resp["name"] for resp in resp_objs]
    )

    # 2. TRANSFORM - Shape data for ingestion
    groups, group_member_relationships, group_owner_relationships = transform_groups(
        resp_objs, group_members
    )

    # 3. LOAD - Ingest to Neo4j using data model
    load_googleworkspace_groups(
        neo4j_session, groups, customer_id, googleworkspace_update_tag
    )

    # Load group-to-group relationships after groups are loaded
    load_googleworkspace_group_to_group_relationships(
        neo4j_session,
        group_member_relationships,
        group_owner_relationships,
        customer_id,
        googleworkspace_update_tag,
    )

    # Load inherited relationships (computed via graph traversal)
    user_member_rels = get_user_inherited_member_relationships(
        neo4j_session, customer_id
    )
    user_owner_rels = get_user_inherited_owner_relationships(neo4j_session, customer_id)
    group_member_rels = get_group_inherited_member_relationships(
        neo4j_session, customer_id
    )
    group_owner_rels = get_group_inherited_owner_relationships(
        neo4j_session, customer_id
    )
    load_googleworkspace_inherited_relationships(
        neo4j_session,
        user_member_rels,
        user_owner_rels,
        group_member_rels,
        group_owner_rels,
        customer_id,
        googleworkspace_update_tag,
    )

    # 4. CLEANUP - Remove stale data
    cleanup_params = {**common_job_parameters, "CUSTOMER_ID": customer_id}
    cleanup_googleworkspace_groups(
        neo4j_session, cleanup_params, customer_id, googleworkspace_update_tag
    )
