from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# The load balancer predicate below mirrors the one in
# cartography.analysis.kubernetes.analysis.K8S_SERVICE_ASSET_EXPOSURE, which sets
# KubernetesService.exposed_internet. The facts re-derive it from the graph rather
# than reading that flag so that each path reports its own exposure_type, and so a
# finding stands on its own evidence even when the analysis job has not yet run.

# Path 1: a service of type LoadBalancer sitting directly behind an internet-facing
# load balancer. Only LoadBalancer-type services carry a USES_LOAD_BALANCER edge:
# the intel module populates load_balancer_dns_names solely for that type.
_kubernetes_service_exposed_direct_load_balancer = Fact(
    id="kubernetes_service_exposed_direct_load_balancer",
    name="Internet-Exposed Kubernetes Service Behind a Load Balancer",
    description=(
        "Kubernetes services of type LoadBalancer whose cloud load balancer "
        "accepts traffic from the public internet. The service's "
        "status.loadBalancer hostname is matched to an AWSLoadBalancerV2, which "
        "qualifies as internet-facing when the AWS asset-exposure job has "
        "flagged it, or when it is an internet-facing network load balancer "
        "(NLBs bypass security groups, so the AWS job does not flag them). "
        "Anyone on the internet can reach the pods this service selects."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(svc:KubernetesService)
    WHERE EXISTS {
        MATCH (svc)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2)
        WHERE lb.exposed_internet = true
           OR (lb.scheme = 'internet-facing' AND lb.type = 'network')
    }
    RETURN
        svc.qualified_name AS name,
        svc.id AS id,
        cluster.name AS cluster_name,
        svc.namespace AS namespace,
        svc.type AS service_type,
        'direct_load_balancer' AS exposure_type
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(svc:KubernetesService)
          -[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2)
    WHERE lb.exposed_internet = true
       OR (lb.scheme = 'internet-facing' AND lb.type = 'network')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (svc:KubernetesService)
    WHERE svc.type = 'LoadBalancer'
    RETURN COUNT(svc) AS count
    """,
    asset_label="KubernetesService",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)


# Path 2: a backend service reached through an Ingress that an ingress controller
# has published on an internet-facing load balancer.
_kubernetes_service_exposed_via_ingress = Fact(
    id="kubernetes_service_exposed_via_ingress",
    name="Internet-Exposed Kubernetes Service Behind an Ingress",
    description=(
        "Kubernetes services named as a backend by an Ingress whose controller "
        "has published it on an internet-facing load balancer. The hostname the "
        "controller writes into the Ingress status is matched to an "
        "AWSLoadBalancerV2, so this covers both a per-Ingress load balancer (AWS "
        "Load Balancer Controller) and a shared one fronting an in-cluster "
        "controller such as nginx. Internet traffic reaches the backend pods "
        "through the controller, whatever the backend service's own type is."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(svc:KubernetesService)
    WHERE EXISTS {
        MATCH (ing:KubernetesIngress)-[:TARGETS]->(svc)
        MATCH (ing)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2)
        WHERE lb.exposed_internet = true
           OR (lb.scheme = 'internet-facing' AND lb.type = 'network')
    }
    RETURN
        svc.qualified_name AS name,
        svc.id AS id,
        cluster.name AS cluster_name,
        svc.namespace AS namespace,
        svc.type AS service_type,
        'ingress_load_balancer' AS exposure_type
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(svc:KubernetesService)
          <-[:TARGETS]-(ing:KubernetesIngress)
          -[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2)
    WHERE lb.exposed_internet = true
       OR (lb.scheme = 'internet-facing' AND lb.type = 'network')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (svc:KubernetesService)
    WHERE EXISTS { MATCH (:KubernetesIngress)-[:TARGETS]->(svc) }
    RETURN COUNT(svc) AS count
    """,
    asset_label="KubernetesService",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)


# TODO: add a NodePort fact once the intel module ingests Service.spec.ports.
# A NodePort service is reachable on every node's address, so the finding needs
# the nodePort value plus a reachable node. The chain
# KubernetesService -> KubernetesPod ... KubernetesNode -[:IS_INSTANCE]->
# AWSEC2Instance{exposed_internet: true} is walkable today, but without the port
# numbers there is nothing to report and no way to tell a node port apart from a
# blocked one.

# TODO: extend both facts beyond AWSLoadBalancerV2 once Kubernetes services and
# ingresses are matched to GCP forwarding rules and Azure load balancers. Only
# AWS load balancers are linked today, so a GKE or AKS service of type
# LoadBalancer produces no finding.

# TODO: add a Gateway API fact. KubernetesGateway -[:ROUTES]-> KubernetesHTTPRoute
# -[:TARGETS]-> KubernetesService already exists, but KubernetesGateway models no
# status addresses or listeners and has no load balancer edge, so there is no way
# to establish that the gateway is internet-facing.


class KubernetesServiceExposed(Finding):
    name: str | None = None
    id: str | None = None
    cluster_name: str | None = None
    namespace: str | None = None
    service_type: str | None = None
    exposure_type: str | None = None


kubernetes_service_exposed = Rule(
    id="kubernetes_service_exposed",
    name="Internet-Exposed Kubernetes Services",
    description=(
        "Kubernetes services reachable from the public internet, by either of "
        "the two routes traffic takes into a cluster: a service of type "
        "LoadBalancer fronted directly by an internet-facing load balancer, or "
        "a backend service published through an Ingress. Covers services whose "
        "load balancer is an AWSLoadBalancerV2; NodePort services, Gateway API "
        "routes, and non-AWS load balancers are not yet detected."
    ),
    output_model=KubernetesServiceExposed,
    facts=(
        _kubernetes_service_exposed_direct_load_balancer,
        _kubernetes_service_exposed_via_ingress,
    ),
    tags=(
        "infrastructure",
        "kubernetes",
        "network",
        "attack_surface",
        "stride:information_disclosure",
        "stride:tampering",
    ),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.20"),
        soc2_tsc("CC6.6"),
    ),
)
