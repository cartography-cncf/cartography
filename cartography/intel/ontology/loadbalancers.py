import logging
from typing import Any

import neo4j

from cartography.analysis.ontology.analysis import LOADBALANCER_EXPOSE_CONTAINER
from cartography.util import run_typed_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    run_typed_analysis_job(
        LOADBALANCER_EXPOSE_CONTAINER,
        neo4j_session,
        common_job_parameters,
    )
