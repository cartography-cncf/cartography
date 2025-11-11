import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.ontology.utils import get_source_nodes_from_graph
from cartography.intel.ontology.utils import link_ontology_nodes
from cartography.models.ontology.device import DeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    source_of_truth: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data = get_source_nodes_from_graph(neo4j_session, source_of_truth, "devices")
    load_devices(
        neo4j_session,
        data,
        update_tag,
    )
    link_ontology_nodes(neo4j_session, "devices", update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def load_devices(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DeviceSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DeviceSchema(), common_job_parameters).run(
        neo4j_session,
    )
