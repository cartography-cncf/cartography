import logging

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.azure.function_app import AzureFunctionAppToRoleAssumesMatchLink
from cartography.models.azure.vm.virtualmachine import (
    AzureVirtualMachineToRoleAssumesMatchLink,
)
from cartography.models.core.relationships import CartographyRelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _sync_assumes_for_label(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    update_tag: int,
    source_label: str,
    matchlink: CartographyRelSchema,
) -> None:
    # Assemble (workload, role definition) pairs by joining the workload's
    # managed-identity principal ids to the role assignments held by that
    # identity. This spans the compute/functions sync (which stamps
    # identity_principal_ids on the node) and the RBAC sync (which loads the
    # role assignments), so it can only run once both are done.
    # source_label is a hardcoded node label, not user input.
    query = f"""
    MATCH (:AzureSubscription {{id: $SubscriptionId}})-[:RESOURCE]->(w:{source_label})
    WHERE w.identity_principal_ids IS NOT NULL
    UNWIND w.identity_principal_ids AS principal_id
    MATCH (ra:AzureRoleAssignment {{principal_id: principal_id}})
        -[:ROLE_ASSIGNED]->(rd:AzureRoleDefinition)
    RETURN DISTINCT w.id AS workload_id, rd.id AS role_definition_id
    """
    pairs = [
        {
            "workload_id": record["workload_id"],
            "role_definition_id": record["role_definition_id"],
        }
        for record in neo4j_session.run(query, SubscriptionId=subscription_id)
    ]

    load_matchlinks(
        neo4j_session,
        matchlink,
        pairs,
        lastupdated=update_tag,
        _sub_resource_label="AzureSubscription",
        _sub_resource_id=subscription_id,
    )

    GraphJob.from_matchlink(
        matchlink,
        sub_resource_label="AzureSubscription",
        sub_resource_id=subscription_id,
        update_tag=update_tag,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Materialize the canonical (:AzureVirtualMachine|:AzureFunctionApp)
    -[:ASSUMES]->(:AzureRoleDefinition) edges from managed-identity role
    assignments. Must run after both the compute/functions and RBAC syncs.
    """
    logger.info(
        "Syncing Azure workload-identity ASSUMES edges for subscription '%s'.",
        subscription_id,
    )
    _sync_assumes_for_label(
        neo4j_session,
        subscription_id,
        update_tag,
        "AzureVirtualMachine",
        AzureVirtualMachineToRoleAssumesMatchLink(),
    )
    _sync_assumes_for_label(
        neo4j_session,
        subscription_id,
        update_tag,
        "AzureFunctionApp",
        AzureFunctionAppToRoleAssumesMatchLink(),
    )
