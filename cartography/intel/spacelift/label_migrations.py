import neo4j

from cartography.client.core.tx import run_write_query


# DEPRECATED: CloudTrailSpaceliftEvent compatibility support will be removed in v1.0.0.
def migrate_cloudtrail_event_label(
    neo4j_session: neo4j.Session,
    spacelift_account_id: str,
) -> None:
    run_write_query(
        neo4j_session,
        """
        MATCH (:SpaceliftAccount{id: $spacelift_account_id})
              -[:RESOURCE]->(event:CloudTrailSpaceliftEvent)
        WHERE NOT event:SpaceliftCloudTrailEvent
        SET event:SpaceliftCloudTrailEvent
        """,
        spacelift_account_id=spacelift_account_id,
    )
