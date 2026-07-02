import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.share import DatabricksShareSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    shares = get(api_session)
    transformed = transform(neo4j_session, api_session, shares, metastore_id)
    load_shares(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list("/api/2.1/unity-catalog/shares", "shares")


def _existing_recipient_names(
    neo4j_session: neo4j.Session, share_scoped_id: str
) -> list[str]:
    """Return the recipient names already linked to a share in the graph."""
    query = """
    MATCH (:DatabricksShare {id: $share_id})-[:SHARED_WITH]->(r:DatabricksRecipient)
    RETURN collect(r.name) AS names
    """
    record = neo4j_session.run(query, share_id=share_scoped_id).single()
    return record["names"] if record else []


def _recipient_names(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    share_name: str,
    share_scoped_id: str,
) -> list[str]:
    """Return the recipients granted access to a share (its SELECT grantees)."""
    uri = f"/api/2.1/unity-catalog/shares/{share_name}/permissions"
    names: list[str] = []
    params: dict[str, Any] = {}
    seen_tokens: set[str] = set()
    while True:
        try:
            data = api_session.get(uri, params=params)
        except requests.HTTPError as e:
            # A share we can't read permissions on (403) or that vanished
            # mid-sync (404) is skippable; anything else aborts the sync. On a
            # skip we carry forward the last-known recipients from the graph:
            # returning [] here would let this run's cleanup delete SHARED_WITH
            # edges that are still valid, silently hiding who a share is exposed
            # to.
            skip_or_raise_http(e, 403, 404)
            logger.warning(
                "Could not read permissions for share %s (%s); keeping "
                "last-known recipients.",
                share_name,
                e,
            )
            return _existing_recipient_names(neo4j_session, share_scoped_id)
        for assignment in data.get("privilege_assignments", []) or []:
            principal = assignment.get("principal")
            if principal:
                names.append(principal)
        next_token = data.get("next_page_token")
        if not next_token:
            break
        if next_token in seen_tokens:
            raise ValueError(
                f"Databricks share permissions for {share_name} repeated page "
                f"token {next_token!r}; aborting to avoid an infinite loop.",
            )
        seen_tokens.add(next_token)
        params = {"page_token": next_token}
    return names


@timeit
def transform(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    shares: list[dict[str, Any]],
    metastore_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for s in shares:
        name = s["name"]
        if not name:
            raise ValueError("Databricks share returned with empty name")
        share_scoped_id = uc_id(metastore_id, name)
        recipient_names = _recipient_names(
            neo4j_session, api_session, name, share_scoped_id
        )
        result.append(
            {
                "id": share_scoped_id,
                "share_id": s.get("id"),
                "name": name,
                "metastore_id": metastore_id,
                "owner": s.get("owner"),
                "comment": s.get("comment"),
                "created_at": epoch_ms_to_datetime(s.get("created_at")),
                "created_by": s.get("created_by"),
                "updated_at": epoch_ms_to_datetime(s.get("updated_at")),
                "updated_by": s.get("updated_by"),
                "recipient_scoped_ids": [
                    uc_id(metastore_id, r) for r in recipient_names
                ],
            }
        )
    return result


@timeit
def load_shares(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksShareSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksShareSchema(), common_job_parameters).run(
        neo4j_session
    )
