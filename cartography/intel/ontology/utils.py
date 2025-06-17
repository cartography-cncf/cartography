import json
import logging
import pkgutil
from typing import Any

import neo4j

from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_ontology_mapping(module_name: str) -> dict:
    # DOC
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
    # DOC
    results: list[dict[str, Any]] = []
    modules_mapping = load_ontology_mapping(module_name)
    for source in source_of_truth:
        if source not in modules_mapping:
            logger.warning(
                "Source of truth '%s' is not supported for '%s'.", source, module_name
            )
            continue
        for node_label, fields in modules_mapping[source]["nodes"].items():
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
