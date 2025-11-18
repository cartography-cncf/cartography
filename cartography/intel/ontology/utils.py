import logging
from dataclasses import asdict
from typing import Any

import neo4j

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.ontology.mapping import ONTOLOGY_MODELS
from cartography.models.ontology.mapping import ONTOLOGY_NODES_MAPPING
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _run_source_node_single_query(
    module_name: str,
    node: OntologyNodeMapping,
    neo4j_session: neo4j.Session,
    query: str,
    results: dict[str, dict[str, Any]],
    **kwargs: Any,
) -> dict[str, dict[str, Any]]:
    # DOC
    for row in neo4j_session.execute_read(read_list_of_dicts_tx, query, **kwargs):
        node_data = row["n"]
        result: dict[str, Any] = {}
        skip_node: bool = False

        # Extract only the fields defined in the ontology mapping
        for field in node.fields:
            value = node_data.get(field.node_field)
            # Skip nodes missing required fields
            if field.required and not value:
                logger.debug(
                    "Skipping node with label '%s' due to missing required field '%s'.",
                    node.node_label,
                    field.node_field,
                )
                skip_node = True
                break
            result[field.ontology_field] = value
        if skip_node:
            continue

        # Merge results based on the node's id field to avoid duplicates
        ontology_model = ONTOLOGY_MODELS[module_name]
        if ontology_model is None:
            # Should not happen as we skip non-eligible nodes above
            logger.warning(
                "No ontology model found for module '%s'. Skipping node label '%s'.",
                module_name,
                node.node_label,
            )
            continue
        id_field = ontology_model().properties.id.name
        existing = results.get(result[id_field])
        if existing:
            logger.debug("Merging node: %s to %s", result[id_field], existing[id_field])
            # Merge existing data with new data, prioritizing non-None values
            for key, value in result.items():
                if existing.get(key) is None and value is not None:
                    existing[key] = value
        else:
            logger.debug("Adding new node: %s", result[id_field])
            results[result[id_field]] = result
    return results


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
    results: dict[str, dict[str, Any]] = {}
    modules_mapping = ONTOLOGY_NODES_MAPPING[module_name]
    if len(source_of_truth) == 0:
        source_of_truth = list(modules_mapping.keys())
    # Check if ontology nodes are used in mapping
    _has_ontology = False
    if modules_mapping.get("ontology") is not None:
        _has_ontology = True
        for node in modules_mapping["ontology"].nodes:
            if not node.eligible_for_source:
                logger.debug(
                    "Skipping ontology node with label '%s' as it is not eligible for source of truth.",
                    node.node_label,
                )
                continue
            # Run the query for every source
            for source in source_of_truth:
                # Use parameterized query to prevent Cypher injection attacks
                query = f"MATCH (n:{node.node_label} {{_ont_source: $source}}) RETURN n"
                results = _run_source_node_single_query(
                    module_name, node, neo4j_session, query, results, source=source
                )

    # Run queries for each source of truth
    for source in source_of_truth:
        if source not in modules_mapping:
            if not _has_ontology:
                logger.warning(
                    "Source of truth '%s' is not supported for '%s'.",
                    source,
                    module_name,
                )
            continue
        for node in modules_mapping[source].nodes:
            if not node.eligible_for_source:
                logger.debug(
                    "Skipping node with label '%s' as it is not eligible for source of truth '%s'.",
                    node.node_label,
                    source,
                )
                continue
            query = f"MATCH (n:{node.node_label}) RETURN n"
            results = _run_source_node_single_query(
                module_name, node, neo4j_session, query, results
            )

    return list(results.values())


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
    modules_mapping = ONTOLOGY_NODES_MAPPING.get(module_name)
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
