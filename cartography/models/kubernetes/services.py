from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the kubernetes service.")
    load_balancer_ips: PropertyRef = PropertyRef(
        "load_balancer_ips",
        description="Assigned IP addresses from the Kubernetes `Service.status.loadBalancer.ingress[].ip` field, not requested spec addresses. Used to match GCP forwarding rules for GKE clusters.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the kubernetes service."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="`<namespace>/<name>` identifier used to match the service from cross-namespace references such as `HTTPRoute.spec.rules[].backendRefs`.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the kubernetes service.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp of the deletion time of the kubernetes service.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this service is deployed.",
    )
    selector: PropertyRef = PropertyRef(
        "selector",
        description="Labels used by the service to select pods. Fetched from `service.spec.selector`. Stored as a JSON-encoded string.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="Type of kubernetes service e.g. `ClusterIP`.",
    )
    cluster_ip: PropertyRef = PropertyRef(
        "cluster_ip",
        description="The internal IP address assigned to the Kubernetes service within the cluster.",
    )
    load_balancer_ip: PropertyRef = PropertyRef(
        "load_balancer_ip",
        description="IP of the load balancer when service type is `LoadBalancer`.",
    )
    load_balancer_ingress: PropertyRef = PropertyRef(
        "load_balancer_ingress",
        description="The list of load balancer ingress points, typically containing the hostname and IP. Stored as a JSON-encoded string.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this service is deployed.",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="`True` when the service, or an ingress targeting it, uses an internet-facing load balancer. `False` otherwise.",
    )  # Populated by the K8S_SERVICE_ASSET_EXPOSURE analysis job.
    exposed_internet_type: PropertyRef = PropertyRef(
        "exposed_internet_type",
        extra_index=True,
        description="How it is exposed. Always `lb`.",
    )  # Populated by the K8S_SERVICE_ASSET_EXPOSURE analysis job.
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)-[:USES_LOAD_BALANCER]->(:LoadBalancerV2)
class KubernetesServiceToLoadBalancerV2Rel(CartographyRelSchema):
    """Links a service of type `LoadBalancer` to the AWS load balancer that exposes it, matching the service's `status.loadBalancer.ingress[].hostname` against `AWSLoadBalancerV2.dnsname`. Both sides are lowercased at ingestion, since AWS preserves the load balancer name's case in the DNS name it hands to the in-cluster controller."""

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"dnsname": PropertyRef("load_balancer_dns_names", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LOAD_BALANCER"
    properties: KubernetesServiceToLoadBalancerV2RelProperties = (
        KubernetesServiceToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToGCPForwardingRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)-[:USES_LOAD_BALANCER]->(:GCPForwardingRule)
class KubernetesServiceToGCPForwardingRuleRel(CartographyRelSchema):
    """Links a service of type `LoadBalancer` to the external GCP forwarding rule that exposes it, matching public `status.loadBalancer.ingress[].ip` addresses against `GCPForwardingRule.ip_address` within the GKE cluster's project. Only created for clusters ingested with GKE metadata. Backend health and firewall reachability are not evaluated."""

    target_node_label: str = "GCPForwardingRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "ip_address": PropertyRef("gcp_public_lb_ips", one_to_many=True),
            "project_id": PropertyRef("gcp_project_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LOAD_BALANCER"
    properties: KubernetesServiceToGCPForwardingRuleRelProperties = (
        KubernetesServiceToGCPForwardingRuleRelProperties()
    )


@dataclass(frozen=True)
# (:KubernetesService)-[:USES_LOAD_BALANCER]->(:GCPForwardingRule)
class KubernetesServiceToGCPInternalForwardingRuleRel(CartographyRelSchema):
    """Links a service of type `LoadBalancer` to the internal GCP forwarding rule that exposes it, matching private `status.loadBalancer.ingress[].ip` addresses against `GCPForwardingRule.ip_address` within the GKE cluster's project and VPC network, so private addresses reused in other networks do not collide."""

    target_node_label: str = "GCPForwardingRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "ip_address": PropertyRef("gcp_private_lb_ips", one_to_many=True),
            "project_id": PropertyRef("gcp_project_id"),
            "network": PropertyRef("gcp_network"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LOAD_BALANCER"
    properties: KubernetesServiceToGCPForwardingRuleRelProperties = (
        KubernetesServiceToGCPForwardingRuleRelProperties()
    )


@dataclass(frozen=True)
class GCPNetworkEndpointGroupToKubernetesServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPNetworkEndpointGroup)-[:TARGETS]->(:KubernetesService)
class GCPNetworkEndpointGroupToKubernetesServiceRel(CartographyRelSchema):
    """Links a GKE network endpoint group to the service whose pods it holds, as recorded by GKE in the service's `cloud.google.com/neg-status` annotation. Matches NEG IDs built from the GKE cluster's project, the annotation's zones and NEG names, so same-named NEGs in other projects never match. Covers standalone NEGs that a load balancer built outside the cluster routes to, as well as NEGs GKE creates for Ingress and Gateway. Only created for clusters ingested with GKE metadata."""

    target_node_label: str = "GCPNetworkEndpointGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcp_neg_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TARGETS"
    properties: GCPNetworkEndpointGroupToKubernetesServiceRelProperties = (
        GCPNetworkEndpointGroupToKubernetesServiceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesServiceToKubernetesClusterRel(CartographyRelSchema):
    """Links a cluster to one of its services."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesServiceToKubernetesClusterRelProperties = (
        KubernetesServiceToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesServiceToKubernetesNamespaceRel(CartographyRelSchema):
    """Links a namespace to a service it contains."""

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesServiceToKubernetesNamespaceRelProperties = (
        KubernetesServiceToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesPodRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)-[:TARGET]->(:KubernetesPod)
class KubernetesServiceToKubernetesPodRel(CartographyRelSchema):
    """Links a service to a pod it sends traffic to."""

    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "id": PropertyRef("pod_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesServiceToKubernetesPodRelProperties = (
        KubernetesServiceToKubernetesPodRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceSchema(CartographyNodeSchema):
    "A Kubernetes service that exposes a set of pods."

    label: str = "KubernetesService"
    properties: KubernetesServiceNodeProperties = KubernetesServiceNodeProperties()
    sub_resource_relationship: KubernetesServiceToKubernetesClusterRel = (
        KubernetesServiceToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesServiceToKubernetesNamespaceRel(),
            KubernetesServiceToKubernetesPodRel(),
            KubernetesServiceToLoadBalancerV2Rel(),
            KubernetesServiceToGCPForwardingRuleRel(),
            KubernetesServiceToGCPInternalForwardingRuleRel(),
            GCPNetworkEndpointGroupToKubernetesServiceRel(),
        ]
    )
