import logging
from typing import Any

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.group import Group

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.entra.users import load_tenant
from cartography.models.entra.group import EntraGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_entra_groups(client: GraphServiceClient) -> list[Group]:
    """Get all groups from Microsoft Graph API with pagination."""
    all_groups: list[Group] = []

    request_configuration = client.groups.GroupsRequestBuilderGetRequestConfiguration(
        query_parameters=client.groups.GroupsRequestBuilderGetQueryParameters(top=999)
    )
    page = await client.groups.get(request_configuration=request_configuration)
    while page:
        if page.value:
            all_groups.extend(page.value)
        if not page.odata_next_link:
            break
        page = await client.groups.with_url(page.odata_next_link).get()

    return all_groups


@timeit
async def get_group_members(client: GraphServiceClient, group_id: str) -> list[str]:
    """Get member user IDs for a given group."""
    members: list[str] = []
    request_builder = client.groups.by_group_id(group_id).members
    page = await request_builder.get()
    while page:
        if page.value:
            for obj in page.value:
                if isinstance(obj, DirectoryObject):
                    # Filter to user objects based on odata_type
                    if getattr(obj, "odata_type", "") == "#microsoft.graph.user":
                        members.append(obj.id)
        if not page.odata_next_link:
            break
        page = await request_builder.with_url(page.odata_next_link).get()
    return members


def transform_groups(
    groups: list[Group], member_map: dict[str, list[str]]
) -> list[dict[str, Any]]:
    """Transform API responses into dictionaries for ingestion."""
    result: list[dict[str, Any]] = []
    for g in groups:
        transformed = {
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
            "member_ids": member_map.get(g.id, []),
        }
        result.append(transformed)
    return result


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

    groups = await get_entra_groups(client)

    member_map: dict[str, list[str]] = {}
    for group in groups:
        try:
            member_map[group.id] = await get_group_members(client, group.id)
        except Exception as e:
            logger.error(f"Failed to fetch members for group {group.id}: {e}")
            member_map[group.id] = []

    transformed_groups = transform_groups(groups, member_map)

    load_tenant(neo4j_session, {"id": tenant_id}, update_tag)
    load_groups(neo4j_session, transformed_groups, update_tag, tenant_id)
    cleanup_groups(neo4j_session, common_job_parameters)
