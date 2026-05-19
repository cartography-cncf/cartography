import logging
from typing import Any

import neo4j

from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Derive `_ont_enabled` on EntraApplication from the linked
    # EntraServicePrincipal.account_enabled, since Microsoft Graph exposes the
    # enabled state on the service principal rather than on the application.
    run_analysis_job(
        "ontology_entra_application_projection.json",
        neo4j_session,
        common_job_parameters,
    )
