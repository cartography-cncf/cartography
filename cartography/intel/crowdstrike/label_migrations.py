import neo4j

from cartography.client.core.tx import run_write_query


# DEPRECATED: SpotlightVulnerability compatibility support will be removed in v1.0.0.
def migrate_spotlight_vulnerability_label(
    neo4j_session: neo4j.Session,
) -> None:
    """Add the provider-specific label to all historical Spotlight findings."""
    run_write_query(
        neo4j_session,
        """
        MATCH (vulnerability:SpotlightVulnerability)
        WHERE NOT vulnerability:CrowdstrikeSpotlightVulnerability
        SET vulnerability:CrowdstrikeSpotlightVulnerability
        """,
    )
