from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.cluster_policies
import cartography.intel.databricks.clusters
import cartography.intel.databricks.instance_pools
from tests.data.databricks.cluster_policies import DATABRICKS_CLUSTER_POLICIES
from tests.data.databricks.clusters import DATABRICKS_CLUSTERS
from tests.data.databricks.instance_pools import DATABRICKS_INSTANCE_POOLS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_policies_and_pools(neo4j_session):
    cartography.intel.databricks.cluster_policies.load_cluster_policies(
        neo4j_session,
        cartography.intel.databricks.cluster_policies.transform(
            DATABRICKS_CLUSTER_POLICIES, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.instance_pools.load_instance_pools(
        neo4j_session,
        cartography.intel.databricks.instance_pools.transform(
            DATABRICKS_INSTANCE_POOLS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.clusters,
    "get",
    return_value=DATABRICKS_CLUSTERS,
)
def test_load_databricks_clusters(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _seed_policies_and_pools(neo4j_session)

    cartography.intel.databricks.clusters.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksCluster",
        ["id", "cluster_id", "cluster_name", "data_security_mode"],
    ) == {
        (
            scoped("0202-cluster-aaaa"),
            "0202-cluster-aaaa",
            "analytics",
            "USER_ISOLATION",
        ),
        (
            scoped("0202-cluster-bbbb"),
            "0202-cluster-bbbb",
            "single-user-uc",
            "SINGLE_USER",
        ),
    }

    # Cluster -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksCluster",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("0202-cluster-aaaa"), DATABRICKS_WORKSPACE_ID),
        (scoped("0202-cluster-bbbb"), DATABRICKS_WORKSPACE_ID),
    }

    # Cluster -> ClusterPolicy HAS_POLICY (only first cluster has a policy)
    assert check_rels(
        neo4j_session,
        "DatabricksCluster",
        "id",
        "DatabricksClusterPolicy",
        "id",
        "HAS_POLICY",
        rel_direction_right=True,
    ) == {(scoped("0202-cluster-aaaa"), scoped("0001-policy-aaaa"))}

    # Cluster -> InstancePool USES_INSTANCE_POOL: first cluster lands edges
    # to *both* its worker pool and its distinct driver pool; the second
    # cluster has no pools attached.
    assert check_rels(
        neo4j_session,
        "DatabricksCluster",
        "id",
        "DatabricksInstancePool",
        "id",
        "USES_INSTANCE_POOL",
        rel_direction_right=True,
    ) == {
        (scoped("0202-cluster-aaaa"), scoped("0101-pool-aaaa")),
        (scoped("0202-cluster-aaaa"), scoped("0101-pool-driver")),
    }
