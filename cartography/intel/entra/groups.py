import logging
from typing import Any, AsyncIterator, Iterable, Iterator, List

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.group import Group
from msgraph.generated.models.user import User

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.entra.users import load_tenant
from cartography.models.entra.group import EntraGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GROUP_BUFFER_SIZE = 5000  # Fewer DB transactions while staying memory-safe

@timeit
async def get_entra_groups(client: GraphServiceClient) -> AsyncIterator[list[Group]]:
    """Yield pages of groups from Microsoft Graph API."""
    request_configuration = client.groups.GroupsRequestBuilderGetRequestConfiguration(
        query_parameters=client.groups.GroupsRequestBuilderGetQueryParameters(
            top=999,
            select=[
                "id",
                "displayName",
                "description",
                "mail",
                "mailNickname",
                "mailEnabled",
                "securityEnabled",
                "groupTypes",
                "visibility",
                "isAssignableToRole",
                "createdDateTime",
                "deletedDateTime",
            ],
            # Graph allows only one expand in many cases; expand members per-page,
            # and fetch owners separately per group if needed.
            expand=["members($select=id)"],
        )
    )
    page = await client.groups.get(request_configuration=request_configuration)
    while page:
        if page.value:
            yield page.value
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
    groups: Iterable[Group],
    user_member_map: dict[str, list[str]],
    group_member_map: dict[str, list[str]],
    group_owner_map: dict[str, list[str]],
) -> Iterator[dict[str, Any]]:
    """Transform API responses into dictionaries for ingestion."""
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
    groups: Iterable[dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> int:
    group_list = groups if isinstance(groups, list) else list(groups)
    logger.info(f"Loading {len(group_list)} Entra groups")
    load(
        neo4j_session,
        EntraGroupSchema(),
        group_list,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )
    return len(group_list)


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

    load_tenant(neo4j_session, {"id": tenant_id}, update_tag)

    total_groups = 0
    # Buffer to limit memory while reducing transaction overhead
    group_buffer: List[dict[str, Any]] = []
    async for groups_page in get_entra_groups(client):
        # Build maps from expanded owners/members to avoid per-group API calls
        user_member_map: dict[str, list[str]] = {}
        group_member_map: dict[str, list[str]] = {}
        group_owner_map: dict[str, list[str]] = {}

        for group in groups_page:
            user_ids: list[str] = []
            subgroup_ids: list[str] = []

            for obj in getattr(group, "members", []) or []:
                # Prefer isinstance to avoid relying on @odata.type selection
                if isinstance(obj, User):
                    user_ids.append(obj.id)
                elif isinstance(obj, Group):
                    subgroup_ids.append(obj.id)

            # Owners not expanded; fetch per group
            try:
                owners_ids = await get_group_owners(client, group.id)
            except Exception as e:
                logger.error(f"Failed to fetch owners for group {group.id}: {e}")
                owners_ids = []

            user_member_map[group.id] = user_ids
            group_member_map[group.id] = subgroup_ids
            group_owner_map[group.id] = owners_ids

        for transformed in transform_groups(
            groups_page, user_member_map, group_member_map, group_owner_map
        ):
            group_buffer.append(transformed)
            if len(group_buffer) >= GROUP_BUFFER_SIZE:
                total_groups += load_groups(
                    neo4j_session, group_buffer, update_tag, tenant_id
                )
                group_buffer.clear()

    # Flush any remaining groups
    if group_buffer:
        total_groups += load_groups(neo4j_session, group_buffer, update_tag, tenant_id)
        group_buffer.clear()

    logger.info(f"Loaded {total_groups} Entra groups")
    cleanup_groups(neo4j_session, common_job_parameters)
