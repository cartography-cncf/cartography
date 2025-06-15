import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.ontology.utils import load_ontology_mapping
from cartography.models.ontology.user import UserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    source_of_truth: List[str],
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    data = get(neo4j_session, source_of_truth)
    load_users(
        neo4j_session,
        data,
        update_tag,
    )
    load_custom_linking(
        neo4j_session,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    neo4j_session: neo4j.Session,
    source_of_truth: List[str],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    modules_mapping = load_ontology_mapping("users")
    for source in source_of_truth:
        if source not in modules_mapping:
            logger.warning(f"Source of truth {source} is not supported.")
            continue

        node_label = modules_mapping[source]["node_label"]
        fields = modules_mapping[source]["fields"]

        query = f"MATCH (n:{node_label}) RETURN n"
        for node in neo4j_session.run(query):
            node_data = node["n"]
            result = {
                o_field: node_data.get(node_field)
                for o_field, node_field in fields.items()
            }
            results.append(result)
    return results


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UserSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_custom_linking(neo4j_session: neo4j.Session, update_tag: int) -> None:
    # DOC
    modules_mapping = load_ontology_mapping("users")
    for module_name, module_data in modules_mapping.items():
        if not module_data.get("custom_linking"):
            logger.debug(f"No custom linking defined for module {module_name}.")
            continue
        query = f"""
            MATCH (src:User)
            MATCH (n:{module_data['node_label']})
            WHERE src.email = n.{module_data['fields']['email']}
            MERGE (src)-[r:HAS_ACCOUNT]->(n)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
        """
        neo4j_session.run(
            query,
            update_tag=update_tag,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UserSchema(), common_job_parameters).run(
        neo4j_session,
    )
