from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.kapsule.clusters
from tests.data.scaleway.kapsule import SCALEWAY_KAPSULE_CLUSTERS
from tests.data.scaleway.kapsule import SCALEWAY_KAPSULE_NODES
from tests.data.scaleway.kapsule import SCALEWAY_KAPSULE_POOLS
from tests.data.scaleway.kapsule import TEST_CLUSTER_ID
from tests.data.scaleway.kapsule import TEST_NODE_ID
from tests.data.scaleway.kapsule import TEST_POOL_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.kapsule.clusters,
    "get",
    return_value=(
        SCALEWAY_KAPSULE_CLUSTERS,
        SCALEWAY_KAPSULE_POOLS,
        SCALEWAY_KAPSULE_NODES,
    ),
)
def test_load_scaleway_kapsule(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.kapsule.clusters.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes exist
    assert check_nodes(neo4j_session, "ScalewayKapsuleCluster", ["id", "name"]) == {
        (TEST_CLUSTER_ID, "demo-cluster"),
    }
    assert check_nodes(neo4j_session, "ScalewayKapsulePool", ["id", "name"]) == {
        (TEST_POOL_ID, "demo-pool"),
    }
    assert check_nodes(neo4j_session, "ScalewayKapsuleNode", ["id", "name"]) == {
        (TEST_NODE_ID, "scw-demo-cluster-demo-pool-abc"),
    }

    # Cross-cloud ontology label on the cluster.
    assert check_nodes(neo4j_session, "ComputeCluster", ["id"]) == {(TEST_CLUSTER_ID,)}

    # Normalized _ont_* fields populated from the ComputeCluster mapping.
    assert check_nodes(
        neo4j_session,
        "ComputeCluster",
        ["_ont_name", "_ont_region", "_ont_version", "_ont_status", "_ont_source"],
    ) == {("demo-cluster", "fr-par", "1.30.2", "active", "scaleway")}

    # Project ownership.
    for label in (
        "ScalewayKapsuleCluster",
        "ScalewayKapsulePool",
        "ScalewayKapsuleNode",
    ):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Cluster -> Pool
    assert check_rels(
        neo4j_session,
        "ScalewayKapsuleCluster",
        "id",
        "ScalewayKapsulePool",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_CLUSTER_ID, TEST_POOL_ID)}

    # Pool -> Node
    assert check_rels(
        neo4j_session,
        "ScalewayKapsulePool",
        "id",
        "ScalewayKapsuleNode",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_POOL_ID, TEST_NODE_ID)}

    # Cluster -> Node (direct, by cluster_id on the node).
    assert check_rels(
        neo4j_session,
        "ScalewayKapsuleCluster",
        "id",
        "ScalewayKapsuleNode",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_CLUSTER_ID, TEST_NODE_ID)}
