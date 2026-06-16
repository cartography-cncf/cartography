from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect

K8S_SCOPE = AnalysisScope("KubernetesCluster", "CLUSTER_ID")

K8S_SERVICE_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes service internet exposure",
    short_name="k8s_service_asset_exposure",
    scope=K8S_SCOPE,
    effect=PropertyEffect(
        "KubernetesService",
        ("exposed_internet", "exposed_internet_type"),
    ),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') WITH DISTINCT svc WHERE svc.exposed_internet_type IS NULL OR NOT 'lb' IN svc.exposed_internet_type SET svc.exposed_internet = true, svc.exposed_internet_type = coalesce(svc.exposed_internet_type, []) + 'lb'",
        ),
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService) WITH DISTINCT svc WHERE svc.exposed_internet_type IS NULL OR NOT 'lb' IN svc.exposed_internet_type SET svc.exposed_internet = true, svc.exposed_internet_type = coalesce(svc.exposed_internet_type, []) + 'lb'",
        ),
    ),
)

K8S_POD_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes pod internet exposure",
    short_name="k8s_pod_asset_exposure",
    scope=K8S_SCOPE,
    effect=PropertyEffect(
        "KubernetesPod",
        ("exposed_internet", "exposed_internet_type"),
    ),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(svc:KubernetesService{exposed_internet: true})-[:TARGETS]->(pod:KubernetesPod) WITH DISTINCT pod WHERE pod.exposed_internet_type IS NULL OR NOT 'lb' IN pod.exposed_internet_type SET pod.exposed_internet = true, pod.exposed_internet_type = coalesce(pod.exposed_internet_type, []) + 'lb'",
        ),
    ),
)

K8S_CONTAINER_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes container internet exposure",
    short_name="k8s_container_asset_exposure",
    scope=K8S_SCOPE,
    effect=PropertyEffect(
        "KubernetesContainer",
        ("exposed_internet", "exposed_internet_type"),
    ),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(pod:KubernetesPod{exposed_internet: true})-[:CONTAINS]->(c:KubernetesContainer) WITH DISTINCT c WHERE c.exposed_internet_type IS NULL OR NOT 'lb' IN c.exposed_internet_type SET c.exposed_internet = true, c.exposed_internet_type = coalesce(c.exposed_internet_type, []) + 'lb'",
        ),
    ),
)

K8S_COMPUTE_ASSET_EXPOSURE_JOBS = (
    K8S_SERVICE_ASSET_EXPOSURE,
    K8S_POD_ASSET_EXPOSURE,
    K8S_CONTAINER_ASSET_EXPOSURE,
)

K8S_LB_POD_EXPOSURE = AnalysisJob(
    name="Kubernetes LoadBalancer to pod EXPOSE relationships",
    short_name="k8s_lb_pod_exposure",
    scope=K8S_SCOPE,
    effect=RelationshipEffect(
        "AWSLoadBalancerV2",
        "EXPOSE",
        "KubernetesPod",
        properties=("exposure_type",),
        scoped_to="target",
    ),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod) MERGE (lb)-[r:EXPOSE]->(pod) SET r.lastupdated = $UPDATE_TAG, r.exposure_type = 'via_lb_only'",
        ),
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod) MERGE (lb)-[r:EXPOSE]->(pod) SET r.lastupdated = $UPDATE_TAG, r.exposure_type = 'via_lb_only'",
        ),
    ),
)

K8S_LB_CONTAINER_EXPOSURE = AnalysisJob(
    name="Kubernetes LoadBalancer to container EXPOSE relationships",
    short_name="k8s_lb_container_exposure",
    scope=K8S_SCOPE,
    effect=RelationshipEffect(
        "AWSLoadBalancerV2",
        "EXPOSE",
        "KubernetesContainer",
        properties=("exposure_type",),
        scoped_to="target",
    ),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer) MERGE (lb)-[r:EXPOSE]->(c) SET r.lastupdated = $UPDATE_TAG, r.exposure_type = 'via_lb_only'",
        ),
        AnalysisStatement(
            "MATCH (cluster:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer) MERGE (lb)-[r:EXPOSE]->(c) SET r.lastupdated = $UPDATE_TAG, r.exposure_type = 'via_lb_only'",
        ),
    ),
)

K8S_LB_EXPOSURE_JOBS = (
    K8S_LB_POD_EXPOSURE,
    K8S_LB_CONTAINER_EXPOSURE,
)
