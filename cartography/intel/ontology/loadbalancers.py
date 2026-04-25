import logging
from typing import Any

import neo4j

from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    run_analysis_job(
        "ontology_loadbalancers_linking.json",
        neo4j_session,
        common_job_parameters,
    )
