"""
Integration tests for ontology packages module
"""

from unittest.mock import patch

import cartography.intel.ontology.packages
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _setup_trivy_graph(neo4j_session):
    """Create TrivyPackage nodes with DEPLOYED and AFFECTS relationships for testing."""
    neo4j_session.run(
        """
        MERGE (p:TrivyPackage {id: 'npm|express|4.18.2'})
        SET p.normalized_id = 'npm|express|4.18.2',
            p.name = 'express', p.version = '4.18.2',
            p.type = 'npm'
        MERGE (img:ECRImage {id: 'sha256:abc123'})
        MERGE (p)-[:DEPLOYED]->(img)
        MERGE (f:TrivyImageFinding {id: 'TIF|CVE-2024-00001'})
        SET f.name = 'CVE-2024-00001'
        MERGE (f)-[:AFFECTS]->(p)
        MERGE (fix:TrivyFix {id: 'npm|express|4.18.3'})
        SET fix.version = '4.18.3'
        MERGE (p)-[:SHOULD_UPDATE_TO]->(fix)
        MERGE (fix)-[:APPLIES_TO]->(f)
        """,
    )
    neo4j_session.run(
        """
        MERGE (p:TrivyPackage {id: 'pypi|requests|2.31.0'})
        SET p.normalized_id = 'pypi|requests|2.31.0',
            p.name = 'requests', p.version = '2.31.0',
            p.type = 'pypi'
        MERGE (img:GitLabContainerImage {id: 'sha256:def456'})
        MERGE (p)-[:DEPLOYED]->(img)
        """,
    )


def _setup_syft_graph(neo4j_session):
    """Create SyftPackage nodes with DEPENDS_ON relationships for testing."""
    neo4j_session.run(
        """
        MERGE (p1:SyftPackage {id: 'npm|express|4.18.2'})
        SET p1.normalized_id = 'npm|express|4.18.2',
            p1.name = 'express', p1.version = '4.18.2',
            p1.type = 'npm'
        MERGE (p2:SyftPackage {id: 'npm|body-parser|1.20.2'})
        SET p2.normalized_id = 'npm|body-parser|1.20.2',
            p2.name = 'body-parser', p2.version = '1.20.2',
            p2.type = 'npm'
        MERGE (p1)-[:DEPENDS_ON]->(p2)
        """,
    )


@patch.object(
    cartography.intel.ontology.packages,
    "get_source_nodes_from_graph",
    return_value=[
        {
            "normalized_id": "npm|express|4.18.2",
            "name": "express",
            "version": "4.18.2",
            "type": "npm",
            "purl": "pkg:npm/express@4.18.2",
        },
        {
            "normalized_id": "pypi|requests|2.31.0",
            "name": "requests",
            "version": "2.31.0",
            "type": "pypi",
            "purl": "pkg:pypi/requests@2.31.0",
        },
        {
            "normalized_id": "npm|body-parser|1.20.2",
            "name": "body-parser",
            "version": "1.20.2",
            "type": "npm",
            "purl": "pkg:npm/body-parser@1.20.2",
        },
    ],
)
def test_load_ontology_packages(_mock_get_source_nodes, neo4j_session):
    """Test end-to-end loading of ontology packages from mocked source nodes."""

    # Arrange
    _setup_trivy_graph(neo4j_session)
    _setup_syft_graph(neo4j_session)

    # Act
    cartography.intel.ontology.packages.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert - Check that Package nodes were created
    expected_packages = {
        ("npm|express|4.18.2", "express", "4.18.2", "npm"),
        ("pypi|requests|2.31.0", "requests", "2.31.0", "pypi"),
        ("npm|body-parser|1.20.2", "body-parser", "1.20.2", "npm"),
    }
    actual_packages = check_nodes(
        neo4j_session,
        "Package",
        ["id", "name", "version", "type"],
    )
    assert actual_packages == expected_packages

    # Assert - Check that Package nodes have Ontology label
    ontology_count = neo4j_session.run(
        "MATCH (p:Package:Ontology) RETURN count(p) as count",
    ).single()["count"]
    assert ontology_count == 3

    # Assert - Check DETECTED_AS relationships to TrivyPackage
    expected_trivy_rels = {
        ("npm|express|4.18.2", "npm|express|4.18.2"),
        ("pypi|requests|2.31.0", "pypi|requests|2.31.0"),
    }
    actual_trivy_rels = check_rels(
        neo4j_session,
        "Package",
        "id",
        "TrivyPackage",
        "normalized_id",
        "DETECTED_AS",
        rel_direction_right=True,
    )
    assert actual_trivy_rels == expected_trivy_rels

    # Assert - Check DETECTED_AS relationships to SyftPackage
    expected_syft_rels = {
        ("npm|express|4.18.2", "npm|express|4.18.2"),
        ("npm|body-parser|1.20.2", "npm|body-parser|1.20.2"),
    }
    actual_syft_rels = check_rels(
        neo4j_session,
        "Package",
        "id",
        "SyftPackage",
        "normalized_id",
        "DETECTED_AS",
        rel_direction_right=True,
    )
    assert actual_syft_rels == expected_syft_rels

    # Assert - Check DEPLOYED propagated from TrivyPackage to Package -> ECRImage
    expected_deployed_ecr = {
        ("npm|express|4.18.2", "sha256:abc123"),
    }
    actual_deployed_ecr = check_rels(
        neo4j_session,
        "Package",
        "id",
        "ECRImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    )
    assert actual_deployed_ecr == expected_deployed_ecr

    # Assert - Check DEPLOYED propagated from TrivyPackage to Package -> GitLabContainerImage
    expected_deployed_gitlab = {
        ("pypi|requests|2.31.0", "sha256:def456"),
    }
    actual_deployed_gitlab = check_rels(
        neo4j_session,
        "Package",
        "id",
        "GitLabContainerImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    )
    assert actual_deployed_gitlab == expected_deployed_gitlab

    # Assert - Check AFFECTS propagated from TrivyImageFinding to Package
    expected_affects = {
        ("TIF|CVE-2024-00001", "npm|express|4.18.2"),
    }
    actual_affects = check_rels(
        neo4j_session,
        "TrivyImageFinding",
        "id",
        "Package",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    )
    assert actual_affects == expected_affects

    # Assert - Check SHOULD_UPDATE_TO propagated from TrivyPackage to Package -> TrivyFix
    expected_should_update_to = {
        ("npm|express|4.18.2", "npm|express|4.18.3"),
    }
    actual_should_update_to = check_rels(
        neo4j_session,
        "Package",
        "id",
        "TrivyFix",
        "id",
        "SHOULD_UPDATE_TO",
        rel_direction_right=True,
    )
    assert actual_should_update_to == expected_should_update_to

    # Assert - Check DEPENDS_ON propagated from SyftPackage to Package -> Package
    expected_depends_on = {
        ("npm|express|4.18.2", "npm|body-parser|1.20.2"),
    }
    actual_depends_on = check_rels(
        neo4j_session,
        "Package",
        "id",
        "Package",
        "id",
        "DEPENDS_ON",
        rel_direction_right=True,
    )
    assert actual_depends_on == expected_depends_on


def test_cleanup_removes_stale_derived_package_relationships(neo4j_session):
    """
    Verify Package cleanup deletes stale derived relationships created by ontology
    mapping propagation while preserving fresh relationships.
    """
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:Package OR n:TrivyPackage OR n:TrivyImageFinding OR n:TrivyFix OR n:ECRImage
        DETACH DELETE n
        """,
    )

    stale_tag = TEST_UPDATE_TAG - 1

    neo4j_session.run(
        """
        MERGE (p:Package:Ontology {id: 'npm|express|4.18.2'})
        SET p.lastupdated = $update_tag

        MERGE (img:ECRImage {id: 'sha256:stale'})
        MERGE (p)-[r1:DEPLOYED]->(img)
        SET r1.lastupdated = $stale_tag

        MERGE (f:TrivyImageFinding {id: 'TIF|CVE-2024-99999'})
        MERGE (f)-[r2:AFFECTS]->(p)
        SET r2.lastupdated = $stale_tag

        MERGE (fix:TrivyFix {id: 'npm|express|4.18.3'})
        MERGE (p)-[r3:SHOULD_UPDATE_TO]->(fix)
        SET r3.lastupdated = $stale_tag

        MERGE (p2:Package:Ontology {id: 'npm|body-parser|1.20.2'})
        SET p2.lastupdated = $update_tag
        MERGE (p)-[r4:DEPENDS_ON]->(p2)
        SET r4.lastupdated = $stale_tag

        MERGE (tp:TrivyPackage {normalized_id: 'npm|express|4.18.2'})
        MERGE (p)-[r5:DETECTED_AS]->(tp)
        SET r5.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
        stale_tag=stale_tag,
    )

    cartography.intel.ontology.packages.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    stale_derived_rels_count = neo4j_session.run(
        """
        MATCH (:Package {id: 'npm|express|4.18.2'})-[r]->()
        WHERE type(r) IN ['DEPLOYED', 'SHOULD_UPDATE_TO', 'DEPENDS_ON']
        RETURN count(r) as count
        """,
    ).single()["count"]
    assert stale_derived_rels_count == 0

    stale_affects_count = neo4j_session.run(
        """
        MATCH (:TrivyImageFinding {id: 'TIF|CVE-2024-99999'})-[r:AFFECTS]->(:Package {id: 'npm|express|4.18.2'})
        RETURN count(r) as count
        """,
    ).single()["count"]
    assert stale_affects_count == 0

    fresh_detected_as_count = neo4j_session.run(
        """
        MATCH (:Package {id: 'npm|express|4.18.2'})-[r:DETECTED_AS]->(:TrivyPackage {normalized_id: 'npm|express|4.18.2'})
        RETURN count(r) as count
        """,
    ).single()["count"]
    assert fresh_detected_as_count == 1
