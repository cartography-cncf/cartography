import json
import logging
import pkgutil
from typing import Any

import neo4j

from cartography.graph.job import GraphJob
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_ontology_mapping(module_name: str) -> dict:
    """Load the ontology mapping for a given module.

    This function loads the ontology mapping from a JSON file located in the
    `cartography.data.ontology` package. The mapping file should be named
    `<module_name>.json`, where `<module_name>` is the name of the module for
    which the mapping is being loaded.

    Args:
        module_name (str): The name of the module for which to load the ontology mapping.

    Raises:
        ValueError: If the mapping file for the specified module is not found.

    Returns:
        dict: A dictionary containing the ontology mapping for the specified module.
    """
    data = pkgutil.get_data("cartography.data.ontology", f"{module_name}.json")
    if data is None:
        raise ValueError(f"Mapping file for {module_name} not found.")
    return json.loads(data.decode("utf-8"))


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

    Args:
        neo4j_session (neo4j.Session): The Neo4j session to use for querying the database.
        source_of_truth (list[str]): A list of source of truth identifiers to filter the modules.
        module_name (str): The name of the ontology module to use for the mapping (eg. users, devices, etc.).

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each containing a node details formatted according to the ontology mapping.
    """
    results: list[dict[str, Any]] = []
    modules_mapping = load_ontology_mapping(module_name)
    for source in source_of_truth:
        if source not in modules_mapping:
            logger.warning(
                "Source of truth '%s' is not supported for '%s'.", source, module_name
            )
            continue
        for node_label, fields in modules_mapping[source].get("nodes", {}).items():
            if not isinstance(fields, dict):
                logger.warning(
                    "Node fields for '%s' in '%s' are not a dictionary.",
                    node_label,
                    source,
                )
                continue
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
    modules_mapping = load_ontology_mapping(module_name)
    for source, mapping in modules_mapping.items():
        if "rels" not in mapping:
            continue
        formated_json = {
            "name": f"Linking ontology nodes for {module_name} for source {source}",
            "statements": mapping["rels"],
        }
        GraphJob.run_from_json(
            neo4j_session,
            formated_json,
            {"UPDATE_TAG": update_tag},
            short_name=f"ontology.{module_name}.{source}.linking",
        )
