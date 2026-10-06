import logging
from typing import Any
from typing import AsyncGenerator

import neo4j
from kiota_abstractions.api_error import APIError
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.groups.item.members.members_request_builder import (
    MembersRequestBuilder,
)
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.group import Group

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra.utils import call_with_retries
from cartography.intel.microsoft.entra.utils import (
    get_paginated_values_with_expired_page_retry,
)
from cartography.intel.microsoft.entra.utils import (
    iter_paginated_values_with_expired_page_retry,
)
from cartography.models.microsoft.entra.group import EntraGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GROUP_BATCH_SIZE = 100
# A tenant-wide group can have hundreds of thousands of members. Flushing on
# pending membership count, not just group count, keeps such a group from
# sitting in memory or in a single transaction whole.
PENDING_MEMBERSHIP_LIMIT = 10_000
MEMBERS_PAGE_SIZE = 999


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


async def get_group_member_pages(
    client: GraphServiceClient, group_id: str
) -> AsyncGenerator[tuple[list[str], list[str]], None]:
    """
    Yield (member user IDs, member subgroup IDs) one page at a time.

    Only member IDs are requested, and only one page of members is held at a
    time. An expired page token restarts paging from the first page, which
    re-yields IDs already seen; the group load is an idempotent MERGE, so the
    duplicates are harmless.
    """
    request_builder = client.groups.by_group_id(group_id).members
    request_configuration = RequestConfiguration(
        query_parameters=MembersRequestBuilder.MembersRequestBuilderGetQueryParameters(
            select=["id"],
            top=MEMBERS_PAGE_SIZE,
        ),
    )
    async for members in iter_paginated_values_with_expired_page_retry(
        lambda: request_builder.get(request_configuration=request_configuration),
        lambda next_link: request_builder.with_url(next_link).get(),
        f"members for Entra group {group_id}",
    ):
        user_ids: list[str] = []
        group_ids: list[str] = []
        for obj in members:
            if isinstance(obj, DirectoryObject):
                odata_type = getattr(obj, "odata_type", "")
                if odata_type == "#microsoft.graph.user":
                    user_ids.append(obj.id)
                elif odata_type == "#microsoft.graph.group":
                    group_ids.append(obj.id)
        yield user_ids, group_ids


@timeit
async def get_group_owners(client: GraphServiceClient, group_id: str) -> list[str]:
    """Get owner user IDs for a given group."""
    owner_ids: list[str] = []
    request_builder = client.groups.by_group_id(group_id).owners
    owners = await get_paginated_values_with_expired_page_retry(
        request_builder.get,
        lambda next_link: request_builder.with_url(next_link).get(),
        f"owners for Entra group {group_id}",
    )
    for obj in owners:
        odata_type = getattr(obj, "odata_type", "")
        if odata_type == "#microsoft.graph.user":
            owner_ids.append(obj.id)
    return owner_ids


def transform_group(
    group: Group,
    owner_ids: list[str],
    member_ids: list[str] | None = None,
    member_group_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": group.id,
        "display_name": group.display_name,
        "description": group.description,
        "mail": group.mail,
        "mail_nickname": group.mail_nickname,
        "mail_enabled": group.mail_enabled,
        "security_enabled": group.security_enabled,
        "group_types": group.group_types,
        "visibility": group.visibility,
        "is_assignable_to_role": group.is_assignable_to_role,
        "created_date_time": group.created_date_time,
        "deleted_date_time": group.deleted_date_time,
        "member_ids": member_ids or [],
        "member_group_ids": member_group_ids or [],
        "owner_ids": owner_ids,
    }


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
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
    client_id: str | None,
    client_secret: str | None,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    *,
    delegated_auth: bool = False,
) -> None:
    """Sync Entra groups, preserving stale data for delegated authentication."""
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
        delegated_auth=delegated_auth,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    pending_rows: list[dict[str, Any]] = []
    pending_groups = 0
    pending_memberships = 0

    def flush() -> None:
        nonlocal pending_rows, pending_groups, pending_memberships
        if pending_rows:
            load_groups(neo4j_session, pending_rows, update_tag, tenant_id)
        pending_rows = []
        pending_groups = 0
        pending_memberships = 0

    delegated_denial: APIError | None = None

    try:
        async for group in get_entra_groups(client):
            # The group may no longer exist by the time we fetch details,
            # returning a 404 or 410. Skip it and move on.
            try:
                owners = await call_with_retries(get_group_owners, client, group.id)
            except APIError as e:
                if e.response_status_code in (404, 410):
                    logger.warning(
                        "Group %s (%s) not found (%d) while fetching owners; skipping.",
                        group.id,
                        group.display_name,
                        e.response_status_code,
                    )
                    continue
                if delegated_auth and e.response_status_code == 403:
                    logger.warning(
                        "Microsoft Graph denied access to owners for Entra group "
                        "%s (%s); continuing without owners.",
                        group.id,
                        group.display_name,
                    )
                    delegated_denial = delegated_denial or e
                    # Delegated mode never runs relationship cleanup, so this
                    # does not erase owners collected by an earlier run.
                    owners = []
                else:
                    logger.exception(
                        "Failed to fetch owners for Entra group %s (%s).",
                        group.id,
                        group.display_name,
                    )
                    raise
            except Exception:
                logger.exception(
                    "Failed to fetch owners for Entra group %s (%s).",
                    group.id,
                    group.display_name,
                )
                raise

            # Each page of members becomes its own row for this group, so a
            # group with a huge membership is loaded across several flushes.
            member_pages_read = 0
            try:
                async for users, subgroups in get_group_member_pages(client, group.id):
                    pending_rows.append(
                        transform_group(group, owners, users, subgroups)
                    )
                    member_pages_read += 1
                    pending_memberships += len(users) + len(subgroups)
                    if pending_memberships >= PENDING_MEMBERSHIP_LIMIT:
                        flush()
            except APIError as e:
                if e.response_status_code in (404, 410):
                    if not member_pages_read:
                        logger.warning(
                            "Group %s (%s) not found (%d) while fetching members; "
                            "skipping.",
                            group.id,
                            group.display_name,
                            e.response_status_code,
                        )
                        continue
                    # Members already read may have been flushed, so keep the
                    # group rather than load it half-way and then disown it.
                    logger.warning(
                        "Group %s (%s) not found (%d) part way through its "
                        "members; keeping the members already read.",
                        group.id,
                        group.display_name,
                        e.response_status_code,
                    )
                elif delegated_auth and e.response_status_code == 403:
                    logger.warning(
                        "Microsoft Graph denied access to members for Entra group "
                        "%s (%s); continuing without members.",
                        group.id,
                        group.display_name,
                    )
                    delegated_denial = delegated_denial or e
                    # Delegated mode never runs relationship cleanup, so this
                    # does not erase members collected by an earlier run.
                else:
                    logger.exception(
                        "Failed to fetch members for Entra group %s (%s).",
                        group.id,
                        group.display_name,
                    )
                    raise
            except Exception:
                logger.exception(
                    "Failed to fetch members for Entra group %s (%s).",
                    group.id,
                    group.display_name,
                )
                raise

            if not member_pages_read:
                pending_rows.append(transform_group(group, owners))
            pending_groups += 1
            if pending_groups >= GROUP_BATCH_SIZE:
                flush()
    except APIError as error:
        if not delegated_auth or error.response_status_code != 403:
            raise
        delegated_denial = delegated_denial or error

    flush()

    if delegated_denial:
        raise delegated_denial

    if not delegated_auth:
        cleanup_groups(neo4j_session, common_job_parameters)
