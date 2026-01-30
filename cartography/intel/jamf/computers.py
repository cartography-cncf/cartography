import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jamf.util import call_jamf_api
from cartography.models.jamf.computergroup import JamfComputerGroupSchema
from cartography.models.jamf.tenant import JamfTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    jamf_base_uri: str,
    jamf_user: str,
    jamf_password: str,
) -> dict[str, Any]:
    return call_jamf_api("/computergroups", jamf_base_uri, jamf_user, jamf_password)


def transform(api_result: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Transform API response into a list of computer groups.
    """
    return api_result["computer_groups"]


def load_computer_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    # Load tenant first
    load(
        neo4j_session,
        JamfTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )

    # Load computer groups
    load(
        neo4j_session,
        JamfComputerGroupSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(JamfComputerGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )

    # DEPRECATED: need to be deleted in v1
    # Clean up orphaned pre-migration nodes without RESOURCE rel
    neo4j_session.run(
        """
        MATCH (n:JamfComputerGroup)
        WHERE n.lastupdated <> $UPDATE_TAG
          AND NOT (n)<-[:RESOURCE]-(:JamfTenant)
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n
        """,
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        LIMIT_SIZE=100,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    jamf_base_uri: str,
    jamf_user: str,
    jamf_password: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    # 1. GET
    raw_data = get(jamf_base_uri, jamf_user, jamf_password)
    # 2. TRANSFORM
    computer_groups = transform(raw_data)
    # 3. LOAD
    load_computer_groups(neo4j_session, computer_groups, jamf_base_uri, update_tag)
    # 4. CLEANUP
    cleanup(neo4j_session, common_job_parameters)
