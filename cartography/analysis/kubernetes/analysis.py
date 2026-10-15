from cartography.analysis.aws.analysis import AWS_LB_INTERFACE_FRONTED_ACCOUNTS
from cartography.analysis.aws.analysis import AWS_LB_MAY_FACE_INTERNET
from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Param
from cartography.graph.analysis import RawCypher
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import SetProperty

K8S_SERVICE_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes service internet exposure",
    short_name="k8s_service_asset_exposure",
    scope=ScopeById(
        "KubernetesCluster",
        "CLUSTER_ID",
        scope_on=("svc", "ing"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService) WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
    ),
)
K8S_POD_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes pod internet exposure",
    short_name="k8s_pod_asset_exposure",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="svc"),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService{exposed_internet: true})-[:TARGETS]->(pod:KubernetesPod) WITH DISTINCT pod",
            effects=(
                SetProperty("pod", "exposed_internet", True, label="KubernetesPod"),
                AddToSet("pod", "exposed_internet_type", "lb", label="KubernetesPod"),
            ),
        ),
    ),
)
K8S_CONTAINER_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes container internet exposure",
    short_name="k8s_container_asset_exposure",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="pod"),
    statements=(
        AnalysisStatement(
            match="MATCH (pod:KubernetesPod{exposed_internet: true})-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                SetProperty("c", "exposed_internet", True, label="KubernetesContainer"),
                AddToSet(
                    "c", "exposed_internet_type", "lb", label="KubernetesContainer"
                ),
            ),
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
    scope=ScopeById(
        "KubernetesCluster",
        "CLUSTER_ID",
        scope_on=("svc", "ing"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "pod",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="KubernetesPod",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "pod",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="KubernetesPod",
                    scoped_to="target",
                ),
            ),
        ),
    ),
)
K8S_LB_CONTAINER_EXPOSURE = AnalysisJob(
    name="Kubernetes LoadBalancer to container EXPOSE relationships",
    short_name="k8s_lb_container_exposure",
    scope=ScopeById(
        "KubernetesCluster",
        "CLUSTER_ID",
        scope_on=("svc", "ing"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="KubernetesContainer",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="KubernetesContainer",
                    scoped_to="target",
                ),
            ),
        ),
    ),
)
K8S_LB_EXPOSURE_JOBS = (K8S_LB_POD_EXPOSURE, K8S_LB_CONTAINER_EXPOSURE)
# Paths into the cluster whose internet reach the graph cannot resolve:
# - an Ingress or a LoadBalancer Service with no matching AWS load balancer, or with
#   a status hostname that matches none, and an Ingress whose status lists an IP
#   with no hostname. Each status address is an entry point, so one the graph cannot
#   resolve may face the internet even when another is an internal load balancer.
#   A LoadBalancer Service's IPs need no check: the pods it selects, and the backends
#   of an Ingress that shares its load balancer, are never marked;
# - a Service without a selector, whose endpoints, and so the pods behind it, are
#   managed by hand and not linked to it, when it is a NodePort or LoadBalancer
#   Service or an Ingress routes to it, and an ExternalName Service an Ingress routes
#   to, which is resolved through DNS and ignores any selector it has;
# - any Gateway or HTTPRoute, since Gateways are not linked to a load balancer;
# - a load balancer that may face the internet and sends traffic straight to a
#   private IP on a node's interface. With the VPC CNI, pod IPs are secondary IPs on
#   node interfaces, and an IP target group (for example a TargetGroupBinding) can
#   reach a pod that no Service or Ingress links to that load balancer;
# - an EC2-backed node whose instance is not in the graph, so the previous check
#   cannot see its interfaces, or whose instance has an interface with an IPv6
#   address or a public IP on a secondary private IP. Those reach pods directly: IPv6
#   pod addresses come from the node's interfaces, and VPC CNI pod IPs are secondary
#   private IPs.
# Every checked cluster records the result, including a count of 0. When
# $CHECK_INPUTS_SYNCED is false, because a list call this check relies on failed and
# the sync kept the previous Services, Ingresses, Gateways or Nodes, nothing is
# written and the stamped cleanup withdraws the cluster's previous result.
K8S_UNMODELED_INTERNET_PATHS = AnalysisJob(
    name="Kubernetes unmodeled internet paths",
    short_name="k8s_unmodeled_internet_paths",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="cluster"),
    statements=(
        AnalysisStatement(
            match="""
            MATCH (cluster:KubernetesCluster)
            WHERE $CHECK_INPUTS_SYNCED
            WITH cluster, """
            + AWS_LB_INTERFACE_FRONTED_ACCOUNTS
            + """ AS fronted_accounts
            WITH cluster,
                COLLECT {
                    MATCH (cluster)-[:RESOURCE]->(entry)
                    WHERE entry:KubernetesGateway
                    OR entry:KubernetesHTTPRoute
                    OR (
                        (entry:KubernetesIngress OR (entry:KubernetesService AND entry.type = 'LoadBalancer'))
                        AND (
                            NOT EXISTS { MATCH (entry)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2) }
                            OR any(
                                dns_name IN coalesce(entry.load_balancer_dns_names, [])
                                WHERE NOT EXISTS {
                                    MATCH (entry)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2 {dnsname: dns_name})
                                }
                            )
                        )
                    )
                    OR (entry:KubernetesIngress AND size(coalesce(entry.load_balancer_ips, [])) > 0)
                    OR (
                        entry:KubernetesService
                        AND (
                            entry.type = 'ExternalName'
                            OR coalesce(entry.selector, 'null') IN ['null', '{}']
                        )
                        AND (
                            entry.type IN ['NodePort', 'LoadBalancer']
                            OR EXISTS { MATCH (:KubernetesIngress)-[:TARGETS]->(entry) }
                        )
                    )
                    RETURN entry.id ORDER BY entry.id
                } + COLLECT {
                    MATCH (cluster)-[:RESOURCE]->(:KubernetesNode)-[:IS_INSTANCE]->(:AWSEC2Instance)
                        -[:NETWORK_INTERFACE]->(:AWSNetworkInterface)-[:PRIVATE_IP_ADDRESS]->(:AWSEC2PrivateIp)
                        <-[:EXPOSE*1..2]-(lb:AWSLoadBalancerV2)
                    WHERE """
            + AWS_LB_MAY_FACE_INTERNET
            + """
                    RETURN DISTINCT lb.id AS id ORDER BY id
                } + COLLECT {
                    MATCH (cluster)-[:RESOURCE]->(node:KubernetesNode)
                    WHERE (
                        node.instance_id IS NOT NULL
                        AND NOT EXISTS { MATCH (node)-[:IS_INSTANCE]->(:AWSEC2Instance) }
                    )
                    OR EXISTS {
                        MATCH (node)-[:IS_INSTANCE]->(:AWSEC2Instance)-[:NETWORK_INTERFACE]->(eni:AWSNetworkInterface)
                        WHERE size(coalesce(eni.ipv6_addresses, [])) > 0
                        OR EXISTS {
                            MATCH (eni)-[:PRIVATE_IP_ADDRESS]->(address:AWSEC2PrivateIp)
                            WHERE address.public_ip IS NOT NULL
                            AND NOT coalesce(address.primary, false)
                        }
                    }
                    RETURN node.id ORDER BY node.id
                } AS paths
            """,
            effects=(
                SetProperties(
                    "cluster",
                    {
                        "unmodeled_internet_paths": RawCypher(
                            "CASE WHEN size(paths) > 0 THEN paths[..10] END"
                        ),
                        "unmodeled_internet_path_count": RawCypher("size(paths)"),
                        "unmodeled_internet_paths_checked_at": Param("UPDATE_TAG"),
                    },
                    label="KubernetesCluster",
                    cleanup_stamp="unmodeled_internet_paths_checked_at",
                ),
            ),
        ),
    ),
)
# A pod has no modeled internet path when its cluster was checked in this run with no
# unmodeled internet paths, it uses neither the host network nor host ports, no
# NodePort or LoadBalancer Service selects it, and every load balancer that reaches it
# through a Service or an Ingress, directly or chained behind another load balancer,
# is internal in a checked, clear AWS account. A LoadBalancer Service opens a node
# port on every node unless allocateLoadBalancerNodePorts is false, which the graph
# does not record, so it counts as a NodePort Service. An Ingress that shares its load
# balancer with a LoadBalancer Service is served by an in-cluster controller such as
# ingress-nginx, which routes what reaches that Service's node port to the Ingress's
# backends, so they count as selected by it. Results are replaced, not cleared first,
# so a reader keeps the previous result until this run decides. The pods are collected
# first so that the load balancer interface rule is evaluated once, not once per pod.
K8S_NO_MODELED_INTERNET_PATH = AnalysisJob(
    name="Kubernetes no modeled internet path",
    short_name="k8s_no_modeled_internet_path",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="pod"),
    statements=(
        AnalysisStatement(
            match="""
            WITH collect(pod) AS pods
            WITH pods, """
            + AWS_LB_INTERFACE_FRONTED_ACCOUNTS
            + """ AS fronted_accounts
            UNWIND pods AS pod
            MATCH (pod:KubernetesPod)
            WHERE NOT coalesce(pod.host_network, false)
            AND NOT coalesce(pod.exposed_internet, false)
            AND EXISTS {
                MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod)
                WHERE cluster.unmodeled_internet_paths_checked_at >= pod.lastupdated
                AND cluster.unmodeled_internet_path_count = 0
            }
            AND size(coalesce(pod.host_ports, [])) = 0
            AND NOT EXISTS {
                MATCH (pod)-[:CONTAINS]->(c:KubernetesContainer)
                WHERE c.exposed_internet = true
            }
            AND NOT EXISTS {
                MATCH (service:KubernetesService)-[:TARGETS]->(pod)
                WHERE service.type IN ['NodePort', 'LoadBalancer']
            }
            AND NOT EXISTS {
                MATCH (ingress:KubernetesIngress)-[:TARGETS]->(:KubernetesService)-[:TARGETS]->(pod)
                MATCH (ingress)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2)
                    <-[:USES_LOAD_BALANCER]-(:KubernetesService)
            }
            AND NOT EXISTS {
                MATCH (front)-[:TARGETS*1..2]->(pod)
                WHERE front:KubernetesService OR front:KubernetesIngress
                MATCH (front)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2)<-[:EXPOSE*0..1]-(lb:AWSLoadBalancerV2)
                WHERE """
            + AWS_LB_MAY_FACE_INTERNET
            + """
            }
            OPTIONAL MATCH (pod)-[:CONTAINS]->(container:KubernetesContainer)
            """,
            incremental_on="pod",
            effects=(
                SetProperties(
                    "pod",
                    {
                        "no_modeled_internet_path": True,
                        "no_modeled_internet_path_checked_at": Param("UPDATE_TAG"),
                    },
                    label="KubernetesPod",
                    cleanup_stamp="no_modeled_internet_path_checked_at",
                ),
                SetProperties(
                    "container",
                    {
                        "no_modeled_internet_path": True,
                        "no_modeled_internet_path_checked_at": Param("UPDATE_TAG"),
                    },
                    label="KubernetesContainer",
                    cleanup_stamp="no_modeled_internet_path_checked_at",
                ),
            ),
        ),
    ),
)
