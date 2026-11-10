from dataclasses import fields

import neo4j

from cartography.client.core.tx import run_write_query
from cartography.models.github.dependencies import GitHubDependencyNodeProperties
from cartography.models.github.repos import GitHubPythonLibraryNodeProperties

_DEPENDENCY_GRAPH_ONLY_PROPERTIES = sorted(
    {field.name for field in fields(GitHubDependencyNodeProperties)}
    - {field.name for field in fields(GitHubPythonLibraryNodeProperties)}
)


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


# DEPRECATED: PythonLibrary nodes labeled GitHubDependency will be migrated until v1.0.0.
def migrate_python_library_dependency_label(neo4j_session: neo4j.Session) -> None:
    """
    Detach PythonLibrary nodes from the dependency graph loader.

    The dependency graph loader used to merge on the shared `Dependency` label,
    which PythonLibrary nodes also carry. It matched those nodes, labeled them
    GitHubDependency, and wrote its properties and HAS_DEP relationships to
    them. A node that kept the label still matches the loader. When the same
    package also has a node of its own, the loader refreshes both, so cleanup
    never removes either.
    """
    removed_properties = ", ".join(
        f"library.{name}" for name in _DEPENDENCY_GRAPH_ONLY_PROPERTIES
    )
    run_write_query(
        neo4j_session,
        f"""
        MATCH (library:PythonLibrary:GitHubDependency)
        OPTIONAL MATCH (library)<-[declared:HAS_DEP]-()
        DELETE declared
        WITH DISTINCT library
        REMOVE library:GitHubDependency, {removed_properties}
        """,
    )
