import neo4j

from cartography.client.core.tx import run_write_query
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema


def touch_skipped_repo_resources(
    neo4j_session: neo4j.Session,
    repo_urls: set[str] | None,
    node_schema: CartographyNodeSchema,
    update_tag: int,
    org_url: str,
    *,
    matchlinks: tuple[CartographyRelSchema, ...] = (),
) -> None:
    """Preserve skipped resources without refreshing links to active repositories."""
    if not repo_urls:
        return
    rel_labels = {
        rel.rel_label
        for rel in (
            node_schema.other_relationships.rels
            if node_schema.other_relationships
            else []
        )
    }
    if node_schema.sub_resource_relationship:
        rel_labels.add(node_schema.sub_resource_relationship.rel_label)
    rel_labels.update(rel.rel_label for rel in matchlinks)
    run_write_query(
        neo4j_session,
        """
        UNWIND $repo_urls AS repo_url
        MATCH (:GitHubRepository {id: repo_url})--(resource)
        WHERE $node_label IN labels(resource)
        SET resource.lastupdated = $update_tag
        WITH DISTINCT resource
        MATCH (resource)-[rel]-(other)
        WHERE type(rel) IN $rel_labels
          AND (NOT other:GitHubRepository OR other.id IN $repo_urls)
          AND (NOT other:GitHubOrganization OR other.id = $org_url)
        SET rel.lastupdated = $update_tag
        """,
        repo_urls=sorted(repo_urls),
        node_label=node_schema.label,
        rel_labels=sorted(rel_labels),
        update_tag=update_tag,
        org_url=org_url,
    )
