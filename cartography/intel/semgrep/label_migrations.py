from typing import Any
from typing import Dict

import neo4j

from cartography.client.core.tx import run_write_query
from cartography.util import run_analysis_job


# DEPRECATED: GoLibrary and NpmLibrary compatibility support will be removed in v1.0.0.
def migrate_dependency_labels(
    neo4j_session: neo4j.Session,
    deployment_id: str,
) -> None:
    run_write_query(
        neo4j_session,
        """
        MATCH (:SemgrepDeployment{id: $DEPLOYMENT_ID})-[:RESOURCE]->(dependency)
        FOREACH (_ IN CASE
            WHEN dependency:GoLibrary AND NOT dependency:SemgrepGoLibrary
            THEN [1] ELSE [] END |
            SET dependency:SemgrepGoLibrary
        )
        FOREACH (_ IN CASE
            WHEN dependency:NpmLibrary AND NOT dependency:SemgrepNpmLibrary
            THEN [1] ELSE [] END |
            SET dependency:SemgrepNpmLibrary
        )
        """,
        DEPLOYMENT_ID=deployment_id,
    )


# DEPRECATED: migrates graphs synced by earlier versions; will be removed in v1.0.0.
def migrate_sca_cve_labels(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    run_analysis_job(
        "semgrep_sca_cve_migration.json",
        neo4j_session,
        common_job_parameters,
    )
