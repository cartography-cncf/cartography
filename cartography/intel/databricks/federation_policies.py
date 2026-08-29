import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.models.databricks.federation_policy import (
    DatabricksFederationPolicySchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    account_policies = get_account_policies(api_session)
    service_principals = get_account_service_principals(neo4j_session, account_id)
    sp_policies, complete = get_service_principal_policies(
        api_session, service_principals
    )
    transformed = transform(account_policies, sp_policies, account_id)
    load_policies(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    # Only clean up when every service principal's policies were read this run. A
    # 403/404 on one SP means its policies were not refreshed, so an
    # account-scoped node cleanup would delete still-valid DatabricksFederationPolicy
    # nodes for it; skip cleanup and let a fully successful run reconcile them.
    if complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Databricks federation policies were partially read for account %s; "
            "skipping cleanup to avoid deleting valid policy nodes.",
            account_id,
        )


@timeit
def get_account_policies(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    """Fetch account-wide federation policies (paginated under ``policies``)."""
    return api_session.uc_list(
        api_session.account_uri("/federationPolicies"), key="policies"
    )


@timeit
def get_account_service_principals(
    neo4j_session: neo4j.Session, account_id: str
) -> list[dict[str, Any]]:
    """Read account service principals to fetch their per-SP federation policies.

    Reads from the graph so this sync does not depend on holding the SCIM SP
    listing in memory; the SP-scoped federation policy endpoint keys off the
    numeric SCIM id.
    """
    query = """
    MATCH (:DatabricksAccount {id: $account_id})-[:RESOURCE]->(sp:DatabricksAccountServicePrincipal)
    RETURN sp.id AS node_id, sp.scim_id AS scim_id
    """
    result = neo4j_session.run(query, account_id=account_id)
    return [
        {"node_id": r["node_id"], "scim_id": r["scim_id"]}
        for r in result
        if r["scim_id"]
    ]


@timeit
def get_service_principal_policies(
    api_session: DatabricksAccountClient,
    service_principals: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch federation policies scoped to each account service principal.

    Returns ``(policies, complete)``. Each row carries the owning SP's node id so
    the OWNED_BY edge lands. ``complete`` is False when any SP's policies were
    skipped (403/404) so the caller can skip cleanup rather than delete the
    unrefreshed policy nodes. Iterating every SP can be heavy; that is acceptable.
    """
    policies: list[dict[str, Any]] = []
    complete = True
    for sp in service_principals:
        uri = api_session.account_uri(
            f"/servicePrincipals/{sp['scim_id']}/federationPolicies"
        )
        try:
            sp_policies = api_session.uc_list(uri, key="policies")
        except requests.HTTPError as e:
            # A SP whose policies the caller can't read (403) or that vanished
            # mid-sync (404) is skippable; any other error must abort so cleanup
            # does not drop still-valid policy nodes.
            skip_or_raise_http(e, 403, 404)
            complete = False
            logger.warning(
                "Skipping federation policies for service principal %s: %s",
                sp["scim_id"],
                e,
            )
            continue
        for policy in sp_policies:
            policies.append(
                {
                    **policy,
                    "sp_node_id": sp["node_id"],
                    "sp_scim_id": sp["scim_id"],
                }
            )
    return policies, complete


def _flatten(policy: dict[str, Any], account_id: str) -> dict[str, Any] | None:
    # The federation policy API keys a policy by its server-assigned ``uid``
    # (falling back to ``policy_id`` / ``name``); there is no ``id`` field, so
    # never index ``policy["id"]``. Drop a policy with no identifier rather than
    # collapse it onto a blank account-scoped key.
    policy_uid = policy.get("uid") or policy.get("policy_id") or policy.get("name")
    if not policy_uid:
        return None
    oidc = policy.get("oidc_policy") or {}
    return {
        "id": account_scoped_id(account_id, str(policy_uid)),
        "name": policy.get("name"),
        "uid": policy.get("uid"),
        "description": policy.get("description"),
        "issuer": oidc.get("issuer"),
        "subject_claim": oidc.get("subject_claim"),
        "audiences": oidc.get("audiences") or [],
        "service_principal_id": policy.get("sp_scim_id"),
        "sp_node_id": policy.get("sp_node_id"),
    }


@timeit
def transform(
    account_policies: list[dict[str, Any]],
    sp_policies: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for policy in (*account_policies, *sp_policies):
        flattened = _flatten(policy, account_id)
        if flattened is not None:
            result.append(flattened)
    return result


@timeit
def load_policies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksFederationPolicySchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksFederationPolicySchema(), common_job_parameters
    ).run(neo4j_session)
