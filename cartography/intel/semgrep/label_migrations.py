import neo4j

from cartography.client.core.tx import run_write_query


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
