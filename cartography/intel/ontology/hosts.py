import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.ontology.utils import get_source_nodes_from_graph
from cartography.models.ontology.host import HostSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    source_of_truth: List[str],
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    data = get_source_nodes_from_graph(neo4j_session, source_of_truth, "hosts")
    load_hosts(
        neo4j_session,
        data,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def load_hosts(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HostSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(HostSchema(), common_job_parameters).run(
        neo4j_session,
    )
