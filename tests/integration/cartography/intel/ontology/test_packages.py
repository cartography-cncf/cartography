"""
Integration tests for ontology packages module
"""

from unittest.mock import patch

import cartography.intel.ontology.packages
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


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
    ],
)
def test_load_ontology_packages(_mock_get_source_nodes, neo4j_session):
    """Test end-to-end loading of ontology packages from mocked source nodes."""

    # Arrange - create source TrivyPackage and SyftPackage nodes for DETECTED_AS rels
    neo4j_session.run(
        """
        MERGE (p:TrivyPackage {id: 'npm|express|4.18.2'})
        SET p.normalized_id = 'npm|express|4.18.2',
            p.name = 'express', p.version = '4.18.2',
            p.type = 'npm'
        """,
    )
    neo4j_session.run(
        """
        MERGE (p:SyftPackage {id: 'npm|express|4.18.2'})
        SET p.normalized_id = 'npm|express|4.18.2',
            p.name = 'express', p.version = '4.18.2',
            p.type = 'npm'
        """,
    )
    neo4j_session.run(
        """
        MERGE (p:TrivyPackage {id: 'pypi|requests|2.31.0'})
        SET p.normalized_id = 'pypi|requests|2.31.0',
            p.name = 'requests', p.version = '2.31.0',
            p.type = 'pypi'
        """,
    )

    # Act
    cartography.intel.ontology.packages.sync(
        neo4j_session, TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert - Check that Package nodes were created
    expected_packages = {
        ("npm|express|4.18.2", "express", "4.18.2", "npm"),
        ("pypi|requests|2.31.0", "requests", "2.31.0", "pypi"),
    }
    actual_packages = check_nodes(
        neo4j_session, "Package", ["normalized_id", "name", "version", "type"],
    )
    assert actual_packages == expected_packages

    # Assert - Check that Package nodes have Ontology label
    ontology_count = neo4j_session.run(
        "MATCH (p:Package:Ontology) RETURN count(p) as count",
    ).single()["count"]
    assert ontology_count == 2

    # Assert - Check DETECTED_AS relationships to TrivyPackage
    expected_trivy_rels = {
        ("npm|express|4.18.2", "npm|express|4.18.2"),
        ("pypi|requests|2.31.0", "pypi|requests|2.31.0"),
    }
    actual_trivy_rels = check_rels(
        neo4j_session,
        "Package",
        "normalized_id",
        "TrivyPackage",
        "normalized_id",
        "DETECTED_AS",
        rel_direction_right=True,
    )
    assert actual_trivy_rels == expected_trivy_rels

    # Assert - Check DETECTED_AS relationships to SyftPackage
    expected_syft_rels = {
        ("npm|express|4.18.2", "npm|express|4.18.2"),
    }
    actual_syft_rels = check_rels(
        neo4j_session,
        "Package",
        "normalized_id",
        "SyftPackage",
        "normalized_id",
        "DETECTED_AS",
        rel_direction_right=True,
    )
    assert actual_syft_rels == expected_syft_rels
