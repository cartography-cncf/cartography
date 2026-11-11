import neo4j

from cartography.client.core.tx import run_write_query


# DEPRECATED: DependencyGraphManifest compatibility support will be removed in v1.0.0.
def migrate_dependency_graph_manifest_label(
    neo4j_session: neo4j.Session,
    owner_org_id: str,
) -> None:
    run_write_query(
        neo4j_session,
        """
        MATCH (org:GitHubOrganization{id: $owner_org_id})
        MATCH (manifest:DependencyGraphManifest)
        WHERE EXISTS {
            MATCH (org)-[:RESOURCE]->(manifest)
        } OR EXISTS {
            MATCH (org)<-[:OWNER]-(:GitHubRepository)
                  -[:HAS_MANIFEST]->(manifest)
        }
        SET manifest:GitHubDependencyGraphManifest
        """,
        owner_org_id=owner_org_id,
    )
