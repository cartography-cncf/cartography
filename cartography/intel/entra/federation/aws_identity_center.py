from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.entra.entra_user_to_aws_sso import (
    EntraUserToAWSSSOUserMatchLink,
)
from cartography.util import timeit


@timeit
def sync_entra_to_aws_identity_center(
    neo4j_session: neo4j.Session,
    update_tag: int,
    tenant_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    query = """
    MATCH (:EntraTenant{id: $TENANT_ID})-[:RESOURCE]->(e:EntraUser)
          -[:HAS_APP_ROLE]->(ar:EntraAppRoleAssignment)
          -[:ASSIGNED_TO]->(n:EntraApplication)
          -[:SERVICE_PRINCIPAL]->(spn:EntraServicePrincipal)
          -[:FEDERATES_TO]->(ic:AWSIdentityCenter)
    MATCH (sso:AWSSSOUser{identity_store_id:ic.identity_store_id})
    WHERE e.user_principal_name = sso.user_name
    RETURN e.user_principal_name as entra_user_principal_name, sso.user_name as aws_user_name, sso.identity_store_id as identity_store_id
    """
    entrauser_to_awssso_users = neo4j_session.execute_read(
        read_list_of_dicts_tx, query, TENANT_ID=tenant_id
    )

    # Load MatchLink relationships from Entra users to AWS SSO users
    load_matchlinks(
        neo4j_session,
        EntraUserToAWSSSOUserMatchLink(),
        entrauser_to_awssso_users,
        lastupdated=update_tag,
        _sub_resource_label="EntraTenant",
        _sub_resource_id=tenant_id,
    )

    cleanup_entra_user_to_aws_sso_user_matchlinks(neo4j_session, common_job_parameters)


@timeit
async def sync_entra_federation(
    neo4j_session: neo4j.Session,
    update_tag: int,
    tenant_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Entra federation relationships to the graph.

    :param neo4j_session: Neo4j session
    :param update_tag: Update tag for tracking data freshness
    :param tenant_id: Entra tenant ID
    :param common_job_parameters: Common job parameters for cleanup
    """
    sync_entra_to_aws_identity_center(
        neo4j_session, update_tag, tenant_id, common_job_parameters
    )


@timeit
def cleanup_entra_user_to_aws_sso_user_matchlinks(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_matchlink(
        EntraUserToAWSSSOUserMatchLink(),
        "EntraTenant",
        common_job_parameters["TENANT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
