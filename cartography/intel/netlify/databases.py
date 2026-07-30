import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.databasebranch import NetlifyDatabaseBranchSchema
from cartography.models.netlify.databasesnapshot import NetlifyDatabaseSnapshotSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Keys that carry a plaintext Postgres URL, password included. Never ingested.
_SECRET_KEYS = frozenset({"connection_string", "connection_strings"})


@timeit
def sync_netlify_databases(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Netlify DB branches and snapshots.

    `GET /sites/{id}/database` is deliberately never called: its entire response body is the
    plaintext connection string. Everything useful is on the branches endpoint instead.
    """
    raw_branches: list[dict[str, Any]] = []
    raw_snapshots: list[dict[str, Any]] = []
    for site in sites:
        # Netlify exposes the branches endpoint on every site, so skip the ones with no database
        # rather than spending two requests each to learn they have none.
        if not site.get("has_database"):
            continue
        site_id = site["id"]
        for branch in get_netlify_database_branches(api_session, base_url, site_id):
            raw_branches.append({**branch, "site_id": site_id})
        for snapshot in get_netlify_database_snapshots(api_session, base_url, site_id):
            raw_snapshots.append({**snapshot, "site_id": site_id})

    branches = transform_netlify_database_branches(raw_branches)
    snapshots = transform_netlify_database_snapshots(raw_snapshots)
    load_netlify_database_branches(neo4j_session, branches, account_id, update_tag)
    load_netlify_database_snapshots(neo4j_session, snapshots, account_id, update_tag)
    cleanup_netlify_databases(neo4j_session, common_job_parameters)


@timeit
def get_netlify_database_branches(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return get_list(
        api_session,
        f"{base_url}/sites/{site_id}/database/branches",
        result_key="branches",
    )


@timeit
def get_netlify_database_snapshots(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return get_list(
        api_session,
        f"{base_url}/sites/{site_id}/database/snapshots",
        result_key="snapshots",
    )


def transform_netlify_database_branches(
    branches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Drop the connection strings, flatten the compute endpoint, and build a site-scoped id.

    `branch_id` is only unique within a site: the primary branch is called "production" on every
    Netlify DB, so the node id has to be `<site_id>|<branch_id>`. Both halves are required to be
    non-empty, because an empty one silently collapses every affected branch onto a single
    "<site_id>|" node rather than failing.
    """
    transformed = []
    for branch in branches:
        site_id = branch["site_id"]
        branch_id = branch["branch_id"]
        if not site_id or not branch_id:
            raise ValueError(
                f"Netlify database branch is missing an identifier needed for its node id "
                f"(site_id={site_id!r}, branch_id={branch_id!r}).",
            )
        compute = branch.get("compute") or {}
        connection_strings = branch.get("connection_strings") or {}
        transformed.append(
            {
                **{
                    k: v
                    for k, v in branch.items()
                    if k not in _SECRET_KEYS and k != "compute"
                },
                "id": f"{site_id}|{branch_id}",
                "compute_state": compute.get("current_state"),
                "compute_min_cu": compute.get("autoscaling_limit_min_cu"),
                "compute_max_cu": compute.get("autoscaling_limit_max_cu"),
                "compute_suspend_timeout_seconds": compute.get(
                    "suspend_timeout_seconds",
                ),
                "compute_last_active": compute.get("last_active"),
                # Only the role names, never the URLs they are keyed to.
                "connection_roles": sorted(connection_strings.keys()),
            },
        )
    return transformed


def transform_netlify_database_snapshots(
    snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Derive a name and the parent branch's node id.

    Netlify gives a snapshot no name, so one is composed from the source branch and the
    point-in-time timestamp to satisfy the Snapshot ontology mapping's required `name`.

    The snapshot's own id and its source branch are required to be non-empty: an empty id would
    have every snapshot collide on one node, and an empty branch id would point the HAS_SNAPSHOT
    edge at whichever branch also ended up with a truncated id.
    """
    transformed = []
    for snapshot in snapshots:
        snapshot_id = snapshot["id"]
        site_id = snapshot["site_id"]
        source_branch_id = snapshot["source_branch_id"]
        if not snapshot_id or not site_id or not source_branch_id:
            raise ValueError(
                f"Netlify database snapshot is missing an identifier needed for its node id "
                f"(id={snapshot_id!r}, site_id={site_id!r}, "
                f"source_branch_id={source_branch_id!r}).",
            )
        timestamp = snapshot.get("timestamp") or snapshot.get("created_at")
        transformed.append(
            {
                **snapshot,
                "source_branch_node_id": f"{site_id}|{source_branch_id}",
                "name": f"{source_branch_id}@{timestamp}",
            },
        )
    return transformed


@timeit
def load_netlify_database_branches(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDatabaseBranchSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def load_netlify_database_snapshots(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDatabaseSnapshotSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_databases(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Snapshots before branches: a snapshot hangs off its branch, so removing the branch first
    # would strip the edge that identifies the orphan.
    GraphJob.from_node_schema(
        NetlifyDatabaseSnapshotSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        NetlifyDatabaseBranchSchema(),
        common_job_parameters,
    ).run(neo4j_session)
