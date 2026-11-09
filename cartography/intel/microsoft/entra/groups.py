import asyncio
import logging
from typing import Any
from typing import AsyncGenerator
from typing import AsyncIterator
from typing import Callable
from typing import Coroutine

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
# Owners and members cost at least two Graph calls per group. Fetched one group
# at a time, a directory with 100k+ groups takes hours and outlives a delegated
# access token. The Graph SDK's retry middleware honors 429 Retry-After, so
# going wider than this mostly trades latency for throttling.
GROUP_DETAIL_CONCURRENCY = 20


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
        "membership_rule": group.membership_rule,
        "membership_rule_processing_state": group.membership_rule_processing_state,
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


async def run_bounded(
    items: AsyncIterator[Group],
    worker: Callable[[Group], Coroutine[Any, Any, None]],
    limit: int,
) -> None:
    """
    Run `worker` over `items` with at most `limit` calls in flight.

    The first worker failure is re-raised as is and the rest are cancelled, so
    an unexpected error stops the sync instead of surfacing hours later.
    """
    pending: set[asyncio.Task[None]] = set()

    async def drain(until: int) -> None:
        nonlocal pending
        while len(pending) > until:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                task.result()

    try:
        async for item in items:
            await drain(limit - 1)
            pending.add(asyncio.create_task(worker(item)))
        await drain(0)
    finally:
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


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
    access_token: str | None = None,
) -> None:
    """Sync Entra groups, preserving stale data for delegated authentication."""
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
        delegated_auth=delegated_auth,
        access_token=access_token,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    delegated_denial: APIError | None = None

    # Pass 1 loads every group node straight from the group list, at one call
    # per 999 groups. A subgroup's MEMBER_OF edge only matches once the
    # subgroup's node exists, and Graph can list a group before the groups
    # nested in it, so owners and memberships wait for pass 2. Listing groups
    # twice keeps memory bounded.
    group_rows: list[dict[str, Any]] = []
    try:
        async for group in get_entra_groups(client):
            group_rows.append(transform_group(group, []))
            if len(group_rows) >= GROUP_BATCH_SIZE:
                load_groups(neo4j_session, group_rows, update_tag, tenant_id)
                group_rows = []
    except APIError as error:
        if not delegated_auth or error.response_status_code != 403:
            raise
        delegated_denial = error
    if group_rows:
        load_groups(neo4j_session, group_rows, update_tag, tenant_id)

    # Pass 2 fetches owners and members for several groups at once. Each page
    # of members becomes its own row, and rows flush on pending membership
    # count, so a group with a huge membership is loaded across several
    # bounded transactions.
    pending_rows: list[dict[str, Any]] = []
    pending_memberships = 0

    def flush() -> None:
        nonlocal pending_rows, pending_memberships
        if pending_rows:
            load_groups(neo4j_session, pending_rows, update_tag, tenant_id)
        pending_rows = []
        pending_memberships = 0

    def add_row(row: dict[str, Any]) -> None:
        nonlocal pending_memberships
        pending_rows.append(row)
        pending_memberships += len(row["member_ids"]) + len(row["member_group_ids"])
        if (
            pending_memberships >= PENDING_MEMBERSHIP_LIMIT
            or len(pending_rows) >= GROUP_BATCH_SIZE
        ):
            flush()

    async def sync_group_details(group: Group) -> None:
        nonlocal delegated_denial
        try:
            owner_ids = await call_with_retries(get_group_owners, client, group.id)
        except APIError as e:
            if e.response_status_code in (404, 410):
                # The group was deleted after it was listed.
                logger.warning(
                    "Group %s (%s) not found (%d) while fetching owners; skipping.",
                    group.id,
                    group.display_name,
                    e.response_status_code,
                )
                return
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
                owner_ids = []
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

        try:
            async for users, subgroups in get_group_member_pages(client, group.id):
                add_row(transform_group(group, owner_ids, users, subgroups))
                owner_ids = []
        except APIError as e:
            if e.response_status_code in (404, 410):
                logger.warning(
                    "Group %s (%s) not found (%d) while fetching members; "
                    "keeping any members already read.",
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
        if owner_ids:
            add_row(transform_group(group, owner_ids))

    try:
        await run_bounded(
            get_entra_groups(client), sync_group_details, GROUP_DETAIL_CONCURRENCY
        )
    except APIError as error:
        if not delegated_auth or error.response_status_code != 403:
            raise
        delegated_denial = delegated_denial or error
    flush()

    if delegated_denial:
        raise delegated_denial

    if not delegated_auth:
        cleanup_groups(neo4j_session, common_job_parameters)
