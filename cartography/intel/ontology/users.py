import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.ontology.utils import get_source_nodes_from_graph
from cartography.models.ontology.user import UserSchema
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    source_of_truth: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data = get_source_nodes_from_graph(neo4j_session, source_of_truth, "users")
    load_users(
        neo4j_session,
        data,
        update_tag,
    )
    # Derive `_ont_has_mfa` and `_ont_active` on AWSUser from related
    # AWSMfaDevice and AccountAccessKey nodes, since AWS does not expose these
    # as direct properties on the IAM user (no credential report ingestion).
    run_analysis_job(
        "ontology_aws_user_projection.json",
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        "ontology_users_linking.json",
        neo4j_session,
        common_job_parameters,
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UserSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UserSchema(), common_job_parameters).run(
        neo4j_session,
    )
