import logging
from dataclasses import asdict
from typing import Any

import neo4j

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.ontology.mapping import ONTOLOGY_MAPPING
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_source_nodes_from_graph(
    neo4j_session: neo4j.Session,
    source_of_truth: list[str],
    module_name: str,
) -> list[dict[str, Any]]:
    """Retrieve source nodes from the Neo4j graph database based on the ontology mapping.

    This function queries the Neo4j database for nodes that match the labels
    defined in the ontology mapping for the specified module and source of truth.
    It returns a list of dictionaries containing the relevant fields for each node.

    If no source of truth is provided, default to all sources defined in the mapping.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session to use for querying the database.
        source_of_truth (list[str]): A list of source of truth identifiers to filter the modules.
        module_name (str): The name of the ontology module to use for the mapping (eg. users, devices, etc.).

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each containing a node details formatted according to the ontology mapping.
    """
    results: list[dict[str, Any]] = []
    modules_mapping = ONTOLOGY_MAPPING.get(module_name)
    if modules_mapping is None:
        logger.warning("No ontology mapping found for module '%s'.", module_name)
        return results
    if len(source_of_truth) == 0:
        source_of_truth = list(modules_mapping.keys())
    for source in source_of_truth:
        if source not in modules_mapping:
            logger.warning(
                "Source of truth '%s' is not supported for '%s'.", source, module_name
            )
            continue
        for node in modules_mapping[source].nodes:
            query = f"MATCH (n:{node.node_label}) RETURN n"
            for row in neo4j_session.execute_read(read_list_of_dicts_tx, query):
                node_data = row["n"]
                result = {
                    field.ontology_field: node_data.get(field.node_field)
                    for field in node.fields
                }
                results.append(result)
    return results


@timeit
def link_ontology_nodes(
    neo4j_session: neo4j.Session,
    module_name: str,
    update_tag: int,
) -> None:
    """Link ontology nodes in the Neo4j graph database based on the ontology mapping.

    This function retrieves the ontology mapping for the specified module and
    executes the relationship statements defined in the mapping to link nodes
    in the Neo4j graph database.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session to use for executing the relationship statements.
        module_name (str): The name of the ontology module for which to link nodes (eg. users, devices, etc.).
        update_tag (int): The update tag of the current run, used to tag the changes in the graph.
    """
    modules_mapping = ONTOLOGY_MAPPING.get(module_name)
    if modules_mapping is None:
        logger.warning("No ontology mapping found for module '%s'.", module_name)
        return
    for source, mapping in modules_mapping.items():
        if len(mapping.rels) == 0:
            continue
        formated_json = {
            "name": f"Linking ontology nodes for {module_name} for source {source}",
            "statements": [asdict(rel) for rel in mapping.rels],
        }
        GraphJob.run_from_json(
            neo4j_session,
            formated_json,
            {"UPDATE_TAG": update_tag},
            short_name=f"ontology.{module_name}.{source}.linking",
        )
