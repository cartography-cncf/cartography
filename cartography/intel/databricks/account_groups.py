import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.account_group import DatabricksAccountGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    groups = get(api_session)
    transformed = transform(groups, account_id)
    load_groups(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.scim_list(api_session.account_uri("/scim/v2/Groups"))


@timeit
def transform(groups: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    """Flatten SCIM nested-group memberships into parent_group_ids on each group.

    Databricks SCIM exposes group nesting via two paths and only one is
    guaranteed to be populated on any given response:
      - the parent's ``members`` list (with ``$ref: "Groups/..."``), and
      - the child's own ``groups`` list (same shape as Users / SPs).
    Both are consumed and deduplicated so the Group -> Group MEMBER_OF edge
    lands regardless of which side the API fills in.

    Edges to users and service principals are reverse-materialised on those
    nodes via the ``group_ids`` list returned by the SCIM Users /
    ServicePrincipals endpoints.

    Node ids are scoped to the account so multi-account ingestion does not
    collide on account-scoped SCIM ids.
    """
    by_scim_id: dict[str, dict[str, Any]] = {}
    for g in groups:
        scim_id = g.get("id")
        # A blank SCIM id would collapse to the account-scoped key
        # "{account_id}/" and merge distinct malformed records onto one node;
        # skip rather than corrupt graph identity.
        if not scim_id:
            logger.warning("Skipping Databricks account group with empty SCIM id.")
            continue
        by_scim_id[scim_id] = {
            "id": account_scoped_id(account_id, scim_id),
            "scim_id": scim_id,
            "display_name": g.get("displayName"),
            "external_id": g.get("externalId"),
            # set() during accumulation, list() before return so the load layer
            # gets a deterministic, JSON-friendly value.
            "_parent_set": set(),
        }
    for g in groups:
        scim_id = g.get("id")
        # Skip the same blank-id records dropped above (not in by_scim_id).
        if not scim_id or scim_id not in by_scim_id:
            continue
        # Upward: the child group's own ``groups`` field.
        for parent in g.get("groups", []) or []:
            parent_id = parent.get("value")
            if parent_id and parent_id in by_scim_id:
                by_scim_id[scim_id]["_parent_set"].add(
                    account_scoped_id(account_id, parent_id)
                )
        # Downward: the parent group's ``members`` field with $ref="Groups/...".
        for member in g.get("members", []) or []:
            member_id = member.get("value")
            member_ref = member.get("$ref", "") or ""
            if not member_id:
                continue
            if member_ref.startswith("Groups/") and member_id in by_scim_id:
                by_scim_id[member_id]["_parent_set"].add(
                    account_scoped_id(account_id, scim_id)
                )
    result: list[dict[str, Any]] = []
    for entry in by_scim_id.values():
        entry["parent_group_ids"] = sorted(entry.pop("_parent_set"))
        result.append(entry)
    return result


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksAccountGroupSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksAccountGroupSchema(), common_job_parameters
    ).run(neo4j_session)
