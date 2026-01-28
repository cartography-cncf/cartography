import logging
from typing import Any

import neo4j

from cartography.intel.ontology.utils import link_semantic_labels
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    link_semantic_labels(neo4j_session, "loadbalancers", update_tag)
