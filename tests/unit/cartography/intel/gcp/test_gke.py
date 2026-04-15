"""
Unit tests for GKE cluster, node pool, and Compute node-pool linking.

File location: tests/unit/cartography/intel/gcp/test_gke.py

Run:
    pytest tests/unit/cartography/intel/gcp/test_gke.py -v

The neo4j_session fixture is provided by cartography's conftest.py.
GKE_CLUSTERS is imported from tests/data/gke.py.
"""
from cartography.intel.gcp.compute import load_gcp_instances
from cartography.intel.gcp.compute import transform_gcp_instances
from cartography.intel.gcp.gke import load_gke_clusters
from cartography.intel.gcp.gke import load_gke_node_pools
from tests.data.gcp.gke import GKE_CLUSTERS

TEST_PROJECT_ID = "test-cluster"
TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 999999999


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cluster_id():
    return "projects/test-cluster/locations/europe-west2/clusters/test-cluster"


def _pool_id(pool_name="default-111-111-111-111-gke-17"):
    return f"{_cluster_id()}/nodePools/{pool_name}"


def _make_gke_instance(
    project_id="test-cluster", cluster_name="test-cluster",
    pool_name="default-111-111-111-111-gke-17",
):
    """Return a minimal transformed GCP instance dict that carries GKE labels."""
    return {
        "partial_uri": f"projects/{project_id}/zones/europe-west2-a/instances/gke-node-1",
        "id": f"projects/{project_id}/zones/europe-west2-a/instances/gke-node-1",
        "project_id": project_id,
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project_id}"
            "/zones/europe-west2-a/instances/gke-node-1"
        ),
        "name": "gke-node-1",
        "zone_name": "europe-west2-a",
        "region": "europe-west2",
        "status": "RUNNING",
        "gke_cluster_name": cluster_name,
        "gke_node_pool_name": pool_name,
        "networkInterfaces": [],
        "tags": {},
        "disks": [],
        "serviceAccounts": [],
    }


def _make_plain_instance(project_id="test-cluster"):
    """Return a transformed GCP instance dict with NO GKE labels."""
    return {
        "partial_uri": f"projects/{project_id}/zones/europe-west2-a/instances/plain-vm",
        "id": f"projects/{project_id}/zones/europe-west2-a/instances/plain-vm",
        "project_id": project_id,
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project_id}"
            "/zones/europe-west2-a/instances/plain-vm"
        ),
        "name": "plain-vm",
        "zone_name": "europe-west2-a",
        "region": "europe-west2",
        "status": "RUNNING",
        "gke_cluster_name": None,
        "gke_node_pool_name": None,
        "networkInterfaces": [],
        "tags": {},
        "disks": [],
        "serviceAccounts": [],
    }


# ---------------------------------------------------------------------------
# Tests: load_gke_clusters (regression guard on existing behaviour)
# ---------------------------------------------------------------------------

def test_load_gke_clusters_creates_cluster_node(neo4j_session):
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    result = neo4j_session.run(
        "MATCH (c:GKECluster{id: $Id}) RETURN c",
        Id=_cluster_id(),
    ).data()

    assert len(result) == 1
    c = result[0]["c"]
    assert c["name"] == "test-cluster"
    assert c["status"] == "RUNNING"
    assert c["network_policy"] == "CALICO"
    assert c["private_nodes"] is True
    assert c["lastupdated"] == TEST_UPDATE_TAG


def test_load_gke_clusters_project_relationship(neo4j_session):
    neo4j_session.run("MERGE (p:GCPProject{id: $Id})", Id=TEST_PROJECT_ID)
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    result = neo4j_session.run(
        "MATCH (p:GCPProject{id: $Pid})-[:RESOURCE]->(c:GKECluster) RETURN c.name AS name",
        Pid=TEST_PROJECT_ID,
    ).data()

    assert len(result) == 1
    assert result[0]["name"] == "test-cluster"


def test_load_gke_clusters_empty_list(neo4j_session):
    load_gke_clusters(neo4j_session, [], TEST_PROJECT_ID, TEST_UPDATE_TAG)
    result = neo4j_session.run("MATCH (c:GKECluster) RETURN c").data()
    assert len(result) == 0


# ---------------------------------------------------------------------------
# Tests: load_gke_node_pools
# ---------------------------------------------------------------------------

def test_load_gke_node_pools_creates_node_pool_node(neo4j_session):
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    result = neo4j_session.run(
        "MATCH (p:GKENodePool{id: $Id}) RETURN p",
        Id=_pool_id(),
    ).data()

    assert len(result) == 1
    pool = result[0]["p"]
    assert pool["name"] == "default-111-111-111-111-gke-17"
    assert pool["status"] == "RUNNING"
    assert pool["machine_type"] == "n1-standard-8"
    assert pool["disk_size_gb"] == 50
    assert pool["image_type"] == "COS"
    assert pool["disk_type"] == "pd-standard"
    assert pool["auto_repair"] is True
    assert pool["max_pods_per_node"] == "10"
    assert pool["cluster_id"] == _cluster_id()
    assert pool["lastupdated"] == TEST_UPDATE_TAG


def test_load_gke_node_pools_creates_has_node_pool_relationship(neo4j_session):
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    result = neo4j_session.run(
        """
        MATCH (c:GKECluster{id: $ClusterId})-[:HAS_NODE_POOL]->(p:GKENodePool)
        RETURN p.name AS name
        """,
        ClusterId=_cluster_id(),
    ).data()

    assert len(result) == 1
    assert result[0]["name"] == "default-111-111-111-111-gke-17"


def test_load_gke_node_pools_is_idempotent(neo4j_session):
    """Running load_gke_node_pools twice must not create duplicate nodes or edges."""
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    pools = neo4j_session.run("MATCH (p:GKENodePool) RETURN p").data()
    assert len(pools) == 1

    rels = neo4j_session.run("MATCH ()-[r:HAS_NODE_POOL]->() RETURN r").data()
    assert len(rels) == 1


def test_load_gke_node_pools_updates_lastupdated(neo4j_session):
    """On re-sync with a newer tag, lastupdated must be refreshed."""
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG_2)

    result = neo4j_session.run(
        "MATCH (p:GKENodePool{id: $Id}) RETURN p.lastupdated AS ts",
        Id=_pool_id(),
    ).data()

    assert result[0]["ts"] == TEST_UPDATE_TAG_2


def test_load_gke_node_pools_empty_cluster_list(neo4j_session):
    load_gke_node_pools(neo4j_session, [], TEST_PROJECT_ID, TEST_UPDATE_TAG)
    result = neo4j_session.run("MATCH (p:GKENodePool) RETURN p").data()
    assert len(result) == 0


def test_load_gke_node_pools_cluster_with_empty_node_pools(neo4j_session):
    """A cluster with an empty nodePools list must not raise."""
    clusters_no_pools = [{**GKE_CLUSTERS[0], "nodePools": []}]
    load_gke_clusters(neo4j_session, clusters_no_pools, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, clusters_no_pools, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    result = neo4j_session.run("MATCH (p:GKENodePool) RETURN p").data()
    assert len(result) == 0


def test_load_gke_node_pools_cluster_missing_node_pools_key(neo4j_session):
    """A cluster dict with no 'nodePools' key at all must not raise."""
    cluster_copy = {k: v for k, v in GKE_CLUSTERS[0].items() if k != "nodePools"}
    load_gke_clusters(neo4j_session, [cluster_copy], TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, [cluster_copy], TEST_PROJECT_ID, TEST_UPDATE_TAG)

    result = neo4j_session.run("MATCH (p:GKENodePool) RETURN p").data()
    assert len(result) == 0


# ---------------------------------------------------------------------------
# Tests: transform_gcp_instances – GKE label extraction
# ---------------------------------------------------------------------------

def test_transform_gcp_instances_extracts_gke_labels(mocker):
    """
    transform_gcp_instances must read goog-gke-cluster-name and goog-gke-nodepool
    from instance labels and expose them as gke_cluster_name / gke_node_pool_name.
    """
    raw_instance = {
        "id": "11111",
        "name": "gke-node-1",
        "selfLink": (
            "https://www.googleapis.com/compute/v1/projects/test-cluster"
            "/zones/europe-west2-a/instances/gke-node-1"
        ),
        "zone": (
            "https://www.googleapis.com/compute/v1/projects/test-cluster"
            "/zones/europe-west2-a"
        ),
        "status": "RUNNING",
        "labels": {
            "goog-gke-cluster-name": "test-cluster",
            "goog-gke-nodepool": "default-111-111-111-111-gke-17",
        },
        "networkInterfaces": [
            {
                "name": "nic0",
                "subnetwork": (
                    "https://www.googleapis.com/compute/v1/projects/test-cluster"
                    "/regions/europe-west2/subnetworks/test-subnet"
                ),
                "network": (
                    "https://www.googleapis.com/compute/v1/projects/test-cluster"
                    "/global/networks/test-network"
                ),
            },
        ],
        "disks": [],
    }
    mocker.patch(
        "cartography.intel.gcp.compute.gcp_console_link.get_console_link",
        return_value="https://console.cloud.google.com/fake",
    )
    mock_compute = mocker.MagicMock()

    instances = transform_gcp_instances([raw_instance], mock_compute)

    assert len(instances) == 1
    assert instances[0]["gke_cluster_name"] == "test-cluster"
    assert instances[0]["gke_node_pool_name"] == "default-111-111-111-111-gke-17"


def test_transform_gcp_instances_no_gke_labels(mocker):
    """Instances without GKE labels must have None for both GKE fields."""
    raw_instance = {
        "id": "22222",
        "name": "plain-vm",
        "selfLink": (
            "https://www.googleapis.com/compute/v1/projects/test-cluster"
            "/zones/europe-west2-a/instances/plain-vm"
        ),
        "zone": (
            "https://www.googleapis.com/compute/v1/projects/test-cluster"
            "/zones/europe-west2-a"
        ),
        "status": "RUNNING",
        "networkInterfaces": [
            {
                "name": "nic0",
                "subnetwork": (
                    "https://www.googleapis.com/compute/v1/projects/test-cluster"
                    "/regions/europe-west2/subnetworks/test-subnet"
                ),
                "network": (
                    "https://www.googleapis.com/compute/v1/projects/test-cluster"
                    "/global/networks/test-network"
                ),
            },
        ],
        "disks": [],
    }
    mocker.patch(
        "cartography.intel.gcp.compute.gcp_console_link.get_console_link",
        return_value="https://console.cloud.google.com/fake",
    )
    mock_compute = mocker.MagicMock()

    instances = transform_gcp_instances([raw_instance], mock_compute)

    assert len(instances) == 1
    assert instances[0]["gke_cluster_name"] is None
    assert instances[0]["gke_node_pool_name"] is None


# ---------------------------------------------------------------------------
# Tests: load_gcp_instances – HAS_NODE relationship creation
# ---------------------------------------------------------------------------

def test_load_gcp_instances_links_gke_node_to_cluster(neo4j_session):
    """A GKE-labeled instance must be linked to its cluster via HAS_NODE."""
    neo4j_session.run("MERGE (p:GCPProject{id: $Id})", Id=TEST_PROJECT_ID)
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    load_gcp_instances(neo4j_session, [_make_gke_instance()], TEST_UPDATE_TAG)

    result = neo4j_session.run(
        "MATCH (c:GKECluster{id: $ClusterId})-[:HAS_NODE]->(i:GCPInstance) RETURN i.instancename AS name",
        ClusterId=_cluster_id(),
    ).data()

    assert len(result) == 1
    assert result[0]["name"] == "gke-node-1"


def test_load_gcp_instances_links_gke_node_to_pool(neo4j_session):
    """A GKE-labeled instance must be linked to its node pool via HAS_NODE."""
    neo4j_session.run("MERGE (p:GCPProject{id: $Id})", Id=TEST_PROJECT_ID)
    load_gke_clusters(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    load_gke_node_pools(neo4j_session, GKE_CLUSTERS, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    load_gcp_instances(neo4j_session, [_make_gke_instance()], TEST_UPDATE_TAG)

    result = neo4j_session.run(
        "MATCH (p:GKENodePool{id: $PoolId})-[:HAS_NODE]->(i:GCPInstance) RETURN i.instancename AS name",
        PoolId=_pool_id(),
    ).data()

    assert len(result) == 1
    assert result[0]["name"] == "gke-node-1"


def test_load_gcp_instances_no_gke_links_for_plain_vms(neo4j_session):
    """Plain VMs must not produce any HAS_NODE relationships."""
    neo4j_session.run("MERGE (p:GCPProject{id: $Id})", Id=TEST_PROJECT_ID)

    load_gcp_instances(neo4j_session, [_make_plain_instance()], TEST_UPDATE_TAG)

    result = neo4j_session.run("MATCH ()-[r:HAS_NODE]->() RETURN r").data()
    assert len(result) == 0


def test_load_gcp_instances_gke_link_skipped_when_cluster_missing(neo4j_session):
    """
    If the GKE sync has not run (cluster node absent), HAS_NODE links must be
    silently skipped rather than raising an error.
    The MATCH-not-MERGE pattern in _link_instance_to_gke_cluster guarantees this.
    """
    neo4j_session.run("MERGE (p:GCPProject{id: $Id})", Id=TEST_PROJECT_ID)
    # Deliberately do NOT call load_gke_clusters

    load_gcp_instances(neo4j_session, [_make_gke_instance()], TEST_UPDATE_TAG)

    instances = neo4j_session.run("MATCH (i:GCPInstance) RETURN i").data()
    assert len(instances) == 1

    rels = neo4j_session.run("MATCH ()-[r:HAS_NODE]->() RETURN r").data()
    assert len(rels) == 0


def test_load_gcp_instances_gke_properties_stored_on_node(neo4j_session):
    """gke_cluster_name and gke_node_pool_name must be persisted on the GCPInstance."""
    neo4j_session.run("MERGE (p:GCPProject{id: $Id})", Id=TEST_PROJECT_ID)

    load_gcp_instances(neo4j_session, [_make_gke_instance()], TEST_UPDATE_TAG)

    result = neo4j_session.run(
        "MATCH (i:GCPInstance) RETURN i.gke_cluster_name AS cn, i.gke_node_pool_name AS pn",
    ).data()

    assert len(result) == 1
    assert result[0]["cn"] == "test-cluster"
    assert result[0]["pn"] == "default-111-111-111-111-gke-17"


def test_load_gcp_instances_plain_vm_gke_properties_are_null(neo4j_session):
    """Plain VMs must have null gke_cluster_name and gke_node_pool_name on the node."""
    neo4j_session.run("MERGE (p:GCPProject{id: $Id})", Id=TEST_PROJECT_ID)

    load_gcp_instances(neo4j_session, [_make_plain_instance()], TEST_UPDATE_TAG)

    result = neo4j_session.run(
        "MATCH (i:GCPInstance) RETURN i.gke_cluster_name AS cn, i.gke_node_pool_name AS pn",
    ).data()

    assert len(result) == 1
    assert result[0]["cn"] is None
    assert result[0]["pn"] is None
