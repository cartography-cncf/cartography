from datetime import datetime

from dateutil.tz import tzutc
from scaleway.k8s.v1 import Cluster
from scaleway.k8s.v1 import ClusterStatus
from scaleway.k8s.v1 import CNI
from scaleway.k8s.v1 import Node
from scaleway.k8s.v1 import NodeStatus
from scaleway.k8s.v1 import Pool
from scaleway.k8s.v1 import PoolStatus
from scaleway.k8s.v1 import PoolVolumeType
from scaleway.k8s.v1 import Runtime

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_CLUSTER_ID = "11111111-1111-4820-b8d6-0eef10cfcd6d"
TEST_POOL_ID = "22222222-2222-4820-b8d6-0eef10cfcd6d"
TEST_NODE_ID = "33333333-3333-4820-b8d6-0eef10cfcd6d"
TEST_PRIVATE_NETWORK_ID = "44444444-4444-4820-b8d6-0eef10cfcd6d"


SCALEWAY_KAPSULE_CLUSTERS = [
    Cluster(
        id=TEST_CLUSTER_ID,
        type_="kapsule",
        name="demo-cluster",
        status=ClusterStatus.READY,
        version="1.30.2",
        region="fr-par",
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        tags=["demo"],
        cni=CNI.CILIUM,
        description="Demo cluster",
        cluster_url="https://demo-cluster.api.k8s.fr-par.scw.cloud",
        dns_wildcard="*.demo-cluster.nodes.k8s.fr-par.scw.cloud",
        upgrade_available=False,
        feature_gates=[],
        admission_plugins=[],
        apiserver_cert_sans=[],
        iam_nodes_group_id="55555555-5555-4820-b8d6-0eef10cfcd6d",
        pod_cidr="100.64.0.0/16",
        service_cidr="10.32.0.0/16",
        service_dns_ip="10.32.0.10",
        private_network_id=TEST_PRIVATE_NETWORK_ID,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]


SCALEWAY_KAPSULE_POOLS = [
    Pool(
        id=TEST_POOL_ID,
        cluster_id=TEST_CLUSTER_ID,
        name="demo-pool",
        status=PoolStatus.READY,
        version="1.30.2",
        node_type="DEV1-M",
        autoscaling=False,
        size=1,
        min_size=1,
        max_size=1,
        container_runtime=Runtime.CONTAINERD,
        autohealing=True,
        tags=["demo"],
        kubelet_args={},
        zone="fr-par-1",
        root_volume_type=PoolVolumeType.B_SSD,
        public_ip_disabled=False,
        security_group_id="",
        labels={},
        taints=[],
        startup_taints=[],
        region="fr-par",
        root_volume_size=21474836480,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]


SCALEWAY_KAPSULE_NODES = [
    Node(
        id=TEST_NODE_ID,
        pool_id=TEST_POOL_ID,
        cluster_id=TEST_CLUSTER_ID,
        provider_id="scaleway://instance/fr-par-1/abc",
        region="fr-par",
        name="scw-demo-cluster-demo-pool-abc",
        conditions={},
        status=NodeStatus.READY,
        public_ip_v4="51.159.0.10",
        public_ip_v6=None,
        error_message=None,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]
