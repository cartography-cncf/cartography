import logging
from typing import Any
from typing import AsyncGenerator
from typing import Generator

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.group import Group

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.entra.group import EntraGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_entra_groups(client: GraphServiceClient) -> AsyncGenerator[Group, None]:
    """Get all groups from Microsoft Graph API with pagination using a generator."""
    request_configuration = client.groups.GroupsRequestBuilderGetRequestConfiguration(
        query_parameters=client.groups.GroupsRequestBuilderGetQueryParameters(top=999)
    )
    page = await client.groups.get(request_configuration=request_configuration)
    while page:
        if page.value:
            for group in page.value:
                yield group
        if not page.odata_next_link:
            break
        page = await client.groups.with_url(page.odata_next_link).get()


@timeit
async def get_group_members(
    client: GraphServiceClient, group_id: str
) -> tuple[list[str], list[str]]:
    """Get member user IDs and subgroup IDs for a given group."""
    user_ids: list[str] = []
    group_ids: list[str] = []
    request_builder = client.groups.by_group_id(group_id).members
    page = await request_builder.get()
    while page:
        if page.value:
            for obj in page.value:
                if isinstance(obj, DirectoryObject):
                    odata_type = getattr(obj, "odata_type", "")
                    if odata_type == "#microsoft.graph.user":
                        user_ids.append(obj.id)
                    elif odata_type == "#microsoft.graph.group":
                        group_ids.append(obj.id)
        if not page.odata_next_link:
            break
        page = await request_builder.with_url(page.odata_next_link).get()
    return user_ids, group_ids


@timeit
async def get_group_owners(client: GraphServiceClient, group_id: str) -> list[str]:
    """Get owner user IDs for a given group."""
    owner_ids: list[str] = []
    request_builder = client.groups.by_group_id(group_id).owners
    page = await request_builder.get()
    while page:
        if page.value:
            for obj in page.value:
                odata_type = getattr(obj, "odata_type", "")
                if odata_type == "#microsoft.graph.user":
                    owner_ids.append(obj.id)
        if not page.odata_next_link:
            break
        page = await request_builder.with_url(page.odata_next_link).get()
    return owner_ids


def transform_groups(
    groups: list[Group],
    user_member_map: dict[str, list[str]],
    group_member_map: dict[str, list[str]],
    group_owner_map: dict[str, list[str]],
) -> Generator[dict[str, Any], None, None]:
    """Transform API responses into dictionaries for ingestion using a generator."""
    for g in groups:
        yield {
            "id": g.id,
            "display_name": g.display_name,
            "description": g.description,
            "mail": g.mail,
            "mail_nickname": g.mail_nickname,
            "mail_enabled": g.mail_enabled,
            "security_enabled": g.security_enabled,
            "group_types": g.group_types,
            "visibility": g.visibility,
            "is_assignable_to_role": g.is_assignable_to_role,
            "created_date_time": g.created_date_time,
            "deleted_date_time": g.deleted_date_time,
            "member_ids": user_member_map.get(g.id, []),
            "member_group_ids": group_member_map.get(g.id, []),
            "owner_ids": group_owner_map.get(g.id, []),
        }


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
    logger.info(f"Loading {len(groups)} Entra groups")
    load(
        neo4j_session,
        EntraGroupSchema(),
        groups,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup_groups(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(EntraGroupSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync_entra_groups(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync Entra groups."""
    credential = ClientSecretCredential(
        tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    # Collect groups in batches to avoid loading all at once
    groups_batch = []
    batch_size = 100  # Process groups in batches

    user_member_map: dict[str, list[str]] = {}
    group_member_map: dict[str, list[str]] = {}
    group_owner_map: dict[str, list[str]] = {}

    # First pass: collect groups and their owners/members
    async for group in get_entra_groups(client):
        groups_batch.append(group)

        # Fetch owners and members for this group
        owners = await get_group_owners(client, group.id)
        group_owner_map[group.id] = owners

        try:
            users, subgroups = await get_group_members(client, group.id)
            user_member_map[group.id] = users
            group_member_map[group.id] = subgroups
        except Exception as e:
            logger.error(f"Failed to fetch members for group {group.id}: {e}")
            user_member_map[group.id] = []
            group_member_map[group.id] = []

        # Process batch when it reaches the size limit
        if len(groups_batch) >= batch_size:
            transformed_groups = list(
                transform_groups(
                    groups_batch, user_member_map, group_member_map, group_owner_map
                )
            )
            load_groups(neo4j_session, transformed_groups, update_tag, tenant_id)

            # Clear the batch and maps for processed groups
            for g in groups_batch:
                user_member_map.pop(g.id, None)
                group_member_map.pop(g.id, None)
                group_owner_map.pop(g.id, None)
            groups_batch.clear()

    # Process any remaining groups
    if groups_batch:
        transformed_groups = list(
            transform_groups(
                groups_batch, user_member_map, group_member_map, group_owner_map
            )
        )
        load_groups(neo4j_session, transformed_groups, update_tag, tenant_id)

    cleanup_groups(neo4j_session, common_job_parameters)
